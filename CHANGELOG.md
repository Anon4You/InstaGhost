# Changelog

## 2.2.0

- Security: session and credential files are created with mode `0600`, and the
  config directory with `0700`.
- Security: Telegram polling/handler errors redact the bot token.
- Security: saved sessions are verified before reuse; an expired session no
  longer blocks a password login, and `--login-user` only resumes that account.
- Security: if several sessions exist without `logindata`, reuse stops and asks
  for `--login-user` instead of picking an account; a session that belongs to a
  different account is rejected.
- Security: usernames are validated at the CLI boundary, and profile-picture
  downloads use the URL already returned by Instagram.
- Correctness: downloads no longer report success when every item failed, and
  media is downloaded from the URLs already fetched instead of re-fetching each
  item by ID.
- Correctness: post/reel counts are clamped to 1–30, so `-P 0` no longer
  downloads the entire feed.
- Correctness: `--url` accepts `/share/p/` links and rejects unsupported story
  URLs; interactive downloads honor `-o/--output`.
- Correctness: profile lookups reuse the cached user and no longer hit the API
  twice per run; cached profile writes are atomic.
- Gateways: web and Telegram jobs share a cross-process lock, old job folders
  are pruned after 7 days, and the web handler has a request timeout.
- CLI: `Ctrl-C` exits cleanly with status 130; dead login retry removed;
  passwords are read with hidden input.
- Telegram bot: prompts for a missing bot token and owner IDs, saves them to
  `~/.config/instaghost/telegram.json` (mode `0600`), and skips prompts when
  environment variables are set.
- Telegram bot: checks the token with `getMe` at startup and accepts commands
  only in private chats with an allowed owner.
- CLI: `--logout` removes saved credentials and all sessions; a missing or
  expired saved session prompts for the password with hidden input.
- CLI: `--login` without saved credentials prompts for the username and reads
  the password with hidden input; `--save-login` works with that prompt.
- Cache: cached profiles with missing or unexpected fields are ignored.
- Web gateway: adds security headers and prunes old job folders after jobs.
- Packaging: dependency upper bounds added and the deprecated license
  classifier removed; GitHub Actions runs the tests on Python 3.11–3.13.
- Release: pushing a `v*` tag runs tests, builds the wheel and sdist, and
  publishes them with the matching `CHANGELOG.md` section as release notes.
- Packaging: version is read from `instaghost.__version__`; duplicate
  `requirements.txt` removed.
- Tests: added coverage for downloads, sessions, credentials, URL parsing,
  token redaction, job pruning, and the web timeout.

## 2.1.0

- Optional web gateway (`instaghost-web`) and Telegram bot (`instaghost-bot`)
  that reuse the saved host session and never ask for an Instagram password.
- Web gateway: token link, HttpOnly cookie auth, dark gallery UI, one job at
  a time; templates and assets live in `instaghost/webui/`.
- Telegram bot: owner allowlist, per-command jobs, sends media back directly.
- Package split into `cli`, `client`, `auth`, `cache`, `config`, `output`,
  `errors`, `gateway`, `web`, and `telegram_bot` modules.
- Gateways cache the target lookup, so each job makes one profile request.
- Documented the TermuxVoid package (`pkg install instaghost`), which installs
  all dependencies and upgrades with normal Termux package updates.
- Expanded the README with installation paths, CLI and authentication details,
  gateway guides, data locations, troubleshooting, and development notes.

## 2.0.0

- Backend rewrite: `instaloader` → `instagrapi` (private mobile API), fixing
  chronic `429` failures on the web profile endpoint.
- Sessions stored as instagrapi settings in `~/.config/instaghost/session-<user>`;
  stale 1.x session files are ignored safely (log in fresh once).
- Login handles 2FA codes, app-approval challenges, bad credentials, and
  rate limits with distinct messages.
- Reels use the dedicated clips API; stories download per item with
  per-item skip instead of all-or-nothing failure.

## 1.0.3

- Fail fast on rate limits (`max_connection_attempts=1`) instead of hanging.
- Session reuse for all commands, including public lookups.
- Cached basic profile info shown (marked) when live fetch is blocked.
- Login-status line on every run; basic report always prints.
- Banner shows version; fixed padding for narrow terminals.
- Packaging: `instaloader>=4.15`, `python>=3.8`, explicit src-layout config.

## 1.0.2

- Interactive terminal, URL downloads, private-account support.

## 1.0.0

- Initial release: profile info, posts, reels, stories via instaloader.
