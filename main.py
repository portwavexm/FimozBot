import discord
from discord.ext import commands
import logging
import sys
import os
import asyncio
from dotenv import load_dotenv

# Ensure log directory exists before configuring logging
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "bot.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    log.error("DISCORD_TOKEN not found in environment variables!")
    sys.exit(1)

# Define bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None  # We'll create custom help
        )
        self.config = {
            "SPOTIFY_CLIENT_ID": os.getenv("SPOTIFY_CLIENT_ID"),
            "SPOTIFY_CLIENT_SECRET": os.getenv("SPOTIFY_CLIENT_SECRET"),
            "LAVALINK_HOST": os.getenv("LAVALINK_HOST", "localhost"),
            "LAVALINK_PORT": int(os.getenv("LAVALINK_PORT", 2333)),
            "LAVALINK_PASSWORD": os.getenv("LAVALINK_PASSWORD"),
            "PLAYLIST_STORE_PATH": os.getenv("PLAYLIST_STORE_PATH", "config/playlists.json"),
        }
        
    async def setup_hook(self):
        """Setup hook called before bot starts."""
        log.info("Loading extensions...")
        await self.load_extension("cogs.music")
        log.info("Music cog loaded.")
        
        # Sync slash commands
        log.info("Syncing slash commands...")
        await self.tree.sync()
        log.info("Slash commands synced.")

    async def on_ready(self):
        """Event triggered when bot is ready."""
        log.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        log.info(f"Connected to {len(self.guilds)} guilds")
        log.info("Bot is ready!")

    async def on_command_error(self, ctx, error):
        """Global error handler for text commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        log.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {str(error)}")

async def main():
    """Main entry point."""
    bot = MusicBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot shutdown by user.")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)