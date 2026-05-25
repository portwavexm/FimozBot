import asyncio
import discord
from discord.ext import commands
import wavelink

class DummyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents, help_command=None)

async def main():
    bot = DummyBot()
    async with bot:
        node = wavelink.Node(uri='http://127.0.0.1:2333', password='2765489Sas')
        try:
            await wavelink.Pool.connect(client=bot, nodes=[node])
            print('connected', node.status)
        except Exception as e:
            print('connect failed', type(e).__name__, e)
            raise
        await asyncio.sleep(5)
        await wavelink.Pool.close()

asyncio.run(main())
