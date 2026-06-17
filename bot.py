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


@bot.event
async def on_interaction(interaction: discord.Interaction):
    print(f"[DEBUG] Interaction: type={interaction.type} user={interaction.user}")


async def main():
    async with bot:
        try:
            await bot.load_extension("cogs.cog")
            print("✅ Cog loaded")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
