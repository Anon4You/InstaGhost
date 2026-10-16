<p align="center">
  <img src="instaghost-logo.png" alt="InstaGhost Logo" width="200"/>
</p>

<h1 align="center">🌌 InstaGhost</h1>
<p align="center">
  <strong>A sleek and powerful tool for Instagram data gathering</strong><br>
  <em>Extract profile pics, posts, reels, stories, and more with ease!</em>
</p>

<p align="center">
  <a href="https://github.com/Anon4You/InstaGhost"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
   <a href="https://github.com/Anon4You/InstaGhost"><img src="https://img.shields.io/badge/Version-1.0.3-green.svg" alt="Version"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.8+-yellow.svg" alt="Python"></a>
</p>

---

## 🚀 Overview

**InstaGhost** is a feature-rich command-line utility for professional Instagram data extraction. Effortlessly download profile pictures, posts, reels, stories, and content from specific URLs, including private accounts with authentication. Explore the full project at [https://github.com/Anon4You/InstaGhost](https://github.com/Anon4You/InstaGhost).

---

## 🛠️ Installation

Install InstaGhost with a single command:

```bash
pip install git+https://github.com/Anon4You/InstaGhost.git
```

> **Note**: Requires Python 3.8+.

---

## 📚 Usage

Run InstaGhost with one of the following syntaxes:

```bash
instaghost <username> [options]
instaghost --url <instagram_url>
instaghost --login
```

### Command Reference

| Option              | Emoji | Description                        |
|---------------------|-------|------------------------------------|
| `-i, --interactive` | 🖥️   | Launch interactive terminal        |
| `-p, --profile-pic` | 📸   | Extract profile picture            |
| `-P, --posts`       | 📷   | Download posts (specify count)     |
| `-r, --reels`       | 🎬   | Download reels (specify count)     |
| `-s, --stories`     | 📖   | Download stories                   |
| `-a, --all`         | 🚀   | Download all intelligence          |
| `-o, --output`      | 💾   | Specify output directory           |
| `-l, --login`       | 🔐   | Login to Instagram                 |
| `--login-user`      | 👤   | Login username                     |
| `--login-pass`      | 🔑   | Login password                     |
| `--save-login`      | 💾   | Save login credentials             |
| `--url`             | 🔗   | Download from specific URL         |
| `--private`         | 🕵️   | Access private accounts            |
| `-h, --help`        | ❓   | Show help message                  |

### Example Commands

```bash
# Launch interactive mode
instaghost username -i

# Download profile picture and 5 posts
instaghost target -p -P 5

# Grab everything available
instaghost user -a

# Download content from a specific URL
instaghost --url https://instagram.com/p/ABC123/

# Login to Instagram with credentials
instaghost --login --login-user myuser --login-pass mypass

# Access a private account
instaghost private_user --private -l
```

---

## 🔐 Login sessions

Every run prints `Logged in as @you` or a `Not logged in` warning. A successful
login is saved to `~/.config/instaghost/session-<user>` and silently reused by
all later commands (public lookups included), so you only log in once. If the
session expires, just log in again.

Basic profile info is cached per target, so it still shows (marked as cached)
when Instagram rate-limits the live request. Downloads always need a live
request and may still fail under a rate limit.

---

## ⚠️ Troubleshooting `429 Too Many Requests`

Instagram aggressively throttles the profile endpoint — this can happen on the
very first request, even logged in (known instaloader 4.15.x issue). The tool
fails fast instead of hanging. If you see it:

1. Close the Instagram app and don't run parallel instances or VPNs.
2. Wait 30–60 minutes, then log in once and make a single request.
3. Repeated restarts make the ban worse — each retry counts as more requests.

---

## ⚖️ License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

Use **InstaGhost** responsibly and in compliance with Instagram's Terms of Service. Ensure you have proper authorization when accessing private accounts. The developers are not liable for any misuse of this tool.

---

<p align="center">
  <strong>Explore, extract, and enjoy! 🌟</strong><br>
  Visit the full repository at <a href="https://github.com/Anon4You/InstaGhost">https://github.com/Anon4You/InstaGhost</a> for issues or feedback.
</p>