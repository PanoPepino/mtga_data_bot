import json

import utils.guild_settings as gs


def test_new_guild_settings_contains_expected_fields():
    settings = gs._new_guild_settings()

    assert settings == {
        "allowed_channels": {
            "challenge": None,
            "ladder": None,
        },
        "input_style": None,
        "delimiter": None,
        "save_location_key": None,
        "challenge_file": None,
        "ladder_file": None,
    }


def test_load_all_settings_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    assert gs.load_all_settings() == {}


def test_save_all_settings_writes_json(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    data = {
        "123": {
            "allowed_channels": {"challenge": None, "ladder": None},
            "input_style": None,
            "delimiter": None,
            "save_location_key": None,
            "challenge_file": None,
            "ladder_file": None,
        }
    }

    gs.save_all_settings(data)

    assert settings_file.exists()
    assert json.loads(settings_file.read_text(encoding="utf-8")) == data


def test_ensure_guild_entry_creates_default_entry(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 321
    gs.ensure_guild_entry(guild_id)
    data = gs.load_all_settings()

    assert str(guild_id) in data
    assert data[str(guild_id)]["challenge_file"] is None
    assert data[str(guild_id)]["ladder_file"] is None


def test_get_guild_settings_includes_file_fields(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 321
    gs.ensure_guild_entry(guild_id)
    data = gs.get_guild_settings(guild_id)

    assert "challenge_file" in data
    assert "ladder_file" in data
    assert data["challenge_file"] is None
    assert data["ladder_file"] is None


def test_effective_file_getters_fall_back_to_config(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(gs.config, "CHALLENGE_FILE", "challenge_default.csv", raising=False)
    monkeypatch.setattr(gs.config, "LADDER_FILE", "ladder_default.csv", raising=False)

    guild_id = 12345

    assert gs.get_effective_challenge_file(guild_id) == "challenge_default.csv"
    assert gs.get_effective_ladder_file(guild_id) == "ladder_default.csv"


def test_effective_file_getters_use_guild_override(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(gs.config, "CHALLENGE_FILE", "challenge_default.csv", raising=False)
    monkeypatch.setattr(gs.config, "LADDER_FILE", "ladder_default.csv", raising=False)

    guild_id = 12345
    gs.set_challenge_file(guild_id, "challenge_custom.csv")
    gs.set_ladder_file(guild_id, "ladder_custom.csv")

    assert gs.get_effective_challenge_file(guild_id) == "challenge_custom.csv"
    assert gs.get_effective_ladder_file(guild_id) == "ladder_custom.csv"


def test_effective_save_directory_uses_guild_override(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(
        gs.config,
        "SAVE_LOCATION_MAP",
        {
            "server_specific": "data/guilds/{guild_id}/",
            "archive": "data/archive/{guild_id}/",
        },
        raising=False,
    )
    monkeypatch.setattr(gs.config, "SAVE_LOCATION_KEY", "server_specific", raising=False)

    guild_id = 999
    gs.set_save_location_key(guild_id, "archive")

    assert gs.get_effective_save_directory(guild_id) == "data/archive/999/"


def test_set_allowed_channel_updates_one_mode(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 777
    gs.set_allowed_channel(guild_id, "challenge", 111)

    data = gs.get_guild_settings(guild_id)
    assert data["allowed_channels"]["challenge"] == 111
    assert data["allowed_channels"]["ladder"] is None


def test_set_input_style_updates_value(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 888
    gs.set_input_style(guild_id, "deck_delimiter_result")

    assert gs.get_guild_settings(guild_id)["input_style"] == "deck_delimiter_result"


def test_set_delimiter_updates_value(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 888
    gs.set_delimiter(guild_id, " | ")

    assert gs.get_guild_settings(guild_id)["delimiter"] == " | "


def test_invalid_mode_raises_value_error(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    try:
        gs.set_allowed_channel(123, "invalid_mode", 999)
        assert False, "Expected ValueError for invalid mode"
    except ValueError as e:
        assert "Mode must be" in str(e)


def test_invalid_save_location_key_raises_value_error(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(
        gs.config,
        "SAVE_LOCATION_MAP",
        {"server_specific": "data/guilds/{guild_id}/"},
        raising=False,
    )

    try:
        gs.set_save_location_key(123, "not_real")
        assert False, "Expected ValueError for invalid save location key"
    except ValueError as e:
        assert "Invalid save location key" in str(e)