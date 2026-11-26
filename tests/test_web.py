import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost import web  # noqa: E402


class Auth(unittest.TestCase):
    def test_token_and_cookie(self):
        web.TOKEN = "t0ken"
        self.assertTrue(web._token_ok("t0ken"))
        self.assertFalse(web._token_ok("nope"))
        self.assertFalse(web._token_ok(""))
        self.assertTrue(web.authorized("/?token=t0ken", ""))
        self.assertTrue(web.authorized("/", "ig_token=t0ken; other=1"))
        self.assertFalse(web.authorized("/", "ig_token=nope"))
        self.assertFalse(web.authorized("/", ""))


class Server(unittest.TestCase):
    def test_handler_timeout(self):
        self.assertEqual(web.Handler.timeout, 30)


class Rendering(unittest.TestCase):
    def test_result_page_escapes(self):
        page = web._result_content(
            "posts", "<b>target</b>", True, "<script>x</script>", [("a b.jpg", "/files/job-x/a%20b.jpg")]
        )
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;b&gt;target&lt;/b&gt;", page)
        self.assertIn('src="/files/job-x/a%20b.jpg"', page)

    def test_ui_files(self):
        web.TOKEN = "t0ken"
        for name in (
            "base.html", "form.html", "result.html", "denied.html",
            "not_found.html", "styles.css", "app.js", "favicon.svg",
        ):
            self.assertTrue((web.UI_DIR / name).is_file(), name)

        page = web._page(web._form_content())
        self.assertNotIn("{{", page)
        self.assertIn('href="/assets/styles.css"', page)
        self.assertIn('src="/assets/app.js"', page)
        self.assertIn('name="csrf" value="t0ken"', page)

        result = web._page(web._result_content("posts", "foo", True, "ok", []))
        self.assertNotIn("{{", result)

        denied = web._page(web._template("denied.html"), show_status=False)
        self.assertNotIn('class="status"', denied)


if __name__ == "__main__":
    unittest.main()
