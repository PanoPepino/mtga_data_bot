from config import (
    TROPHY_WIN_COUNT,
    DELIMITER,
    PH_DECK_DELIMITER_RESULT,
    PH_RESULT_DELIMITER_DECK)


def get_placeholder(input_style: str) -> str:
    """
    Depending on input style, the placeholder for errors and examples will differ. This function selects automatically
    """

    if input_style == 'result_delimiter_deck':
        return PH_RESULT_DELIMITER_DECK

    if input_style == 'deck_delimiter_result':
        return PH_DECK_DELIMITER_RESULT

    return "Wrong input style"


def parse_match_line(line: str, input_style: str) -> tuple[str, str] | None:
    """
    Parse a match line and return (oppo_deck, result). The way to parse is following the input_style defined.
    """

    line = line.strip()
    if not line:
        return None

    if DELIMITER not in line:
        return None

    if input_style == 'deck_delimiter_result':
        parts = line.rsplit(DELIMITER, 1)
        if len(parts) != 2:
            return None
        oppo_deck, result = parts
        return oppo_deck.strip(), result.strip()

    if input_style == 'result_delimiter_deck':
        parts = line.split(DELIMITER, 1)
        if len(parts) != 2:
            return None
        result, oppo_deck = parts
        return oppo_deck.strip(), result.strip()

    return None


def check_valid_result(result: str) -> bool:
    """
    Check if the result is W-L is valid
    """

    parts = result.split("-")
    if len(parts) != 2:
        return False
    try:
        int(parts[0]),
        int(parts[1])
    except ValueError:
        return False
    return True


def parse_runs(text: str,
               input_style: str) -> list[list[tuple[str, str]]]:
    """
    Parse a multi-run block into a list of runs. Each run is a list of (oppo_deck, result) tuples.

    Expected format:
        Run 1:
        ...

        Run 2:
        ...

        Run 3:
        ...
    """

    runs = []  # Number of runs user inputs
    current_run = []  # The specific run the system is checking

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("run") and line.endswith(":"):  # Check the structure for beginning of each run
            if current_run:
                runs.append(current_run)
            current_run = []
        else:
            parsed = parse_match_line(line, input_style)
            if parsed is not None:
                current_run.append(parsed)
            else:
                current_run.append((line, "?"))

    if current_run:
        runs.append(current_run)

    return runs


def validate_runs_metagame(runs: list[list[tuple[str, str]]],
                           raw_text: str,
                           input_style: str) -> list[str]:
    """
    Validates the parsed runs for a metagame. Returns a list of error strings.
    Empty list means everything is valid.

    Rules enforced:
    - Input must contain at least one 'Run N:' header
    - Each run has max TROPHY_WIN_COUNT (7) matches
    - Each match is on its own line (no commas)
    - Each line follows the predefined input style
    - Each result is in N-N format
    """
    errors = []

    # Rule 1: must have at least one 'Run N:' header
    # Check raw text directly — if no line starts with 'run' and ends with ':'
    # the player forgot the header entirely
    has_header = any(
        line.strip().lower().startswith("run") and line.strip().endswith(":")
        for line in raw_text.splitlines()
    )
    if not has_header:
        errors.append(
            "Missing run headers. Each run must start with `Run 1:`, `Run 2:`, etc."
        )
        return errors   # no point checking further without headers

    # Rule 2: no runs parsed at all
    if not runs:
        errors.append("No runs found. Make sure each run starts with `Run 1:`, `Run 2:`, etc.")
        return errors

    for i, run in enumerate(runs, 1):  # For several runs, check all

        # Rule 3: empty run
        if not run:
            errors.append(f"Run {i} has no matches.")
            continue

        # Rule 4: max 7 matches per run in Metagame challenge
        if len(run) > TROPHY_WIN_COUNT:
            errors.append(
                f"Run {i} has {len(run)} matches — maximum is {TROPHY_WIN_COUNT}. "
                f"Each run in a Metagame Challenge ends at 7 wins or 3 losses."
            )

        # Rule 5: no comma
        for oppo_deck, result in run:
            if "," in oppo_deck or "," in result:
                errors.append(f"Run {i}: put each match on its own line, don't use commas.")
                continue

            # Rule 6: result must be W-L format
            if result == "?":
                errors.append(f"Run {i}: invalid format for the current input style.")
                continue

            # Rule 7: checking the right structure
            if not check_valid_result(result):
                errors.append(f"Run {i}: `{oppo_deck} {result}`: Result must be `2-1`, `0-2`, etc.")

    return errors


def validate_run_ladder(raw_text: str,
                        input_style: str) -> list[str]:
    """
    Validates a ladder entry. Returns a list of error strings. Empty list means everything is valid.

    Rules:
    - Each match is on its own line (no commas)
    - Each line follows the input_style defined
    - Each result is in W-L format
    """
    errors: list[str] = []

    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # Rule 1: no comma
        if "," in line:
            errors.append(f"`{line}`: put each match on its own line, don't use commas.")
            continue

        parsed = parse_match_line(line, input_style)

        # Rule 2: Following the predifined style
        if parsed is None:
            errors.append(f"`{line}`: invalid format according to the defined input style.")
            continue

        _, result = parsed

        # Rule 3: checking the W-L format
        if not check_valid_result(result):
            errors.append(f"`{line}`: invalid format W-L. Result should be `2-1`, `0-2`, etc.")

    return errors


def summarise_run_record(matches: list[tuple[str, str]]) -> str:
    """
    Count wins in a run to identify trophy records. Identify the result and add counters to wins and losses
    """

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
    """
    This function checks if a given run is a trophy (i.e. 7-0 in metagame challenge). It uses summarise run record.
    """
    return summarise_run_record(matches) == '7-0'
