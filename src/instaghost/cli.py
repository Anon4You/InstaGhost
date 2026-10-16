#!/usr/bin/env python3

from instagrapi import Client
from instagrapi import exceptions as ig_exc
import argparse
import json
import sys
import os
import requests
import time
import threading
import re
from datetime import datetime
from pathlib import Path

# Errors that mean "Instagram throttled us, back off and retry later"
RATE_LIMIT_ERRORS = (
    ig_exc.RateLimitError,
    ig_exc.PleaseWaitFewMinutes,
    ig_exc.ClientThrottledError,
    ig_exc.ClientConnectionError,
)
# Errors that mean "this session is not logged in (or no longer valid)"
LOGIN_ERRORS = (
    ig_exc.LoginRequired,
    ig_exc.ClientLoginRequired,
    ig_exc.ClientUnauthorizedError,
)


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    PURPLE = '\033[95m'
    ORANGE = '\033[33m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class HackerStyle:
    @staticmethod
    def banner():
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")
        try:
            from instaghost import __version__ as _ver
        except Exception:
            _ver = "2.0.0"
        pad = ' ' * 2
        banner = f"""
{Colors.CYAN}
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣾⣿⣿⣿⣿⣿⣿⣶⣄
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⠿⢿⣿⣿⣿⣿⣆
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⠁⠀⠿⢿⣿⡿⣿⣿⡆
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣦⣤⣴⣿⠃⠀⠿⣿⡇
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⡿⠋⠁⣿⠟⣿⣿⢿⣧⣤⣴⣿⡇
{pad}⠀⠀⠀⠀⢀⣠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠘⠁⢸⠟⢻⣿⡿
{pad}⠀⠀⠙⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣴⣇⢀⣤⠀⠀⠀⠀⠘⣿⠃
{pad}⠀⠀⠀⠀⠀⢈⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣴⣿⢀⣴⣾⠇
{pad}⠀⠀⣀⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏
{pad}⠀⠀⠉⠉⠉⠉⣡⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃
{pad}⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⡿⠟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁
{pad}⠀⠀⣴⡾⠿⠿⠿⠛⠋⠉⠀⢸⣿⣿⣿⣿⠿⠋⢸⣿⡿⠋
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⡿⠟⠋⠁⠀⠀⡿⠋
{pad}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠈
{Colors.RESET}

{Colors.BLUE}{Colors.BOLD}{pad}InstaGhost v{_ver} - Instagram OSINT Tool{Colors.RESET}
{Colors.GREEN}{pad}Author: Anon4You  |  GitHub: github.com/Anon4You/InstaGhost{Colors.RESET}

{Colors.WHITE}{pad}Simple and professional Instagram data gathering{Colors.RESET}
"""
        print(banner)

    @staticmethod
    def print_success(text):
        print(f"{Colors.GREEN}┃ ✓ {Colors.RESET}{text}")

    @staticmethod
    def print_error(text):
        print(f"{Colors.RED}┃ ✗ {Colors.RESET}{text}")

    @staticmethod
    def print_warning(text):
        print(f"{Colors.ORANGE}┃ ! {Colors.RESET}{text}")

    @staticmethod
    def print_info(text):
        print(f"{Colors.BLUE}┃ * {Colors.RESET}{text}")

    @staticmethod
    def print_system(text):
        print(f"{Colors.PURPLE}┃ ⚡ {Colors.RESET}{text}")

    @staticmethod
    def print_data(text):
        print(f"{Colors.CYAN}┃ → {Colors.RESET}{text}")

class LoadingAnimation:
    def __init__(self, message="Loading"):
        self.message = message
        self.running = False
        self.thread = None

    def __animate(self):
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while self.running:
            print(f"\r{Colors.PURPLE}┃ {frames[i]} {Colors.RESET}{self.message}...", end="", flush=True)
            i = (i + 1) % len(frames)
            time.sleep(0.1)
        print("\r", end="", flush=True)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.__animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

