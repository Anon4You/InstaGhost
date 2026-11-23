"""Web gateway for InstaGhost.

Stdlib HTTP server over the templates in `webui/`. The printed URL carries a
per-run token, stored in a session cookie after the first visit. One job runs
at a time and reuses the host session from `instaghost --login`.
"""

import argparse
import hmac
import html
import mimetypes
import os
import secrets
import shutil
import subprocess
import sys
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import config
from .gateway import resolve_job_file, run_job, valid_username

UI_DIR = Path(__file__).with_name("webui")
ASSETS = {
    "styles.css": "text/css; charset=utf-8",
    "app.js": "application/javascript; charset=utf-8",
    "favicon.svg": "image/svg+xml",
}

TOKEN = ""
COOKIE_NAME = "ig_token"

ACTION_TILES = [
    ("profile", "Profile", "Bio, stats, links"),
    ("pic", "Picture", "Full-size avatar"),
    ("posts", "Posts", "Latest feed posts"),
    ("reels", "Reels", "Latest clips"),
    ("stories", "Stories", "Active stories"),
    ("all", "Everything", "Pic, 10 posts, 5 reels, stories"),
    ("url", "From URL", "One post or reel link"),
]
ACTION_LABELS = {key: title for key, title, _ in ACTION_TILES}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".webm"}


def _template(name):
    return (UI_DIR / name).read_text(encoding="utf-8")


def _token_ok(value):
    return bool(TOKEN) and hmac.compare_digest(value or "", TOKEN)


def _cookie_token(header):
    if not header:
        return ""
    try:
        jar = SimpleCookie()
        jar.load(header)
    except CookieError:
        return ""
    morsel = jar.get(COOKIE_NAME)
    return morsel.value if morsel else ""


def authorized(path, cookie_header):
    if _token_ok(_cookie_token(cookie_header)):
        return True
    return _token_ok(parse_qs(urlparse(path).query).get("token", [""])[0])


def _session_badge():
    try:
        found = any(config.CONFIG_DIR.glob("session-*"))
    except OSError:
        found = False
    if found:
        return "Session saved", "ok"
    return "No saved session", "warn"


def _page(content, title="InstaGhost · Web Gateway", show_status=True):
    badge, dot = _session_badge()
    status = (
        f'<div class="status"><span class="dot {dot}"></span>{html.escape(badge)}</div>'
        if show_status else ""
    )
    return (
        _template("base.html")
        .replace("{{title}}", html.escape(title))
        .replace("{{status}}", status)
        .replace("{{content}}", content)
    )


def _tile(name, href):
    suffix = Path(name).suffix.lower()
    safe_href = html.escape(href)
    safe_name = html.escape(name)
    if suffix in IMAGE_EXT:
        return (
            f'<a class="tile" href="{safe_href}" target="_blank" rel="noopener">'
            f'<img loading="lazy" src="{safe_href}" alt="{safe_name}">'
            f'<span class="name">{safe_name}</span></a>'
        )
    if suffix in VIDEO_EXT:
        return (
            f'<div class="tile"><video src="{safe_href}" controls preload="metadata"></video>'
            f'<a class="name" href="{safe_href}" target="_blank" rel="noopener">{safe_name}</a></div>'
        )
    return (
        f'<a class="tile file" href="{safe_href}" download>'
        f'<span class="name">{safe_name}</span><span class="meta">Download</span></a>'
    )


def _form_content():
    tiles = "".join(
        f'<input type="radio" id="a-{key}" name="action" value="{key}"'
        + (" checked" if key == "profile" else "")
        + f'><label for="a-{key}"><span class="t">{title}</span>'
        + f'<span class="d">{desc}</span></label>'
        for key, title, desc in ACTION_TILES
    )
    return _template("form.html").replace("{{csrf}}", html.escape(TOKEN)).replace("{{tiles}}", tiles)


def _result_content(action, target, ok, text, files):
    title = ACTION_LABELS.get(action, str(action).title())
    target_html = f'<span class="target">{html.escape(target)}</span>' if target else ""
    status = '<span class="pill ok">Done</span>' if ok else '<span class="pill fail">Failed</span>'
    eyebrow = "Job complete" if ok else "Job failed"
    log = f'<pre class="log-pre">{html.escape(text or "No output.")}</pre>'
    if files:
        gallery = "".join(_tile(name, href) for name, href in files)
        main = (
            f'<div class="panel"><div class="panel-head"><h2>Downloads</h2>'
            f'<span class="muted">{len(files)} file{"s" if len(files) != 1 else ""}</span></div>'
            f'<div class="gallery">{gallery}</div></div>'
        )
        side = f'<aside class="panel side"><h2>Job log</h2>{log}</aside>'
    else:
        main = f'<div class="panel"><h2>Result</h2>{log}</div>'
        side = (
            '<aside class="panel side"><h2>Next</h2>'
            '<div class="tip">Try another action, or open a different profile.</div></aside>'
        )
    return (
        _template("result.html")
        .replace("{{eyebrow}}", eyebrow)
        .replace("{{title}}", html.escape(title))
        .replace("{{target}}", target_html)
        .replace("{{status}}", status)
        .replace("{{main}}", main)
        .replace("{{side}}", side)
    )


