from config import TROPHY_WIN_COUNT


def parse_runs(text: str) -> list[list[tuple[str, str]]]:
    """
    Parse a multi-run block into a list of runs. Each run is a list of (opponent, result) tuples.

    Expected format:
        Run 1:
        GB Lands 2-1
        W Stompy 0-2

        Run 2:
        Sultai Shadow 2-0
    """

    runs = []  # Number of runs user inputs
    current_run = []  # The specific run the system is checking

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("run") and line.endswith(":"):  # Enforcing structure to identify runs
            if current_run:
                runs.append(current_run)
            current_run = []
        else:
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                current_run.append((parts[0], parts[1]))
            else:
                current_run.append((line, "?"))

    if current_run:
        runs.append(current_run)

    return runs


def validate_runs_metagame(runs: list[list[tuple[str, str]]], raw_text: str) -> list[str]:
    """
    Validates the parsed runs for a metagame. Returns a list of error strings.
    Empty list means everything is valid.

    Rules enforced:
    - Input must contain at least one 'Run N:' header
    - Each run has max TROPHY_WIN_COUNT (7) matches
    - Each match is on its own line (no commas)
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
        for opponent, result in run:
            if "," in opponent or "," in result:
                errors.append(f"Run {i}: put each match on its own line, don't use commas.")
                continue

            # Rule 6: result must be N-N format
            parts = result.split("-")
            if len(parts) != 2:
                errors.append(
                    f"Run {i}: `{opponent} {result}` — result must be `2-1`, `0-2`, etc."
                )
                continue
            try:
                int(parts[0]), int(parts[1])
            except ValueError:
                errors.append(
                    f"Run {i}: `{opponent} {result}` — result must be numbers like `2-1`."
                )

    return errors


def validate_run_ladder(raw_text: str) -> list[str]:
    """
    Validates a ladder entry. Returns a list of error strings. Empty list means everything is valid.

    Rules:
    - Each match is on its own line (no commas)
    - Each result is in N-N format
    """
    errors: list[str] = []

    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # opponent and result separated by last space
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            errors.append(f"`{line}` — must be `Opponent 2-1`, `Opponent 0-2`, etc.")
            continue

        opponent, result = parts

        # Rule 1: no comma
        if "," in opponent or "," in result:
            errors.append(f"`{line}` — put each match on its own line, don't use commas.")
            continue

        # Rule 2: result must be N-N format
        score = result.split("-")
        if len(score) != 2:
            errors.append(f"`{line}` — result must be `2-1`, `0-2`, etc.")
            continue

        try:
            int(score[0]), int(score[1])
        except ValueError:
            errors.append(f"`{line}` — result must be numbers like `2-1`.")

    return errors


def check_trophy(matches: list[tuple[str, str]]) -> bool:
    """
    This function checks if a given run is a trophy (i.e. 7-0 in metagame challenge). It will count lines and wins. If it meets the criteria, voila, that player gets a trophy!!
    """

    if len(matches) != TROPHY_WIN_COUNT:
        return False

    for _, result in matches:
        win_loss = result.split("-")  # [win, loss]
        if len(win_loss) != 2:
            return False
        try:
            if int(win_loss[0]) <= int(win_loss[1]):  # More lost games than wins
                return False  # Then nothing

        except ValueError:
            return False

    return True


def build_ladder_description(deck: str, matches: str, comments: str) -> str:
    lines = [f"**deck:** {deck}", ""]
    lines.append(matches.strip())
    if comments:
        lines.append("")
        lines.append(f"*comments: {comments}*")
    return "\n".join(lines)
