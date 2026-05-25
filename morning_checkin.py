#!/usr/bin/env python3
"""
Morning check-in bot:
1. Polls Telegram for a reply to the nightly question
2. If reply contains a screenshot, uploads it to Drive and saves the URL
3. Updates yesterday's row in the sheet:
   - Column D (Schermtijd): screentime number if provided (e.g. "ja 3.5")
   - Column E (Screenshot): Drive link if photo was sent
   - Column F (Naar bed no tellie): TRUE if answer was ja
"""

import urllib.request
import urllib.parse
import json
import os
import subprocess
import tempfile
import sys
from datetime import date, timedelta

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "8544793397"
SHEET_ID = "1ekISTx560LJPP7QR_BLiufEvKJtWoZiJ8SVrDFNwF3Y"
ACCOUNT = "golfbekkers@gmail.com"

def api(method, params=None, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_updates():
    return api("getUpdates", {"limit": 20, "timeout": 10})

def get_file_url(file_id):
    result = api("getFile", {"file_id": file_id})
    path = result["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{TOKEN}/{path}"

def download_file(url, suffix=".jpg"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        tmp.write(r.read())
    tmp.close()
    return tmp.name

def upload_to_drive(local_path, filename):
    result = subprocess.run(
        ["gog", "drive", "upload", local_path, "--name", filename,
         "--json", "--account", ACCOUNT],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Drive upload failed: {result.stderr}")
        return None
    data = json.loads(result.stdout)
    file_id = data.get("result", {}).get("id") or data.get("id")
    if file_id:
        url_result = subprocess.run(
            ["gog", "drive", "url", file_id, "--account", ACCOUNT],
            capture_output=True, text=True
        )
        return url_result.stdout.strip()
    return None

def find_yesterday_row():
    yesterday = (date.today() - timedelta(days=1)).strftime("%-d-%-m-%Y")
    result = subprocess.run(
        ["gog", "sheets", "get", SHEET_ID, "Q2!A1:A110",
         "--json", "--account", ACCOUNT],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    rows = data.get("values", [])
    for i, row in enumerate(rows):
        if row and row[0] == yesterday:
            return i + 1  # spreadsheet row number
    return None

def update_sheet(row, tellie=None, screenshot_url=None, schermtijd=None):
    updates = []
    if schermtijd is not None:
        updates.append(("D", schermtijd))
    if screenshot_url:
        updates.append(("E", screenshot_url))
    if tellie is not None:
        updates.append(("F", tellie))

    for col, value in updates:
        cell = f"Q2!{col}{row}"
        val = json.dumps([[value]])
        subprocess.run(
            ["gog", "sheets", "update", SHEET_ID, cell,
             "--values-json", val, "--input", "USER_ENTERED", "--account", ACCOUNT],
            capture_output=True, text=True
        )
        print(f"  ✅ Updated {cell} = {value}")

def send_message(text):
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    api("sendMessage", data=data)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set")
        sys.exit(1)

    updates = get_updates()
    messages = updates.get("result", [])

    # Find the most recent message from our user
    reply_text = None
    photo_file_id = None

    for update in reversed(messages):
        msg = update.get("message", {})
        if str(msg.get("chat", {}).get("id", "")) != CHAT_ID:
            continue

        reply_text = msg.get("text") or msg.get("caption") or ""
        reply_text = reply_text.strip().lower()

        # Check for photo
        photos = msg.get("photo")
        if photos:
            # Pick highest resolution
            photo_file_id = photos[-1]["file_id"]

        break  # most recent message found

    if reply_text is None and photo_file_id is None:
        print("No reply found from user.")
        sys.exit(0)

    print(f"Reply text: '{reply_text}'")
    print(f"Photo: {'yes' if photo_file_id else 'no'}")

    row = find_yesterday_row()
    if not row:
        print("❌ Yesterday's row not found in sheet")
        sys.exit(1)

    print(f"Updating row {row} (yesterday)")

    # Parse yes/no
    tellie = None
    if any(w in reply_text for w in ["ja", "yes", "j", "y"]):
        tellie = True
    elif any(w in reply_text for w in ["nee", "no", "n"]):
        tellie = False

    # Parse optional screentime number e.g. "ja 3.5"
    schermtijd = None
    words = reply_text.split()
    for w in words:
        try:
            schermtijd = float(w.replace(",", "."))
            break
        except ValueError:
            continue

    # Upload photo if present
    screenshot_url = None
    if photo_file_id:
        yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        print("Uploading screenshot to Drive...")
        file_url = get_file_url(photo_file_id)
        local_path = download_file(file_url, suffix=".jpg")
        screenshot_url = upload_to_drive(local_path, f"screentime-wolf-{yesterday_str}.jpg")
        os.unlink(local_path)
        if screenshot_url:
            print(f"  📸 Uploaded: {screenshot_url}")

    update_sheet(row, tellie=tellie, screenshot_url=screenshot_url, schermtijd=schermtijd)

    # Confirm back to user
    parts = []
    if tellie is True:
        parts.append("📵 Naar bed no tellie: ✅")
    elif tellie is False:
        parts.append("📱 Naar bed no tellie: ❌")
    if schermtijd is not None:
        parts.append(f"⏱ Schermtijd: {schermtijd}u")
    if screenshot_url:
        parts.append("📸 Screenshot opgeslagen")

    if parts:
        send_message("Sheet bijgewerkt!\n" + "\n".join(parts))
        print("Confirmation sent to Telegram.")
    else:
        print("Nothing to update (no clear yes/no found).")
