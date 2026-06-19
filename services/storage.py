"""CSV persistence layer for match data.

This module has no Discord dependencies and can be tested independently.
All writes are append-only; files are created with column headers on first use.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_path(save_dir: str, file_name: str) -> Path:
    return Path(save_dir) / file_name


def _ensure_header(path: Path, headers: list[str]) -> None:
    """Create the CSV file with column headers if it does not yet exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


_METAGAME_HEADERS = [
    "timestamp_utc",
    "user_name",
    "user_deck",
    "run_result",
    "oppo_deck",
    "result",
    "comments",
]

_LADDER_HEADERS = [
    "timestamp_utc",
    "user_name",
    "user_deck",
    "oppo_deck",
    "result",
    "comments",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    path = _resolve_path(save_dir, file_name)
    _ensure_header(path, _METAGAME_HEADERS)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(
            [ts, user_name, user_deck, run_result, oppo_deck, result, comments]
        )


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
    path = _resolve_path(save_dir, file_name)
    _ensure_header(path, _LADDER_HEADERS)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(
            [ts, user_name, user_deck, oppo_deck, result, comments]
        )
