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

    All values default to None, which instructs every effective getter
    to fall back to the corresponding value in config.py.  This means
    the bot always has a usable value even before an admin has run any
    /settings command.

    Returns:
        dict: A settings template with None for every configurable key.
    """
    return {
        "allowed_channels": {
            "challenge": None,   # int channel ID, or None = no restriction
            "ladder": None,      # int channel ID, or None = no restriction
        },
        "input_style": None,        # e.g. "result_delimiter_deck" or None = use config
        "delimiter": None,          # e.g. " vs " or None = use config
        "save_location_key": None,  # e.g. "server_specific" or None = use config
        "challenge_file": None,     # e.g. "challenge_june.csv" or None = use config
        "ladder_file": None,        # e.g. "ladder_june.csv" or None = use config
    }


# ---------------------------------------------------------------------------
# Low-level read / write helpers
# ---------------------------------------------------------------------------

def load_all_settings() -> dict:
    """Load the full guild settings JSON file into a dict.

    Returns:
        dict: Mapping of guild_id (str) -> settings dict.
              Returns an empty dict if the file does not exist yet.
    """
    if not SETTINGS_FILE.exists():
        return {}
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_all_settings(data: dict) -> None:
    """Write the full settings dict back to the JSON file.

    Creates the parent directory automatically if it does not exist.

    Args:
        data: The complete settings mapping to persist.
    """
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ensure_guild_entry(guild_id: int) -> None:
    """Create a blank settings entry for this guild if one does not already exist.

    This is called automatically by get_guild_settings, so most callers do
    not need to call it directly.

    Args:
        guild_id: The Discord guild (server) ID.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
        save_all_settings(data)


def get_guild_settings(guild_id: int) -> dict:
    """Return the raw stored settings for this guild (not merged with config defaults).

    Callers that need a guaranteed usable value should use one of the
    get_effective_* functions instead, which apply the config.py fallback.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        dict: The stored settings for this guild, with None for any key
              that has not been set by an admin yet.
    """
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
        "challenge_file": stored.get("challenge_file"),
        "ladder_file": stored.get("ladder_file"),
    }


# ---------------------------------------------------------------------------
# Setters — called by /settings commands in cogs/settings.py
# ---------------------------------------------------------------------------

def set_allowed_channel(guild_id: int, mode: str, channel_id: int | None) -> None:
    """Set or clear the allowed channel for a given mode in this guild.

    Args:
        guild_id:   The Discord guild (server) ID.
        mode:       Either "challenge" or "ladder".
        channel_id: The channel ID to restrict to, or None to remove the restriction.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["allowed_channels"][mode] = channel_id
    save_all_settings(data)


def set_input_style(guild_id: int, input_style: str | None) -> None:
    """Set or reset the input style for this guild.

    Args:
        guild_id:    The Discord guild (server) ID.
        input_style: One of the INPUT_STYLE values defined in config.py,
                     or None to fall back to the config default.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["input_style"] = input_style
    save_all_settings(data)


def set_delimiter(guild_id: int, delimiter: str | None) -> None:
    """Set or reset the match-line delimiter for this guild.

    Args:
        guild_id:  The Discord guild (server) ID.
        delimiter: The separator string (e.g. " vs "), or None to use config default.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["delimiter"] = delimiter
    save_all_settings(data)


def set_save_location_key(guild_id: int, location_key: str | None) -> None:
    """Set or reset the save-location policy key for this guild.

    Args:
        guild_id:     The Discord guild (server) ID.
        location_key: A key from config.SAVE_LOCATION_MAP (e.g. "server_specific"),
                      or None to fall back to the config default.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["save_location_key"] = location_key
    save_all_settings(data)


