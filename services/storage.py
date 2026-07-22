"""CSV persistence layer for match data.

This module has no Discord dependencies and can be tested independently.
All writes are append-only; files are created with column headers on first use.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path
import asyncio




# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------



_FILE_LOCKS: dict[str, asyncio.Lock] = {}

def _get_file_lock(path: Path) -> asyncio.Lock: 
    """
    This function is a helper to ensure that submissions are properly saved eventhough submitted same time.
    """

    key = str(path.resolve())
    lock = _FILE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _FILE_LOCKS[key] = lock
    return lock

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

async def save_metagame_match(
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
    _lock = _get_file_lock(path)

    async with _lock:
        _ensure_header(path, _METAGAME_HEADERS)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [ts, user_name, user_deck, run_result, oppo_deck, result, comments]
            )


async def save_ladder_match(
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
    _lock = _get_file_lock(path)

    async with _lock:
        _ensure_header(path, _LADDER_HEADERS)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [ts, user_name, user_deck, oppo_deck, result, comments]
            )
