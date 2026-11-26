import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost import config  # noqa: E402
from instaghost.auth import LoginManager  # noqa: E402


class LoginData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patch = mock.patch.object(config, "CONFIG_DIR", Path(self.tmp.name))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_save_is_private(self):
        self.assertTrue(LoginManager.save_login_data("user", "pass"))
        path = LoginManager.get_login_data_path()
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_load_rejects_malformed(self):
        path = LoginManager.get_login_data_path()
        path.write_text("[]")
        self.assertIsNone(LoginManager.load_login_data())
        path.write_text(json.dumps({"username": "user"}))
        self.assertIsNone(LoginManager.load_login_data())
        path.write_text(json.dumps({"username": 1, "password": "pass"}))
        self.assertIsNone(LoginManager.load_login_data())

    def test_load_round_trip(self):
        LoginManager.save_login_data("user", "pass")
        self.assertEqual(LoginManager.load_login_data(),
                         {"username": "user", "password": "pass"})

    def test_clear(self):
        LoginManager.save_login_data("user", "pass")
        self.assertTrue(LoginManager.clear_login_data())
        self.assertFalse(LoginManager.clear_login_data())


if __name__ == "__main__":
    unittest.main()
