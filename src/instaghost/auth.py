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
            with open(login_path, 'w') as f:
                json.dump(login_data, f)
            os.chmod(login_path, 0o600)  # Secure file permissions
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
                    return json.load(f)
            except Exception as e:
                HackerStyle.print_error(f"Failed to load login data: {e}")
        return None

    @staticmethod
    def clear_login_data():
        login_path = LoginManager.get_login_data_path()
        if login_path.exists():
            login_path.unlink()
            HackerStyle.print_success("Login data cleared")
            return True
        return False
