# Changelog

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
