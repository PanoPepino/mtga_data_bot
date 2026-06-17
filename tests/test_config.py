from config import (
    CHALLENGE_CHANNEL_ID,
    LADDER_CHANNEL_ID,
    TROPHY_WIN_COUNT,
    MAX_DECK_LENGTH,
)


def test_channel_ids_are_set():  #  evaluate that channels have ID not 0 and different from each other
    assert CHALLENGE_CHANNEL_ID != 0
    assert LADDER_CHANNEL_ID != 0
    assert CHALLENGE_CHANNEL_ID != LADDER_CHANNEL_ID


def test_trophy_win_count():
    assert TROPHY_WIN_COUNT == 7


def test_limits_are_positive():
    assert MAX_DECK_LENGTH > 0
