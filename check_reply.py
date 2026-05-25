#!/usr/bin/env python3
"""
Polls Telegram for a yes/no reply and updates the sheet if 'ja'.
Run this ~5-10 min after ask_tellie.py to catch the reply.
"""
import urllib.request
import urllib.parse
import json
import os
import subprocess
from datetime import date, timedelta

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "8544793397"
SHEET_ID = "1ekISTx560LJPP7QR_BLiufEvKJtWoZiJ8SVrDFNwF3Y"
ACCOUNT = "golfbekkers@gmail.com"

def get_updates(token, offset=0):
    url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&limit=10&timeout=30"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def find_today_row():
    today = (date.today() - timedelta(days=1)).strftime("%-d-%-m-%Y")  # yesterday
    result = subprocess.run(
        ["gog", "sheets", "get", SHEET_ID, "Q2!A1:A110", "--json", "--account", ACCOUNT],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    rows = data.get("values", [])
    for i, row in enumerate(rows):
        if row and row[0] == today:
            return i + 1  # spreadsheet row number
    return None

def update_tellie(row):
    cell = f"Q2!F{row}"
    subprocess.run(
        ["gog", "sheets", "update", SHEET_ID, cell,
         "--values-json", '[[true]]', "--input", "USER_ENTERED", "--account", ACCOUNT],
        capture_output=True, text=True
    )
    print(f"✅ Checked 'Naar bed no tellie' for row {row}")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set")
        exit(1)

    updates = get_updates(TOKEN)
    messages = updates.get("result", [])

    # Look for the most recent message from our chat
    for update in reversed(messages):
        msg = update.get("message", {})
        if str(msg.get("chat", {}).get("id", "")) == CHAT_ID:
            text = msg.get("text", "").strip().lower()
            print(f"Latest reply: '{text}'")
            if text in ["ja", "yes", "j", "y"]:
                row = find_today_row()
                if row:
                    update_tellie(row)
                else:
                    print("❌ Today's row not found in sheet")
            else:
                print("Reply was not 'ja' — not updating sheet")
            break
    else:
        print("No messages found")
