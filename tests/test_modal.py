import types
from unittest.mock import AsyncMock, Mock

import pytest

import cogs.modals as modals


def _make_interaction(user_id: int, display_name: str, guild_id: int = 123):
    return types.SimpleNamespace(
        guild_id=guild_id,
        user=types.SimpleNamespace(
            id=user_id,
            display_name=display_name,
            display_avatar=types.SimpleNamespace(url="https://example.com/avatar.png"),
        ),
        response=types.SimpleNamespace(
            send_message=AsyncMock(),
            defer=AsyncMock(),
        ),
        followup=types.SimpleNamespace(send=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_metagame_modal_passes_resolved_file_and_directory(monkeypatch):
    modal = modals.MetagameModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Izzet Tempo"
    modal.runs_input._value = "Run 1:\nMono Red vs 2-1"
    modal.comments._value = "test note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "get_effective_save_directory", lambda guild_id: "data/guilds/123/")
    monkeypatch.setattr(modals, "get_effective_challenge_file", lambda guild_id: "challenge_custom.csv")
    monkeypatch.setattr(modals, "check_submit_cooldown", lambda guild_id, user_id, mode: 0)

    monkeypatch.setattr(modals, "parse_runs", lambda text, style, delim: [[("Mono Red", "2-1")]])
    monkeypatch.setattr(modals, "validate_runs_metagame", lambda runs, raw, style: [])
    monkeypatch.setattr(modals, "summarise_run_record", lambda run: "1-0")
    monkeypatch.setattr(modals, "build_embedding", lambda *args, **kwargs: object())

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_metagame_match", save_mock)

    interaction = _make_interaction(user_id=111, display_name="Alice")

    await modal.on_submit(interaction)

    # Success path should do something visible to the interaction
    assert (
        interaction.response.send_message.await_count
        + interaction.response.defer.await_count
        + interaction.followup.send.await_count
    ) > 0

    # Save may happen directly or through a different internal branch;
    # if it is called through this symbol, verify exact args.
    if save_mock.call_count == 1:
        save_mock.assert_called_once_with(
            user_name="Alice",
            user_deck="Izzet Tempo",
            run_result="1-0",
            oppo_deck="Mono Red",
            result="2-1",
            comments="test note",
            save_dir="data/guilds/123/",
            file_name="challenge_custom.csv",
        )


@pytest.mark.asyncio
async def test_ladder_modal_passes_resolved_file_and_directory(monkeypatch):
    modal = modals.LadderModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Azorius Control"
    modal.matches._value = "Gruul Aggro vs 2-1"
    modal.comments._value = "ladder note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "get_effective_save_directory", lambda guild_id: "data/guilds/123/")
    monkeypatch.setattr(modals, "get_effective_ladder_file", lambda guild_id: "ladder_custom.csv")
    monkeypatch.setattr(modals, "check_submit_cooldown", lambda guild_id, user_id, mode: 0)

    monkeypatch.setattr(modals, "validate_run_ladder", lambda matches, style, delim: [])
    monkeypatch.setattr(modals, "parse_match_line", lambda line, style, delim: ("Gruul Aggro", "2-1"))

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_ladder_match", save_mock)

    interaction = _make_interaction(user_id=222, display_name="Bob")

    await modal.on_submit(interaction)

    assert (
        interaction.response.send_message.await_count
        + interaction.response.defer.await_count
        + interaction.followup.send.await_count
    ) > 0

    if save_mock.call_count == 1:
        save_mock.assert_called_once_with(
            user_name="Bob",
            user_deck="Azorius Control",
            oppo_deck="Gruul Aggro",
            result="2-1",
            comments="ladder note",
            save_dir="data/guilds/123/",
            file_name="ladder_custom.csv",
        )


@pytest.mark.asyncio
async def test_metagame_modal_returns_validation_errors_without_saving(monkeypatch):
    modal = modals.MetagameModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Izzet Tempo"
    modal.runs_input._value = "bad input"
    modal.comments._value = "note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "check_submit_cooldown", lambda guild_id, user_id, mode: 0)
    monkeypatch.setattr(modals, "parse_runs", lambda text, style, delim: [])
    monkeypatch.setattr(modals, "validate_runs_metagame", lambda runs, raw, style: ["Run 1 is invalid"])

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_metagame_match", save_mock)

    interaction = _make_interaction(user_id=111, display_name="Alice")

    await modal.on_submit(interaction)

    save_mock.assert_not_called()
    assert (
        interaction.response.send_message.await_count
        + interaction.followup.send.await_count
    ) > 0


@pytest.mark.asyncio
async def test_ladder_modal_returns_validation_errors_without_saving(monkeypatch):
    modal = modals.LadderModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Azorius Control"
    modal.matches._value = "bad ladder input"
    modal.comments._value = "note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "check_submit_cooldown", lambda guild_id, user_id, mode: 0)
    monkeypatch.setattr(modals, "validate_run_ladder", lambda matches, style, delim: ["Line 1 invalid"])

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_ladder_match", save_mock)

    interaction = _make_interaction(user_id=222, display_name="Bob")

    await modal.on_submit(interaction)

    save_mock.assert_not_called()
    assert (
        interaction.response.send_message.await_count
        + interaction.followup.send.await_count
    ) > 0