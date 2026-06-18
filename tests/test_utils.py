import pytest

from utils.parse_and_check import (
    check_trophy,
    get_placeholder,
    parse_match_line,
    parse_runs,
    summarise_run_record,
    validate_run_ladder,
    validate_runs_metagame,
)


@pytest.mark.parametrize(
    "line,input_style,delimiter,expected",
    [
        ("GB Lands vs 2-1", "deck_delimiter_result", " vs ", ("GB Lands", "2-1")),
        ("2-1 vs GB Lands", "result_delimiter_deck", " vs ", ("GB Lands", "2-1")),
        ("Mono Red - 0-2", "deck_delimiter_result", " - ", ("Mono Red", "0-2")),
        ("2-0 | Azorius Control", "result_delimiter_deck", " | ", ("Azorius Control", "2-0")),
    ],
)
def test_parse_match_line_valid(line, input_style, delimiter, expected):
    assert parse_match_line(line, input_style, delimiter) == expected


@pytest.mark.parametrize(
    "line,input_style,delimiter",
    [
        ("GB Lands 2-1", "deck_delimiter_result", " vs "),
        ("", "deck_delimiter_result", " vs "),
        ("2-1", "result_delimiter_deck", " vs "),
    ],
)
def test_parse_match_line_invalid_structure(line, input_style, delimiter):
    assert parse_match_line(line, input_style, delimiter) is None


def test_parse_match_line_bad_result_is_parsed_but_invalid_later():
    parsed = parse_match_line("GB Lands vs win", "deck_delimiter_result", " vs ")
    assert parsed == ("GB Lands", "win")


def test_parse_runs_two_runs_deck_delimiter_result():
    text = (
        "Run 1:\n"
        "GB Lands vs 2-1\n"
        "W Stompy vs 0-2\n\n"
        "Run 2:\n"
        "Sultai Shadow vs 2-0"
    )

    runs = parse_runs(text, "deck_delimiter_result", " vs ")

    assert len(runs) == 2
    assert runs[0][0] == ("GB Lands", "2-1")
    assert runs[0][1] == ("W Stompy", "0-2")
    assert runs[1][0] == ("Sultai Shadow", "2-0")


def test_parse_runs_two_runs_result_delimiter_deck():
    text = (
        "Run 1:\n"
        "2-1 vs GB Lands\n"
        "0-2 vs W Stompy\n\n"
        "Run 2:\n"
        "2-0 vs Sultai Shadow"
    )

    runs = parse_runs(text, "result_delimiter_deck", " vs ")

    assert len(runs) == 2
    assert runs[0][0] == ("GB Lands", "2-1")
    assert runs[0][1] == ("W Stompy", "0-2")
    assert runs[1][0] == ("Sultai Shadow", "2-0")


def test_validate_runs_metagame_valid_deck_delimiter_result():
    raw = (
        "Run 1:\n"
        "GB Lands vs 2-1\n"
        "W Stompy vs 0-2"
    )
    runs = [[("GB Lands", "2-1"), ("W Stompy", "0-2")]]

    assert validate_runs_metagame(runs, raw, "deck_delimiter_result") == []


def test_validate_runs_metagame_valid_result_delimiter_deck():
    raw = (
        "Run 1:\n"
        "2-1 vs GB Lands\n"
        "0-2 vs W Stompy"
    )
    runs = [[("GB Lands", "2-1"), ("W Stompy", "0-2")]]

    assert validate_runs_metagame(runs, raw, "result_delimiter_deck") == []


def test_validate_runs_metagame_empty():
    raw = "Run 1:\n"
    errors = validate_runs_metagame([], raw, "deck_delimiter_result")
    assert errors != []


def test_validate_runs_metagame_empty_run():
    raw = "Run 1:\n"
    runs = [[]]
    errors = validate_runs_metagame(runs, raw, "deck_delimiter_result")
    assert errors != []


def test_validate_runs_metagame_bad_result():
    raw = "Run 1:\nGB Lands vs win"
    runs = [[("GB Lands", "win")]]
    errors = validate_runs_metagame(runs, raw, "deck_delimiter_result")
    assert errors != []


def test_validate_run_ladder_valid_deck_delimiter_result():
    raw = "GB Lands vs 2-1\nW Stompy vs 0-2"
    errors = validate_run_ladder(raw, "deck_delimiter_result", " vs ")
    assert errors == []


def test_validate_run_ladder_valid_result_delimiter_deck():
    raw = "2-1 vs GB Lands\n0-2 vs W Stompy"
    errors = validate_run_ladder(raw, "result_delimiter_deck", " vs ")
    assert errors == []


def test_validate_run_ladder_invalid_missing_delimiter():
    raw = "GB Lands 2-1"
    errors = validate_run_ladder(raw, "deck_delimiter_result", " vs ")
    assert errors != []


def test_validate_run_ladder_invalid_bad_result():
    raw = "GB Lands vs win"
    errors = validate_run_ladder(raw, "deck_delimiter_result", " vs ")
    assert errors != []


def test_summarise_run_record_all_wins():
    run = [("Deck A", "2-1"), ("Deck B", "2-0"), ("Deck C", "2-1")]
    assert summarise_run_record(run) == "3-0"


def test_summarise_run_record_mixed():
    run = [("Deck A", "2-1"), ("Deck B", "0-2"), ("Deck C", "2-0")]
    assert summarise_run_record(run) == "2-1"


def test_trophy_7_wins():
    matches = [
        ("GB Lands", "2-1"),
        ("W Stompy", "2-0"),
        ("UR Tempo", "2-1"),
        ("R Stompy", "2-0"),
        ("UWR Necro", "2-1"),
        ("R Burn", "2-0"),
        ("UBG Shadow", "2-1"),
    ]
    assert check_trophy(matches) is True


def test_trophy_fails_with_loss():
    matches = [
        ("GB Lands", "2-1"),
        ("W Stompy", "2-0"),
        ("UR Tempo", "2-1"),
        ("R Stompy", "2-0"),
        ("UWR Necro", "2-1"),
        ("R Burn", "2-0"),
        ("UBG Shadow", "0-2"),
    ]
    assert check_trophy(matches) is False


def test_trophy_fails_wrong_count():
    matches = [
        ("GB Lands", "2-1"),
        ("W Stompy", "2-0"),
        ("UR Tempo", "2-1"),
        ("R Stompy", "2-0"),
        ("UWR Necro", "2-1"),
        ("R Burn", "2-0"),
    ]
    assert check_trophy(matches) is False


@pytest.mark.parametrize(
    "input_style,delimiter,expected",
    [
        ("deck_delimiter_result", " vs ", "GB Lands vs 2-1\nW Stompy vs 0-2"),
        ("result_delimiter_deck", " vs ", "2-1 vs GB Lands\n0-2 vs R Stompy"),
        ("deck_delimiter_result", " - ", "GB Lands - 2-1\nW Stompy - 0-2"),
        ("result_delimiter_deck", " | ", "2-1 | GB Lands\n0-2 | R Stompy"),
    ],
)
def test_get_placeholder(input_style, delimiter, expected):
    assert get_placeholder(input_style, delimiter) == expected
