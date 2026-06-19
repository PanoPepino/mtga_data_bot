import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s) globally")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


async def main():
    async with bot:
        try:
            await bot.load_extension("cogs.cog")
            print("✅ Main cog loaded")
        except Exception as e:
            print(f"❌ Failed to load cogs.cog: {e}")

        try:
            await bot.load_extension("cogs.settings")
            print("✅ Settings cog loaded")
        except Exception as e:
            print(f"❌ Failed to load cogs.settings: {e}")

        try:
            await bot.load_extension("cogs.export")
            print("✅ Export cog loaded")
        except Exception as e:
            print(f"❌ Failed to load cogs.export: {e}")

        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s) globally")
        except Exception as e:
            print(f"❌ Sync failed: {e}")

        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
