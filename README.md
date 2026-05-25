# telegram-daily

Sends a daily Telegram message at 21:30 Amsterdam time.

## Setup

1. Put your bot token in `.env` (replace `PASTE_YOUR_TOKEN_HERE`)
2. The cron job calls `run.sh` which loads the token and runs `send.py`

## Files

- `send.py` — Python script that sends the message
- `run.sh` — wrapper that loads `.env` and calls the script
- `.env` — your secret token (never commit this!)

## Changing the message

Edit the `MESSAGE` variable in `send.py`.
