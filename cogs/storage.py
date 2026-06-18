import csv
from datetime import datetime, timezone
from pathlib import Path


def _resolve_metagame_path(save_dir: str, file_name: str) -> Path:
    """Return the full path to the metagame CSV."""
    return Path(save_dir) / file_name


def _resolve_ladder_path(save_dir: str, file_name: str) -> Path:
    """Return the full path to the ladder CSV."""
    return Path(save_dir) / file_name


def _ensure_header_metagame(path: Path) -> None:
    """Create the metagame CSV with column headers if it does not yet exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp_utc",
                    "user_name",
                    "user_deck",
                    "run_result",
                    "oppo_deck",
                    "result",
                    "comments",
                ]
            )


def _ensure_header_ladder(path: Path) -> None:
    """Create the ladder CSV with column headers if it does not yet exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp_utc",
                    "user_name",
                    "user_deck",
                    "oppo_deck",
                    "result",
                    "comments",
                ]
            )


def save_metagame_match(
    *,
    user_name: str,
    user_deck: str,
    run_result: str,
    oppo_deck: str,
    result: str,
    comments: str,
    save_dir: str,
    file_name: str,
) -> None:
    """Append one match row to the metagame CSV."""
    path = _resolve_metagame_path(save_dir, file_name)
    _ensure_header_metagame(path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, user_name, user_deck, run_result, oppo_deck, result, comments])


def save_ladder_match(
    *,
    user_name: str,
    user_deck: str,
    oppo_deck: str,
    result: str,
    comments: str,
    save_dir: str,
    file_name: str,
) -> None:
    """Append one match row to the ladder CSV."""
    path = _resolve_ladder_path(save_dir, file_name)
    _ensure_header_ladder(path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, user_name, user_deck, oppo_deck, result, comments])
