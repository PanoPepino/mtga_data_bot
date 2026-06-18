import csv
from datetime import datetime, timezone
from pathlib import Path

from config import CHALLENGE_FILE, LADDER_FILE, MTGA_DATA_DIR

# Global fallback paths used when no guild-specific save_dir is provided.
# These resolve to the directory defined in config.MTGA_DATA_DIR.
_DEFAULT_DATA_DIR = Path(MTGA_DATA_DIR)
_DEFAULT_METAGAME_FILE = _DEFAULT_DATA_DIR / CHALLENGE_FILE
_DEFAULT_LADDER_FILE = _DEFAULT_DATA_DIR / LADDER_FILE


def _resolve_metagame_path(save_dir: str | None) -> Path:
    """Return the full path to the metagame CSV for the given save directory.
    Falls back to the global default if save_dir is None."""
    if save_dir is None:
        return _DEFAULT_METAGAME_FILE
    base = Path(save_dir)
    return base / CHALLENGE_FILE


def _resolve_ladder_path(save_dir: str | None) -> Path:
    """Return the full path to the ladder CSV for the given save directory.
    Falls back to the global default if save_dir is None."""
    if save_dir is None:
        return _DEFAULT_LADDER_FILE
    base = Path(save_dir)
    return base / LADDER_FILE


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
    save_dir: str | None = None,  # guild-specific directory; None = use global default
) -> None:
    """Append one match row to the metagame CSV.
    save_dir is the resolved directory for this guild (from get_effective_save_directory).
    """
    path = _resolve_metagame_path(save_dir)
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
    save_dir: str | None = None,  # guild-specific directory; None = use global default
) -> None:
    """Append one match row to the ladder CSV.
    save_dir is the resolved directory for this guild (from get_effective_save_directory).
    """
    path = _resolve_ladder_path(save_dir)
    _ensure_header_ladder(path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, user_name, user_deck, oppo_deck, result, comments])
