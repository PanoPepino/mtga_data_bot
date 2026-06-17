
import discord
from config import MAX_COMMENT_LENGTH, MAX_DECK_LENGTH, MAX_MATCHES_LENGTH, COLOR_NORMAL
from cogs.embedding import build_embedding
from cogs.utils import (
    parse_runs,
    validate_runs_metagame,
    build_ladder_description,
    validate_run_ladder)


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
        placeholder="Run 1:\nGB Lands 2-1\nW Stompy 0-2\n\nRun 2:\nSultai Shadow 2-0",
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
        runs = parse_runs(self.runs_input.value)

        # Check formatting before submission
        # If not valid, do not post and tell user with a private message
        errors = validate_runs_metagame(runs, self.runs_input.value)
        if errors:
            error_text = "\n".join(f"• {e}" for e in errors)
            await interaction.response.send_message(
                f"❌ I cannot parse your runs ❌",
                f"Please fix:\n\n{error_text}\n\n"
                f"Required format format:\n"
                f"```Run 1:\nGB Lands 2-1\nW Stompy 0-2\netc.\n\n"
                f"Run 2:\nSultai Shadow 2-0\nR Stompy 1-2```",
                ephemeral=True,
            )
            return

        # If everything ok, private message with validation of submission
        await interaction.response.send_message(
            f"✅ {len(runs)} run(s) logged!", ephemeral=True
        )

        # Convert introduced data to dictionaries for easy storage and posting
        session_runs = []
        for i, run in enumerate(runs):
            # Reconstruct match text from parsed tuples for display
            matches_text = "\n".join(f"{opponent} {result}" for opponent, result in run)
            session_runs.append({
                "matches": matches_text,
                "comments": self.comments.value if i == 0 else "",
            })

        # The bot will post it
        embed = build_embedding(interaction.user, self.pilot_deck.value, session_runs)
        message = await interaction.followup.send(embed=embed)


class LadderModal(discord.ui.Modal, title="Log your Ladder run"):
    """
    Class that operates in same terms as :class:`MetagameModal`, but allows user to upload a given run with any deck. Could be useful to extract data from the ladder and get better insights to establish tier lists. 
    """

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Blue Cope",
        max_length=MAX_DECK_LENGTH,
    )

    matches = discord.ui.TextInput(
        label="Matches (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="GB Lands 2-1\nW Stompy 0-2\nUR Tempo 2-0",
        max_length=MAX_MATCHES_LENGTH,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):
        errors = validate_run_ladder(self.matches.value)
        if errors:
            error_text = "\n".join(f"• {e}" for e in errors)
            msg = (
                "❌ I cannot parse your ladder entry ❌ \n\n"
                f"{error_text}\n\n"
                "Required format:\n"
                "```"
                "GB Lands 2-1\n"
                "W Stompy 0-2\n"
                "UR Tempo 2-0\n"
                "```"
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

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

        # Single ephemeral response visible only to the user
        await interaction.response.send_message(
            content="✅ Ladder run logged (private).",
            embed=embed,
            ephemeral=True,
        )
