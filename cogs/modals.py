import asyncio
import time

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

from utils.guild_settings import (
    get_effective_input_style,
    get_effective_delimiter,
    get_effective_save_directory,
    get_effective_challenge_file,
    get_effective_ladder_file,
)

from config import (
    MAX_COMMENT_LENGTH,
    MAX_DECK_LENGTH,
    MAX_MATCHES_LENGTH,
    COLOR_NORMAL,
    GUILD_ACTIVE_LIMIT,
    USER_SUBMIT_COOLDOWN,
)

from services.storage import save_metagame_match, save_ladder_match


# One semaphore per guild, limits simultaneous save operations
_guild_write_semaphores: dict[int, asyncio.Semaphore] = {}

# Tracks last submit time per (guild, user, modal type)
_last_submit_times: dict[tuple[int, int, str], float] = {}


def get_guild_write_semaphore(guild_id: int) -> asyncio.Semaphore:
    # Create one write semaphore per guild
    if guild_id not in _guild_write_semaphores:
        _guild_write_semaphores[guild_id] = asyncio.Semaphore(GUILD_ACTIVE_LIMIT)
    return _guild_write_semaphores[guild_id]


def check_submit_cooldown(guild_id: int, user_id: int, modal_type: str) -> int | None:
    # Return remaining cooldown time if user submitted too recently
    now = time.monotonic()
    key = (guild_id, user_id, modal_type)
    last_time = _last_submit_times.get(key)

    if last_time is not None:
        retry_after = USER_SUBMIT_COOLDOWN - (now - last_time)
        if retry_after > 0:
            return max(1, int(retry_after))

    _last_submit_times[key] = now
    return None


def sanitize_text(value: str) -> str:
    # Trim text and remove null bytes
    value = value.replace("\x00", "").strip()

    # Prevent CSV formula injection in spreadsheet apps
    if value.startswith(("=", "+", "-", "@")):
        value = "'" + value

    return value


class MetagameModal(discord.ui.Modal, title="Log your Metagame Challenge Run(s)"):
    """Collect all Metagame runs for one deck in one modal."""

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Izzet Tempo (avoid long names)",
        max_length=MAX_DECK_LENGTH,
    )

    runs_input = discord.ui.TextInput(
        label="Your runs (without final run result)",
        style=discord.TextStyle.paragraph,
        placeholder="Loading style ...",
        max_length=MAX_MATCHES_LENGTH,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any notes about your run(s)?",
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    def __init__(self, input_style: str, delimiter: str):
        super().__init__()
        self.input_style = input_style
        self.delimiter = delimiter
        self.runs_input.placeholder = (
            f"Run 1:\n{get_placeholder(input_style, delimiter)}\n\n"
            f"Run 2:\n{get_placeholder(input_style, delimiter)}"
        )[:100]

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "This modal must be used in a server.",
                ephemeral=True,
            )
            return

        # Stop one user from spamming repeated submissions
        retry_after = check_submit_cooldown(guild_id, interaction.user.id, "metagame")
        if retry_after is not None:
            await interaction.response.send_message(
                f"Cooldown active. Try again in {retry_after}s.",
                ephemeral=True,
            )
            return

        # Limit simultaneous save operations per guild
        semaphore = get_guild_write_semaphore(guild_id)
        if semaphore.locked():
            await interaction.response.send_message(
                "Too many submissions right now. Try again in few seconds.",
                ephemeral=True,
            )
            return

        async with semaphore:
            input_style = get_effective_input_style(guild_id)
            delimiter = get_effective_delimiter(guild_id)
            save_dir = get_effective_save_directory(guild_id)
            challenge_file = get_effective_challenge_file(guild_id)

            runs = parse_runs(self.runs_input.value, input_style, delimiter)

            errors = validate_runs_metagame(runs, self.runs_input.value, input_style)
            if errors:
                msg = (
                    "\u274c I cannot parse your runs \u274c\n"
                    "Required format:\n"
                    f"```Run 1:\n{get_placeholder(input_style, delimiter)}\netc.\n\n"
                    f"Run 2:\n{get_placeholder(input_style, delimiter)}```"
                )
                await interaction.response.send_message(msg, ephemeral=True)
                return

            user_name = sanitize_text(interaction.user.display_name)
            user_deck = sanitize_text(self.pilot_deck.value)
            user_comment = sanitize_text(self.comments.value)

            session_runs = []
            for i, run in enumerate(runs):
                if input_style == "deck_delimiter_result":
                    matches_text = "\n".join(
                        f"{sanitize_text(oppo_deck)}{delimiter}{result}"
                        for oppo_deck, result in run
                    )
                elif input_style == "result_delimiter_deck":
                    matches_text = "\n".join(
                        f"{result}{delimiter}{sanitize_text(oppo_deck)}"
                        for oppo_deck, result in run
                    )
                else:
                    matches_text = "\n".join(
                        f"{sanitize_text(oppo_deck)}{delimiter}{result}"
                        for oppo_deck, result in run
                    )

                session_runs.append({
                    "matches": matches_text,
                    "comments": user_comment if i == len(runs) - 1 else "",
                })

            for run in runs:
                run_result = summarise_run_record(run)
                for oppo_deck, result in run:
                    save_metagame_match(
                        user_name=user_name,
                        user_deck=user_deck,
                        run_result=run_result,
                        oppo_deck=sanitize_text(oppo_deck),
                        result=result,
                        comments=user_comment,
                        save_dir=save_dir,
                        file_name=challenge_file,
                    )

            embed = build_embedding(
                interaction.user,
                user_deck,
                session_runs,
                input_style=input_style,
                delimiter=delimiter,
            )

            await interaction.response.send_message(
                f"\u2705 {len(runs)} run(s) logged!",
                ephemeral=True,
            )
            await interaction.followup.send(embed=embed)


