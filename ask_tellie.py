#!/usr/bin/env python3
"""
Sends the nightly 'naar bed no tellie?' question via Telegram.
"""
import urllib.request
import urllib.parse
import json
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "8544793397"
MESSAGE = "Goedemorgen! 📵 Ging je gisternacht naar bed zonder je telefoon? (ja/nee)"

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set")
        exit(1)
    result = send_message(TOKEN, CHAT_ID, MESSAGE)
    if result.get("ok"):
        print("Question sent!")
    else:
        print(f"Failed: {result}")
