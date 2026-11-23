# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| < 2.1   | :x:                |

Only the latest release line receives security fixes. The 1.x line
(instaloader backend) is unmaintained.

## Reporting a Vulnerability

Open a GitHub issue at
[Anon4You/InstaGhost/issues](https://github.com/Anon4You/InstaGhost/issues)
with the `security` label. Include:

- InstaGhost version (`instaghost --version`)
- Python version and install source (pip, TermuxVoid, or Termux TUR index)
- Steps to reproduce (redact usernames, passwords, and session data)

Do **not** paste credentials, session files, or target account details in
public issues. You will get a response within a reasonable time, and fixes
ship as patch releases.

## Credential Handling

InstaGhost stores sensitive data on your device. Know where it lives:

| Data                | Location                                    | Protection |
| ------------------- | ------------------------------------------- | ---------- |
| Login credentials   | `~/.config/instaghost/logindata` (only with `--save-login`) | `0600` file mode |
| Session cookies     | `~/.config/instaghost/session-<user>`       | OS file permissions |
| Cached profile info | `~/.config/instaghost/profile-<user>.json`  | OS file permissions (non-sensitive) |

Notes and expectations:

- `logindata` holds your Instagram password in **plaintext JSON**. It is only
  written when you pass `--save-login`. Prefer session-only use (plain
  `--login` reuses the session file without storing your password).
- Session files grant account access like a password. Never share, upload, or
  commit them. They are covered by `.gitignore`, but that only protects this
  repository — keep them out of backups and screenshots too.
- `Clear saved login` (interactive menu, option 8 → 4) removes `logindata`;
  delete `session-<user>` files manually for a full logout.
- Only run InstaGhost on machines and networks you trust, and only against
  accounts you own or are explicitly authorized to access (see the README
  disclaimer and Instagram's Terms of Service).

## Gateways

- `instaghost-web` prints a login URL with a per-run token and stores the
  token in an HttpOnly cookie on first visit. Anyone with the URL or cookie
  can use your session: treat it like a password, and keep it out of chats,
  screenshots, and issue reports. It binds to `127.0.0.1` by default;
  `--host` exposes it to the network, so use that only on a network you
  trust. Set `INSTAGHOST_WEB_TOKEN` only on a trusted machine.
- `instaghost-bot` requires `TELEGRAM_BOT_TOKEN` and a numeric
  `TELEGRAM_ALLOWED_USER_ID`; every other user is rejected. Anyone with the
  bot token controls the bot, so keep it out of shell arguments and logs.
- Both gateways reuse the host session file and never accept Instagram
  credentials over the network; log in with the CLI first.
- Media sent through the Telegram bot (and downloaded through the web page)
  leaves this machine.
