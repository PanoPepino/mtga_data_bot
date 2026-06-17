# cogs/modals.py

import discord
from config import MAX_COMMENT_LENGTH, MAX_DECK_LENGTH, MAX_MATCHES_LENGTH
from cogs.sessions import create_session, add_run, get_session
from cogs.embedding import build_embedding
from cogs.utils import parse_runs, validate_runs


class FirstRunModal(discord.ui.Modal, title="Log your Metagame Challenge Run"):
    """
    Single modal that collects ALL runs for a given deck at once.
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
        placeholder="Any notes about your runs?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):

        # --- Step 1: Parse the raw text into structured runs ---
        # parse_runs splits the text into a list of runs,
        # each run being a list of (opponent, result) tuples
        runs = parse_runs(self.runs_input.value)

        # --- Step 2: Validate — check format before doing anything ---
        errors = validate_runs(runs, self.runs_input.value)
        if errors:
            # If invalid, tell the user privately and stop — nothing is posted
            error_text = "\n".join(f"• {e}" for e in errors)
            await interaction.response.send_message(
                f"❌ Could not parse your runs. Please fix:\n{error_text}\n\n"
                f"Expected format:\n```\nRun 1:\nGB Lands 2-1\nW Stompy 0-2\netc.\n\n"
                f"Run 2:\nSultai Shadow 2-0\n```",
                ephemeral=True,
            )
            return   # stop here, nothing posted publicly

        # --- Step 3: Respond to Discord first (3 second rule) ---
        await interaction.response.send_message(
            f"✅ {len(runs)} run(s) logged!", ephemeral=True
        )

        # --- Step 4: Convert parsed runs back into session format ---
        # Each run becomes a dict with raw matches text and comments
        session_runs = []
        for i, run in enumerate(runs):
            # Reconstruct match text from parsed tuples for display
            matches_text = "\n".join(f"{opponent} {result}" for opponent, result in run)
            session_runs.append({
                "matches": matches_text,
                "comments": self.comments.value if i == 0 else "",
            })

        # --- Step 5: Build and post the embed publicly ---
        embed = build_embedding(interaction.user, self.pilot_deck.value, session_runs)
        message = await interaction.followup.send(embed=embed)

        # --- Step 6: Save everything to session in case we need it later ---
        create_session(
            user_id=interaction.user.id,
            deck=self.pilot_deck.value,
            message_id=message.id,
            channel_id=interaction.channel_id,
        )
        for run in session_runs:
            add_run(
                user_id=interaction.user.id,
                matches=run["matches"],
                comments=run["comments"],
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        # Catches any unexpected crash and prints it to terminal
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] Modal on_error: {error}")
