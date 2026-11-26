"""Shared job runner for the web and Telegram gateways.

Gateways reuse the session created by `instaghost --login` on the host and
never accept Instagram passwords.
"""

import contextlib
import io
import re
import shutil
import tempfile
import time
from pathlib import Path

from .config import valid_username

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

JOB_ROOT = Path.home() / ".cache" / "instaghost-gateway"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
JOB_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

ACTIONS = ("profile", "pic", "posts", "reels", "stories", "url", "all")


def clean_output(text):
    text = ANSI_RE.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_command(text):
    """Turn a Telegram command into (action, run_job kwargs)."""
    parts = (text or "").split()
    if not parts or not parts[0].startswith("/"):
        return None
    cmd = parts[0][1:].split("@", 1)[0].lower()
    args = parts[1:]
    if cmd in ("start", "help"):
        return "help", {}
    if cmd in ("profile", "pic", "posts", "reels", "stories", "all"):
        if not args:
            return "usage", {"command": cmd}
        kwargs = {"username": args[0]}
        if cmd in ("posts", "reels"):
            raw = args[1] if len(args) > 1 else ""
            kwargs["count"] = int(raw) if raw.isdigit() else 5
        return cmd, kwargs
    if cmd == "url":
        if not args:
            return "usage", {"command": cmd}
        return "url", {"url": args[0]}
    return "help", {}


def resolve_job_file(job_id, rel):
    """Resolve a file inside a job folder, or None if it escapes it."""
    if not JOB_ID_RE.fullmatch(job_id or ""):
        return None
    root = (JOB_ROOT / job_id).resolve()
    path = (root / rel).resolve()
    if root != path and root not in path.parents:
        return None
    return path if path.is_file() else None


def job_files(jobdir):
    return sorted(p for p in Path(jobdir).rglob("*") if p.is_file())


@contextlib.contextmanager
def job_lock():
    """Serialize jobs across the web and Telegram processes."""
    JOB_ROOT.mkdir(parents=True, exist_ok=True)
    lock_file = JOB_ROOT / "job.lock"
    with open(lock_file, "w") as handle:
        if fcntl:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(handle, fcntl.LOCK_UN)


def prune_jobs(max_age=7 * 24 * 60 * 60):
    """Delete job folders older than max_age seconds."""
    if not JOB_ROOT.exists():
        return 0
    cutoff = time.time() - max_age
    removed = 0
    for path in JOB_ROOT.iterdir():
        try:
            if path.is_dir() and path.stat().st_mtime < cutoff:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        except OSError:
            pass
    return removed


def run_job(action, username=None, count=5, url=None):
    """Run one action with the saved session. Returns (ok, text, jobdir)."""
    from .client import InstaGhost
    from .output import LoadingAnimation

    if action not in ACTIONS:
        return False, f"Unknown action: {action}", None
    if action == "url":
        if not (url or "").startswith(("http://", "https://")):
            return False, "Invalid URL.", None
    elif not valid_username(username):
        return False, "Invalid Instagram username.", None

    try:
        count = max(1, min(int(count), 30))
    except (TypeError, ValueError):
        count = 5

    with job_lock():
        LoadingAnimation.enabled = False
        jobdir = None
        if action != "profile":
            jobdir = Path(tempfile.mkdtemp(prefix="job-", dir=str(JOB_ROOT)))

        out = io.StringIO()
        tool = InstaGhost()
        with contextlib.redirect_stdout(out):
            tool.try_saved_session(verify=True)
            if not tool.is_logged_in:
                print("No saved session. On the host run: instaghost --login ...")
            if action == "profile":
                info = tool.get_profile_info(username)
                if info:
                    tool.print_profile_info(info)
                ok = bool(info)
            elif action == "url":
                ok = bool(tool.download_from_url(url, str(jobdir)))
            else:
                ok = True
                if action in ("pic", "all"):
                    ok = bool(tool.download_profile_pic(username, str(jobdir))) and ok
                if action in ("posts", "all"):
                    ok = tool.download_posts(username, count if action == "posts" else 10, str(jobdir)) and ok
                if action in ("reels", "all"):
                    ok = tool.download_reels(username, count if action == "reels" else 5, str(jobdir)) and ok
                if action in ("stories", "all"):
                    ok = tool.download_stories(username, str(jobdir)) and ok

        text = clean_output(out.getvalue())
        files = job_files(jobdir) if jobdir else []
        if jobdir and not files:
            shutil.rmtree(jobdir, ignore_errors=True)
            jobdir = None
            ok = False
            text = (text + "\nNothing was downloaded.").strip()
        return ok, text, jobdir
