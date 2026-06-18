# utils/guild_settings.py

import json
from pathlib import Path

import config

SETTINGS_FILE = Path("data/guild_settings.json")

DEFAULT_SETTINGS = {
    "allowed_channels": {
        "challenge": None,
        "ladder": None,
    },
    "input_style": None,
    "delimiter": None,
    "save_location_key": None,
}


def load_all_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}

    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_all_settings(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _new_guild_settings() -> dict:
    return {
        "allowed_channels": {
            "challenge": None,
            "ladder": None,
        },
        "input_style": None,
        "delimiter": None,
        "save_location_key": None,
    }


def ensure_guild_entry(guild_id: int) -> None:
    data = load_all_settings()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
        save_all_settings(data)


def get_guild_settings(guild_id: int) -> dict:
    ensure_guild_entry(guild_id)

    data = load_all_settings()
    guild_key = str(guild_id)
    stored = data[guild_key]

    return {
        "allowed_channels": {
            "challenge": stored.get("allowed_channels", {}).get("challenge"),
            "ladder": stored.get("allowed_channels", {}).get("ladder"),
        },
        "input_style": stored.get("input_style"),
        "delimiter": stored.get("delimiter"),
        "save_location_key": stored.get("save_location_key"),
    }


def set_allowed_channel(guild_id: int, mode: str, channel_id: int | None) -> None:
    data = load_all_settings()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = _new_guild_settings()

    data[guild_key]["allowed_channels"][mode] = channel_id
    save_all_settings(data)


def set_input_style(guild_id: int, input_style: str | None) -> None:
    data = load_all_settings()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = _new_guild_settings()

    data[guild_key]["input_style"] = input_style
    save_all_settings(data)


def set_delimiter(guild_id: int, delimiter: str | None) -> None:
    data = load_all_settings()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = _new_guild_settings()

    data[guild_key]["delimiter"] = delimiter
    save_all_settings(data)


def set_save_location_key(guild_id: int, location_key: str | None) -> None:
    data = load_all_settings()
    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = _new_guild_settings()

    data[guild_key]["save_location_key"] = location_key
    save_all_settings(data)


def get_effective_allowed_channel(guild_id: int, mode: str):
    settings = get_guild_settings(guild_id)
    channel_id = settings["allowed_channels"].get(mode)

    if channel_id is not None:
        return channel_id

    fallback_map = {
        "challenge": getattr(config, "CHALLENGE_CHANNEL_ID", None),
        "ladder": getattr(config, "LADDER_CHANNEL_ID", None),
    }

    return fallback_map.get(mode)


def get_effective_input_style(guild_id: int) -> str:
    settings = get_guild_settings(guild_id)

    if settings["input_style"] is not None:
        return settings["input_style"]

    return getattr(config, "INPUT_STYLE", "result_delimiter_deck")


def get_effective_delimiter(guild_id: int) -> str:
    settings = get_guild_settings(guild_id)

    if settings["delimiter"] is not None:
        return settings["delimiter"]

    return getattr(config, "DELIMETER", " vs ")


def get_effective_save_location_key(guild_id: int) -> str:
    settings = get_guild_settings(guild_id)

    if settings["save_location_key"] is not None:
        return settings["save_location_key"]

    return getattr(config, "SAVE_LOCATION_KEY", "server_specific")


def get_effective_save_directory(guild_id: int) -> str:
    location_key = get_effective_save_location_key(guild_id)
    location_map = getattr(config, "SAVE_LOCATION_MAP", {})

    template = location_map.get(location_key)
    if template is None:
        template = "data/guilds/{guild_id}/"

    return template.format(guild_id=guild_id)
