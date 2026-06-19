# mtga_data_bot

A Discord bot for collecting MTG Arena match data from multiple servers and storing it as CSV files for later analysis.

---

## Requirements

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- The bot must have the **applications.commands** and **bot** scopes, with **Send Messages** and **Attach Files** permissions

---

## Setup

```bash
git clone https://github.com/PanoPepino/mtga_data_bot.git
cd mtga_data_bot
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env with your values
python bot.py
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Your bot token from the Developer Portal |
| `COMMAND_SYNC_MODE` | Yes | `guild` for local dev, `global` for production |
| `DISCORD_GUILD_ID` | Dev only | Server ID of your test server (guild mode only) |

See `.env.example` for a ready-to-copy template.

---

## Commands

| Command | Who can use | What it does |
|---|---|---|
| `/challenge` | Any member | Opens a modal to log Metagame Challenge run(s) |
| `/ladder` | Any member | Opens a modal to log a Ladder session |
| `/export` | Admin | Exports a CSV file or all CSVs as a zip |
| `/settings show` | Admin | Shows current server configuration |
| `/settings set ...` | Admin | Changes a server-specific setting |
| `/settings reset` | Admin | Resets server settings to defaults |

---

## Data storage

All match data is stored locally under:

```
data/guilds/<guild_id>/
```

Two CSV files are created per server:

- **challenge.csv** — Metagame Challenge runs (`timestamp_utc`, `user_name`, `user_deck`, `run_result`, `oppo_deck`, `result`, `comments`)
- **ladder.csv** — Ladder matches (`timestamp_utc`, `user_name`, `user_deck`, `oppo_deck`, `result`, `comments`)

File names and save paths can be overridden per server with `/settings`.

---

## Project structure

```
mtga_data_bot/
├── bot.py                  # Entry point and cog loader
├── config.py               # Shared constants
├── .env.example            # Environment variable template
├── requirements.txt
├── pyproject.toml
├── cogs/
│   ├── gameplay.py         # /challenge and /ladder commands
│   ├── settings.py         # /settings commands
│   ├── export.py           # /export command
│   ├── modals.py           # Discord UI modals
│   └── embedding.py        # Discord embed builders
├── services/
│   ├── storage.py          # CSV read/write (no Discord dependency)
│   └── parser_service.py   # Match parsing re-exports
├── utils/
│   ├── guild_settings.py   # Per-server config helpers
│   └── parse_and_check.py  # Match parsing and validation
└── data/
    ├── guild_settings.json
    └── guilds/<guild_id>/   # One folder per Discord server
```

---

## Deploying to a cloud host

1. Set `COMMAND_SYNC_MODE=global` and `DISCORD_TOKEN` as environment variables on the host.
2. Do **not** set `DISCORD_GUILD_ID` in production.
3. Make sure the `data/` folder is on a persistent volume — match CSVs are written there at runtime.
4. The bot starts with `python bot.py`.

---

## Local development

Set `COMMAND_SYNC_MODE=guild` and `DISCORD_GUILD_ID=<your_test_server_id>` in `.env`. Slash commands will register instantly in that server every time the bot restarts, instead of waiting for Discord’s global propagation delay.
