from cogs.sessions import create_session, add_run, get_session, close_session

USER = 123456789  # Fake test user


def setup_function():
    """Runs before each test — ensures clean state."""
    close_session(USER)


def test_session_created():
    create_session(USER, "Death Shadow", message_id=1, channel_id=2)
    session = get_session(USER)
    assert session is not None
    assert session["deck"] == "Death Shadow"
    assert session["runs"] == []


def test_add_run_increments_count():
    create_session(USER, "Izzet Tempo", message_id=1, channel_id=2)
    count = add_run(USER, "GB Lands 2-1\nW Stompy 0-2", comments="")
    assert count == 1
    count = add_run(USER, "Sultai Shadow 2-0", comments="easy run")
    assert count == 2


def test_run_stores_timestamp():
    create_session(USER, "Izzet Tempo", message_id=1, channel_id=2)
    add_run(USER, "GB Lands 2-1", comments="")
    run = get_session(USER)["runs"][0]
    assert "UTC" in run["timestamp"]


def test_close_session():
    create_session(USER, "Izzet Tempo", message_id=1, channel_id=2)
    close_session(USER)
    assert get_session(USER) is None


def test_no_session_returns_none():
    assert get_session(99999) is None
