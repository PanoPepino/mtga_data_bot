import discord

from cogs.utils import check_trophy, parse_runs, validate_runs
from config import COLOR_NORMAL, COLOR_TROPHY


def build_embedding(user: discord.User | discord.Member,
                    deck: str,
                    runs: list[dict]) -> discord.Embed:
    """
    Builds a Discord embed from all runs in a session.
    Shows each run with its matches, optional comments,
    and a trophy field if any run was a 7-0.
    """

    lines = [f"**deck:** {deck}\n"]  # heading line
    has_trophy = False

    for i, run in enumerate(runs, 1):

        # Parse match lines into (opponent, result) tuples for trophy check
        parsed_run = [
            tuple(line.rsplit(" ", 1)) if " " in line else (line, "?")
            for line in run["matches"].strip().splitlines()
            if line.strip()
        ]

        # Check if this run is a 7-0
        run_is_trophy = check_trophy(parsed_run)
        if run_is_trophy:
            has_trophy = True

        # Run header with trophy emoji if applicable
        lines.append(f"**Run {i}:** " + ("🏆" if run_is_trophy else ""))
        lines.append("")                    # blank line after header
        lines.append(run["matches"])        # match lines

        # Comments belong to each run — must be inside the loop
        if run.get("comments"):
            lines.append("")
            lines.append(f'*comments: {run["comments"]}*')

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

    embed.add_field(name="\u200b", value="\u200b", inline=False)  # ← invisible spacer field

    # Trophy field — appears in embed body, much more visible than footer
    if has_trophy:
        embed.add_field(
            name="🏆 TROPHY RUN 🏆",
            value=f"**{user.display_name}** went 7-0 with **{deck}**! Congratulations! 🎉",
            inline=False,
        )

    return embed