class LadderModal(discord.ui.Modal, title="Log your Ladder run"):
    """Collect one ladder session for one deck."""

    pilot_deck = discord.ui.TextInput(
        label="Your deck",
        placeholder="e.g. Blue Cope",
        max_length=MAX_DECK_LENGTH,
    )

    matches = discord.ui.TextInput(
        label="Matches (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="Loading text...",
        max_length=MAX_MATCHES_LENGTH,
    )

    comments = discord.ui.TextInput(
        label="Comments (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=MAX_COMMENT_LENGTH,
    )

    def __init__(self, input_style: str, delimiter: str):
        super().__init__()
        self.input_style = input_style
        self.delimiter = delimiter
        self.matches.placeholder = (
            f"{get_placeholder(input_style, delimiter)}\n"
            f"{get_placeholder(input_style, delimiter)}"
        )[:100]

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "This modal must be used in a server.",
                ephemeral=True,
            )
            return

        # Stop one user from spamming repeated submissions
        retry_after = check_submit_cooldown(guild_id, interaction.user.id, "ladder")
        if retry_after is not None:
            await interaction.response.send_message(
                f"Cooldown active. Try again in {retry_after}s.",
                ephemeral=True,
            )
            return

        # Limit simultaneous save operations per guild
        semaphore = get_guild_write_semaphore(guild_id)
        if semaphore.locked():
            await interaction.response.send_message(
                "Too many submissions right now. Try again in few seconds.",
                ephemeral=True,
            )
            return

        async with semaphore:
            input_style = get_effective_input_style(guild_id)
            delimiter = get_effective_delimiter(guild_id)
            save_dir = get_effective_save_directory(guild_id)
            ladder_file = get_effective_ladder_file(guild_id)

            errors = validate_run_ladder(self.matches.value, input_style, delimiter)
            if errors:
                msg = (
                    "\u274c I cannot parse your ladder entry \u274c\n"
                    "Required format:\n"
                    f"```{get_placeholder(input_style, delimiter)}```"
                )
                await interaction.response.send_message(msg, ephemeral=True)
                return

            user_name = sanitize_text(interaction.user.display_name)
            user_deck = sanitize_text(self.pilot_deck.value)
            user_comment = sanitize_text(self.comments.value)

            desc = build_ladder_description(
                user_deck,
                self.matches.value,
                user_comment,
            )
            embed = discord.Embed(description=desc, color=COLOR_NORMAL)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )

            for line in self.matches.value.strip().splitlines():
                line = line.strip()
                if not line:
                    continue

                parsed = parse_match_line(line, input_style, delimiter)
                if parsed is None:
                    continue

                oppo_deck, result = parsed
                save_ladder_match(
                    user_name=user_name,
                    user_deck=user_deck,
                    oppo_deck=sanitize_text(oppo_deck),
                    result=result,
                    comments=user_comment,
                    save_dir=save_dir,
                    file_name=ladder_file,
                )

            await interaction.response.send_message(
                content="\u2705 Ladder run logged (private).",
                embed=embed,
                ephemeral=True,
            )