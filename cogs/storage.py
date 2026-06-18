import csv
from datetime import datetime, timezone
from pathlib import Path

from config import CHALLENGE_FILE, LADDER_FILE, MTGA_DATA_DIR

# Global fallback paths used when no guild-specific override is provided.
# These resolve to the directory defined in config.MTGA_DATA_DIR.
_DEFAULT_DATA_DIR = Path(MTGA_DATA_DIR)
_DEFAULT_METAGAME_FILE = _DEFAULT_DATA_DIR / CHALLENGE_FILE
_DEFAULT_LADDER_FILE = _DEFAULT_DATA_DIR / LADDER_FILE


def _resolve_metagame_path(save_dir: str | None, file_name: str | None) -> Path:
    """Return the full path to the metagame CSV.

    Priority order:
      1. save_dir + file_name  (both provided by the guild-settings layer)
      2. save_dir + config.CHALLENGE_FILE  (custom directory, default filename)
      3. _DEFAULT_METAGAME_FILE  (everything falls back to config)

    Args:
        save_dir:  The resolved directory for this guild, or None for global default.
        file_name: The bare CSV filename for this guild, or None for config default.

    Returns:
        Path: The full path where metagame rows should be written.
    """
    if save_dir is None:
        # No custom directory — use the global fallback path entirely.
        # file_name is intentionally ignored here because the global default
        # already pairs MTGA_DATA_DIR with CHALLENGE_FILE from config.
        return _DEFAULT_METAGAME_FILE
    base = Path(save_dir)
    name = file_name if file_name is not None else CHALLENGE_FILE
    return base / name


def _resolve_ladder_path(save_dir: str | None, file_name: str | None) -> Path:
    """Return the full path to the ladder CSV.

    Priority order:
      1. save_dir + file_name  (both provided by the guild-settings layer)
      2. save_dir + config.LADDER_FILE  (custom directory, default filename)
      3. _DEFAULT_LADDER_FILE  (everything falls back to config)

    Args:
        save_dir:  The resolved directory for this guild, or None for global default.
        file_name: The bare CSV filename for this guild, or None for config default.

    Returns:
        Path: The full path where ladder rows should be written.
    """
    if save_dir is None:
        return _DEFAULT_LADDER_FILE
    base = Path(save_dir)
    name = file_name if file_name is not None else LADDER_FILE
    return base / name


def _ensure_header_metagame(path: Path) -> None:
    """Create the metagame CSV with column headers if it does not yet exist.

    The parent directory is also created automatically.  This means admins
    can point the bot at a brand-new filename and the file will be
    initialised correctly on the first submission.

    Args:
        path: Full path to the metagame CSV file.
    """
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
    """Create the ladder CSV with column headers if it does not yet exist.

    The parent directory is also created automatically.  This means admins
    can point the bot at a brand-new filename and the file will be
    initialised correctly on the first submission.

    Args:
        path: Full path to the ladder CSV file.
    """
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
    save_dir: str | None = None,
    file_name: str | None = None,
) -> None:
    """Append one match row to the metagame (challenge) CSV.

    If the target file does not exist yet it is created automatically with
    the correct column headers, so admins can freely set a new filename via
    /settings set_challenge_file without any manual setup.

    Args:
        user_name:  Discord display name of the player.
        user_deck:  Name of the deck the player used.
        run_result: Overall run record (e.g. "7-2").
        oppo_deck:  Name of the opponent's deck.
        result:     Outcome of this individual match ("W" / "L" / "D").
        comments:   Optional free-text note from the player.
        save_dir:   Resolved directory for this guild
                    (from get_effective_save_directory).  None = global default.
        file_name:  Bare CSV filename for this guild
                    (from get_effective_challenge_file).  None = config default.
    """
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
    save_dir: str | None = None,
    file_name: str | None = None,
) -> None:
    """Append one match row to the ladder CSV.

    If the target file does not exist yet it is created automatically with
    the correct column headers, so admins can freely set a new filename via
    /settings set_ladder_file without any manual setup.

    Args:
        user_name: Discord display name of the player.
        user_deck: Name of the deck the player used.
        oppo_deck: Name of the opponent's deck.
        result:    Outcome of this match ("W" / "L" / "D").
        comments:  Optional free-text note from the player.
        save_dir:  Resolved directory for this guild
                   (from get_effective_save_directory).  None = global default.
        file_name: Bare CSV filename for this guild
                   (from get_effective_ladder_file).  None = config default.
    """
    path = _resolve_ladder_path(save_dir, file_name)
    _ensure_header_ladder(path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, user_name, user_deck, oppo_deck, result, comments])
