from datetime import datetime, timezone  # People will play at different timezones, so better to collect

# Creating the mock seassion dic

_sessions: dict[int, dict] = {}


def create_session(user_id: int,
                   deck: str,
                   message_id: int,  # Required to make the bot display all runs in one message
                   channel_id: int) -> None:
    """
    Create a session for any user if they want to add several runs. Mainly used for metagame. 
    """

    _sessions[user_id] = {
        "deck": deck,
        "runs": [],
        "message_id": message_id,
        "channel_id": channel_id
    }


def add_run(user_id: int,
            matches: str,
            comments: str) -> int:
    """
    It collects a given run for a given player, their matches in the run and possible comments for that run. Returns how many runs the player has played.
    """

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    _sessions[user_id]["runs"].append(
        {
            "matches": matches,
            "comments": comments,
            "timestamp": ts,
        }

    )

    return len(_sessions[user_id]["runs"])


def get_session(user_id: int) -> dict | None:
    return _sessions.get(user_id)


def close_session(user_id: int) -> None:
    _sessions.pop(user_id, None)
