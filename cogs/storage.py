import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from config import CHALLENGE_FILE, MTGA_DATA_DIR, LADDER_FILE

DATA_DIR = Path(MTGA_DATA_DIR)
METAGAME_FILE = DATA_DIR/CHALLENGE_FILE
LADDER_FILE = DATA_DIR/LADDER_FILE


def _ensure_header(path: Path) -> None:
    """
    Create a csv file with the column titles
    """

    if not path.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp_utc",
                    "user_name",
                    "user_deck",
                    "oppo_deck",
                    "result",
                    "comments"
                ]
            )


def save_metagame_match(
        *,                  # placeholder for anything
        user_name: str,
        user_deck: str,
        oppo_deck: str,
        result:    str,
        comments:  str
) -> None:
    """
    Function to save the information provided by the user
    """
    _ensure_header(METAGAME_FILE)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with METAGAME_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [ts,
             user_name,
             user_deck,
             oppo_deck,
             result,
             comments]
        )


def save_ladder_match(
        *,                  # placeholder for anything
        user_name: str,
        user_deck: str,
        oppo_deck: str,
        result:    str,
        comments:  str
) -> None:
    """
    Function to save the information provided by the user
    """
    _ensure_header(LADDER_FILE)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with LADDER_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [ts,
             user_name,
             user_deck,
             oppo_deck,
             result,
             comments]
        )
