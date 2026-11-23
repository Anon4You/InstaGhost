"""Telegram bot gateway for InstaGhost.

Owner-only long polling. Reuses the session from `instaghost --login` on the
host; never asks for Instagram credentials in chat.
"""

import os
import shutil
import sys
import time

import requests

from .gateway import job_files, parse_command, run_job

HELP = """InstaGhost commands:
/profile <user>      profile report
/pic <user>          profile picture
/posts <user> [n]    posts (default 5, max 30)
/reels <user> [n]    reels (default 5, max 30)
/stories <user>      stories
/all <user>          picture + 10 posts + 5 reels + stories
/url <instagram_url> one post or reel

Uses the host session. Run `instaghost --login ...` on the server first."""

MAX_FILE = 50 * 1024 * 1024


class Bot:
    def __init__(self, token, allowed):
        self.api = f"https://api.telegram.org/bot{token}/"
        self.allowed = allowed
        self.http = requests.Session()

    def call(self, method, files=None, timeout=60, **data):
        response = self.http.post(self.api + method, data=data, files=files, timeout=timeout)
        try:
            return response.json()
        except ValueError:
            return {"ok": False, "description": response.text[:200]}

    def send_text(self, chat_id, text):
        self.call("sendMessage", chat_id=chat_id, text=(text or "Done.")[:3500])

    def send_file(self, chat_id, path):
        size = path.stat().st_size
        if size > MAX_FILE:
            self.send_text(chat_id, f"Skipped {path.name}: over Telegram's 50 MB limit.")
            return
        suffix = path.suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png", ".webp") and size <= 10 * 1024 * 1024:
            method, field = "sendPhoto", "photo"
        elif suffix == ".mp4":
            method, field = "sendVideo", "video"
        else:
            method, field = "sendDocument", "document"
        with open(path, "rb") as fh:
            result = self.call(method, files={field: (path.name, fh)}, chat_id=chat_id, timeout=180)
        if not result.get("ok") and method != "sendDocument":
            with open(path, "rb") as fh:
                result = self.call(
                    "sendDocument", files={"document": (path.name, fh)}, chat_id=chat_id, timeout=180
                )
        if not result.get("ok"):
            self.send_text(chat_id, f"Could not send {path.name}: {result.get('description', 'error')}")
        time.sleep(1)

    def handle(self, message):
        chat_id = message["chat"]["id"]
        if message.get("from", {}).get("id") not in self.allowed:
            self.send_text(chat_id, "Not allowed.")
            return
        parsed = parse_command(message.get("text"))
        if not parsed:
            return
        action, kwargs = parsed
        if action == "help":
            self.send_text(chat_id, HELP)
            return
        if action == "usage":
            self.send_text(chat_id, f"Usage: /{kwargs['command']} <username>")
            return

        self.send_text(chat_id, "Working...")
        try:
            ok, text, jobdir = run_job(action, **kwargs)
        except Exception as e:
            self.send_text(chat_id, f"Job failed: {e}")
            return
        self.send_text(chat_id, text or ("Done." if ok else "Failed."))
        if jobdir:
            try:
                for path in job_files(jobdir):
                    self.send_file(chat_id, path)
            finally:
                shutil.rmtree(jobdir, ignore_errors=True)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    allowed_raw = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").replace(",", " ").split()
    if not token or not allowed_raw:
        sys.exit(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID "
            "(your numeric Telegram user id) before starting the bot."
        )
    try:
        allowed = {int(value) for value in allowed_raw}
    except ValueError:
        sys.exit("TELEGRAM_ALLOWED_USER_ID must be numeric ids, e.g. 123456789.")

    bot = Bot(token, allowed)
    print("InstaGhost Telegram bot polling. Ctrl-C to stop.")
    offset = None
    try:
        while True:
            try:
                response = bot.http.get(
                    bot.api + "getUpdates",
                    params={"timeout": 30, "offset": offset},
                    timeout=(10, 40),
                )
                data = response.json()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(5)
                continue
            if not data.get("ok"):
                print(f"Telegram error: {data.get('description')}")
                time.sleep(5)
                continue
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message") or {}
                if not message.get("text"):
                    continue
                try:
                    bot.handle(message)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Handler error: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
