# Madoka

Discord bot for [madxka.com](https://madxka.com) catalog monitoring, item inspection, and wallet purchases.

## Setup

1. Copy `.env.example` to `.env` and fill in values.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

## Commands

- `/inspect` — look up an item by id or name
- `/balance` — wallet robux and tickets (owner only)
- `/buy free` — purchase all free on-sale catalog items (owner only)
- `/catalog stats` / `/catalog refresh` — cache info and force sync
- `/test random` — random item inspect

## Config

| Variable | Description |
|----------|-------------|
| `TOKEN` | Discord bot token |
| `COOKIE` | madxka session cookie (JWT or full browser cookie string) |
| `DISCORD_GUILD_ID` | Guild for slash command sync |
| `WATCH_CHANNEL_ID` | Channel for catalog poll embeds |
| `WALLET_OWNER_ID` | Discord user id allowed to use wallet commands |
| `POLL_INTERVAL_MINUTES` | Catalog poll interval (default 1) |
