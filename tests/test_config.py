import config


def test_channel_ids_are_none_or_int():
    """Global channel restrictions are optional and must be None or an int."""
    assert config.CHALLENGE_CHANNEL_ID is None or isinstance(config.CHALLENGE_CHANNEL_ID, int)
    assert config.LADDER_CHANNEL_ID is None or isinstance(config.LADDER_CHANNEL_ID, int)


def test_trophy_win_count_is_expected():
    """A trophy run is still defined as 7 wins."""
    assert config.TROPHY_WIN_COUNT == 7


def test_length_limits_are_positive_integers():
    """User-facing text limits should be positive integer values."""
    assert isinstance(config.MAX_DECK_LENGTH, int)
    assert config.MAX_DECK_LENGTH > 0

    assert isinstance(config.MAX_COMMENT_LENGTH, int)
    assert config.MAX_COMMENT_LENGTH > 0

    assert isinstance(config.MAX_MATCHES_LENGTH, int)
    assert config.MAX_MATCHES_LENGTH > 0


def test_runtime_limits_are_positive():
    """Concurrency and cooldown values must be usable positive numbers."""
    assert isinstance(config.GUILD_ACTIVE_LIMIT, int)
    assert config.GUILD_ACTIVE_LIMIT > 0

    assert isinstance(config.USER_SUBMIT_COOLDOWN, (int, float))
    assert config.USER_SUBMIT_COOLDOWN > 0


def test_default_input_settings_are_valid():
    """Parser defaults should use one of the supported styles and a non-empty delimiter."""
    assert config.INPUT_STYLE in {
        "deck_delimiter_result",
        "result_delimiter_deck",
    }
    assert isinstance(config.DELIMITER, str)
    assert config.DELIMITER != ""


def test_csv_file_defaults_look_safe():
    """Default CSV file names should be plain .csv filenames, not paths."""
    for filename in (config.CHALLENGE_FILE, config.LADDER_FILE):
        assert isinstance(filename, str)
        assert filename.endswith(".csv")
        assert "/" not in filename
        assert "\\" not in filename
        assert filename.strip() == filename
        assert filename != ""


def test_save_location_defaults_are_consistent():
    """Default save-location config should point to a known key in the save-location map."""
    assert isinstance(config.SAVE_LOCATION_MAP, dict)
    assert config.SAVE_LOCATION_MAP
    assert config.SAVE_LOCATION_KEY in config.SAVE_LOCATION_MAP


def test_allowed_guild_ids_are_ints():
    """Guild allowlist should contain only integer guild IDs."""
    assert isinstance(config.ALLOWED_GUILD_IDS, set)
    assert all(isinstance(guild_id, int) for guild_id in config.ALLOWED_GUILD_IDS)