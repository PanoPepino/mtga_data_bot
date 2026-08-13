import re

from config import TROPHY_WIN_COUNT


_RUN_HEADER_RE = re.compile(r"^run\s+\d+\s*:$", re.IGNORECASE)
_RESULT_FIRST_RE = re.compile(r"^(\d+\s*-\s*\d+)\s+(.+)$")
_RESULT_LAST_RE = re.compile(r"^(.+?)\s+(\d+\s*-\s*\d+)$")


def get_placeholder(input_style: str, delimiter: str) -> str:
    """
    Return the example placeholder text for the selected input style
    and the currently active delimiter.
    """

    if input_style == "result_delimiter_deck":
        return (
            f"2-1{delimiter}GB Lands # <-- Observe delimiter and result+deck order\n"
            f"0-2{delimiter}R Stompy\n"
            f"1-2{delimiter}UR Tempo"
        )

    if input_style == "deck_delimiter_result":
        return (
            f"GB Lands{delimiter}2-1\n"
            f"W Stompy{delimiter}0-2"
        )

    return "Wrong input style"


def parse_match_line(
    line: str,
    input_style: str,
    delimiter: str | None = None,
) -> tuple[str, str] | None:
    """Parse one match line and return (oppo_deck, result).

    delimiter: separator to split on. Defaults to config.DELIMITER when None.
    input_style: controls which side is the deck and which is the result.
    Returns None if the line cannot be parsed.
    """
    sep = delimiter if delimiter is not None else "-"

    line = line.strip()
    if not line:
        return None
    if sep not in line:
        return None

    if input_style == "deck_delimiter_result":
        parts = line.rsplit(sep, 1)
        if len(parts) != 2:
            return None
        oppo_deck, result = parts
        return oppo_deck.strip(), result.strip()

    if input_style == "result_delimiter_deck":
        parts = line.split(sep, 1)
        if len(parts) != 2:
            return None
        result, oppo_deck = parts
        return oppo_deck.strip(), result.strip()

    return None


def check_valid_result(result: str) -> bool:
    """Return True if result is in W-L format (e.g. '2-1', '0-2')."""
    parts = result.split("-")
    if len(parts) != 2:
        return False
    try:
        int(parts[0])
        int(parts[1])
    except ValueError:
        return False
    return True


def _annotate_match_line(line: str, input_style: str, delimiter: str) -> str:
    """Return one submission line with an inline correction where possible."""
    stripped = line.strip()
    if not stripped:
        return line

    if "," in stripped:
        return f"{stripped} # <-- put each match on its own line; do not use commas"

    parsed = parse_match_line(stripped, input_style, delimiter)
    if parsed is not None:
        _, result = parsed
        if not check_valid_result(result):
            return f"{stripped} # <-- result must be W-L, for example `2-1`"
        return stripped

    # If the score and deck name are unambiguous, repair only the missing
    # delimiter. This lets users copy the preview straight back into the modal.
    if input_style == "result_delimiter_deck":
        match = _RESULT_FIRST_RE.match(stripped)
        if match:
            return (
                f"{match.group(1)}{delimiter}{match.group(2)} "
                f"# <-- missing delimiter `{delimiter}`"
            )
        example = f"2-1{delimiter}Opponent deck"
    else:
        match = _RESULT_LAST_RE.match(stripped)
        if match:
            return (
                f"{match.group(1)}{delimiter}{match.group(2)} "
                f"# <-- missing delimiter `{delimiter}`"
            )
        example = f"Opponent deck{delimiter}2-1"

    return f"{stripped} # <-- use the format `{example}`"


def build_ladder_correction(
    raw_text: str,
    input_style: str,
    delimiter: str,
) -> str:
    """Build a line-by-line correction preview for a ladder submission."""
    return "\n".join(
        _annotate_match_line(line, input_style, delimiter)
        for line in raw_text.splitlines()
    ).strip()


def build_metagame_correction(
    raw_text: str,
    input_style: str,
    delimiter: str,
) -> str:
    """Build a copyable correction preview for a Metagame Challenge entry.

    The preview retains the submitted matches and adds comments on the exact
    header or match line that needs attention. When a run header is absent, a
    corrected first header is supplied before the user's first match.
    """
    lines = raw_text.splitlines()
    has_valid_header = any(_RUN_HEADER_RE.match(line.strip()) for line in lines)
    has_header_like_line = any(
        line.strip().lower().startswith("run") and line.strip().endswith(":")
        for line in lines
    )
    corrected: list[str] = []

    if not has_valid_header and not has_header_like_line:
        corrected.append("Run 1: # <-- missing run header; add one before your matches")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            corrected.append(line)
        elif stripped.lower().startswith("run") and stripped.endswith(":"):
            if _RUN_HEADER_RE.match(stripped):
                corrected.append(stripped)
            else:
                corrected.append(
                    f"{stripped} # <-- use a numbered header, for example `Run 1:`"
                )
        else:
            corrected.append(_annotate_match_line(line, input_style, delimiter))

    return "\n".join(corrected).strip()


