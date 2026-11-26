# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| < 2.2   | :x:                |

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
| Session cookies     | `~/.config/instaghost/session-<user>`       | `0600` file mode |
| Cached profile info | `~/.config/instaghost/profile-<user>.json`  | OS file permissions (non-sensitive) |
| Telegram settings   | `~/.config/instaghost/telegram.json`        | `0600` file mode |

Notes and expectations:

- `logindata` holds your Instagram password in **plaintext JSON**. It is only
  written when you pass `--save-login`. Prefer session-only use (plain
  `--login` reuses the session file without storing your password).
- Session files grant account access like a password. Never share, upload, or
  commit them. They are covered by `.gitignore`, but that only protects this
  repository — keep them out of backups and screenshots too.
- `Clear saved login` (interactive menu, option 8 → 3) removes `logindata`;
  run `instaghost --logout` to remove both `logindata` and all `session-<user>`
  files.
- Prefer `instaghost --login` or `--login-user` without `--login-pass`: the
  password prompt is hidden and avoids shell history and process-list exposure.
  Use `--login-pass` only for automation where that risk is acceptable.
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
- `instaghost-bot` requires a bot token and numeric owner IDs. Missing values
  are prompted for and saved to `~/.config/instaghost/telegram.json` with mode
  `0600`; environment variables override the saved values. The token is checked
  with Telegram at startup, and commands are accepted only in private chats
  with an allowed owner. Anyone with the bot token controls the bot, so keep it
  out of shell arguments and logs.
- Both gateways reuse the host session file and never accept Instagram
  credentials over the network; log in with the CLI first. They share a lock
  so only one job runs at a time, and old job folders are pruned after 7 days.
  When several sessions exist, the gateways use the account in `logindata` or
  stop instead of guessing.
- Media sent through the Telegram bot (and downloaded through the web page)
  leaves this machine.
