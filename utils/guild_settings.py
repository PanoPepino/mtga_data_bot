# utils/guild_settings.py
#
# Stores and retrieves per-server (guild) settings.
#
# HOW IT WORKS:
#   - All settings are saved in data/guild_settings.json, keyed by guild ID.
#   - Each getter first checks the JSON for a guild-specific override.
#   - If no override exists, it falls back to the global value in config.py.
#   - Admins update these settings via the /settings slash commands in Discord.
#     You should never need to edit the JSON file manually.

import json
from pathlib import Path

import config

# Path to the JSON file that stores all per-guild settings.
SETTINGS_FILE = Path("data/guild_settings.json")


def _new_guild_settings() -> dict:
    """Return a blank settings block for a new guild.
    All values are None, which tells every getter to fall back to config.py."""
    return {
        "allowed_channels": {
            "challenge": None,  # channel ID (int) or None = no restriction
            "ladder": None,
        },
        "input_style": None,      # e.g. "result_delimiter_deck" or None = use config
        "delimiter": None,        # e.g. " vs " or None = use config
        "save_location_key": None, # e.g. "server_specific" or None = use config
    }


# ---------------------------------------------------------------------------
# Low-level read / write helpers
# ---------------------------------------------------------------------------

def load_all_settings() -> dict:
    """Load the full JSON file into a dict. Returns {} if file does not exist."""
    if not SETTINGS_FILE.exists():
        return {}
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_all_settings(data: dict) -> None:
    """Write the full settings dict back to the JSON file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ensure_guild_entry(guild_id: int) -> None:
    """Create a blank entry for this guild if one does not already exist."""
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
        save_all_settings(data)


def get_guild_settings(guild_id: int) -> dict:
    """Return the raw stored settings for this guild (not merged with config defaults)."""
    ensure_guild_entry(guild_id)
    data = load_all_settings()
    stored = data[str(guild_id)]
    return {
        "allowed_channels": {
            "challenge": stored.get("allowed_channels", {}).get("challenge"),
            "ladder": stored.get("allowed_channels", {}).get("ladder"),
        },
        "input_style": stored.get("input_style"),
        "delimiter": stored.get("delimiter"),
        "save_location_key": stored.get("save_location_key"),
    }


# ---------------------------------------------------------------------------
# Setters — called by /settings commands
# ---------------------------------------------------------------------------

def set_allowed_channel(guild_id: int, mode: str, channel_id: int | None) -> None:
    """Set (or clear) the allowed channel for 'challenge' or 'ladder' in this guild."""
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["allowed_channels"][mode] = channel_id
    save_all_settings(data)


def set_input_style(guild_id: int, input_style: str | None) -> None:
    """Set (or reset to None) the input style for this guild."""
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["input_style"] = input_style
    save_all_settings(data)


def set_delimiter(guild_id: int, delimiter: str | None) -> None:
    """Set (or reset to None) the delimiter for this guild."""
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["delimiter"] = delimiter
    save_all_settings(data)


def set_save_location_key(guild_id: int, location_key: str | None) -> None:
    """Set (or reset to None) the save location key for this guild."""
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["save_location_key"] = location_key
    save_all_settings(data)


# ---------------------------------------------------------------------------
# Effective getters — merge guild override with config.py fallback
# ---------------------------------------------------------------------------

def get_effective_allowed_channel(guild_id: int, mode: str) -> int | None:
    """Return the allowed channel ID for this mode in this guild.
    Returns None if no restriction is set (command allowed anywhere)."""
    settings = get_guild_settings(guild_id)
    channel_id = settings["allowed_channels"].get(mode)
    if channel_id is not None:
        return channel_id
    # Fall back to config.py values
    fallback_map = {
        "challenge": getattr(config, "CHALLENGE_CHANNEL_ID", None),
        "ladder": getattr(config, "LADDER_CHANNEL_ID", None),
    }
    return fallback_map.get(mode)


def get_effective_input_style(guild_id: int) -> str:
    """Return the input style for this guild, falling back to config.INPUT_STYLE."""
    settings = get_guild_settings(guild_id)
    if settings["input_style"] is not None:
        return settings["input_style"]
    return getattr(config, "INPUT_STYLE", "result_delimiter_deck")


def get_effective_delimiter(guild_id: int) -> str:
    """Return the delimiter for this guild, falling back to config.DELIMITER.
    Note: config.py spells it DELIMITER (no extra E)."""
    settings = get_guild_settings(guild_id)
    if settings["delimiter"] is not None:
        return settings["delimiter"]
    return getattr(config, "DELIMITER", " vs ")  # fixed: was DELIMETER (typo)


def get_effective_save_location_key(guild_id: int) -> str:
    """Return the save location key for this guild, falling back to config.SAVE_LOCATION_KEY."""
    settings = get_guild_settings(guild_id)
    if settings["save_location_key"] is not None:
        return settings["save_location_key"]
    return getattr(config, "SAVE_LOCATION_KEY", "server_specific")


def get_effective_save_directory(guild_id: int) -> str:
    """Return the resolved save directory path for this guild.
    Looks up the location key, then formats the path template with the guild ID."""
    location_key = get_effective_save_location_key(guild_id)
    location_map = getattr(config, "SAVE_LOCATION_MAP", {})
    template = location_map.get(location_key, "data/guilds/{guild_id}/")
    return template.format(guild_id=guild_id)
