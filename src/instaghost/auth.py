"""Saved login credentials and instagrapi session files."""

import json
import os

from . import config
from .output import HackerStyle


class LoginManager:
    @staticmethod
    def get_login_data_path():
        return config.login_data_path()

    @staticmethod
    def get_session_path(username):
        """instagrapi settings file for a login user (reuse avoids relogin blocks)."""
        return config.session_path(username)

    @staticmethod
    def save_login_data(username, password):
        login_path = LoginManager.get_login_data_path()
        login_data = {'username': username, 'password': password}
        try:
            fd = os.open(login_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            if hasattr(os, "fchmod"):
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(login_data, f)
            os.chmod(login_path, 0o600)
            HackerStyle.print_success(f"Login data saved for @{username}")
            return True
        except Exception as e:
            HackerStyle.print_error(f"Failed to save login data: {e}")
            return False

    @staticmethod
    def load_login_data():
        login_path = LoginManager.get_login_data_path()
        if login_path.exists():
            try:
                with open(login_path, 'r') as f:
                    data = json.load(f)
                if (isinstance(data, dict)
                        and isinstance(data.get('username'), str)
                        and isinstance(data.get('password'), str)
                        and data['username'] and data['password']):
                    return data
                HackerStyle.print_error("Login data is incomplete or malformed")
            except Exception as e:
                HackerStyle.print_error(f"Failed to load login data: {e}")
        return None

    @staticmethod
    def clear_login_data():
        login_path = LoginManager.get_login_data_path()
        try:
            if login_path.exists():
                login_path.unlink()
                HackerStyle.print_success("Login data cleared")
                return True
        except OSError as e:
            HackerStyle.print_error(f"Failed to clear login data: {e}")
        return False

    @staticmethod
    def clear_sessions():
        removed = 0
        try:
            for path in config.CONFIG_DIR.glob("session-*"):
                if path.is_file():
                    path.unlink()
                    removed += 1
        except OSError as e:
            HackerStyle.print_error(f"Failed to clear sessions: {e}")
        return removed
