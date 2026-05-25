import os
import asyncio
import logging
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("DISCORD_TOKEN not set in environment. Exiting.")
    raise SystemExit(1)

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as: {client.user} (ID: {client.user.id})")
    for g in client.guilds:
        print(f"Guild: {g.name} (ID: {g.id})")
        m = g.get_member(client.user.id)
        if not m:
            try:
                m = await g.fetch_member(client.user.id)
            except Exception as e:
                print(f"  Could not fetch member object: {e}")
                continue
        status = getattr(m, 'status', None)
        activity = getattr(m, 'activity', None)
        print(f"  Member: {m.display_name} | status={status} | activity={activity}")

    await client.close()


def main():
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"Failed to run client: {e}")


if __name__ == '__main__':
    main()
