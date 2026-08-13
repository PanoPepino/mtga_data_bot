import discord
import asyncio

from config import (
    MAX_COMMENT_LENGTH,
    MAX_DECK_LENGTH,
    MAX_MATCHES_LENGTH,
    COLOR_NORMAL,
    MAX_CONCURRENT_SESSIONS,
)

from cogs.embedding import build_embedding, build_ladder_description

from utils.parse_and_check import (
    parse_runs,
    summarise_run_record,
    validate_runs_metagame,
    validate_run_ladder,
    parse_match_line,
    get_placeholder,
)

from utils.guild_settings import (
    get_effective_input_style,
    get_effective_delimiter,
    get_effective_save_directory,
    get_effective_challenge_file,
    get_effective_ladder_file,
)

from services.storage import save_metagame_match, save_ladder_match


_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_SESSIONS)


class MetagameModal(
    discord.ui.Modal,
    title="Log your Metagame Challenge Run(s)",
):
    """
    Single modal that collects ALL Metagame runs.

    Can optionally reopen with previous failed input.
    """

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Izzet Tempo (avoid long names)",
        max_length=MAX_DECK_LENGTH,
        required=True,
    )

    runs_input = discord.ui.TextInput(
        label="Your runs",
        style=discord.TextStyle.paragraph,
        placeholder="Run 1:\nGB Lands | 2-1\nR Stompy | 0-2",
        max_length=4000,
        required=True,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any notes/comments about your run(s)?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    def __init__(
        self,
        input_style: str,
        delimiter: str,
        previous_deck: str = None,
        previous_runs: str = None,
        previous_comments: str = None,
        retry_view_factory=None,
    ):
        super().__init__()

        self.input_style = input_style
        self.delimiter = delimiter

        self.retry_view_factory = retry_view_factory

        # Short input hint only.
        if input_style == "result_delimiter_deck":
            example_1 = f"2-1{delimiter}GB Lands"
            example_2 = f"0-2{delimiter}R Stompy"
            example_3 = f"1-2{delimiter}UR Tempo"

        else:
            example_1 = f"GB Lands{delimiter}2-1"
            example_2 = f"R Stompy{delimiter}0-2"
            example_3 = f"UR Tempo{delimiter}1-2"

        self.runs_input.placeholder = (
            "Run 1:\n"
            f"{example_1}\n"
            f"{example_2}\n"
            f"{example_3}"
        )[:100]

        # Restore failed submission.
        if previous_deck is not None:
            self.pilot_deck.default = previous_deck

        if previous_runs is not None:
            self.runs_input.default = previous_runs

        if previous_comments is not None:
            self.comments.default = previous_comments


    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        async with _SEMAPHORE:

            guild_id = interaction.guild_id

            input_style = get_effective_input_style(guild_id)
            delimiter = get_effective_delimiter(guild_id)

            save_dir = get_effective_save_directory(guild_id)
            challenge_file = get_effective_challenge_file(guild_id)

            runs_text = self.runs_input.value

            runs = parse_runs(
                runs_text,
                input_style,
                delimiter,
            )

            errors = validate_runs_metagame(
                runs,
                runs_text,
                input_style,
            )

            if errors:

                view = None

                if self.retry_view_factory:
                    view = self.retry_view_factory(
                        input_style=input_style,
                        delimiter=delimiter,
                        previous_deck=self.pilot_deck.value,
                        previous_runs=runs_text,
                        previous_comments=self.comments.value,
                    )

                msg = (
                    "❌ I found problems in your Metagame "
                    "Challenge submission.\n\n"
                    "Your input:\n"
                    "```text\n"
                    f"{runs_text}\n"
                    "```\n\n"
                    "Please correct the input and submit again."
                )

                await interaction.response.send_message(
                    msg,
                    view=view,
                    ephemeral=True,
                )

                return


            session_runs = []

            for i, run in enumerate(runs):

                if input_style == "deck_delimiter_result":

                    matches_text = "\n".join(
                        f"{oppo_deck}{delimiter}{result}"
                        for oppo_deck, result in run
                    )

                else:

                    matches_text = "\n".join(
                        f"{result}{delimiter}{oppo_deck}"
                        for oppo_deck, result in run
                    )

                session_runs.append(
                    {
                        "matches": matches_text,
                        "comments": (
                            self.comments.value
                            if i == len(runs)-1
                            else ""
                        ),
                    }
                )


            user_name = interaction.user.display_name
            user_deck = self.pilot_deck.value
            user_comment = self.comments.value


            for run in runs:

                run_result = summarise_run_record(run)

                for oppo_deck, result in run:

                    await save_metagame_match(
                        user_name=user_name,
                        user_deck=user_deck,
                        run_result=run_result,
                        oppo_deck=oppo_deck,
                        result=result,
                        comments=user_comment,
                        save_dir=save_dir,
                        file_name=challenge_file,
                    )


            embed = build_embedding(
                interaction.user,
                self.pilot_deck.value,
                session_runs,
                input_style=input_style,
                delimiter=delimiter,
            )


            await interaction.response.send_message(
                f"✅ {len(runs)} run(s) logged!",
                ephemeral=True,
            )

            await interaction.followup.send(
                embed=embed
            )



class LadderModal(
    discord.ui.Modal,
    title="Log your Ladder run",
):

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Blue Cope",
        max_length=MAX_DECK_LENGTH,
        required=True,
    )


    matches = discord.ui.TextInput(
        label="Your matches",
        style=discord.TextStyle.paragraph,
        placeholder="One match per line...",
        max_length=4000,
        required=True,
    )


    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any notes about your run?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )


    def __init__(
        self,
        input_style: str,
        delimiter: str,
    ):
        super().__init__()

        self.input_style = input_style
        self.delimiter = delimiter

        self.matches.placeholder = (
            f"{get_placeholder(input_style, delimiter)}"
        )[:100]


    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        async with _SEMAPHORE:

            guild_id = interaction.guild_id

            input_style = get_effective_input_style(guild_id)
            delimiter = get_effective_delimiter(guild_id)

            save_dir = get_effective_save_directory(guild_id)
            ladder_file = get_effective_ladder_file(guild_id)

            matches_text = self.matches.value


            errors = validate_run_ladder(
                matches_text,
                input_style,
                delimiter,
            )

            if errors:

                await interaction.response.send_message(
                    "❌ I found problems in your ladder submission.\n\n"
                    "Your input:\n"
                    "```text\n"
                    f"{matches_text}\n"
                    "```\n\n"
                    "Please correct the input and submit again.",
                    ephemeral=True,
                )

                return


            desc = build_ladder_description(
                self.pilot_deck.value,
                matches_text,
                self.comments.value,
            )


            embed = discord.Embed(
                description=desc,
                color=COLOR_NORMAL,
            )


            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )


            for line in matches_text.strip().splitlines():

                parsed = parse_match_line(
                    line.strip(),
                    input_style,
                    delimiter,
                )

                if parsed is None:
                    continue

                oppo_deck, result = parsed


                await save_ladder_match(
                    user_name=interaction.user.display_name,
                    user_deck=self.pilot_deck.value,
                    oppo_deck=oppo_deck,
                    result=result,
                    comments=self.comments.value,
                    save_dir=save_dir,
                    file_name=ladder_file,
                )


            await interaction.response.send_message(
                content="✅ Ladder run logged (private).",
                embed=embed,
                ephemeral=True,
            )