class LoginManager:
    @staticmethod
    def get_login_data_path():
        """Get the path for storing login data"""
        config_dir = Path.home() / '.config' / 'instaghost'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'logindata'

    @staticmethod
    def get_session_path(username):
        """instagrapi settings file for a login user (reuse avoids relogin blocks)."""
        config_dir = Path.home() / '.config' / 'instaghost'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / f'session-{username}'

    @staticmethod
    def get_profile_cache_path(username):
        """Cached basic info so it works even when IG rate-limits fresh fetches."""
        config_dir = Path.home() / '.config' / 'instaghost'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / f'profile-{username}.json'

    @staticmethod
    def save_login_data(username, password):
        """Save login credentials securely"""
        login_path = LoginManager.get_login_data_path()
        login_data = {
            'username': username,
            'password': password
        }
        try:
            with open(login_path, 'w') as f:
                json.dump(login_data, f)
            os.chmod(login_path, 0o600)  # Secure file permissions
            HackerStyle.print_success(f"Login data saved for @{username}")
            return True
        except Exception as e:
            HackerStyle.print_error(f"Failed to save login data: {e}")
            return False

    @staticmethod
    def load_login_data():
        """Load saved login credentials"""
        login_path = LoginManager.get_login_data_path()
        if login_path.exists():
            try:
                with open(login_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                HackerStyle.print_error(f"Failed to load login data: {e}")
        return None

    @staticmethod
    def clear_login_data():
        """Clear saved login credentials"""
        login_path = LoginManager.get_login_data_path()
        if login_path.exists():
            login_path.unlink()
            HackerStyle.print_success("Login data cleared")
            return True
        return False

class InstaGhost:
    def __init__(self):
        self.cl = Client()
        self.is_logged_in = False
        self.login_user = None

    def _load_session_file(self, username):
        """Attach a saved instagrapi session. No network call (lazy trust)."""
        session_file = LoginManager.get_session_path(username)
        if not session_file.exists():
            return False
        try:
            self.cl.load_settings(str(session_file))
            self.is_logged_in = True
            self.login_user = username
            return True
        except Exception:
            return False

    def try_saved_session(self, username=None):
        """Resume a saved session without a password prompt. Returns True on success."""
        candidates = []
        if username:
            candidates.append(username)
        saved_login = LoginManager.load_login_data()
        if saved_login and saved_login.get('username') not in candidates:
            candidates.append(saved_login['username'])
        # Fall back to any session-* file (logindata may be missing)
        try:
            config_dir = Path.home() / '.config' / 'instaghost'
            for p in config_dir.glob('session-*'):
                name = p.name[len('session-'):]
                if name and name not in candidates:
                    candidates.append(name)
        except Exception:
            pass
        for name in candidates:
            if self._load_session_file(name):
                return True
        return False

    def login(self, username=None, password=None):
        """Login to Instagram account"""
        loading = None
        try:
            # Try to load saved credentials first
            saved_login = LoginManager.load_login_data()

            if saved_login and not username:
                username = saved_login['username']
                password = saved_login['password']
                HackerStyle.print_info("Using saved login credentials")

            # Reuse session file so we don't trigger a fresh login challenge
            if username and not password:
                if self.try_saved_session(username):
                    HackerStyle.print_success(f"Resumed saved session as @{self.login_user}")
                    return True
                HackerStyle.print_error("Username and password required for login")
                return False

            if not username or not password:
                HackerStyle.print_error("Username and password required for login")
                return False

            # Session reuse before password login
            if self._load_session_file(username):
                HackerStyle.print_success(f"Resumed saved session as @{username}")
                return True

            loading = LoadingAnimation("Authenticating with Instagram")
            loading.start()

            try:
                self.cl.login(username, password)
            except ig_exc.TwoFactorRequired:
                loading.stop()
                loading = None
                HackerStyle.print_info("Two-factor authentication required")
                code = input(f"{Colors.YELLOW}Enter 2FA code: {Colors.RESET}").strip()
                loading = LoadingAnimation("Verifying 2FA code")
                loading.start()
                self.cl.login(username, password, verification_code=code)
            loading.stop()
            loading = None

            try:
                self.cl.dump_settings(str(LoginManager.get_session_path(username)))
            except Exception:
                pass
            self.is_logged_in = True
            self.login_user = username
            HackerStyle.print_success(f"Successfully logged in as @{username}")
            return True

        except (ig_exc.BadPassword, ig_exc.BadCredentials):
            if loading:
                loading.stop()
            HackerStyle.print_error("Invalid credentials - login failed")
            return False
        except ig_exc.ChallengeRequired:
            if loading:
                loading.stop()
            HackerStyle.print_error("Challenge required - approve the login in your Instagram app, then retry")
            return False
        except RATE_LIMIT_ERRORS as e:
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Rate-limited during login: {e} - wait a few minutes and retry")
            return False
        except Exception as e:
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Login failed: {e}")
            return False

    @staticmethod
    def _user_to_info(user):
        pic = getattr(user, 'profile_pic_url_hd', None) or user.profile_pic_url
        return {
            'username': user.username,
            'full_name': user.full_name or '',
            'biography': user.biography or '',
            'external_url': user.external_url or '',
            'posts': user.media_count or 0,
            'followers': user.follower_count or 0,
            'following': user.following_count or 0,
            'userid': str(user.pk),
            'is_private': bool(user.is_private),
            'is_verified': bool(user.is_verified),
            'profile_pic_url': str(pic),
            'fetched_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _load_cached_profile(self, username):
        """Return cached basic info if a previous successful fetch exists."""
        cache_path = LoginManager.get_profile_cache_path(username)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path) as f:
                data = json.load(f)
            data['cached'] = True
            return data
        except Exception:
            return None

    def _resolve_user(self, username):
        """Fetch a user or print exactly why not. None on failure."""
        try:
            return self.cl.user_info_by_username(username)
        except (ig_exc.UserNotFound, ig_exc.ClientNotFoundError):
            HackerStyle.print_error(f"Target not found: @{username}")
        except RATE_LIMIT_ERRORS as e:
            HackerStyle.print_error(f"Rate-limited: {e} - wait, then retry")
        except LOGIN_ERRORS:
            HackerStyle.print_error("Login required - run with --login first")
        except Exception as e:
            HackerStyle.print_error(f"Lookup failed: {e}")
        return None

    def get_profile_info(self, username):
        loading = None
        try:
            loading = LoadingAnimation(f"Scanning target @{username}")
            loading.start()

            user = self.cl.user_info_by_username(username)
            loading.stop()
            loading = None

            profile_info = self._user_to_info(user)

            HackerStyle.print_success(f"Target acquired: @{username}")
            HackerStyle.print_system("Profile data extracted successfully")

            try:
                with open(LoginManager.get_profile_cache_path(username), 'w') as f:
                    json.dump(profile_info, f)
            except Exception:
                pass

            return profile_info

        except (ig_exc.UserNotFound, ig_exc.ClientNotFoundError):
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Target not found: @{username}")
            return None
        except RATE_LIMIT_ERRORS as e:
            if loading:
                loading.stop()
            cached = self._load_cached_profile(username)
            if cached:
                HackerStyle.print_warning(f"Live fetch rate-limited, showing cached info for @{username}")
                return cached
            HackerStyle.print_error(f"Rate-limited by Instagram: {e}")
            HackerStyle.print_info("Wait a few minutes, then retry (session is reused).")
            return None
        except LOGIN_ERRORS:
            if loading:
                loading.stop()
            cached = self._load_cached_profile(username)
            if cached:
                HackerStyle.print_warning(f"Login required, showing cached info for @{username}")
                return cached
            HackerStyle.print_error("Instagram requires login for this request - run with --login first")
            return None
        except Exception as e:
            if loading:
                loading.stop()
            cached = self._load_cached_profile(username)
            if cached:
                HackerStyle.print_warning(f"Live fetch failed, showing cached info for @{username}")
                return cached
            HackerStyle.print_error(f"Scanning failed: {str(e)}")
            return None

    def get_private_profile_info(self, username):
        """Get profile information for private accounts (requires login)"""
        if not self.is_logged_in:
            HackerStyle.print_error("Login required to access private accounts")
            return None

        try:
            user = self._resolve_user(username)
            if not user:
                return None

            if user.is_private:
                # One probe post: PrivateError means we don't follow them
                try:
                    self.cl.user_medias(str(user.pk), 1)
                except ig_exc.PrivateError:
                    HackerStyle.print_error(f"You don't follow private account @{username}")
                    return None

            profile_info = self.get_profile_info(username)
            if profile_info:
                HackerStyle.print_success(f"Private account data extracted: @{username}")

            return profile_info

        except Exception as e:
            HackerStyle.print_error(f"Failed to access private account: {e}")
            return None

    def _download_media(self, media, folder):
        """Download one media by type. Returns True on success."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if media.media_type == 8:
                self.cl.album_download(media.pk, folder)
            elif media.media_type == 2:
                if getattr(media, 'product_type', '') == 'clips':
                    self.cl.clip_download(media.pk, folder)
                else:
                    self.cl.video_download(media.pk, folder)
            else:
                self.cl.photo_download(media.pk, folder)
            return True
        except Exception as e:
            HackerStyle.print_warning(f"Skipped one item: {e}")
            return False

    def download_profile_pic(self, username, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return None
        try:
            HackerStyle.print_info("Extracting profile picture...")
            pic_url = str(getattr(user, 'profile_pic_url_hd', None) or user.profile_pic_url)

            Path(output_dir).mkdir(parents=True, exist_ok=True)

            response = requests.get(pic_url, timeout=30)
            response.raise_for_status()
            filename = f"{output_dir}/{username}_profile_pic.jpg"

            with open(filename, 'wb') as f:
                f.write(response.content)

            HackerStyle.print_success(f"Profile picture extracted: {filename}")
            return filename
        except Exception as e:
            HackerStyle.print_error(f"Extraction failed: {e}")
            return None

    def download_posts(self, username, count=10, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        try:
            if user.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False

            HackerStyle.print_info(f"Downloading {count} posts...")

            target = Path(output_dir) / username / "posts"
            done = sum(
                self._download_media(m, target)
                for m in self.cl.user_medias(str(user.pk), count)
            )

            HackerStyle.print_success(f"Downloaded {done} posts")
            return True
        except ig_exc.PrivateError:
            HackerStyle.print_error("Private account - you don't follow it or login is required")
            return False
        except RATE_LIMIT_ERRORS as e:
            HackerStyle.print_error(f"Rate-limited: {e} - wait, then retry with --login")
            return False
        except LOGIN_ERRORS:
            HackerStyle.print_error("Login required - run with --login first")
            return False
        except Exception as e:
            HackerStyle.print_error(f"Download failed: {e}")
            return False

    def download_reels(self, username, count=5, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        try:
            if user.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False

            HackerStyle.print_info(f"Downloading {count} reels...")

            target = Path(output_dir) / username / "reels"
            done = sum(
                self._download_media(m, target)
                for m in self.cl.user_clips(str(user.pk), count)
            )

            HackerStyle.print_success(f"Downloaded {done} reels")
            return True
        except ig_exc.PrivateError:
            HackerStyle.print_error("Private account - you don't follow it or login is required")
            return False
        except RATE_LIMIT_ERRORS as e:
            HackerStyle.print_error(f"Rate-limited: {e} - wait, then retry with --login")
            return False
        except LOGIN_ERRORS:
            HackerStyle.print_error("Login required - run with --login first")
            return False
        except Exception as e:
            HackerStyle.print_error(f"Download failed: {e}")
            return False

    def download_stories(self, username, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        try:
            if user.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False

            HackerStyle.print_info("Downloading stories...")

            target = Path(output_dir) / username / "stories"
            target.mkdir(parents=True, exist_ok=True)

            stories = self.cl.user_stories(str(user.pk))
            done = 0
            for s in stories:
                try:
                    self.cl.story_download(s.pk, folder=target)
                    done += 1
                except Exception as e:
                    HackerStyle.print_warning(f"Skipped one story: {e}")

            HackerStyle.print_success(f"Downloaded {done} stories")
            return True
        except ig_exc.PrivateError:
            HackerStyle.print_error("Private account - you don't follow it or login is required")
            return False
        except RATE_LIMIT_ERRORS as e:
            HackerStyle.print_error(f"Rate-limited: {e} - wait, then retry with --login")
            return False
        except LOGIN_ERRORS:
            HackerStyle.print_error("Login required - run with --login first")
            return False
        except Exception as e:
            HackerStyle.print_warning(f"Stories download failed: {e}")
            return False

    def download_from_url(self, url, output_dir="downloads"):
        """Download specific post or reel from URL"""
        loading = None
        try:
            # Fast offline check before any network call
            if not self.extract_shortcode_from_url(url):
                HackerStyle.print_error("Invalid Instagram URL")
                return False

            loading = LoadingAnimation("Fetching post from URL")
            loading.start()

            media_pk = self.cl.media_pk_from_url(url)
            media = self.cl.media_info(media_pk)
            loading.stop()
            loading = None

            HackerStyle.print_info(f"Downloading: {media.code if media.code else 'Instagram Post'}")

            self._download_media(media, Path(output_dir))

            HackerStyle.print_success(f"Downloaded post to {output_dir}")
            return True

        except ig_exc.PrivateError:
            if loading:
                loading.stop()
            HackerStyle.print_error("Private account - you need to follow this account or login")
            return False
        except RATE_LIMIT_ERRORS as e:
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Rate-limited: {e} - wait, then retry with --login")
            return False
        except LOGIN_ERRORS:
            if loading:
                loading.stop()
            HackerStyle.print_error("Login required for this URL - run with --login first")
            return False
        except Exception as e:
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Download from URL failed: {e}")
            return False

    def extract_shortcode_from_url(self, url):
        """Extract Instagram shortcode from various URL formats"""
        patterns = [
            r'(?<!\w)instagram\.com/p/([^/?#&]+)',
            r'(?<!\w)instagram\.com/reels?/([^/?#&]+)',
            r'(?<!\w)instagram\.com/stories/[^/]+/([^/?#&]+)',
            r'(?<!\w)instagram\.com/tv/([^/?#&]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def print_profile_info(self, profile_info):
        if not profile_info:
            return

        if profile_info.get('cached'):
            HackerStyle.print_warning(f"Cached data (live fetch blocked) - from {profile_info.get('fetched_at', '?')}")

        print(f"\n{Colors.PURPLE}{'═'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🛰️  TARGET PROFILE INTELLIGENCE REPORT{Colors.RESET}")
        print(f"{Colors.PURPLE}{'═'*60}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}📱 BASIC INTEL:{Colors.RESET}")
        HackerStyle.print_data(f"Username: {Colors.WHITE}{profile_info['username']}{Colors.RESET}")
        HackerStyle.print_data(f"Full Name: {Colors.WHITE}{profile_info['full_name']}{Colors.RESET}")
        HackerStyle.print_data(f"User ID: {Colors.WHITE}{profile_info['userid']}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}📝 PROFILE DATA:{Colors.RESET}")
        HackerStyle.print_data(f"Bio: {Colors.WHITE}{profile_info['biography']}{Colors.RESET}")
        HackerStyle.print_data(f"Website: {Colors.WHITE}{profile_info['external_url']}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}📊 STATISTICS:{Colors.RESET}")
        HackerStyle.print_data(f"Posts: {Colors.WHITE}{profile_info['posts']:,}{Colors.RESET}")
        HackerStyle.print_data(f"Followers: {Colors.WHITE}{profile_info['followers']:,}{Colors.RESET}")
        HackerStyle.print_data(f"Following: {Colors.WHITE}{profile_info['following']:,}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}🔒 ACCOUNT STATUS:{Colors.RESET}")
        HackerStyle.print_data(f"Private: {Colors.RED if profile_info['is_private'] else Colors.GREEN}{'Yes' if profile_info['is_private'] else 'No'}{Colors.RESET}")
        HackerStyle.print_data(f"Verified: {Colors.GREEN if profile_info['is_verified'] else Colors.YELLOW}{'Yes' if profile_info['is_verified'] else 'No'}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}⏰ DATA ACQUIRED:{Colors.RESET}")
        HackerStyle.print_data(f"Scan Time: {Colors.WHITE}{profile_info['fetched_at']}{Colors.RESET}")

        print(f"{Colors.PURPLE}{'═'*60}{Colors.RESET}")

    def interactive_menu(self, profile_info):
        if not profile_info:
            return

        print(f"\n{Colors.CYAN}{'═'*50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}🖥️  INSTAGHOST INTERACTIVE TERMINAL{Colors.RESET}")
        print(f"{Colors.CYAN}{'═'*50}{Colors.RESET}")

        while True:
            print(f"\n{Colors.WHITE}🎯 Target: {Colors.GREEN}@{profile_info['username']}{Colors.RESET}")
            print(f"{Colors.WHITE}💻 Available Operations:{Colors.RESET}")
            print(f"  {Colors.CYAN}1{Colors.RESET} - 📸 Download Profile Picture")
            print(f"  {Colors.CYAN}2{Colors.RESET} - 📷 Download Posts")
            print(f"  {Colors.CYAN}3{Colors.RESET} - 🎬 Download Reels")
            print(f"  {Colors.CYAN}4{Colors.RESET} - 📖 Download Stories")
            print(f"  {Colors.CYAN}5{Colors.RESET} - 🚀 Download Everything")
            print(f"  {Colors.CYAN}6{Colors.RESET} - 📊 Show Profile Intel")
            print(f"  {Colors.CYAN}7{Colors.RESET} - 🔗 Download from URL")
            print(f"  {Colors.CYAN}8{Colors.RESET} - 🔐 Login Operations")
            print(f"  {Colors.CYAN}0{Colors.RESET} - ⛔ Exit Terminal")

            choice = input(f"\n{Colors.YELLOW}🛠️  Select operation: {Colors.RESET}").strip()

            if choice == '1':
                self.download_profile_pic(profile_info['username'])
            elif choice == '2':
                count = input(f"{Colors.YELLOW}📦 Number of posts: {Colors.RESET}").strip()
                count = int(count) if count.isdigit() else 10
                self.download_posts(profile_info['username'], count)
            elif choice == '3':
                count = input(f"{Colors.YELLOW}🎥 Number of reels: {Colors.RESET}").strip()
                count = int(count) if count.isdigit() else 5
                self.download_reels(profile_info['username'], count)
            elif choice == '4':
                self.download_stories(profile_info['username'])
            elif choice == '5':
                self.download_profile_pic(profile_info['username'])
                self.download_posts(profile_info['username'], 10)
                self.download_reels(profile_info['username'], 5)
                self.download_stories(profile_info['username'])
            elif choice == '6':
                self.print_profile_info(profile_info)
            elif choice == '7':
                url = input(f"{Colors.YELLOW}🔗 Enter Instagram URL: {Colors.RESET}").strip()
                if url:
                    self.download_from_url(url)
            elif choice == '8':
                self.login_menu()
            elif choice == '0':
                HackerStyle.print_success("Terminal session terminated. Stay stealthy! 🏴‍☠️")
                break
            else:
                HackerStyle.print_error("Invalid command. Try again.")

    def login_menu(self):
        """Interactive login menu"""
        print(f"\n{Colors.CYAN}{'═'*30}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}🔐 LOGIN OPERATIONS{Colors.RESET}")
        print(f"{Colors.CYAN}{'═'*30}{Colors.RESET}")

        print(f"  {Colors.CYAN}1{Colors.RESET} - Login with credentials")
        print(f"  {Colors.CYAN}2{Colors.RESET} - Login with saved data")
        print(f"  {Colors.CYAN}3{Colors.RESET} - Save current login")
        print(f"  {Colors.CYAN}4{Colors.RESET} - Clear saved login")
        print(f"  {Colors.CYAN}5{Colors.RESET} - Check login status")

        choice = input(f"\n{Colors.YELLOW}Select option: {Colors.RESET}").strip()

        if choice == '1':
            username = input(f"{Colors.YELLOW}Username: {Colors.RESET}").strip()
            password = input(f"{Colors.YELLOW}Password: {Colors.RESET}").strip()
            if username and password:
                self.login(username, password)
        elif choice == '2':
            self.login()  # Use saved credentials
        elif choice == '3':
            if self.is_logged_in:
                username = input(f"{Colors.YELLOW}Username to save: {Colors.RESET}").strip()
                password = input(f"{Colors.YELLOW}Password to save: {Colors.RESET}").strip()
                if username and password:
                    LoginManager.save_login_data(username, password)
            else:
                HackerStyle.print_error("Not logged in")
        elif choice == '4':
            LoginManager.clear_login_data()
        elif choice == '5':
            status = "Logged in" if self.is_logged_in else "Not logged in"
            color = Colors.GREEN if self.is_logged_in else Colors.RED
            HackerStyle.print_info(f"Login status: {color}{status}{Colors.RESET}")

def main():
    HackerStyle.banner()

    parser = argparse.ArgumentParser(description='InstaGhost - Advanced Instagram OSINT Tool', add_help=False)
    parser.add_argument('username', nargs='?', help='Instagram username')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive terminal mode')
    parser.add_argument('-p', '--profile-pic', action='store_true', help='Download profile picture')
    parser.add_argument('-P', '--posts', type=int, help='Download posts (specify count)')
    parser.add_argument('-r', '--reels', type=int, help='Download reels (specify count)')
    parser.add_argument('-s', '--stories', action='store_true', help='Download stories')
    parser.add_argument('-a', '--all', action='store_true', help='Download all data')
    parser.add_argument('-o', '--output', help='Output directory (default: downloads)')
    parser.add_argument('-l', '--login', action='store_true', help='Login to Instagram')
    parser.add_argument('--login-user', help='Instagram username for login')
    parser.add_argument('--login-pass', help='Instagram password for login')
    parser.add_argument('--save-login', action='store_true', help='Save login credentials')
    parser.add_argument('--url', help='Download specific post/reel from URL')
    parser.add_argument('--private', action='store_true', help='Access private account data (requires login)')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    parser.add_argument('-V', '--version', action='store_true', help='Show version and exit')

    args = parser.parse_args()

    if args.version:
        try:
            from instaghost import __version__ as _ver
        except Exception:
            _ver = "2.0.0"
        print(f"InstaGhost v{_ver}")
        sys.exit(0)

    if args.help or (not args.username and not args.url and not args.login):
        print(f"{Colors.BOLD}{Colors.CYAN}🛠️  INSTAGHOST COMMAND REFERENCE{Colors.RESET}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.RESET}")
        print(f"\n{Colors.GREEN}Usage:{Colors.RESET}")
        print(f"  instaghost {Colors.YELLOW}<username>{Colors.RESET} {Colors.CYAN}[options]{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}--url <instagram_url>{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}--login{Colors.RESET}")
        print(f"\n{Colors.GREEN}Options:{Colors.RESET}")
        print(f"  {Colors.YELLOW}-i, --interactive{Colors.RESET}  🖥️  Launch interactive terminal")
        print(f"  {Colors.YELLOW}-p, --profile-pic{Colors.RESET}  📸 Extract profile picture")
        print(f"  {Colors.YELLOW}-P, --posts{Colors.RESET}       📷 Download posts (specify count)")
        print(f"  {Colors.YELLOW}-r, --reels{Colors.RESET}       🎬 Download reels (specify count)")
        print(f"  {Colors.YELLOW}-s, --stories{Colors.RESET}     📖 Download stories")
        print(f"  {Colors.YELLOW}-a, --all{Colors.RESET}         🚀 Download all intelligence")
        print(f"  {Colors.YELLOW}-o, --output{Colors.RESET}      💾 Output directory")
        print(f"  {Colors.YELLOW}-l, --login{Colors.RESET}       🔐 Login to Instagram")
        print(f"  {Colors.YELLOW}--login-user{Colors.RESET}      👤 Login username")
        print(f"  {Colors.YELLOW}--login-pass{Colors.RESET}      🔑 Login password")
        print(f"  {Colors.YELLOW}--save-login{Colors.RESET}      💾 Save login credentials")
        print(f"  {Colors.YELLOW}--url{Colors.RESET}             🔗 Download from specific URL")
        print(f"  {Colors.YELLOW}--private{Colors.RESET}         🕵️  Access private accounts")
        print(f"  {Colors.YELLOW}-h, --help{Colors.RESET}        📖 Show this help")
        print(f"  {Colors.YELLOW}-V, --version{Colors.RESET}     🔖 Show version and exit")
        print(f"\n{Colors.GREEN}Examples:{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}username -i{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}target -p -P 5{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}user -a{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}--url https://instagram.com/p/ABC123/{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}--login --login-user myuser --login-pass mypass{Colors.RESET}")
        print(f"  instaghost {Colors.CYAN}private_user --private -l{Colors.RESET}")
        sys.exit(0)

    tool = InstaGhost()
    output_dir = args.output or "downloads"

    # Handle login operations
    if args.login or args.login_user:
        if tool.login(args.login_user, args.login_pass):
            if args.save_login and args.login_user and args.login_pass:
                LoginManager.save_login_data(args.login_user, args.login_pass)
        else:
            sys.exit(1)

    # Attach any saved session so even public lookups benefit from login
    if not tool.is_logged_in:
        tool.try_saved_session(args.login_user)

    if tool.is_logged_in:
        HackerStyle.print_info(f"Logged in as @{tool.login_user}")
    else:
        HackerStyle.print_warning("Not logged in - anonymous mode (expect rate limits)")

    # Handle URL download
    if args.url:
        ok = tool.download_from_url(args.url, output_dir)
        sys.exit(0 if ok else 1)

    # Handle profile operations
    if args.username:
        if args.private:
            if not tool.is_logged_in:
                # Same-invocation `-l` or a previous saved session both work
                if args.login:
                    tool.login(args.login_user, args.login_pass)
                if not tool.is_logged_in:
                    tool.try_saved_session()
                if not tool.is_logged_in:
                    HackerStyle.print_error("Login required for private account access")
                    sys.exit(1)
            profile_info = tool.get_private_profile_info(args.username)
        else:
            profile_info = tool.get_profile_info(args.username)

        if not profile_info:
            sys.exit(1)

        # Basic info always shows, even if downloads below fail
        tool.print_profile_info(profile_info)

        if args.interactive:
            tool.interactive_menu(profile_info)
            return

        failed = False

        if args.profile_pic or args.all:
            if not tool.download_profile_pic(args.username, output_dir):
                failed = True

        if args.posts or args.all:
            count = args.posts or 10
            if not tool.download_posts(args.username, count, output_dir):
                failed = True

        if args.reels or args.all:
            count = args.reels or 5
            if not tool.download_reels(args.username, count, output_dir):
                failed = True

        if args.stories or args.all:
            if not tool.download_stories(args.username, output_dir):
                failed = True

        if failed:
            HackerStyle.print_error("Completed with errors - see messages above 🏴‍☠️")
            sys.exit(1)

    HackerStyle.print_success("Mission accomplished! 🏴‍☠️")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}")
        sys.exit(130)
