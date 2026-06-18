import discord
from utils.parse_and_check import check_trophy, parse_match_line, summarise_run_record
from config import COLOR_NORMAL, COLOR_TROPHY

# Note: INPUT_STYLE is intentionally NOT imported here at module level.
# The caller (modals.py) resolves the guild-specific style and passes it in.


def build_embedding(
    user: discord.User | discord.Member,
    deck: str,
    runs: list[dict],
    input_style: str | None = None,
    delimiter: str | None = None,
) -> discord.Embed:
    """Build a Discord embed from all runs for a metagame challenge session.

    input_style / delimiter: pass the guild-resolved values from on_submit so
    that trophy detection and record counting use the correct parsing rules.
    Both fall back to config defaults inside parse_match_line when None.
    """
    lines = [f"**deck:** {deck}\n"]
    has_trophy = False

    for i, run in enumerate(runs, 1):
        # Re-parse the stored match text with the guild's style + delimiter
        # so that trophy detection and the run record are always accurate.
        parsed_run = []
        for line in run["matches"].strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = parse_match_line(line, input_style, delimiter)
            if parsed is None:
                parsed_run.append((line, "?"))
            else:
                parsed_run.append(parsed)

        run_record = summarise_run_record(parsed_run)
        run_is_trophy = check_trophy(parsed_run)
        if run_is_trophy:
            has_trophy = True

        # Run header with record + trophy emoji when applicable
        lines.append(
            f"**Run {i}: {run_record}** " + ("\U0001f3c6" if run_is_trophy else "")
        )
        lines.append("")               # blank line after header
        lines.append(run["matches"])   # raw match text

        if run.get("comments"):
            lines.append("")
            lines.append(f'*comments*: {run["comments"]}')

        lines.append("")               # blank line between runs

    embed = discord.Embed(
        description="\n".join(lines).strip(),
        color=COLOR_TROPHY if has_trophy else COLOR_NORMAL,
    )
    embed.set_author(
        name=user.display_name,
        icon_url=user.display_avatar.url,
    )

    if has_trophy:
        embed.add_field(
            name="\U0001f3c6 TROPHY RUN \U0001f3c6",
            value=(
                f"**{user.display_name}** went 7-0 with **{deck}**! "
                f"Congratulations! \U0001f389"
            ),
            inline=False,
        )

    return embed


def build_ladder_description(deck: str, matches: str, comments: str) -> str:
    """Build the description text for a ladder run embed."""
    lines = [f"**deck:** {deck}", ""]
    lines.append(matches.strip())
    if comments:
        lines.append("")
        lines.append(f"*comments: {comments}*")
    return "\n".join(lines)
