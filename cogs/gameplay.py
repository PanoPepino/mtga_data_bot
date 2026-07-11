"""Gameplay commands cog — /challenge and /ladder.

This is a renamed copy of cogs/cog.py. All imports now point to services.storage
instead of cogs.storage, keeping Discord UI concerns separate from storage logic.
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_delimiter,
)

from cogs.modals import MetagameModal, LadderModal


class MTGADataBot(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="challenge", description="Log your Metagame Challenge Run(s)")
    async def cmd_challenge(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command must be used in a server.",
                ephemeral=True,
            )
            return

        allowed = get_effective_allowed_channel(interaction.guild.id, "challenge")
        if allowed is not None and interaction.channel_id != allowed:
            channel = interaction.guild.get_channel(allowed)
            mention = channel.mention if channel else f"<#{allowed}>"
            await interaction.response.send_message(
                f"\u274c Use this command in {mention}",
                ephemeral=True,
            )
            return

        input_style = get_effective_input_style(interaction.guild.id)
        delimiter = get_effective_delimiter(interaction.guild.id)
        await interaction.response.send_modal(
            MetagameModal(input_style=input_style, delimiter=delimiter)
        )

    @app_commands.command(name="ladder", description="Log your Ladder Run")
    async def cmd_ladder(self, interaction: discord.Interaction):
        allowed = get_effective_allowed_channel(interaction.guild.id, "ladder")
        if allowed is not None and interaction.channel_id != allowed:
            channel = interaction.guild.get_channel(allowed)
            mention = channel.mention if channel else f"<#{allowed}>"
            await interaction.response.send_message(
                f"\u274c Use this command in {mention}", ephemeral=True
            )
            return

        input_style = get_effective_input_style(interaction.guild.id)
        delimiter = get_effective_delimiter(interaction.guild.id)
        await interaction.response.send_modal(
            LadderModal(input_style=input_style, delimiter=delimiter)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(MTGADataBot(bot))
