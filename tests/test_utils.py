from cogs.utils import parse_runs, validate_runs, check_trophy


def test_parse_two_runs():
    text = "Run 1:\nGB Lands 2-1\nW Stompy 0-2\n\nRun 2:\nSultai Shadow 2-0"
    runs = parse_runs(text)
    assert len(runs) == 2
    assert runs[0][0] == ("GB Lands", "2-1")
    assert runs[1][0] == ("Sultai Shadow", "2-0")


def test_validate_valid_runs():
    runs = [[("GB Lands", "2-1"), ("W Stompy", "0-2")]]
    assert validate_runs(runs) == []


def test_validate_empty():
    assert validate_runs([]) != []


def test_validate_bad_result():
    runs = [[("GB Lands", "win")]]
    errors = validate_runs(runs)
    assert len(errors) > 0


def test_validate_empty_run():
    runs = [[]]
    errors = validate_runs(runs)
    assert len(errors) > 0


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
