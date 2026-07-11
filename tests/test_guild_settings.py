from pathlib import Path

import utils.guild_settings as gs


def test_new_guild_settings_contains_file_fields():
    settings = gs._new_guild_settings()

    assert "challenge_file" in settings
    assert "ladder_file" in settings
    assert settings["challenge_file"] is None
    assert settings["ladder_file"] is None


def test_effective_file_getters_fall_back_to_config(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(gs.config, "CHALLENGE_FILE", "challenge_default.csv")
    monkeypatch.setattr(gs.config, "LADDER_FILE", "ladder_default.csv")

    guild_id = 12345

    assert gs.get_effective_challenge_file(guild_id) == "challenge_default.csv"
    assert gs.get_effective_ladder_file(guild_id) == "ladder_default.csv"


def test_effective_file_getters_use_guild_override(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)
    monkeypatch.setattr(gs.config, "CHALLENGE_FILE", "challenge_default.csv")
    monkeypatch.setattr(gs.config, "LADDER_FILE", "ladder_default.csv")

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
    )
    monkeypatch.setattr(gs.config, "SAVE_LOCATION_KEY", "server_specific")

    guild_id = 999
    gs.set_save_location_key(guild_id, "archive")

    assert gs.get_effective_save_directory(guild_id) == "data/archive/999/"


def test_get_guild_settings_includes_file_fields(tmp_path, monkeypatch):
    settings_file = tmp_path / "guild_settings.json"
    monkeypatch.setattr(gs, "SETTINGS_FILE", settings_file)

    guild_id = 321
    gs.ensure_guild_entry(guild_id)
    data = gs.get_guild_settings(guild_id)

    assert "challenge_file" in data
    assert "ladder_file" in data
