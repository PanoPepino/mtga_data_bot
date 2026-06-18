from config import (
    CHALLENGE_CHANNEL_ID,
    LADDER_CHANNEL_ID,
    TROPHY_WIN_COUNT,
    MAX_DECK_LENGTH,
)


def test_channel_ids_are_none_or_int():
    """Channel IDs default to None in config.py.
    Per-guild overrides are handled by guild_settings, not config.
    """
    assert CHALLENGE_CHANNEL_ID is None or isinstance(CHALLENGE_CHANNEL_ID, int)
    assert LADDER_CHANNEL_ID is None or isinstance(LADDER_CHANNEL_ID, int)


def test_trophy_win_count():
    assert TROPHY_WIN_COUNT == 7


def test_limits_are_positive():
    assert MAX_DECK_LENGTH > 0
