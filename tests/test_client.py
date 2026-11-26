import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost import config  # noqa: E402
from instagrapi import exceptions as ig_exc  # noqa: E402

from instaghost.auth import LoginManager  # noqa: E402
from instaghost.cache import load_profile  # noqa: E402
from instaghost.client import InstaGhost, _clamp_count  # noqa: E402
from instaghost.output import LoadingAnimation  # noqa: E402


def fake_user():
    return SimpleNamespace(
        username="user",
        full_name="User",
        biography="",
        external_url="",
        media_count=1,
        follower_count=2,
        following_count=3,
        pk=1,
        is_private=False,
        is_verified=False,
        profile_pic_url_hd="https://cdn.example/p.jpg",
        profile_pic_url="https://cdn.example/p.jpg",
    )


class ClientTests(unittest.TestCase):
    def setUp(self):
        LoadingAnimation.enabled = False
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config_patch = mock.patch.object(config, "CONFIG_DIR", Path(self.tmp.name))
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)
        self.tool = InstaGhost()
        self.tool._user_cache["user"] = fake_user()

    def test_clamp_count(self):
        self.assertEqual(_clamp_count(0, 10), 1)
        self.assertEqual(_clamp_count(-5, 10), 1)
        self.assertEqual(_clamp_count(99, 10), 30)
        self.assertEqual(_clamp_count("bad", 10), 10)
        self.assertEqual(_clamp_count(None, 5), 5)

    def test_download_posts_clamps_count(self):
        with mock.patch.object(self.tool.cl, "user_medias", return_value=[]) as fetch:
            self.assertTrue(self.tool.download_posts("user", 0, self.tmp.name))
            fetch.assert_called_once_with("1", 1)
            fetch.reset_mock()
            self.assertTrue(self.tool.download_posts("user", 99, self.tmp.name))
            fetch.assert_called_once_with("1", 30)

    def test_download_posts_all_failed(self):
        media = SimpleNamespace(media_type=1)
        with mock.patch.object(self.tool.cl, "user_medias", return_value=[media]):
            with mock.patch.object(self.tool, "_download_media", return_value=False):
                self.assertFalse(self.tool.download_posts("user", 5, self.tmp.name))

    def test_download_posts_empty_is_not_an_error(self):
        with mock.patch.object(self.tool.cl, "user_medias", return_value=[]):
            self.assertTrue(self.tool.download_posts("user", 5, self.tmp.name))

    def test_download_media_uses_url_without_refetch(self):
        media = SimpleNamespace(
            media_type=1,
            pk=123,
            thumbnail_url="https://cdn.example/a.jpg",
            user=SimpleNamespace(username="user"),
        )
        with mock.patch.object(self.tool.cl, "photo_download_by_url") as download:
            self.assertTrue(self.tool._download_media(media, self.tmp.name))
            download.assert_called_once()

    def test_download_stories_uses_url_without_refetch(self):
        story = SimpleNamespace(
            pk=1,
            media_type=1,
            thumbnail_url="https://cdn.example/s.jpg",
            video_url=None,
        )
        with mock.patch.object(self.tool.cl, "user_stories", return_value=[story]):
            with mock.patch.object(self.tool.cl, "story_download_by_url") as download:
                self.assertTrue(self.tool.download_stories("user", self.tmp.name))
                download.assert_called_once()

    def test_download_from_url_reports_failure(self):
        media = SimpleNamespace(media_type=1, thumbnail_url=None, code="abc")
        with mock.patch.object(self.tool.cl, "media_pk_from_url", return_value="123"):
            with mock.patch.object(self.tool.cl, "media_info", return_value=media):
                self.assertFalse(self.tool.download_from_url(
                    "https://instagram.com/p/abc/", self.tmp.name))

    def test_extract_shortcode(self):
        self.assertEqual(self.tool.extract_shortcode_from_url(
            "https://www.instagram.com/p/ABC123/?igsh=1"), "ABC123")
        self.assertEqual(self.tool.extract_shortcode_from_url(
            "https://instagram.com/share/p/XYZ/"), "XYZ")
        self.assertIsNone(self.tool.extract_shortcode_from_url(
            "https://instagram.com/stories/user/123/"))

    def test_explicit_session_does_not_fall_back(self):
        with mock.patch.object(self.tool, "_load_session_file", return_value=False) as load:
            with mock.patch("instaghost.client.LoginManager.load_login_data",
                            side_effect=AssertionError("fallback used")):
                self.assertFalse(self.tool.try_saved_session("user"))
                load.assert_called_once_with("user")

    def test_saved_login_preferred_over_other_sessions(self):
        LoginManager.save_login_data("user", "pass")
        config.session_path("other").write_text("{}")
        with mock.patch.object(self.tool, "_load_session_file", return_value=True) as load:
            self.assertTrue(self.tool.try_saved_session())
            load.assert_called_once_with("user")

    def test_multiple_sessions_without_login_data_fails(self):
        config.session_path("one").write_text("{}")
        config.session_path("two").write_text("{}")
        with mock.patch.object(self.tool, "_load_session_file") as load:
            self.assertFalse(self.tool.try_saved_session())
            load.assert_not_called()

    def test_invalid_session_username_is_rejected(self):
        self.assertFalse(self.tool.try_saved_session("../escape"))

    def test_profile_pic_uses_download_helper(self):
        target = Path(self.tmp.name) / "user_profile_pic.jpg"
        with mock.patch.object(self.tool.cl, "photo_download_by_url",
                               return_value=target) as download:
            self.assertEqual(self.tool.download_profile_pic("user", self.tmp.name),
                             str(target))
            download.assert_called_once()

    def test_login_prompts_for_password_when_session_is_gone(self):
        def write_session(path):
            Path(path).write_text("{}")

        with mock.patch.object(self.tool, "_resume_session", return_value=False):
            with mock.patch("instaghost.client.sys.stdin",
                            SimpleNamespace(isatty=lambda: True)):
                with mock.patch("instaghost.client.getpass.getpass", return_value="pass"):
                    with mock.patch.object(self.tool.cl, "login") as login:
                        with mock.patch.object(self.tool.cl, "dump_settings",
                                               side_effect=write_session):
                            self.assertTrue(self.tool.login("user"))
                            login.assert_called_once_with("user", "pass")

    def test_load_profile_rejects_incomplete_cache(self):
        config.profile_cache_path("user").write_text('{"username": "user"}')
        self.assertIsNone(load_profile("user"))

    def test_session_for_other_account_is_rejected(self):
        with mock.patch.object(self.tool, "_load_session_file", return_value=True):
            with mock.patch.object(self.tool.cl, "account_info",
                                   return_value=SimpleNamespace(username="other")):
                self.assertFalse(self.tool.try_saved_session("user", verify=True))
                self.assertFalse(self.tool.is_logged_in)

    def test_stale_session_without_password_fails(self):
        with mock.patch.object(self.tool, "_load_session_file", return_value=True):
            with mock.patch.object(self.tool.cl, "account_info",
                                   side_effect=ig_exc.LoginRequired("expired")):
                with mock.patch("instaghost.client.sys.stdin",
                                SimpleNamespace(isatty=lambda: False)):
                    self.assertFalse(self.tool.login("user"))

    def test_stale_session_falls_back_to_password(self):
        with mock.patch.object(self.tool, "_load_session_file", return_value=True):
            with mock.patch.object(self.tool.cl, "account_info",
                                   side_effect=ig_exc.LoginRequired("expired")):
                with mock.patch.object(self.tool.cl, "login") as login:
                    self.assertTrue(self.tool.login("user", "pass"))
                    login.assert_called_once_with("user", "pass")

    def test_login_can_save_credentials(self):
        def write_session(path):
            Path(path).write_text("{}")

        with mock.patch.object(self.tool, "_resume_session", return_value=False):
            with mock.patch.object(self.tool.cl, "login"):
                with mock.patch.object(self.tool.cl, "dump_settings",
                                       side_effect=write_session):
                    self.assertTrue(self.tool.login("user", "pass", save=True))
        self.assertEqual(LoginManager.load_login_data(),
                         {"username": "user", "password": "pass"})

    def test_session_file_is_private(self):
        def write_session(path):
            Path(path).write_text("{}")

        with mock.patch.object(self.tool, "_load_session_file", return_value=False):
            with mock.patch.object(self.tool.cl, "login"):
                with mock.patch.object(self.tool.cl, "account_info", return_value=fake_user()):
                    with mock.patch.object(self.tool.cl, "dump_settings",
                                           side_effect=write_session):
                        self.assertTrue(self.tool.login("user", "pass"))
        path = config.session_path("user")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_get_profile_info_uses_cached_user(self):
        with mock.patch.object(self.tool.cl, "user_info_by_username",
                               side_effect=AssertionError("refetched")):
            info = self.tool.get_profile_info("user")
        self.assertEqual(info["username"], "user")

    def test_interactive_menu_passes_output_dir(self):
        info = {"username": "user"}
        with mock.patch.object(self.tool, "download_posts") as posts:
            with mock.patch("builtins.input", side_effect=["2", "7", "0"]):
                self.tool.interactive_menu(info, "out")
        posts.assert_called_once_with("user", "7", "out")


if __name__ == "__main__":
    unittest.main()
