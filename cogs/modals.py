import discord

from cogs.embedding import build_embedding, build_ladder_description
from cogs.utils import (
    parse_runs,
    validate_runs_metagame,
    validate_run_ladder,
    parse_match_line,
    get_placeholder)

from config import (
    DELIMITER,
    MAX_COMMENT_LENGTH,
    MAX_DECK_LENGTH,
    MAX_MATCHES_LENGTH,
    COLOR_NORMAL,
    INPUT_STYLE)

from cogs.storage import save_metagame_match, save_ladder_match


class MetagameModal(discord.ui.Modal, title="Log your Metagame Challenge Run(s)"):
    """
    Single modal that collects ALL Metagame runs for a given deck at once.
    The player separates runs with 'Run N:' headers.
    """

    # The deck the player piloted
    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Izzet Tempo (avoid long names)",
        max_length=MAX_DECK_LENGTH,
    )

    # All runs in one box — player uses Run 1: / Run 2: headers
    runs_input = discord.ui.TextInput(
        label="Your runs  (Run N: then matches)",
        style=discord.TextStyle.paragraph,
        placeholder=f"Run 1:\n{get_placeholder(INPUT_STYLE)}\n\nRun 2:\n{get_placeholder(INPUT_STYLE)}",
        max_length=MAX_MATCHES_LENGTH,
    )

    # Optional comments for the whole session
    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any notes about your run(s)?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):

        # parse_runs splits the text into a list of runs,
        # each run being a list of (opponent, result) tuples
        runs = parse_runs(self.runs_input.value, INPUT_STYLE)

        # Check formatting before submission
        # If not valid, do not post and tell user with a private message
        errors = validate_runs_metagame(runs, self.runs_input.value, INPUT_STYLE)
        if errors:
            msg = (
                "\u274c I cannot parse your runs \u274c\n"
                "Required format:\n"
                f"```Run 1:\n{get_placeholder(INPUT_STYLE)}\netc.\n\n"
                f"Run 2:\n{get_placeholder(INPUT_STYLE)}"
                "```"
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # If everything ok, private message with validation of submission
        await interaction.response.send_message(
            f"\u2705 {len(runs)} run(s) logged!", ephemeral=True
        )

        # Convert introduced data to dictionaries for easy storage and posting
        session_runs = []
        for i, run in enumerate(runs):
            # Reconstruct match text from parsed tuples for display depending on the input style
            if INPUT_STYLE == "deck_delimiter_result":
                matches_text = "\n".join(
                    f"{oppo_deck}{DELIMITER}{result}" for oppo_deck, result in run
                )
            elif INPUT_STYLE == "result_delimiter_deck":
                matches_text = "\n".join(
                    f"{result}{DELIMITER}{oppo_deck}" for oppo_deck, result in run
                )
            else:
                # Safe fallback — deck first
                matches_text = "\n".join(
                    f"{oppo_deck}{DELIMITER}{result}" for oppo_deck, result in run
                )

            session_runs.append(
                {
                    "matches": matches_text,
                    "comments": self.comments.value if i == len(runs) - 1 else "",
                }
            )

        # Save data to database
        user_name = interaction.user.display_name
        user_deck = self.pilot_deck.value
        user_comment = self.comments.value
        for run in runs:
            for oppo_deck, result in run:  # Each new row is a new row in database
                save_metagame_match(
                    user_name=user_name,
                    user_deck=user_deck,
                    oppo_deck=oppo_deck,
                    result=result,
                    comments=user_comment,
                )

        # The bot will post it
        embed = build_embedding(interaction.user, self.pilot_deck.value, session_runs)
        await interaction.followup.send(embed=embed)


class LadderModal(discord.ui.Modal, title="Log your Ladder run"):
    """
    Class that operates in same terms as :class:`MetagameModal`, but allows user to upload a given run with any deck.
    Could be useful to extract data from the ladder and get better insights to establish tier lists.
    """

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Blue Cope",
        max_length=MAX_DECK_LENGTH,
    )

    matches = discord.ui.TextInput(
        label="Matches (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder=f"{get_placeholder(INPUT_STYLE)}",
        max_length=MAX_MATCHES_LENGTH,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):

        # Validate the raw text
        errors = validate_run_ladder(self.matches.value, INPUT_STYLE)

        if errors:
            msg = (
                "\u274c I cannot parse your ladder entry \u274c\n"
                "Required format:\n"
                "```"
                f"{get_placeholder(INPUT_STYLE)}"
                "```"
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Build the private summary
        desc = build_ladder_description(
            self.pilot_deck.value,
            self.matches.value,
            self.comments.value,
        )
        embed = discord.Embed(description=desc, color=COLOR_NORMAL)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        # Save each match as one row in the ladder CSV
        user_name = interaction.user.display_name
        user_deck = self.pilot_deck.value
        user_comment = self.comments.value

        for line in self.matches.value.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            parsed = parse_match_line(line, INPUT_STYLE)
            if parsed is None:
                continue

            oppo_deck, result = parsed
            save_ladder_match(
                user_name=user_name,
                user_deck=user_deck,
                oppo_deck=oppo_deck,
                result=result,
                comments=user_comment,
            )

        # Single ephemeral response visible only to the user
        await interaction.response.send_message(
            content="\u2705 Ladder run logged (private).",
            embed=embed,
            ephemeral=True,
        )
