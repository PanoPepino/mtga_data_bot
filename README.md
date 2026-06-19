# MTGA DataBot

A Discord bot for collecting MTG Arena data from Metagame and Ladder matches (in any format). Data is stored as CSV files for later competitive analysis.

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