def parse_runs(
    text: str,
    input_style: str,
    delimiter: str | None = None,
) -> list[list[tuple[str, str]]]:
    """Parse a multi-run block into a list of runs.
    Each run is a list of (oppo_deck, result) tuples.

    Expected format:
        Run 1:
        <match line>
        ...

        Run 2:
        <match line>
        ...

    delimiter: forwarded to parse_match_line. None = use config default.
    """
    runs = []
    current_run = []

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("run") and line.endswith(":"):
            if current_run:
                runs.append(current_run)
            current_run = []
        else:
            parsed = parse_match_line(line, input_style, delimiter)
            if parsed is not None:
                current_run.append(parsed)
            else:
                current_run.append((line, "?"))

    if current_run:
        runs.append(current_run)

    return runs


def validate_runs_metagame(
    runs: list[list[tuple[str, str]]],
    raw_text: str,
    input_style: str,
) -> list[str]:
    """
    Validate parsed metagame runs. Returns a list of error strings.
    An empty list means everything is valid.
    """
    errors = []

    has_header = any(_RUN_HEADER_RE.match(line.strip()) for line in raw_text.splitlines())
    if not has_header:
        errors.append(
            "Missing numbered run headers. Each run must start with `Run 1:`, `Run 2:`, etc."
        )
        return errors

    if not runs:
        errors.append("No runs found. Make sure each run starts with `Run 1:`, `Run 2:`, etc.")
        return errors

    for i, run in enumerate(runs, 1):
        if not run:
            errors.append(f"Run {i} has no matches.")
            continue

        if len(run) > TROPHY_WIN_COUNT:
            errors.append(
                f"Run {i} has {len(run)} matches \u2014 maximum is {TROPHY_WIN_COUNT}. "
                f"Each run in a Metagame Challenge ends at 7 wins or 3 losses."
            )

        for oppo_deck, result in run:
            if "," in oppo_deck or "," in result:
                errors.append(f"Run {i}: put each match on its own line, don't use commas.")
                continue

            if result == "?":
                errors.append(f"Run {i}: invalid format for the current input style.")
                continue

            if not check_valid_result(result):
                errors.append(f"Run {i}: `{oppo_deck} {result}`: Result must be `2-1`, `0-2`, etc.")

    return errors


def validate_run_ladder(
    raw_text: str,
    input_style: str,
    delimiter: str | None = None,
) -> list[str]:
    """
    Validate a ladder entry. Returns a list of error strings.
    An empty list means everything is valid.
    """
    errors: list[str] = []

    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        if "," in line:
            errors.append(f"`{line}`: put each match on its own line, don't use commas.")
            continue

        parsed = parse_match_line(line, input_style, delimiter)

        if parsed is None:
            errors.append(f"`{line}`: invalid format according to the defined input style.")
            continue

        _, result = parsed

        if not check_valid_result(result):
            errors.append(f"`{line}`: invalid format W-L. Result should be `2-1`, `0-2`, etc.")

    return errors


def summarise_run_record(matches: list[tuple[str, str]]) -> str:
    """Count wins and losses in a run and return a 'W-L' summary string."""
    wins = 0
    losses = 0

    for _, result in matches:
        parts = result.split("-")
        if len(parts) != 2:
            continue
        try:
            games_won = int(parts[0])
            games_lost = int(parts[1])
        except ValueError:
            continue
        if games_won > games_lost:
            wins += 1
        elif games_won < games_lost:
            losses += 1

    return f"{wins}-{losses}"


def check_trophy(matches: list[tuple[str, str]]) -> bool:
    """Return True if the run is a 7-0 trophy."""
    return summarise_run_record(matches) == "7-0"


def build_ladder_description(
    pilot_deck: str,
    matches_text: str,
    comments: str,
) -> str:
    """Build a plain-text description for a ladder submission.

    Always includes deck name and match lines.
    Appends italicised comments line only when comments is non-empty.
    """
    lines = [
        f"**deck:** {pilot_deck}",
        matches_text.strip(),
    ]
    if comments.strip():
        lines.append(f"*comments: {comments.strip()}*")
    return "\n".join(lines)


def build_placeholder_deck_delimiter_result(delimiter: str) -> str:
    return (
        f"GB Lands{delimiter}2-1\n"
        f"W Stompy{delimiter}0-2"
    )


def build_placeholder_result_delimiter_deck(delimiter: str) -> str:
    return (
        f"2-1{delimiter}GB Lands\n"
        f"0-2{delimiter}R Stompy"
    )
