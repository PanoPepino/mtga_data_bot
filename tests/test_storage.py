import csv
from pathlib import Path

from cogs.storage import (
    _resolve_metagame_path,
    _resolve_ladder_path,
    save_metagame_match,
    save_ladder_match,
)


def test_resolve_metagame_path_joins_directory_and_filename():
    path = _resolve_metagame_path("data/guilds/123", "challenge_july.csv")
    assert path == Path("data/guilds/123") / "challenge_july.csv"


def test_resolve_ladder_path_joins_directory_and_filename():
    path = _resolve_ladder_path("data/guilds/123", "ladder_july.csv")
    assert path == Path("data/guilds/123") / "ladder_july.csv"


def test_save_metagame_match_creates_file_and_header(tmp_path):
    save_dir = str(tmp_path / "guild_1")
    file_name = "challenge_test.csv"

    save_metagame_match(
        user_name="Alice",
        user_deck="Izzet Tempo",
        run_result="7-2",
        oppo_deck="Mono Red",
        result="W",
        comments="nice run",
        save_dir=save_dir,
        file_name=file_name,
    )

    path = Path(save_dir) / file_name
    assert path.exists()

    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == [
        "timestamp_utc",
        "user_name",
        "user_deck",
        "run_result",
        "oppo_deck",
        "result",
        "comments",
    ]
    assert rows[1][1:] == ["Alice", "Izzet Tempo", "7-2", "Mono Red", "W", "nice run"]


def test_save_ladder_match_creates_file_and_header(tmp_path):
    save_dir = str(tmp_path / "guild_1")
    file_name = "ladder_test.csv"

    save_ladder_match(
        user_name="Bob",
        user_deck="Azorius Control",
        oppo_deck="Gruul Aggro",
        result="L",
        comments="flooded out",
        save_dir=save_dir,
        file_name=file_name,
    )

    path = Path(save_dir) / file_name
    assert path.exists()

    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == [
        "timestamp_utc",
        "user_name",
        "user_deck",
        "oppo_deck",
        "result",
        "comments",
    ]
    assert rows[1][1:] == ["Bob", "Azorius Control", "Gruul Aggro", "L", "flooded out"]


def test_save_metagame_match_appends_multiple_rows(tmp_path):
    save_dir = str(tmp_path / "guild_2")
    file_name = "challenge_test.csv"

    save_metagame_match(
        user_name="Alice",
        user_deck="Deck A",
        run_result="7-1",
        oppo_deck="Deck X",
        result="W",
        comments="",
        save_dir=save_dir,
        file_name=file_name,
    )
    save_metagame_match(
        user_name="Alice",
        user_deck="Deck A",
        run_result="7-1",
        oppo_deck="Deck Y",
        result="L",
        comments="",
        save_dir=save_dir,
        file_name=file_name,
    )

    path = Path(save_dir) / file_name
    rows = list(csv.reader(path.open(encoding="utf-8")))

    assert len(rows) == 3
    assert rows[1][4] == "Deck X"
    assert rows[2][4] == "Deck Y"
