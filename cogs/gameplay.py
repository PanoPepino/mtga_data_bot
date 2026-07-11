"""Gameplay commands cog — /challenge and /ladder."""

import discord
from discord import app_commands
from discord.ext import commands

import asyncio
from utils.audit import send_audit_log

from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_delimiter,
)

from config import GUILD_ACTIVE_LIMIT, USER_SUBMIT_COOLDOWN

from cogs.modals import MetagameModal, LadderModal

# Per-guild active command limit (How many people can use the bot exactly same time)


# Track active work per guild
_guild_semaphores: dict[int, asyncio.Semaphore] = {}

def get_guild_semaphore(guild_id: int) -> asyncio.Semaphore:
    # Create one semaphore per guild
    if guild_id not in _guild_semaphores:
        _guild_semaphores[guild_id] = asyncio.Semaphore(GUILD_ACTIVE_LIMIT)
    return _guild_semaphores[guild_id]


# Check whether command is used in allowed channel for this mode
async def ensure_allowed_channel(
    interaction: discord.Interaction,
    mode: str,
) -> bool:
    # Commands must run inside a server
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command must be used in a server.",
            ephemeral=True,
        )
        return False

    # Read configured channel for this mode
    allowed = get_effective_allowed_channel(interaction.guild.id, mode)

    # If no channel is configured, allow command anywhere in server
    if allowed is None:
        return True

    # If used in wrong channel, stop and redirect user
    if interaction.channel_id != allowed:
        channel = interaction.guild.get_channel(allowed)
        mention = channel.mention if channel else f"<#{allowed}>"
        await interaction.response.send_message(
            f"Use this command in {mention}.",
            ephemeral=True,
        )
        return False

    return True


class MTGADataBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="challenge", description="Log your Metagame Challenge Run(s)")
    @app_commands.checks.cooldown(1, USER_SUBMIT_COOLDOWN, key=lambda i: (i.guild_id, i.user.id))
    async def cmd_challenge(self, interaction: discord.Interaction):
        # Enforce per-mode channel restriction
        if not await ensure_allowed_channel(interaction, "challenge"):
            return

        guild_id = interaction.guild.id
        semaphore = get_guild_semaphore(guild_id)

        # Refuse if too many active requests already running in this guild
        if semaphore.locked():
            await interaction.response.send_message(
                "Too many users using bot right now. Try again in few seconds.",
                ephemeral=True,
            )
            return

        async with semaphore:
            # Load parsing settings for this server
            input_style = get_effective_input_style(interaction.guild.id)
            delimiter = get_effective_delimiter(interaction.guild.id)

            # Open modal for challenge data entry
            await interaction.response.send_modal(
                MetagameModal(input_style=input_style, delimiter=delimiter)
            )

    @app_commands.command(name="ladder", description="Log your Ladder Run")
    @app_commands.checks.cooldown(1, USER_SUBMIT_COOLDOWN, key=lambda i: (i.guild_id, i.user.id))
    async def cmd_ladder(self, interaction: discord.Interaction):
        # Enforce per-mode channel restriction
        if not await ensure_allowed_channel(interaction, "ladder"):
            return

        guild_id = interaction.guild.id
        semaphore = get_guild_semaphore(guild_id)

        # Refuse if too many active requests already running in this guild
        if semaphore.locked():
            await interaction.response.send_message(
                "Too many users using bot right now. Try again in few seconds.",
                ephemeral=True,
            )
            return

        async with semaphore:
            # Load parsing settings for this server
            input_style = get_effective_input_style(interaction.guild.id)
            delimiter = get_effective_delimiter(interaction.guild.id)

            # Open modal for ladder data entry
            await interaction.response.send_modal(
                LadderModal(input_style=input_style, delimiter=delimiter)
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(MTGADataBot(bot))