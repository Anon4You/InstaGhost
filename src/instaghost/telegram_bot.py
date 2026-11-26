"""Telegram bot gateway for InstaGhost.

Owner-only long polling. Reuses the session from `instaghost --login` on the
host; never asks for Instagram credentials in chat.
"""

import getpass
import json
import os
import shutil
import sys
import time

import requests

from . import config
from .gateway import job_files, parse_command, prune_jobs, run_job

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


def _parse_allowed(raw):
    values = (raw or "").replace(",", " ").split()
    return {int(value) for value in values}


def _load_saved_settings():
    path = config.telegram_config_path()
    try:
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None, None
        token = data.get("token")
        user_ids = data.get("user_ids")
        if isinstance(token, str) and token.strip() and isinstance(user_ids, list) and user_ids:
            return token.strip(), {int(value) for value in user_ids}
    except (OSError, ValueError, TypeError):
        pass
    return None, None


def _save_settings(token, allowed):
    path = config.telegram_config_path()
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        if hasattr(os, "fchmod"):
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"token": token, "user_ids": sorted(allowed)}, f)
        os.chmod(path, 0o600)
        print(f"Saved Telegram settings to {path}")
        return True
    except OSError as e:
        print(f"Could not save Telegram settings: {e}")
        return False


def _resolve_settings():
    saved_token, saved_allowed = _load_saved_settings()
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    env_allowed_raw = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()

    token = env_token or saved_token
    allowed = saved_allowed
    prompted = False

    if not token:
        token = getpass.getpass("Telegram bot token: ").strip()
        prompted = True
    if not token:
        sys.exit("A Telegram bot token is required.")

    if env_allowed_raw:
        try:
            allowed = _parse_allowed(env_allowed_raw)
        except ValueError:
            sys.exit("TELEGRAM_ALLOWED_USER_ID must be numeric ids, e.g. 123456789.")
    elif not allowed:
        raw = input("Telegram user ID(s), comma-separated: ").strip()
        while True:
            try:
                allowed = _parse_allowed(raw)
                if allowed:
                    break
            except ValueError:
                pass
            raw = input("Numeric Telegram user ID(s), comma-separated: ").strip()
        prompted = True

    if prompted:
        _save_settings(token, allowed)
    return token, allowed


def _redact(text, token):
    return str(text).replace(token, "<token>") if token else str(text)


def _check_token(bot, token):
    try:
        result = bot.call("getMe", timeout=15)
    except Exception as e:
        sys.exit(f"Telegram connection failed: {_redact(e, token)}")
    if not isinstance(result, dict) or not result.get("ok"):
        description = result.get("description") if isinstance(result, dict) else "invalid response"
        sys.exit(f"Telegram rejected the bot token: {_redact(description, token)}")


class Bot:
    def __init__(self, token, allowed):
        self.token = token
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
        chat = message.get("chat") or {}
        if chat.get("type") != "private":
            return
        chat_id = chat.get("id")
        if chat_id is None:
            return
        if (message.get("from") or {}).get("id") not in self.allowed:
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
        prune_jobs()


def main():
    token, allowed = _resolve_settings()

    bot = Bot(token, allowed)
    _check_token(bot, token)
    prune_jobs()
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
                print(f"Polling error: {_redact(e, token)}")
                time.sleep(5)
                continue
            if not data.get("ok"):
                print(f"Telegram error: {_redact(data.get('description'), token)}")
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
                    print(f"Handler error: {_redact(e, token)}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
