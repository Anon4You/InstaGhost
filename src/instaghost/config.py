"""Filesystem locations and defaults shared by the whole package."""

import os
import re
from pathlib import Path

APP_NAME = "instaghost"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
DEFAULT_OUTPUT_DIR = "downloads"
USERNAME_RE = re.compile(r"^(?!\.+$)[A-Za-z0-9._]{1,30}$")


def valid_username(name):
    return isinstance(name, str) and bool(USERNAME_RE.fullmatch(name))


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(CONFIG_DIR, 0o700)
    return CONFIG_DIR


def login_data_path():
    return ensure_config_dir() / "logindata"


def telegram_config_path():
    return ensure_config_dir() / "telegram.json"


def session_path(username):
    return ensure_config_dir() / f"session-{username}"


def profile_cache_path(username):
    return ensure_config_dir() / f"profile-{username}.json"
