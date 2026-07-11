import csv
import threading
from datetime import datetime, timezone
from pathlib import Path


# One in-process lock per file path
_file_locks: dict[str, threading.Lock] = {}


def _get_file_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    if key not in _file_locks:
        _file_locks[key] = threading.Lock()
    return _file_locks[key]


def _validate_file_name(file_name: str) -> str:
    # Only allow plain .csv file names, never paths
    file_name = file_name.strip()

    if not file_name:
        raise ValueError("Filename must not be empty.")

    if not file_name.endswith(".csv"):
        raise ValueError("Filename must end with .csv.")

    if "/" in file_name or "\\" in file_name:
        raise ValueError("Filename must not contain path separators.")

    return file_name


def _resolve_safe_path(save_dir: str, file_name: str) -> Path:
    # Build final path and ensure it stays inside save_dir
    base_dir = Path(save_dir).resolve()
    safe_name = _validate_file_name(file_name)
    full_path = (base_dir / safe_name).resolve()

    if full_path.parent != base_dir:
        raise ValueError("Resolved path escapes save directory.")

    return full_path


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_header_if_missing(path: Path, headers: list[str]) -> None:
    # Create file with header only if it does not exist yet
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def _append_row(path: Path, row: list[str], headers: list[str]) -> None:
    # Lock header creation + append as one critical section
    lock = _get_file_lock(path)

    with lock:
        _ensure_parent_dir(path)
        _write_header_if_missing(path, headers)

        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)


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
    path = _resolve_safe_path(save_dir, file_name)

    headers = [
        "timestamp_utc",
        "user_name",
        "user_deck",
        "run_result",
        "oppo_deck",
        "result",
        "comments",
    ]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    row = [ts, user_name, user_deck, run_result, oppo_deck, result, comments]

    _append_row(path, row, headers)


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
    path = _resolve_safe_path(save_dir, file_name)

    headers = [
        "timestamp_utc",
        "user_name",
        "user_deck",
        "oppo_deck",
        "result",
        "comments",
    ]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    row = [ts, user_name, user_deck, oppo_deck, result, comments]

    _append_row(path, row, headers)