"""Gameplay commands cog — /challenge and /ladder.

Handles the Discord commands for logging Metagame Challenge and
Ladder data.

 /challenge shows an ephemeral control panel first:
    - Show example
    - Log your runs

The MetagameModal is opened only after the user clicks
"Log your runs".
"""

import time

import discord
from discord import app_commands
from discord.ext import commands

from config import COMMAND_COOLDOWN

from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_delimiter,
)

from cogs.modals import MetagameModal, LadderModal


class ChallengeView(discord.ui.View):
    """
    Ephemeral control panel for /challenge.

    Normal mode:
        - Show example
        - Log your runs

    Retry mode:
        - Show example
        - Edit submission

    Retry mode preserves the user's failed submission.
    """

    def __init__(
        self,
        input_style: str,
        delimiter: str,
        previous_deck: str = None,
        previous_runs: str = None,
        previous_comments: str = None,
        retry_mode: bool = False,
    ):
        super().__init__(timeout=300)

        self.input_style = input_style
        self.delimiter = delimiter

        self.previous_deck = previous_deck
        self.previous_runs = previous_runs
        self.previous_comments = previous_comments

        self.retry_mode = retry_mode
        self.example_visible = False

        if retry_mode:
            self.log_runs.label = "Edit submission"

    def create_retry_view(
        self,
        input_style: str,
        delimiter: str,
        previous_deck: str,
        previous_runs: str,
        previous_comments: str,
    ):
        """
        Factory used by MetagameModal after validation fails.

        This avoids a circular import between gameplay.py and modals.py.
        """

        return ChallengeView(
            input_style=input_style,
            delimiter=delimiter,
            previous_deck=previous_deck,
            previous_runs=previous_runs,
            previous_comments=previous_comments,
            retry_mode=True,
        )

    def _example_text(self) -> str:
        """
        Detailed example explaining the complete submission format.
        """

        if self.input_style == "deck_delimiter_result":
            match_1 = f"GB Lands{self.delimiter}2-1"
            match_2 = f"R Stompy{self.delimiter}2-0"
            match_3 = f"UW Control{self.delimiter}2-1"
            match_4 = f"Mono Red{self.delimiter}1-2"

        elif self.input_style == "result_delimiter_deck":
            match_1 = f"2-1{self.delimiter}GB Lands"
            match_2 = f"0-2{self.delimiter}R Stompy"
            match_3 = f"2-0{self.delimiter}UW Control"
            match_4 = f"2-1{self.delimiter}Mono Red"

        else:
            match_1 = f"GB Lands{self.delimiter}2-1"
            match_2 = f"R Stompy{self.delimiter}2-0"
            match_3 = f"UW Control{self.delimiter}2-1"
            match_4 = f"Mono Red{self.delimiter}1-2"

        return (
            "**Example submission**\n\n"
            "• Each run starts with `Run N:`\n"
            "• Enter one match per line\n"
            "• The run result is calculated automatically\n"
            "• Do not enter the final run score/result\n\n"
            "```text\n"
            "Run 1:\n"
            f"{match_1}\n"
            f"{match_2}\n"
            f"{match_3}\n"
            f"{match_4}\n"
            "\n"
            "Run 2:\n"
            f"{match_1}\n"
            f"{match_3}\n"
            f"{match_4}\n"
            "```\n\n"
            "**Important:**\n"
            "• Use exactly one match per line.\n"
            "• Keep the Run headers.\n"
            "• Use the configured delimiter/order."
        )

    @discord.ui.button(
        label="Show example",
        style=discord.ButtonStyle.secondary,
    )
    async def show_example(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        """
        Show the example.

        In retry mode, send a new message so the failed
        submission remains visible.
        """

        if self.retry_mode:
            await interaction.response.send_message(
                self._example_text(),
                ephemeral=True,
            )
            return

        self.example_visible = not self.example_visible

        if self.example_visible:
            content = self._example_text()
            button.label = "Hide example"

        else:
            content = (
                "Enter your Metagame Challenge run(s).\n\n"
                "Click **Show example** if you need to check the format."
            )
            button.label = "Show example"

        await interaction.response.edit_message(
            content=content,
            view=self,
        )

    @discord.ui.button(
        label="Log your runs",
        style=discord.ButtonStyle.primary,
    )
    async def log_runs(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        """
        Open MetagameModal.

        If this is a retry, restore previous values.
        """

        await interaction.response.send_modal(
    MetagameModal(
        input_style=self.input_style,
        delimiter=self.delimiter,
        retry_view_factory=self.create_retry_view,
    )
)
        


class MTGADataBot(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        self._cooldowns = {
            "challenge": {},
            "ladder": {},
        }

    async def _check_and_set_cooldown(
        self,
        interaction: discord.Interaction,
        key: str,
        command_name: str,
    ) -> bool:

        now = time.time()
        user_id = interaction.user.id

        last = self._cooldowns[key].get(user_id)

        if last is not None:
            elapsed = now - last

            if elapsed < COMMAND_COOLDOWN:

                remaining = int(
                    COMMAND_COOLDOWN - elapsed
                )

                await interaction.response.send_message(
                    f"⏳ Take it easy, Fittipaldi! "
                    f"Use /{command_name} again in {remaining}s.",
                    ephemeral=True,
                )

                return False

        self._cooldowns[key][user_id] = now

        return True

    @app_commands.command(
        name="challenge",
        description="Log your Metagame Challenge Run(s)",
    )
    async def cmd_challenge(
        self,
        interaction: discord.Interaction,
    ):

        ok = await self._check_and_set_cooldown(
            interaction,
            "challenge",
            "challenge",
        )

        if not ok:
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command must be used in a server.",
                ephemeral=True,
            )
            return

        allowed = get_effective_allowed_channel(
            interaction.guild.id,
            "challenge",
        )

        if (
            allowed is not None
            and interaction.channel_id != allowed
        ):
            channel = interaction.guild.get_channel(
                allowed
            )

            mention = (
                channel.mention
                if channel
                else f"<#{allowed}>"
            )

            await interaction.response.send_message(
                f"❌ Use this command in {mention}",
                ephemeral=True,
            )

            return

        input_style = get_effective_input_style(
            interaction.guild.id
        )

        delimiter = get_effective_delimiter(
            interaction.guild.id
        )

        view = ChallengeView(
            input_style=input_style,
            delimiter=delimiter,
        )

        await interaction.response.send_message(
            "Enter your Metagame Challenge run(s).\n\n"
            "Click **Show example** if you need to check the format.",
            view=view,
            ephemeral=True,
        )

    @app_commands.command(
        name="ladder",
        description="Log your Ladder Run",
    )
    async def cmd_ladder(
        self,
        interaction: discord.Interaction,
    ):

        ok = await self._check_and_set_cooldown(
            interaction,
            "ladder",
            "ladder",
        )

        if not ok:
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command must be used in a server.",
                ephemeral=True,
            )
            return

        allowed = get_effective_allowed_channel(
            interaction.guild.id,
            "ladder",
        )

        if (
            allowed is not None
            and interaction.channel_id != allowed
        ):
            channel = interaction.guild.get_channel(
                allowed
            )

            mention = (
                channel.mention
                if channel
                else f"<#{allowed}>"
            )

            await interaction.response.send_message(
                f"❌ Use this command in {mention}",
                ephemeral=True,
            )

            return

        input_style = get_effective_input_style(
            interaction.guild.id
        )

        delimiter = get_effective_delimiter(
            interaction.guild.id
        )

        await interaction.response.send_modal(
            LadderModal(
                input_style=input_style,
                delimiter=delimiter,
            )
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        MTGADataBot(bot)
    )