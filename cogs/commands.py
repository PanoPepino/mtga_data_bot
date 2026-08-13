import discord
from discord import app_commands
from discord.ext import commands

# Guild-aware channel lookup — reads from data/guild_settings.json,
# falls back to config.py if no override is set for this server.
from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_delimiter,
)

from utils.parse_and_check import get_placeholder

from cogs.modals import MetagameModal, LadderModal


class ChallengeView(discord.ui.View):
    """
    Ephemeral control panel shown after /challenge.

    Normal mode:
        - Show/hide the example submission.
        - Open a blank Metagame Challenge modal.

    Retry mode:
        - Show the example in a separate ephemeral message.
        - Reopen the Metagame Challenge modal with the previous
          submission already filled in.
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

        # Change the second button's label when this is a retry view.
        if retry_mode:
            self.log_runs.label = "Edit submission"

    def build_example(self) -> str:
        """
        Build the detailed example using the guild's active
        input style and delimiter.
        """

        if self.input_style == "result_delimiter_deck":
            example_1 = f"2-1{self.delimiter}GB Lands"
            example_2 = f"0-2{self.delimiter}R Stompy"
            example_3 = f"2-0{self.delimiter}UW Control"
            example_4 = f"2-1{self.delimiter}Mono Red"

        elif self.input_style == "deck_delimiter_result":
            example_1 = f"GB Lands{self.delimiter}2-1"
            example_2 = f"R Stompy{self.delimiter}0-2"
            example_3 = f"UW Control{self.delimiter}2-0"
            example_4 = f"Mono Red{self.delimiter}2-1"

        else:
            example_1 = f"GB Lands{self.delimiter}2-1"
            example_2 = f"R Stompy{self.delimiter}0-2"
            example_3 = f"UW Control{self.delimiter}2-0"
            example_4 = f"Mono Red{self.delimiter}2-1"

        return (
            "**Example submission**\n\n"
            "Each run starts with `Run N:`.\n"
            "Enter one match per line.\n"
            "The final run result is calculated automatically.\n\n"
            "```text\n"
            "Run 1:\n"
            f"{example_1}\n"
            f"{example_2}\n"
            f"{example_3}\n"
            f"{example_4}\n"
            "\n"
            "Run 2:\n"
            f"{example_1}\n"
            f"{example_3}\n"
            f"{example_2}\n"
            "```\n\n"
            "**Important:**\n"
            "• Keep the `Run 1:`, `Run 2:`, etc. headers.\n"
            "• Use one match per line.\n"
            "• Do not enter the final run result."
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
        Show/hide the example.

        In retry mode, the example is sent as a NEW ephemeral
        message. This is important because the original error
        message contains the user's failed input and must remain
        untouched.
        """

        if self.retry_mode:
            await interaction.response.send_message(
                self.build_example(),
                ephemeral=True,
            )
            return

        # Normal /challenge mode:
        # toggle the example in the original message.

        self.example_visible = not self.example_visible

        if self.example_visible:
            content = self.build_example()
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
        Open the Metagame Challenge modal.

        Normal mode:
            Open a blank modal.

        Retry mode:
            Reopen the modal with the previous submission
            already filled in.
        """

        await interaction.response.send_modal(
            MetagameModal(
                input_style=self.input_style,
                delimiter=self.delimiter,
                previous_deck=self.previous_deck,
                previous_runs=self.previous_runs,
                previous_comments=self.previous_comments,
            )
        )


class MTGADataBot(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="challenge",
        description="Log your Metagame Challenge Run(s)",
    )
    async def cmd_challenge(
        self,
        interaction: discord.Interaction,
    ):
        # /challenge must be used inside a server.
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command must be used in a server.",
                ephemeral=True,
            )
            return

        # Look up the allowed channel for this specific server.
        # Returns None if no restriction is configured.
        allowed = get_effective_allowed_channel(
            interaction.guild.id,
            "challenge",
        )

        if allowed is not None and interaction.channel_id != allowed:
            channel = interaction.guild.get_channel(allowed)
            mention = channel.mention if channel else f"<#{allowed}>"

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
        # Same pattern as /challenge — guild-specific
        # channel restriction.
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

        if allowed is not None and interaction.channel_id != allowed:
            channel = interaction.guild.get_channel(allowed)
            mention = channel.mention if channel else f"<#{allowed}>"

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


async def setup(bot: commands.Bot):
    await bot.add_cog(MTGADataBot(bot))