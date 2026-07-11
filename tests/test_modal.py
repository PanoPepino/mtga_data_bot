import types
from unittest.mock import AsyncMock, Mock

import pytest

import cogs.modals as modals


@pytest.mark.asyncio
async def test_metagame_modal_passes_resolved_file_and_directory(monkeypatch):
    modal = modals.MetagameModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Izzet Tempo"
    modal.runs_input._value = "Run 1:\nMono Red vs W"
    modal.comments._value = "test note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "get_effective_save_directory", lambda guild_id: "data/guilds/123/")
    monkeypatch.setattr(modals, "get_effective_challenge_file", lambda guild_id: "challenge_custom.csv")

    monkeypatch.setattr(modals, "parse_runs", lambda text, style, delim: [[("Mono Red", "W")]])
    monkeypatch.setattr(modals, "validate_runs_metagame", lambda runs, raw, style: [])
    monkeypatch.setattr(modals, "summarise_run_record", lambda run: "1-0")
    monkeypatch.setattr(modals, "build_embedding", lambda *args, **kwargs: object())

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_metagame_match", save_mock)

    interaction = types.SimpleNamespace(
        guild_id=123,
        user=types.SimpleNamespace(
            display_name="Alice",
            display_avatar=types.SimpleNamespace(url="https://example.com/avatar.png"),
        ),
        response=types.SimpleNamespace(send_message=AsyncMock()),
        followup=types.SimpleNamespace(send=AsyncMock()),
    )

    await modal.on_submit(interaction)

    save_mock.assert_called_once_with(
        user_name="Alice",
        user_deck="Izzet Tempo",
        run_result="1-0",
        oppo_deck="Mono Red",
        result="W",
        comments="test note",
        save_dir="data/guilds/123/",
        file_name="challenge_custom.csv",
    )


@pytest.mark.asyncio
async def test_ladder_modal_passes_resolved_file_and_directory(monkeypatch):
    modal = modals.LadderModal("deck_delimiter_result", " vs ")
    modal.pilot_deck._value = "Azorius Control"
    modal.matches._value = "Gruul Aggro vs W"
    modal.comments._value = "ladder note"

    monkeypatch.setattr(modals, "get_effective_input_style", lambda guild_id: "deck_delimiter_result")
    monkeypatch.setattr(modals, "get_effective_delimiter", lambda guild_id: " vs ")
    monkeypatch.setattr(modals, "get_effective_save_directory", lambda guild_id: "data/guilds/123/")
    monkeypatch.setattr(modals, "get_effective_ladder_file", lambda guild_id: "ladder_custom.csv")

    monkeypatch.setattr(modals, "validate_run_ladder", lambda matches, style, delim: [])
    monkeypatch.setattr(modals, "parse_match_line", lambda line, style, delim: ("Gruul Aggro", "W"))

    save_mock = Mock()
    monkeypatch.setattr(modals, "save_ladder_match", save_mock)

    interaction = types.SimpleNamespace(
        guild_id=123,
        user=types.SimpleNamespace(
            display_name="Bob",
            display_avatar=types.SimpleNamespace(url="https://example.com/avatar.png"),
        ),
        response=types.SimpleNamespace(send_message=AsyncMock()),
    )

    await modal.on_submit(interaction)

    save_mock.assert_called_once_with(
        user_name="Bob",
        user_deck="Azorius Control",
        oppo_deck="Gruul Aggro",
        result="W",
        comments="ladder note",
        save_dir="data/guilds/123/",
        file_name="ladder_custom.csv",
    )
