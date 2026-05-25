import urllib.request
import urllib.parse
import json
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "8544793397"
MESSAGE = "Hello World at 9:30"

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        return result

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set")
        exit(1)
    result = send_message(TOKEN, CHAT_ID, MESSAGE)
    if result.get("ok"):
        print("Message sent successfully!")
    else:
        print(f"Failed: {result}")
