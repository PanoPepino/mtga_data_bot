import os
import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from config import ALLOWED_GUILD_IDS
from utils.audit import send_audit_log

load_dotenv()

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

SYNC_MODE = os.getenv("COMMAND_SYNC_MODE", "global").lower()
GUILD_ID_RAW = os.getenv("DISCORD_GUILD_ID")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def guild_allowed(guild) -> bool:
    if guild is None:
        return False
    if not ALLOWED_GUILD_IDS:
        return False
    return guild.id in ALLOWED_GUILD_IDS


@bot.check
async def global_guild_check(ctx):
    allowed = await guild_allowed(ctx.guild)
    if not allowed:
        guild_id = ctx.guild.id if ctx.guild else "none"
        await send_audit_log(
            f"[DENIED] guild={guild_id} user={ctx.author.id} action=prefix_guild_block command={ctx.command}"
        )
    return allowed


@bot.tree.interaction_check
async def interaction_guild_check(interaction):
    allowed = await guild_allowed(interaction.guild)
    if not allowed:
        guild_id = interaction.guild.id if interaction.guild else "none"
        command_name = interaction.command.name if interaction.command else "unknown"
        await send_audit_log(
            f"[DENIED] guild={guild_id} user={interaction.user.id} action=slash_guild_block command={command_name}"
        )
    return allowed


@bot.event
async def on_guild_join(guild):
    if not await guild_allowed(guild):
        await send_audit_log(
            f"[SECURITY] guild={guild.id} action=auto_leave reason=not_whitelisted"
        )
        await guild.leave()


async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    command_name = interaction.command.name if interaction.command else "unknown"
    guild_id = interaction.guild.id if interaction.guild else "none"
    user_id = interaction.user.id if interaction.user else "none"

    if isinstance(error, app_commands.CheckFailure):
        await send_audit_log(
            f"[DENIED] guild={guild_id} user={user_id} action=slash_check_failure command={command_name}"
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Not allowed.", ephemeral=True)
            else:
                await interaction.response.send_message("Not allowed.", ephemeral=True)
        except Exception:
            pass
        return

    if isinstance(error, app_commands.CommandOnCooldown):
        retry_after = max(1, int(error.retry_after))
        message = f"Cooldown active. Try again in {retry_after}s."

        await send_audit_log(
            f"[RATE_LIMIT] guild={guild_id} user={user_id} action=slash_cooldown command={command_name} retry_after={retry_after}"
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception:
            pass
        return

    LOGGER.exception("Slash command failed", exc_info=error)

    await send_audit_log(
        f"[ERROR] guild={guild_id} user={user_id} action=slash_error command={command_name} error_type={type(error).__name__}"
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send("Something failed.", ephemeral=True)
        else:
            await interaction.response.send_message("Something failed.", ephemeral=True)
    except Exception:
        pass


bot.tree.on_error = on_tree_error


@bot.event
async def on_command_error(ctx, error):
    command_name = ctx.command.qualified_name if ctx.command else "unknown"
    guild_id = ctx.guild.id if ctx.guild else "none"

    if isinstance(error, commands.CheckFailure):
        await send_audit_log(
            f"[DENIED] guild={guild_id} user={ctx.author.id} action=prefix_check_failure command={command_name}"
        )
        await ctx.reply("Not allowed.", mention_author=False)
        return

    LOGGER.exception("Prefix command failed", exc_info=error)

    await send_audit_log(
        f"[ERROR] guild={guild_id} user={ctx.author.id} action=prefix_error command={command_name} error_type={type(error).__name__}"
    )

    await ctx.reply("Something failed.", mention_author=False)


@bot.event
async def on_ready():
    LOGGER.info(f"Logged in as {bot.user}")

    try:
        if SYNC_MODE == "guild":
            if not GUILD_ID_RAW:
                raise RuntimeError(
                    "DISCORD_GUILD_ID must be set when COMMAND_SYNC_MODE=guild"
                )

            guild = discord.Object(id=int(GUILD_ID_RAW))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            LOGGER.info(f"Synced {len(synced)} command(s) to guild {GUILD_ID_RAW} (dev mode)")

            await send_audit_log(
                f"[STARTUP] bot={bot.user} action=sync_success mode=guild guild={GUILD_ID_RAW} commands={len(synced)}"
            )
        else:
            synced = await bot.tree.sync()
            LOGGER.info(f"Synced {len(synced)} command(s) globally (production mode)")

            await send_audit_log(
                f"[STARTUP] bot={bot.user} action=sync_success mode=global commands={len(synced)}"
            )

    except Exception as error:
        LOGGER.exception("Command sync failed", exc_info=error)

        await send_audit_log(
            f"[ERROR] action=sync_failed mode={SYNC_MODE} error_type={type(error).__name__}"
        )


async def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing from .env or environment")

    async with bot:
        for extension, label in [
            ("cogs.gameplay", "Gameplay cog"),
            ("cogs.settings", "Settings cog"),
            ("cogs.export", "Export cog"),
        ]:
            try:
                await bot.load_extension(extension)
                LOGGER.info(f"{label} loaded")
            except Exception as error:
                LOGGER.exception(f"Failed to load {extension}", exc_info=error)
                await send_audit_log(
                    f"[ERROR] action=cog_load_failed extension={extension} error_type={type(error).__name__}"
                )

        await bot.start(DISCORD_TOKEN)


asyncio.run(main())