def _open_browser(url):
    for command in ("xdg-open", "termux-open-url", "open"):
        path = shutil.which(command)
        if not path:
            continue
        try:
            subprocess.Popen(
                [path, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    server_version = "InstaGhostGateway"

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _login_redirect(self, target):
        cookie = SimpleCookie()
        cookie[COOKIE_NAME] = TOKEN
        cookie[COOKIE_NAME]["path"] = "/"
        cookie[COOKIE_NAME]["httponly"] = True
        cookie[COOKIE_NAME]["samesite"] = "Lax"
        self.send_response(303)
        self.send_header("Location", target or "/")
        self.send_header("Set-Cookie", cookie.output(header="").strip())
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _denied(self):
        self._send(401, _page(_template("denied.html"), show_status=False))

    def _not_found(self):
        self._send(404, _page(_template("not_found.html")))

    def _asset(self, name):
        ctype = ASSETS.get(name)
        if not ctype:
            return self._send(404, b"Not found", "text/plain; charset=utf-8")
        try:
            data = (UI_DIR / name).read_bytes()
        except OSError:
            return self._send(404, b"Not found", "text/plain; charset=utf-8")
        self._send(200, data, ctype)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            return self._send(204, b"")
        if parsed.path.startswith("/assets/"):
            return self._asset(unquote(parsed.path[len("/assets/"):]))
        if _token_ok(parse_qs(parsed.query).get("token", [""])[0]):
            return self._login_redirect(parsed.path or "/")
        if not _token_ok(_cookie_token(self.headers.get("Cookie", ""))):
            return self._denied()

        if parsed.path == "/":
            return self._send(200, _page(_form_content()))
        if parsed.path.startswith("/files/"):
            parts = parsed.path.split("/", 3)
            if len(parts) != 4:
                return self._not_found()
            target = resolve_job_file(unquote(parts[2]), unquote(parts[3]))
            if not target:
                return self._not_found()
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            try:
                size = target.stat().st_size
                fh = open(target, "rb")
            except OSError:
                return self._not_found()
            try:
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
                self.end_headers()
                shutil.copyfileobj(fh, self.wfile)
            finally:
                fh.close()
            return
        return self._not_found()

    def do_POST(self):
        if not authorized(self.path, self.headers.get("Cookie", "")):
            return self._denied()
        if urlparse(self.path).path != "/run":
            return self._not_found()
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, _page(_template("not_found.html")))
        if length <= 0 or length > 64 * 1024:
            return self._send(400, _page(_template("not_found.html")))
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        if not _token_ok(form.get("csrf", [""])[0]):
            return self._send(403, _page(_template("denied.html")))

        action = form.get("action", ["profile"])[0]
        username = form.get("username", [""])[0].strip() or None
        url = form.get("url", [""])[0].strip() or None
        count = form.get("count", ["5"])[0]

        ok, text, jobdir = (False, "", None)
        try:
            ok, text, jobdir = run_job(action, username=username, count=count, url=url)
        except Exception as e:
            text = f"Job failed: {e}"

        files = []
        if jobdir:
            for path in sorted(jobdir.rglob("*")):
                if path.is_file():
                    files.append(
                        (
                            path.name,
                            f"/files/{quote(jobdir.name)}/{quote(path.relative_to(jobdir).as_posix())}",
                        )
                    )
        if action == "url":
            target = url
        else:
            target = f"@{username}" if username and valid_username(username) else (username or "")
        label = ACTION_LABELS.get(action, str(action).title())
        return self._send(200, _page(_result_content(action, target, ok, text, files), title=f"{label} · InstaGhost"))


def main():
    global TOKEN
    parser = argparse.ArgumentParser(
        prog="instaghost-web", description="Web gateway for InstaGhost"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default 8080)")
    args = parser.parse_args()

    TOKEN = os.environ.get("INSTAGHOST_WEB_TOKEN") or secrets.token_urlsafe(24)
    try:
        server = HTTPServer((args.host, args.port), Handler)
    except OSError as e:
        sys.exit(f"Cannot listen on {args.host}:{args.port}: {e}")

    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{display_host}:{args.port}/?token={TOKEN}"
    print("InstaGhost web gateway is running.")
    print(f"Open: {url}")
    print("This link signs you in. Keep it private.")
    _open_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
