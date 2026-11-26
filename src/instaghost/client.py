"""Instagram client: session reuse, profile lookups, and media downloads."""

import getpass
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from instagrapi import Client
from instagrapi import exceptions as ig_exc

from . import config
from .auth import LoginManager
from .cache import load_profile, save_profile
from .errors import LOGIN_ERRORS, RATE_LIMIT_ERRORS
from .output import Colors, HackerStyle, LoadingAnimation

MAX_COUNT = 30


def _clamp_count(value, default):
    try:
        return max(1, min(int(value), MAX_COUNT))
    except (TypeError, ValueError):
        return default


class InstaGhost:
    def __init__(self):
        self.cl = Client()
        self.is_logged_in = False
        self.login_user = None
        self._user_cache = {}

    def _load_session_file(self, username):
        """Attach a saved instagrapi session. No network call (lazy trust)."""
        if not config.valid_username(username):
            return False
        session_file = LoginManager.get_session_path(username)
        if not session_file.exists():
            return False
        try:
            self.cl.load_settings(str(session_file))
        except Exception:
            return False
        try:
            os.chmod(session_file, 0o600)
        except OSError:
            pass
        self.is_logged_in = True
        self.login_user = username
        return True

    def try_saved_session(self, username=None, verify=False):
        """Resume one saved session without guessing between accounts."""
        if username:
            candidates = [username]
        else:
            saved_login = LoginManager.load_login_data()
            if saved_login:
                candidates = [saved_login['username']]
            else:
                try:
                    candidates = sorted(
                        path.name[len('session-'):]
                        for path in config.CONFIG_DIR.glob('session-*')
                        if path.is_file()
                        and config.valid_username(path.name[len('session-'):])
                    )
                except OSError:
                    candidates = []
                if len(candidates) > 1:
                    HackerStyle.print_error(
                        "Multiple saved sessions found - use --login-user to choose one"
                    )
                    return False
        for name in candidates:
            if self._load_session_file(name):
                if verify and not self._verify_session(name):
                    return False
                return True
        return False

    def _verify_session(self, username=None):
        try:
            info = self.cl.account_info()
        except LOGIN_ERRORS:
            self.is_logged_in = False
            self.login_user = None
            HackerStyle.print_warning("Saved session is no longer valid - logging in again")
            return False
        except Exception as e:
            HackerStyle.print_warning(f"Could not verify saved session: {e}")
            return True
        if username and str(getattr(info, "username", "")).lower() != username.lower():
            self.is_logged_in = False
            self.login_user = None
            HackerStyle.print_warning("Saved session belongs to a different account")
            return False
        return True

    def _resume_session(self, username):
        """Load a session for one account and verify it is still accepted."""
        return self.try_saved_session(username, verify=True)

    def login(self, username=None, password=None, save=False):
        """Login to Instagram account"""
        loading = None
        try:
            # Try to load saved credentials first
            saved_login = LoginManager.load_login_data()

            if saved_login and not username:
                username = saved_login['username']
                password = saved_login['password']
                HackerStyle.print_info("Using saved login credentials")

            if username and not config.valid_username(username):
                HackerStyle.print_error("Invalid Instagram username")
                return False

            # Reuse a verified session for this account so we don't trigger a fresh login
            session_checked = False
            if username and not password:
                session_checked = True
                if self._resume_session(username):
                    HackerStyle.print_success(f"Resumed saved session as @{self.login_user}")
                    return True
                if (saved_login
                        and saved_login['username'].lower() == username.lower()):
                    password = saved_login['password']
                    HackerStyle.print_info("Using saved login credentials")
                elif sys.stdin and sys.stdin.isatty():
                    try:
                        password = getpass.getpass(
                            f"{Colors.YELLOW}Instagram password: {Colors.RESET}"
                        )
                    except EOFError:
                        password = None
                if not password:
                    HackerStyle.print_error("Saved session missing or expired - password required")
                    return False

            if not username or not password:
                HackerStyle.print_error("Username and password required for login")
                return False

            # Session reuse before password login
            if not session_checked and self._resume_session(username):
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

            session_path = LoginManager.get_session_path(username)
            try:
                self.cl.dump_settings(str(session_path))
                os.chmod(session_path, 0o600)
            except Exception as e:
                HackerStyle.print_warning(f"Could not save session file: {e}")
            self.is_logged_in = True
            self.login_user = username
            if save:
                LoginManager.save_login_data(username, password)
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

    def _resolve_user(self, username):
        """Fetch a user or print exactly why not. None on failure."""
        if not config.valid_username(username):
            HackerStyle.print_error("Invalid Instagram username")
            return None
        if username in self._user_cache:
            return self._user_cache[username]
        try:
            user = self.cl.user_info_by_username(username)
            self._user_cache[username] = user
            return user
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
        if not config.valid_username(username):
            HackerStyle.print_error("Invalid Instagram username")
            return None
        loading = None
        try:
            loading = LoadingAnimation(f"Scanning target @{username}")
            loading.start()

            user = self._user_cache.get(username)
            if user is None:
                user = self.cl.user_info_by_username(username)
                self._user_cache[username] = user
            loading.stop()
            loading = None

            profile_info = self._user_to_info(user)

            HackerStyle.print_success(f"Target acquired: @{username}")
            HackerStyle.print_system("Profile data extracted successfully")
            save_profile(username, profile_info)
            return profile_info

        except (ig_exc.UserNotFound, ig_exc.ClientNotFoundError):
            if loading:
                loading.stop()
            HackerStyle.print_error(f"Target not found: @{username}")
            return None
        except RATE_LIMIT_ERRORS as e:
            if loading:
                loading.stop()
            cached = load_profile(username)
            if cached:
                HackerStyle.print_warning(f"Live fetch rate-limited, showing cached info for @{username}")
                return cached
            HackerStyle.print_error(f"Rate-limited by Instagram: {e}")
            HackerStyle.print_info("Wait a few minutes, then retry (session is reused).")
            return None
        except LOGIN_ERRORS:
            if loading:
                loading.stop()
            cached = load_profile(username)
            if cached:
                HackerStyle.print_warning(f"Login required, showing cached info for @{username}")
                return cached
            HackerStyle.print_error("Instagram requires login for this request - run with --login first")
            return None
        except Exception as e:
            if loading:
                loading.stop()
            cached = load_profile(username)
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
        """Download one media from URLs already fetched. Returns True on success."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            username = getattr(getattr(media, "user", None), "username", "media")
            if media.media_type == 8:
                resources = list(getattr(media, "resources", None) or [])
                if not resources:
                    raise ValueError("Album has no resources")
                for resource in resources:
                    url = resource.thumbnail_url if resource.media_type == 1 else resource.video_url
                    if not url:
                        raise ValueError("Media URL is empty")
                    name = f"{username}_{resource.pk}"
                    if resource.media_type == 1:
                        self.cl.photo_download_by_url(str(url), name, folder)
                    elif resource.media_type == 2:
                        self.cl.video_download_by_url(str(url), name, folder)
                    else:
                        raise ValueError("Unsupported album item")
            elif media.media_type == 2:
                url = media.video_url
                if not url:
                    raise ValueError("Video URL is empty")
                name = f"{username}_{media.pk}"
                if getattr(media, 'product_type', '') == 'clips':
                    self.cl.clip_download_by_url(str(url), name, folder)
                else:
                    self.cl.video_download_by_url(str(url), name, folder)
            else:
                url = media.thumbnail_url
                if not url:
                    raise ValueError("Photo URL is empty")
                self.cl.photo_download_by_url(str(url), f"{username}_{media.pk}", folder)
            return True
        except Exception as e:
            HackerStyle.print_warning(f"Skipped one item: {e}")
            return False

    def download_profile_pic(self, username, output_dir="downloads"):
        if not config.valid_username(username):
            HackerStyle.print_error("Invalid Instagram username")
            return None
        user = self._resolve_user(username)
        if not user:
            return None
        try:
            HackerStyle.print_info("Extracting profile picture...")
            pic_url = getattr(user, 'profile_pic_url_hd', None) or user.profile_pic_url
            if not pic_url:
                raise ValueError("Profile picture URL is empty")

            target = Path(output_dir)
            target.mkdir(parents=True, exist_ok=True)
            filename = self.cl.photo_download_by_url(
                str(pic_url), f"{username}_profile_pic", target
            )

            HackerStyle.print_success(f"Profile picture extracted: {filename}")
            return str(filename)
        except Exception as e:
            HackerStyle.print_error(f"Extraction failed: {e}")
            return None

    def _download_collection(self, username, kind, fetch, output_dir, label):
        """Download a list of media. Returns False when nothing was downloaded."""
        try:
            items = list(fetch())
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

        target = Path(output_dir) / username / kind
        done = 0
        for item in items:
            if kind == "stories":
                try:
                    url = item.thumbnail_url if item.media_type == 1 else item.video_url
                    if not url:
                        raise ValueError("Story URL is empty")
                    target.mkdir(parents=True, exist_ok=True)
                    self.cl.story_download_by_url(
                        str(url), f"{username}_{item.pk}", target
                    )
                    done += 1
                except Exception as e:
                    HackerStyle.print_warning(f"Skipped one story: {e}")
            elif self._download_media(item, target):
                done += 1

        HackerStyle.print_success(f"Downloaded {done} {label}")
        if done == 0 and items:
            HackerStyle.print_error(f"Nothing downloaded - {len(items)} {label} failed")
            return False
        return done > 0 or not items

    def download_posts(self, username, count=10, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        if user.is_private and not self.is_logged_in:
            HackerStyle.print_error("Private account - login required")
            return False
        count = _clamp_count(count, 10)
        HackerStyle.print_info(f"Downloading up to {count} posts...")
        return self._download_collection(
            username, "posts",
            lambda: self.cl.user_medias(str(user.pk), count),
            output_dir, "posts",
        )

    def download_reels(self, username, count=5, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        if user.is_private and not self.is_logged_in:
            HackerStyle.print_error("Private account - login required")
            return False
        count = _clamp_count(count, 5)
        HackerStyle.print_info(f"Downloading up to {count} reels...")
        return self._download_collection(
            username, "reels",
            lambda: self.cl.user_clips(str(user.pk), count),
            output_dir, "reels",
        )

    def download_stories(self, username, output_dir="downloads"):
        user = self._resolve_user(username)
        if not user:
            return False
        if user.is_private and not self.is_logged_in:
            HackerStyle.print_error("Private account - login required")
            return False
        HackerStyle.print_info("Downloading stories...")
        return self._download_collection(
            username, "stories",
            lambda: self.cl.user_stories(str(user.pk)),
            output_dir, "stories",
        )

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

            if not self._download_media(media, Path(output_dir)):
                HackerStyle.print_error("Download failed - media URL was not available")
                return False

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
        """Extract an Instagram post/reel/tv shortcode (stories are unsupported)."""
        match = re.search(r'(?<!\w)instagram\.com/(?:p|reels?|tv|share/p)/([^/?#&]+)', url)
        return match.group(1) if match else None

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

    def interactive_menu(self, profile_info, output_dir="downloads"):
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
                self.download_profile_pic(profile_info['username'], output_dir)
            elif choice == '2':
                count = input(f"{Colors.YELLOW}📦 Number of posts (1-{MAX_COUNT}): {Colors.RESET}").strip()
                self.download_posts(profile_info['username'], count or 10, output_dir)
            elif choice == '3':
                count = input(f"{Colors.YELLOW}🎥 Number of reels (1-{MAX_COUNT}): {Colors.RESET}").strip()
                self.download_reels(profile_info['username'], count or 5, output_dir)
            elif choice == '4':
                self.download_stories(profile_info['username'], output_dir)
            elif choice == '5':
                self.download_profile_pic(profile_info['username'], output_dir)
                self.download_posts(profile_info['username'], 10, output_dir)
                self.download_reels(profile_info['username'], 5, output_dir)
                self.download_stories(profile_info['username'], output_dir)
            elif choice == '6':
                self.print_profile_info(profile_info)
            elif choice == '7':
                url = input(f"{Colors.YELLOW}🔗 Enter Instagram URL: {Colors.RESET}").strip()
                if url:
                    self.download_from_url(url, output_dir)
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
        print(f"  {Colors.CYAN}3{Colors.RESET} - Clear saved login")
        print(f"  {Colors.CYAN}4{Colors.RESET} - Check login status")

        choice = input(f"\n{Colors.YELLOW}Select option: {Colors.RESET}").strip()

        if choice == '1':
            username = input(f"{Colors.YELLOW}Username: {Colors.RESET}").strip()
            password = getpass.getpass(f"{Colors.YELLOW}Password: {Colors.RESET}")
            if username and password:
                self.login(username, password)
        elif choice == '2':
            self.login()  # Use saved credentials
        elif choice == '3':
            LoginManager.clear_login_data()
        elif choice == '4':
            status = "Logged in" if self.is_logged_in else "Not logged in"
            color = Colors.GREEN if self.is_logged_in else Colors.RED
            HackerStyle.print_info(f"Login status: {color}{status}{Colors.RESET}")
