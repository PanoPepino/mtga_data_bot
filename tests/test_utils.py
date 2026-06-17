from cogs.utils import build_ladder_description
from cogs.utils import parse_runs, validate_run_ladder, validate_runs_metagame, check_trophy


def test_parse_two_runs():
    text = "Run 1:\nGB Lands 2-1\nW Stompy 0-2\n\nRun 2:\nSultai Shadow 2-0"
    runs = parse_runs(text)
    assert len(runs) == 2
    assert runs[0][0] == ("GB Lands", "2-1")
    assert runs[1][0] == ("Sultai Shadow", "2-0")


def test_validate_valid_runs():
    runs = [[("GB Lands", "2-1"), ("W Stompy", "0-2")]]
    raw = "Run 1:\nGB Lands 2-1\nW Stompy 0-2"
    assert validate_runs_metagame(runs, raw) == []


def test_validate_empty():
    raw = "Run 1:\n"
    assert validate_runs_metagame([], raw) != []


def test_validate_bad_result():
    runs = [[("GB Lands", "win")]]
    raw = "Run 1:\nGB Lands win"
    errors = validate_runs_metagame(runs, raw)
    assert len(errors) > 0


def test_validate_empty_run():
    runs = [[]]
    raw = "Run 1:\n"  # header but no matches
    errors = validate_runs_metagame(runs, raw)
    assert len(errors) > 0


def test_build_ladder_description_basic():
    desc = build_ladder_description(
        "Izzet Tempo",
        "GB Lands 2-1\nW Stompy 0-2",
        "",
    )
    assert "**deck:** Izzet Tempo" in desc
    assert "GB Lands 2-1" in desc
    assert "W Stompy 0-2" in desc
    assert "comments" not in desc


def test_build_ladder_description_with_comments():
    desc = build_ladder_description(
        "Izzet Tempo",
        "GB Lands 2-1",
        "felt great",
    )
    assert "*comments: felt great*" in desc


def test_trophy_7_wins():
    matches = [("GB Lands", "2-1"),
               ("W Stompy", "2-0"),
               ("UR Tempo", "2-1"),
               ("R Stompy", "2-0"),
               ("UWR Necro", "2-1"),
               ("R Burn",   "2-0"),
               ("UBG Shadow", "2-1")]
    assert check_trophy(matches) is True


def test_trophy_fails_with_loss():
    matches = [("GB Lands", "2-1"),
               ("W Stompy", "2-0"),
               ("UR Tempo", "2-1"),
               ("R Stompy", "2-0"),
               ("UWR Necro", "2-1"),
               ("R Burn",   "2-0"),
               ("UBG Shadow", "0-2")]
    assert check_trophy(matches) is False


def test_trophy_fails_wrong_count():
    matches = [("GB Lands", "2-1"),
               ("W Stompy", "2-0"),
               ("UR Tempo", "2-1"),
               ("R Stompy", "2-0"),
               ("UWR Necro", "2-1"),
               ("R Burn",   "2-0")]
    assert check_trophy(matches) is False
