import discord

from cogs.embedding import build_embedding, build_ladder_description
from utils.parse_and_check import (
    parse_runs,
    summarise_run_record,
    validate_runs_metagame,
    validate_run_ladder,
    parse_match_line,
    get_placeholder,
)

# Guild-aware getters: each returns the per-server override if set,
# otherwise falls back to the global value in config.py.
from utils.guild_settings import (
    get_effective_input_style,
    get_effective_delimiter,
    get_effective_save_directory,
)

from config import (
    MAX_COMMENT_LENGTH,
    MAX_DECK_LENGTH,
    MAX_MATCHES_LENGTH,
    COLOR_NORMAL,
)

from cogs.storage import save_metagame_match, save_ladder_match


class MetagameModal(discord.ui.Modal, title="Log your Metagame Challenge Run(s)"):
    """
    Single modal that collects ALL Metagame runs for a given deck at once.
    The player separates runs with 'Run N:' headers.
    """

    # The deck the player piloted this session.
    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Izzet Tempo (avoid long names)",
        max_length=MAX_DECK_LENGTH,
    )

    # All runs in one text box. Player uses 'Run 1:' / 'Run 2:' headers.
    # The placeholder shows the generic format; actual parsing uses guild style.
    runs_input = discord.ui.TextInput(
        label="Your runs  (No need to write run result like 7-0. It is built automatically!)",
        style=discord.TextStyle.paragraph,
        placeholder="Run 1:\n<deck> vs <result>\n\nRun 2:\n<deck> vs <result>",
        max_length=MAX_MATCHES_LENGTH,
    )

    # Optional free-text notes for the whole session.
    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any notes about your run(s)?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Resolve per-guild settings at submit time so we always use the
        # latest values, even if an admin changed them after the modal opened.
        guild_id = interaction.guild_id
        input_style = get_effective_input_style(guild_id)
        delimiter = get_effective_delimiter(guild_id)
        save_dir = get_effective_save_directory(guild_id)

        # Split the raw text into runs using the guild's style + delimiter.
        # Each run is a list of (oppo_deck, result) tuples.
        runs = parse_runs(self.runs_input.value, input_style, delimiter)

        # Validate formatting. If invalid, respond privately and abort.
        errors = validate_runs_metagame(runs, self.runs_input.value, input_style)
        if errors:
            msg = (
                "\u274c I cannot parse your runs \u274c\n"
                "Required format:\n"
                f"```Run 1:\n{get_placeholder(input_style)}\netc.\n\n"
                f"Run 2:\n{get_placeholder(input_style)}```"
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Convert parsed runs into display dicts for the embed.
        session_runs = []
        for i, run in enumerate(runs):
            # Reconstruct match text using the guild's delimiter and style.
            if input_style == "deck_delimiter_result":
                matches_text = "\n".join(
                    f"{oppo_deck}{delimiter}{result}" for oppo_deck, result in run
                )
            elif input_style == "result_delimiter_deck":
                matches_text = "\n".join(
                    f"{result}{delimiter}{oppo_deck}" for oppo_deck, result in run
                )
            else:
                # Safe fallback.
                matches_text = "\n".join(
                    f"{oppo_deck}{delimiter}{result}" for oppo_deck, result in run
                )

            session_runs.append({
                "matches": matches_text,
                # Only attach the comment to the last run to avoid duplication.
                "comments": self.comments.value if i == len(runs) - 1 else "",
            })

        # Persist every match as one row in the guild's metagame CSV.
        user_name = interaction.user.display_name
        user_deck = self.pilot_deck.value
        user_comment = self.comments.value

        for run in runs:
            run_result = summarise_run_record(run)
            for oppo_deck, result in run:
                save_metagame_match(
                    user_name=user_name,
                    user_deck=user_deck,
                    run_result=run_result,
                    oppo_deck=oppo_deck,
                    result=result,
                    comments=user_comment,
                    save_dir=save_dir,
                )

        # Build the public embed with the guild's style + delimiter so that
        # trophy detection inside build_embedding is accurate.
        embed = build_embedding(
            interaction.user,
            self.pilot_deck.value,
            session_runs,
            input_style=input_style,
            delimiter=delimiter,
        )

        # Respond once: acknowledge privately, then send the embed publicly.
        await interaction.response.send_message(
            f"\u2705 {len(runs)} run(s) logged!", ephemeral=True
        )
        await interaction.followup.send(embed=embed)


class LadderModal(discord.ui.Modal, title="Log your Ladder run"):
    """
    Collects a single ladder session for any deck.
    Useful for extracting ladder data and building tier lists.
    """

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Blue Cope",
        max_length=MAX_DECK_LENGTH,
    )

    matches = discord.ui.TextInput(
        label="Matches (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="<deck> vs <result>",
        max_length=MAX_MATCHES_LENGTH,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Resolve per-guild settings at submit time.
        guild_id = interaction.guild_id
        input_style = get_effective_input_style(guild_id)
        save_dir = get_effective_save_directory(guild_id)

        # Validate the raw text against the guild's current input style.
        errors = validate_run_ladder(self.matches.value, input_style)
        if errors:
            msg = (
                "\u274c I cannot parse your ladder entry \u274c\n"
                "Required format:\n"
                f"```{get_placeholder(input_style)}```"
            )
            # Discord only allows one response per interaction.
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Build the summary embed.
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

        # Save each match line as one row in the guild's ladder CSV.
        user_name = interaction.user.display_name
        user_deck = self.pilot_deck.value
        user_comment = self.comments.value

        for line in self.matches.value.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = parse_match_line(line, input_style)
            if parsed is None:
                continue
            oppo_deck, result = parsed
            save_ladder_match(
                user_name=user_name,
                user_deck=user_deck,
                oppo_deck=oppo_deck,
                result=result,
                comments=user_comment,
                save_dir=save_dir,
            )

        # Single response: ladder runs are shown privately only.
        await interaction.response.send_message(
            content="\u2705 Ladder run logged (private).",
            embed=embed,
            ephemeral=True,
        )
