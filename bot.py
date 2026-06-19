import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Sync mode
#
#   COMMAND_SYNC_MODE=guild   → sync immediately to one test server (dev)
#   COMMAND_SYNC_MODE=global  → sync globally (production / cloud host)
#
# Set DISCORD_GUILD_ID in .env when using guild mode.
# ---------------------------------------------------------------------------
SYNC_MODE = os.getenv("COMMAND_SYNC_MODE", "global").lower()
GUILD_ID_RAW = os.getenv("DISCORD_GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # application_id is guaranteed to exist here — safe to sync.
    print(f"Logged in as {bot.user}")
    try:
        if SYNC_MODE == "guild":
            if not GUILD_ID_RAW:
                raise RuntimeError(
                    "DISCORD_GUILD_ID must be set in .env when "
                    "COMMAND_SYNC_MODE=guild"
                )
            guild = discord.Object(id=int(GUILD_ID_RAW))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID_RAW} (dev mode)")
        else:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s) globally (production mode)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


async def main():
    async with bot:
        # Load all cogs before connecting — sync happens in on_ready()
        for extension, label in [
            ("cogs.cog",      "Main cog"),
            ("cogs.settings", "Settings cog"),
            ("cogs.export",   "Export cog"),
        ]:
            try:
                await bot.load_extension(extension)
                print(f"✅ {label} loaded")
            except Exception as e:
                print(f"❌ Failed to load {extension}: {e}")

        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
