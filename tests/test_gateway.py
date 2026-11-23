import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from instaghost.gateway import (  # noqa: E402
    clean_output,
    parse_command,
    resolve_job_file,
    run_job,
    valid_username,
)


class Validators(unittest.TestCase):
    def test_username(self):
        self.assertTrue(valid_username("foo.bar_1"))
        self.assertFalse(valid_username("../etc/passwd"))
        self.assertFalse(valid_username(".."))
        self.assertFalse(valid_username("bad/name"))
        self.assertFalse(valid_username("a" * 31))
        self.assertFalse(valid_username(""))

    def test_commands(self):
        self.assertEqual(parse_command("/profile foo"), ("profile", {"username": "foo"}))
        self.assertEqual(parse_command("/posts foo 7"), ("posts", {"username": "foo", "count": 7}))
        self.assertEqual(parse_command("/posts foo x"), ("posts", {"username": "foo", "count": 5}))
        self.assertEqual(parse_command("/reels@bot foo"), ("reels", {"username": "foo", "count": 5}))
        self.assertEqual(parse_command("/url https://instagram.com/p/x/")[0], "url")
        self.assertEqual(parse_command("/profile")[0], "usage")
        self.assertEqual(parse_command("/wat")[0], "help")
        self.assertEqual(parse_command("/start")[0], "help")
        self.assertIsNone(parse_command("hello"))
        self.assertIsNone(parse_command(None))

    def test_clean_output(self):
        self.assertEqual(clean_output("\x1b[91m> x\x1b[0m\r\n\n\n\nend"), "> x\n\nend")

    def test_file_traversal(self):
        self.assertIsNone(resolve_job_file("../etc", "passwd"))
        self.assertIsNone(resolve_job_file("job-x", "../../etc/passwd"))
        self.assertIsNone(resolve_job_file("job-x", "/etc/passwd"))

    def test_run_job_rejects_bad_input(self):
        self.assertFalse(run_job("nope")[0])
        self.assertFalse(run_job("posts", username="../x")[0])
        self.assertFalse(run_job("url", url="ftp://example.com/a")[0])


if __name__ == "__main__":
    unittest.main()
