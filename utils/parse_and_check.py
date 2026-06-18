from config import (
    TROPHY_WIN_COUNT,
)


def get_placeholder(input_style: str, delimiter: str) -> str:
    """
    Return the example placeholder text for the selected input style
    and the currently active delimiter.
    """

    if input_style == "result_delimiter_deck":
        return (
            f"2-1{delimiter}GB Lands\n"
            f"0-2{delimiter}R Stompy"
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
    # Use the guild's delimiter if provided, otherwise fall back to config default.
    sep = delimiter if delimiter is not None else "-"

    line = line.strip()
    if not line:
        return None
    if sep not in line:
        return None

    if input_style == "deck_delimiter_result":
        # Format: <deck> <sep> <result>
        parts = line.rsplit(sep, 1)
        if len(parts) != 2:
            return None
        oppo_deck, result = parts
        return oppo_deck.strip(), result.strip()

    if input_style == "result_delimiter_deck":
        # Format: <result> <sep> <deck>
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
        # A line like "Run 1:" marks the start of a new run block.
        if line.lower().startswith("run") and line.endswith(":"):
            if current_run:
                runs.append(current_run)
            current_run = []
        else:
            parsed = parse_match_line(line, input_style, delimiter)
            if parsed is not None:
                current_run.append(parsed)
            else:
                # Keep invalid lines so validation can report them.
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

    Rules:
    - At least one 'Run N:' header must be present.
    - Each run has at most TROPHY_WIN_COUNT (7) matches.
    - No commas — each match on its own line.
    - Each line follows the configured input style.
    - Each result is in N-N format.
    """
    errors = []

    has_header = any(
        line.strip().lower().startswith("run") and line.strip().endswith(":")
        for line in raw_text.splitlines()
    )
    if not has_header:
        errors.append(
            "Missing run headers. Each run must start with `Run 1:`, `Run 2:`, etc."
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
                f"Run {i} has {len(run)} matches — maximum is {TROPHY_WIN_COUNT}. "
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

    Rules:
    - Each match on its own line (no commas).
    - Each line follows the configured input style and delimiter.
    - Each result is in W-L format.
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
