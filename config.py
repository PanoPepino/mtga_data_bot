# Basic .py file to locate ID of channels, coloring etc.


# Channels
LADDER_CHANNEL_ID = None  # ID for ladder channel
CHALLENGE_CHANNEL_ID = None   # ID for challenge channel

# Colors
COLOR_NORMAL = 0x5865F2
COLOR_TROPHY = 0xFFD700  # Gold

# To avoid over-clogging the bot/channels, I will set some limits

# Limits input
MAX_MATCHES_LENGTH = 700
MAX_DECK_LENGTH = 80
MAX_COMMENT_LENGTH = 300


# Trophy condition
TROPHY_WIN_COUNT = 7

# Default delimiter used to separate deck name and result in match lines.
# Admins can override this per-server via /settings.
DELIMITER = " vs "

# Default input style: which side of the delimiter is the deck name.
# Options: "deck_delimiter_result" | "result_delimiter_deck"
# Admins can override this per-server via /settings.
INPUT_STYLE = "result_delimiter_deck"

# Saving location
SAVE_LOCATION_KEY = "server_specific"

SAVE_LOCATION_MAP = {
    "server_specific": "data/guilds/{guild_id}/",
    "shared": "data/shared/",
    "archive": "data/archive/{guild_id}/",
}

MTGA_DATA_DIR = 'collected_data'
LADDER_FILE = 'ladder_2026_06.csv'
CHALLENGE_FILE = 'challenge_2026_07.csv'


# Ladder 1515989671631519754
# challenge 1515970497974632561
