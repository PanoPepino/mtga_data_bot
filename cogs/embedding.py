import discord
from utils.parse_and_check import check_trophy, parse_match_line, summarise_run_record
from config import COLOR_NORMAL, COLOR_TROPHY, INPUT_STYLE


def build_embedding(user: discord.User | discord.Member,
                    deck: str,
                    runs: list[dict]) -> discord.Embed:
    """
    Builds a Discord embed from all runs. Shows each run with its matches,
    optional comments, and a trophy field if any run was a 7-0.
    """

    lines = [f"**deck:** {deck}\n"]  # heading line
    has_trophy = False

    for i, run in enumerate(runs, 1):

        # Parse match lines into (oppo_deck, result) tuples for trophy check
        parsed_run = []
        for line in run["matches"].strip().splitlines():
            line = line.strip()
            if not line:
                continue

            parsed = parse_match_line(line, INPUT_STYLE)
            if parsed is None:
                parsed_run.append((line, "?"))
            else:
                parsed_run.append(parsed)

        run_record = summarise_run_record(parsed_run)
        run_is_trophy = check_trophy(parsed_run)
        if run_is_trophy:
            has_trophy = True

        # Run header with record and trophy emoji if applicable
        lines.append(f"**Run {i}: {run_record}** " + ("\U0001f3c6" if run_is_trophy else ""))
        lines.append("")                    # blank line after header
        lines.append(run["matches"])        # match lines

        # Comments are tied to this specific run
        if run.get("comments"):
            lines.append("")
            lines.append(f'*comments*: {run["comments"]}')

        lines.append("")                    # blank line between runs

    # Build embed once after all runs are processed
    embed = discord.Embed(
        description="\n".join(lines).strip(),
        color=COLOR_TROPHY if has_trophy else COLOR_NORMAL,
    )

    embed.set_author(
        name=user.display_name,
        icon_url=user.display_avatar.url,
    )

    # Trophy field, appears in embed body
    if has_trophy:
        lines.append("")
        embed.add_field(
            name="\U0001f3c6 TROPHY RUN \U0001f3c6",
            value=f"**{user.display_name}** went 7-0 with **{deck}**! Congratulations! \U0001f389",
            inline=False,
        )

    return embed


def build_ladder_description(deck: str, matches: str, comments: str) -> str:
    lines = [f"**deck:** {deck}", ""]
    lines.append(matches.strip())
    if comments:
        lines.append("")
        lines.append(f"*comments: {comments}*")
    return "\n".join(lines)
