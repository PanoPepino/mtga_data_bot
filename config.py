# Basic .py file to locate ID of channels, coloring etc.


# Channels
LADDER_CHANNEL_ID = 1515989671631519754   # ID for ladder channel
CHALLENGE_CHANNEL_ID = 1515970497974632561   # ID for challenge channel

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


# Saving location
MTGA_DATA_DIR = 'collected_data'
LADDER_FILE = 'ladder_2026_06.csv'
CHALLENGE_FILE = 'challenge_2026_07.csv'


# input style
DELIMITER = ' vs '  # how to separate results and oppo_deck inf
INPUT_STYLE = 'result_delimiter_deck'  # change to deck_delimiter_result to place first deck and then result


# Placeholder error and example for discord messages

PH_DECK_DELIMITER_RESULT = (
    f"GB Lands{DELIMITER}2-1\n"
    f"W Stompy{DELIMITER}0-2"
)

PH_RESULT_DELIMITER_DECK = (
    f"2-1{DELIMITER}GB Lands\n"
    f"0-2{DELIMITER}R Stompy"
)
