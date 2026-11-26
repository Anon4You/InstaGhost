import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost import config  # noqa: E402
from instaghost.telegram_bot import (  # noqa: E402
    Bot,
    _check_token,
    _load_saved_settings,
    _parse_allowed,
    _redact,
    _resolve_settings,
    _save_settings,
)


class Redaction(unittest.TestCase):
    def test_hides_token(self):
        token = "123:secret"
        self.assertNotIn(token, _redact(f"error at /bot{token}/getUpdates", token))
        self.assertIn("<token>", _redact(f"error at /bot{token}/getUpdates", token))


class BotBehavior(unittest.TestCase):
    def test_group_chats_are_ignored(self):
        bot = Bot("token", {1})
        with mock.patch.object(bot, "send_text") as send:
            bot.handle({"chat": {"id": -1, "type": "group"}, "from": {"id": 1},
                        "text": "/profile user"})
            send.assert_not_called()

    def test_private_chat_owner_check(self):
        bot = Bot("token", {1})
        with mock.patch.object(bot, "send_text") as send:
            bot.handle({"chat": {"id": 2, "type": "private"}, "from": {"id": 2},
                        "text": "/profile user"})
            send.assert_called_once_with(2, "Not allowed.")

    def test_check_token_rejects_invalid_token(self):
        bot = mock.Mock()
        bot.call.return_value = {"ok": False, "description": "Unauthorized"}
        with self.assertRaises(SystemExit):
            _check_token(bot, "token")

    def test_check_token_accepts_valid_token(self):
        bot = mock.Mock()
        bot.call.return_value = {"ok": True}
        _check_token(bot, "token")


class Settings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patch = mock.patch.object(config, "CONFIG_DIR", Path(self.tmp.name))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_parse_allowed(self):
        self.assertEqual(_parse_allowed("1, 2 3"), {1, 2, 3})
        with self.assertRaises(ValueError):
            _parse_allowed("abc")

    def test_save_is_private_and_round_trips(self):
        self.assertTrue(_save_settings("token", {1, 2}))
        path = config.telegram_config_path()
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(_load_saved_settings(), ("token", {1, 2}))

    def test_malformed_config_is_ignored(self):
        config.telegram_config_path().write_text("[]")
        self.assertEqual(_load_saved_settings(), (None, None))

    def test_saved_settings_skip_prompts(self):
        _save_settings("token", {1})
        with mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_ID": "",
        }):
            with mock.patch("builtins.input", side_effect=AssertionError("prompted")):
                with mock.patch("instaghost.telegram_bot.getpass.getpass",
                                side_effect=AssertionError("prompted")):
                    self.assertEqual(_resolve_settings(), ("token", {1}))

    def test_env_overrides_saved(self):
        _save_settings("saved", {1})
        with mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "env-token",
            "TELEGRAM_ALLOWED_USER_ID": "9",
        }):
            self.assertEqual(_resolve_settings(), ("env-token", {9}))

    def test_prompts_only_for_missing_values(self):
        with mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_ID": "",
        }):
            with mock.patch("instaghost.telegram_bot.getpass.getpass",
                            return_value="prompted-token"):
                with mock.patch("builtins.input", side_effect=["abc", "1, 2"]):
                    self.assertEqual(_resolve_settings(), ("prompted-token", {1, 2}))
        self.assertEqual(_load_saved_settings(), ("prompted-token", {1, 2}))

    def test_invalid_env_user_id_exits(self):
        with mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "token",
            "TELEGRAM_ALLOWED_USER_ID": "abc",
        }):
            with self.assertRaises(SystemExit):
                _resolve_settings()


if __name__ == "__main__":
    unittest.main()
