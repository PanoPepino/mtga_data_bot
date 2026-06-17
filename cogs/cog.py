
import discord
from discord import app_commands
from discord.ext import commands
from config import CHALLENGE_CHANNEL_ID, LADDER_CHANNEL_ID
from cogs.modals import MetagameModal, LadderModal


class MTGADataBot(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="challenge", description="Log your Metagame Challenge Run(s)")
    async def cmd_challenge(self, interaction: discord.Interaction):
        if interaction.channel_id != CHALLENGE_CHANNEL_ID:
            await interaction.response.send_message("❌ Wrong Channel ❌", ephemeral=True)
            return
        await interaction.response.send_modal(MetagameModal())

    @app_commands.command(name="ladder", description="Log your Ladder Run")
    async def cmd_ladder(self, interaction: discord.Interaction):
        if interaction.channel_id != LADDER_CHANNEL_ID:
            await interaction.response.send_message("❌ Wrong Channel ❌", ephemeral=True)
            return
        await interaction.response.send_modal(LadderModal())


async def setup(bot: commands.Bot):
    await bot.add_cog(MTGADataBot(bot))
