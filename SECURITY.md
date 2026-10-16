# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

Only the latest major line receives security fixes. The 1.x line (instaloader
backend) is unmaintained.

## Reporting a Vulnerability

Open a GitHub issue at
[Anon4You/InstaGhost/issues](https://github.com/Anon4You/InstaGhost/issues)
with the `security` label. Include:

- InstaGhost version (`instaghost --version`)
- Python version and install source (pip / Termux TUR index)
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
