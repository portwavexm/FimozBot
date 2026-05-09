#!/usr/bin/env python3
"""
Launcher script for Discord Music Bot.
This script helps start both Lavalink and the bot.
"""
import subprocess
import sys
import os
import time
import signal
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def run_lavalink():
    """Run Lavalink server."""
    lavalink_dir = "lavalink-server"
    if not os.path.exists(lavalink_dir):
        log.error(f"Lavalink directory '{lavalink_dir}' not found!")
        return None
    
    # Check if Lavalink.jar exists
    jar_path = os.path.join(lavalink_dir, "Lavalink.jar")
    if not os.path.exists(jar_path):
        log.error(f"Lavalink.jar not found in '{lavalink_dir}'!")
        log.error("Please download it from https://github.com/lavalink-devs/Lavalink/releases")
        return None
    
    # Check for application.yml
    config_path = os.path.join(lavalink_dir, "application.yml")
    if not os.path.exists(config_path):
        log.error(f"application.yml not found in '{lavalink_dir}'!")
        log.error("Please create it following the guide.")
        return None
    
    log.info("Starting Lavalink server...")
    try:
        # Start Lavalink process
        process = subprocess.Popen(
            ["java", "-jar", "Lavalink.jar"],
            cwd=lavalink_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(5)
        if process.poll() is None:
            log.info("Lavalink started successfully!")
            return process
        else:
            stderr = process.stderr.read()
            log.error(f"Lavalink failed to start: {stderr}")
            return None
    except Exception as e:
        log.error(f"Failed to start Lavalink: {e}")
        return None

def run_bot():
    """Run the bot."""
    log.info("Starting Discord Music Bot...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Bot exited with error: {e}")
    except KeyboardInterrupt:
        log.info("Bot stopped by user.")

def main():
    """Main launcher."""
    log.info("=" * 50)
    log.info("Discord Music Bot Launcher")
    log.info("=" * 50)
    
    # Check Java availability
    try:
        subprocess.run(["java", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.error("Java is not installed or not in PATH. Lavalink requires Java 17+.")
        sys.exit(1)
    
    # Start Lavalink in separate thread
    lavalink_process = run_lavalink()
    if not lavalink_process:
        log.warning("Failed to start Lavalink. The bot will not function properly.")
        proceed = input("Continue anyway? (y/N): ")
        if proceed.lower() != 'y':
            sys.exit(1)
    else:
        log.info("Lavalink is running in background.")
    
    # Run bot
    run_bot()
    
    # Cleanup
    if lavalink_process:
        log.info("Shutting down Lavalink...")
        lavalink_process.terminate()
        lavalink_process.wait(timeout=10)
        log.info("Lavalink stopped.")

if __name__ == "__main__":
    main()