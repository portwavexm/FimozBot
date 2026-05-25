#!/usr/bin/env python3
"""
Launcher script for Discord Music Bot.
This script starts Lavalink and the bot together for one-click launch.
"""
import argparse
import logging
import os
import socket
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

LAVALINK_DIR = "lavalink-server"
BOT_SCRIPT = "main.py"


def get_lavalink_host() -> str:
    return os.getenv("LAVALINK_HOST", "127.0.0.1")


def get_lavalink_port() -> int:
    raw_port = os.getenv("LAVALINK_PORT", "2333")
    try:
        return int(raw_port)
    except (TypeError, ValueError):
        return 2333


def find_java() -> bool:
    try:
        subprocess.run(["java", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def wait_for_lavalink(process: subprocess.Popen, host: str, port: int, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False

        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(1)

    return False


def is_lavalink_running(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def run_lavalink(host: str, port: int) -> tuple[subprocess.Popen | None, bool]:
    if is_lavalink_running(host, port):
        log.info(f"Lavalink is already running on {host}:{port}. Reusing existing instance.")
        return None, True

    lavalink_dir = os.path.abspath(LAVALINK_DIR)
    if not os.path.isdir(lavalink_dir):
        log.error(f"Lavalink directory '{lavalink_dir}' not found!")
        return None, False

    jar_path = os.path.abspath(os.path.join(lavalink_dir, "Lavalink.jar"))
    if not os.path.isfile(jar_path):
        log.error(f"Lavalink.jar not found in '{lavalink_dir}'!")
        log.error("Download it from https://github.com/lavalink-devs/Lavalink/releases")
        return None

    config_path = os.path.abspath(os.path.join(lavalink_dir, "application.yml"))
    if not os.path.isfile(config_path):
        log.error(f"application.yml not found in '{lavalink_dir}'!")
        log.error("Please create it using the Lavalink guide.")
        return None

    log.info("Starting Lavalink server...")
    try:
        process = subprocess.Popen(
            ["java", "-jar", jar_path],
            cwd=lavalink_dir,
            stdout=None,
            stderr=None,
            text=False,
        )

        if not wait_for_lavalink(process, host, port):
            if process.poll() is None:
                log.error("Lavalink did not become ready in time.")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            else:
                log.error("Lavalink exited before becoming ready.")
            return None, False

        log.info(f"Lavalink started successfully on {host}:{port}.")
        return process, False
    except Exception as e:
        log.error(f"Failed to start Lavalink: {e}")
    return None, False


def run_bot() -> int:
    log.info("Starting Discord Music Bot...")
    if not os.path.isfile(BOT_SCRIPT):
        log.error(f"Bot script '{BOT_SCRIPT}' not found.")
        return 1
    try:
        return subprocess.call([sys.executable, BOT_SCRIPT])
    except KeyboardInterrupt:
        log.info("Bot stopped by user.")
        return 0
    except Exception as e:
        log.error(f"Failed to start bot: {e}")
        return 1


def shutdown_process(process: subprocess.Popen) -> None:
    if process and process.poll() is None:
        log.info("Stopping Lavalink...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            log.warning("Lavalink did not stop cleanly, killing...")
            process.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Discord Music Bot and Lavalink together.")
    parser.add_argument("--no-lavalink", action="store_true", help="Run only the bot without starting Lavalink.")
    parser.add_argument("--lavalink-only", action="store_true", help="Start only Lavalink and do not run the bot.")
    parser.add_argument("--playlist-store", default=None, help="Custom path for playlist storage JSON file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lavalink_host = get_lavalink_host()
    lavalink_port = get_lavalink_port()

    log.info("=" * 50)
    log.info("Discord Music Bot Launcher")
    log.info("=" * 50)
    log.info(f"Using Lavalink host={lavalink_host} port={lavalink_port}")

    if args.playlist_store:
        os.environ["PLAYLIST_STORE_PATH"] = args.playlist_store
        log.info(f"Using playlist storage: {args.playlist_store}")

    lavalink_process = None
    lavalink_external = False
    if not args.no_lavalink:
        if not find_java():
            log.error("Java is not installed or not in PATH. Lavalink requires Java 17+.")
            if args.lavalink_only:
                return 1
            log.warning("Continuing without Lavalink — bot may not work correctly.")
        else:
            lavalink_process, lavalink_external = run_lavalink(lavalink_host, lavalink_port)
            if not lavalink_process and not lavalink_external:
                log.warning("Lavalink did not start.")
                if args.lavalink_only:
                    return 1
                log.warning("Continuing without Lavalink — bot may not work correctly.")

    exit_code = 0
    if not args.lavalink_only:
        exit_code = run_bot()

    if lavalink_process:
        shutdown_process(lavalink_process)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
