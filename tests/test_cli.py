import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost import cli, config  # noqa: E402
from instaghost.auth import LoginManager  # noqa: E402


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patch = mock.patch.object(config, "CONFIG_DIR", Path(self.tmp.name))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_cli(self, *args):
        with mock.patch.object(sys, "argv", ["instaghost", *args]):
            with self.assertRaises(SystemExit) as caught:
                cli._main()
        return caught.exception.code

    def test_rejects_invalid_target(self):
        self.assertEqual(self.run_cli("bad/name"), 2)

    def test_rejects_invalid_login_user(self):
        self.assertEqual(self.run_cli("--login-user", "bad/name"), 2)

    def test_logout_removes_session_and_login_data(self):
        LoginManager.save_login_data("user", "pass")
        session = config.session_path("user")
        session.write_text("{}")
        self.assertEqual(self.run_cli("--logout"), 0)
        self.assertFalse(session.exists())
        self.assertFalse(LoginManager.get_login_data_path().exists())

    def test_interactive_login_prompts_for_credentials(self):
        with mock.patch.object(sys, "argv", ["instaghost", "--login"]):
            with mock.patch.object(cli.InstaGhost, "login", return_value=True) as login:
                with mock.patch("instaghost.cli.sys.stdin",
                                type("Tty", (), {"isatty": lambda self: True})()):
                    with mock.patch("builtins.input", return_value="user"):
                        with mock.patch("instaghost.cli.getpass.getpass", return_value="pass"):
                            cli._main()
        login.assert_called_once_with("user", "pass", save=False)

    def test_login_without_tty_fails_before_prompting(self):
        with mock.patch.object(sys, "argv", ["instaghost", "--login"]):
            with mock.patch("instaghost.cli.sys.stdin",
                            type("NoTty", (), {"isatty": lambda self: False})()):
                with self.assertRaises(SystemExit) as caught:
                    cli._main()
        self.assertEqual(caught.exception.code, 1)

    def test_keyboard_interrupt_exits_130(self):
        with mock.patch.object(cli, "_main", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as caught:
                cli.main()
        self.assertEqual(caught.exception.code, 130)


if __name__ == "__main__":
    unittest.main()