def set_challenge_file(guild_id: int, filename: str | None) -> None:
    """Set or reset the challenge CSV filename for this guild.

    Only the bare filename (e.g. "challenge_june.csv") should be stored here.
    The directory is resolved separately by get_effective_save_directory.
    Pass None to fall back to config.CHALLENGE_FILE.

    Args:
        guild_id: The Discord guild (server) ID.
        filename: A .csv filename string, or None to use the config default.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["challenge_file"] = filename
    save_all_settings(data)


def set_ladder_file(guild_id: int, filename: str | None) -> None:
    """Set or reset the ladder CSV filename for this guild.

    Only the bare filename (e.g. "ladder_june.csv") should be stored here.
    The directory is resolved separately by get_effective_save_directory.
    Pass None to fall back to config.LADDER_FILE.

    Args:
        guild_id: The Discord guild (server) ID.
        filename: A .csv filename string, or None to use the config default.
    """
    data = load_all_settings()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = _new_guild_settings()
    data[guild_key]["ladder_file"] = filename
    save_all_settings(data)


# ---------------------------------------------------------------------------
# Effective getters — merge guild override with config.py fallback
# ---------------------------------------------------------------------------

def get_effective_allowed_channel(guild_id: int, mode: str) -> int | None:
    """Return the allowed channel ID for a mode in this guild.

    Returns None if no restriction is set, meaning the command is
    allowed in any channel.

    Args:
        guild_id: The Discord guild (server) ID.
        mode:     Either "challenge" or "ladder".

    Returns:
        int | None: The restricted channel ID, or None for no restriction.
    """
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
    """Return the input style for this guild, falling back to config.INPUT_STYLE.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: The input style key (e.g. "result_delimiter_deck").
    """
    settings = get_guild_settings(guild_id)
    if settings["input_style"] is not None:
        return settings["input_style"]
    return getattr(config, "INPUT_STYLE", "result_delimiter_deck")


def get_effective_delimiter(guild_id: int) -> str:
    """Return the match-line delimiter for this guild, falling back to config.DELIMITER.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: The delimiter string (e.g. " vs ").
    """
    settings = get_guild_settings(guild_id)
    if settings["delimiter"] is not None:
        return settings["delimiter"]
    return getattr(config, "DELIMITER", " vs ")


def get_effective_save_location_key(guild_id: int) -> str:
    """Return the save-location policy key for this guild, falling back to config.SAVE_LOCATION_KEY.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: A key from config.SAVE_LOCATION_MAP (e.g. "server_specific").
    """
    settings = get_guild_settings(guild_id)
    if settings["save_location_key"] is not None:
        return settings["save_location_key"]
    return getattr(config, "SAVE_LOCATION_KEY", "server_specific")


def get_effective_save_directory(guild_id: int) -> str:
    """Return the resolved save-directory path string for this guild.

    Looks up the location key then formats the path template from
    config.SAVE_LOCATION_MAP with the guild ID substituted in.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: The directory path where this guild's CSV files are stored
             (e.g. "data/guilds/123456789/").
    """
    location_key = get_effective_save_location_key(guild_id)
    location_map = getattr(config, "SAVE_LOCATION_MAP", {})
    template = location_map.get(location_key, "data/guilds/{guild_id}/")
    return template.format(guild_id=guild_id)


def get_effective_challenge_file(guild_id: int) -> str:
    """Return the challenge CSV filename for this guild, falling back to config.CHALLENGE_FILE.

    This is the bare filename only (e.g. "challenge_june.csv").
    Combine it with get_effective_save_directory() to get the full path.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: The CSV filename for challenge data.
    """
    settings = get_guild_settings(guild_id)
    if settings.get("challenge_file") is not None:
        return settings["challenge_file"]
    return getattr(config, "CHALLENGE_FILE", "challenge.csv")


def get_effective_ladder_file(guild_id: int) -> str:
    """Return the ladder CSV filename for this guild, falling back to config.LADDER_FILE.

    This is the bare filename only (e.g. "ladder_june.csv").
    Combine it with get_effective_save_directory() to get the full path.

    Args:
        guild_id: The Discord guild (server) ID.

    Returns:
        str: The CSV filename for ladder data.
    """
    settings = get_guild_settings(guild_id)
    if settings.get("ladder_file") is not None:
        return settings["ladder_file"]
    return getattr(config, "LADDER_FILE", "ladder.csv")
