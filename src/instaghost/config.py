"""Filesystem locations and defaults shared by the whole package."""

from pathlib import Path

APP_NAME = "instaghost"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
DEFAULT_OUTPUT_DIR = "downloads"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def login_data_path():
    return ensure_config_dir() / "logindata"


def session_path(username):
    return ensure_config_dir() / f"session-{username}"


def profile_cache_path(username):
    return ensure_config_dir() / f"profile-{username}.json"
