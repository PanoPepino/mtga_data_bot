# MTGA Data Bot

MTGA Data Bot is a Discord bot that collects **Metagame Challenge** and **Ladder** results for Magic: The Gathering Arena and stores them as CSV files for later analysis.

---

## Features

- `/challenge` (Metagame)
  - Modal to log all runs for a given deck using `Run N:` headers.
  - Validates input format (`Run 1:` and `Opponent 2-1` style).
  - Sends a public embed summarizing the runs.
  - Saves each match as one CSV row.

- `/ladder`
  - Modal to log ladder matches, one per line (`Opponent 2-1`).
  - Validates input format also.
  - Saves each match as one CSV row.


<!--
-->