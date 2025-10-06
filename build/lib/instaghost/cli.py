#!/usr/bin/env python3

import instaloader
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
from urllib.parse import urlparse

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
        os.system("clear")
        banner = f"""
{Colors.CYAN}
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣾⣿⣿⣿⣿⣿⣿⣶⣄⠀⠀⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⠿⢿⣿⣿⣿⣿⣆⠀⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⠁⠀⠿⢿⣿⡿⣿⣿⡆⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣦⣤⣴⣿⠃⠀⠿⣿⡇⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⡿⠋⠁⣿⠟⣿⣿⢿⣧⣤⣴⣿⡇⠀
{' '*10}⠀⠀⠀⠀⢀⣠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠘⠁⢸⠟⢻⣿⡿⠀⠀
{' '*10}⠀⠀⠙⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣴⣇⢀⣤⠀⠀⠀⠀⠘⣿⠃⠀⠀
{' '*10}⠀⠀⠀⠀⠀⢈⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣴⣿⢀⣴⣾⠇⠀⠀⠀
{' '*10}⠀⠀⣀⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀
{' '*10}⠀⠀⠉⠉⠉⠉⣡⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⠀
{' '*10}⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⡿⠟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀
{' '*10}⠀⠀⣴⡾⠿⠿⠿⠛⠋⠉⠀⢸⣿⣿⣿⣿⠿⠋⢸⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⡿⠟⠋⠁⠀⠀⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
{' '*10}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠈⠀⠀
{Colors.RESET}

{Colors.BLUE}{Colors.BOLD}       InstaGhost - Instagram OSINT Tool{Colors.RESET}
{Colors.GREEN}                Author: Anon4You{Colors.RESET}
{Colors.YELLOW}       GitHub: github.com/Anon4You/InstaGhost{Colors.RESET}

{Colors.WHITE} Simple and professional Instagram data gathering{Colors.RESET}
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
        self.loader = instaloader.Instaloader()
        self.loader.save_metadata = False
        self.loader.download_video_thumbnails = False
        self.loader.compress_json = False
        self.is_logged_in = False
    
    def login(self, username=None, password=None):
        """Login to Instagram account"""
        try:
            # Try to load saved credentials first
            saved_login = LoginManager.load_login_data()
            
            if saved_login and not username:
                username = saved_login['username']
                password = saved_login['password']
                HackerStyle.print_info("Using saved login credentials")
            
            if not username or not password:
                HackerStyle.print_error("Username and password required for login")
                return False
            
            loading = LoadingAnimation("Authenticating with Instagram")
            loading.start()
            
            self.loader.login(username, password)
            loading.stop()
            
            self.is_logged_in = True
            HackerStyle.print_success(f"Successfully logged in as @{username}")
            return True
            
        except instaloader.exceptions.BadCredentialsException:
            loading.stop()
            HackerStyle.print_error("Invalid credentials - login failed")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            loading.stop()
            HackerStyle.print_info("Two-factor authentication required")
            two_factor_code = input(f"{Colors.YELLOW}Enter 2FA code: {Colors.RESET}").strip()
            try:
                self.loader.two_factor_login(two_factor_code)
                self.is_logged_in = True
                HackerStyle.print_success(f"Successfully logged in as @{username}")
                return True
            except Exception as e:
                HackerStyle.print_error(f"2FA login failed: {e}")
                return False
        except Exception as e:
            loading.stop()
            HackerStyle.print_error(f"Login failed: {e}")
            return False
    
    def get_profile_info(self, username):
        try:
            loading = LoadingAnimation(f"Scanning target @{username}")
            loading.start()
            time.sleep(1)
            
            profile = instaloader.Profile.from_username(self.loader.context, username)
            loading.stop()
            
            HackerStyle.print_success(f"Target acquired: @{username}")
            HackerStyle.print_system("Profile data extracted successfully")
            
            profile_info = {
                'username': profile.username,
                'full_name': profile.full_name,
                'biography': profile.biography,
                'external_url': profile.external_url,
                'posts': profile.mediacount,
                'followers': profile.followers,
                'following': profile.followees,
                'userid': profile.userid,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'profile_pic_url': profile.profile_pic_url,
                'fetched_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return profile_info
            
        except instaloader.exceptions.ProfileNotExistsException:
            loading.stop()
            HackerStyle.print_error(f"Target not found: @{username}")
            return None
        except Exception as e:
            loading.stop()
            HackerStyle.print_error(f"Scanning failed: {str(e)}")
            return None
    
    def get_private_profile_info(self, username):
        """Get profile information for private accounts (requires login)"""
        if not self.is_logged_in:
            HackerStyle.print_error("Login required to access private accounts")
            return None
        
        try:
            loading = LoadingAnimation(f"Accessing private account @{username}")
            loading.start()
            
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Check if we follow this private account
            if not profile.followed_by_viewer:
                loading.stop()
                HackerStyle.print_error(f"You don't follow private account @{username}")
                return None
            
            loading.stop()
            
            profile_info = self.get_profile_info(username)
            if profile_info:
                HackerStyle.print_success(f"Private account data extracted: @{username}")
            
            return profile_info
            
        except Exception as e:
            loading.stop()
            HackerStyle.print_error(f"Failed to access private account: {e}")
            return None
    
    def download_profile_pic(self, username, output_dir="downloads"):
        try:
            HackerStyle.print_info("Extracting profile picture...")
            profile = instaloader.Profile.from_username(self.loader.context, username)
            pic_url = profile.profile_pic_url
            
            Path(output_dir).mkdir(exist_ok=True)
            
            response = requests.get(pic_url)
            filename = f"{output_dir}/{username}_profile_pic.jpg"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            HackerStyle.print_success(f"Profile picture extracted: {filename}")
            return filename
        except Exception as e:
            HackerStyle.print_error(f"Extraction failed: {e}")
            return None
    
    def download_posts(self, username, count=10, output_dir="downloads"):
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False
            
            HackerStyle.print_info(f"Downloading {count} posts...")
            
            posts_downloaded = 0
            for post in profile.get_posts():
                if posts_downloaded >= count:
                    break
                self.loader.download_post(post, target=f"{output_dir}/{username}/posts")
                posts_downloaded += 1
            
            HackerStyle.print_success(f"Downloaded {posts_downloaded} posts")
            return True
        except Exception as e:
            HackerStyle.print_error(f"Download failed: {e}")
            return False
    
    def download_reels(self, username, count=5, output_dir="downloads"):
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False
            
            HackerStyle.print_info(f"Downloading {count} reels...")
            
            reels_dir = f"{output_dir}/{username}/reels"
            Path(reels_dir).mkdir(parents=True, exist_ok=True)
            
            reel_count = 0
            for post in profile.get_posts():
                if reel_count >= count:
                    break
                if post.is_video:
                    self.loader.download_post(post, target=reels_dir)
                    reel_count += 1
            
            HackerStyle.print_success(f"Downloaded {reel_count} reels")
            return True
        except Exception as e:
            HackerStyle.print_error(f"Download failed: {e}")
            return False
    
    def download_stories(self, username, output_dir="downloads"):
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private and not self.is_logged_in:
                HackerStyle.print_error("Private account - login required")
                return False
            
            HackerStyle.print_info("Downloading stories...")
            
            stories_dir = f"{output_dir}/{username}/stories"
            Path(stories_dir).mkdir(parents=True, exist_ok=True)
            
            self.loader.download_stories(userids=[profile.userid], filename_target=stories_dir)
            
            HackerStyle.print_success("Stories downloaded successfully")
            return True
        except Exception as e:
            HackerStyle.print_warning(f"Stories may require login: {e}")
            return False
    
    def download_from_url(self, url, output_dir="downloads"):
        """Download specific post or reel from URL"""
        try:
            # Extract shortcode from URL
            shortcode = self.extract_shortcode_from_url(url)
            if not shortcode:
                HackerStyle.print_error("Invalid Instagram URL")
                return False
            
            loading = LoadingAnimation("Fetching post from URL")
            loading.start()
            
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            loading.stop()
            
            HackerStyle.print_info(f"Downloading: {post.title if post.title else 'Instagram Post'}")
            
            Path(output_dir).mkdir(exist_ok=True)
            self.loader.download_post(post, target=output_dir)
            
            HackerStyle.print_success(f"Downloaded post to {output_dir}")
            return True
            
        except instaloader.exceptions.PrivateAccountNotFollowedException:
            loading.stop()
            HackerStyle.print_error("Private account - you need to follow this account or login")
            return False
        except Exception as e:
            loading.stop()
            HackerStyle.print_error(f"Download from URL failed: {e}")
            return False
    
    def extract_shortcode_from_url(self, url):
        """Extract Instagram shortcode from various URL formats"""
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/stories/[^/]+/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def print_profile_info(self, profile_info):
        if not profile_info:
            return
        
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
    
    args = parser.parse_args()
    
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
    
    # Handle URL download
    if args.url:
        tool.download_from_url(args.url, output_dir)
        sys.exit(0)
    
    # Handle profile operations
    if args.username:
        if args.private:
            if not tool.is_logged_in:
                HackerStyle.print_error("Login required for private account access")
                sys.exit(1)
            profile_info = tool.get_private_profile_info(args.username)
        else:
            profile_info = tool.get_profile_info(args.username)
        
        if not profile_info:
            sys.exit(1)
        
        if args.interactive:
            tool.interactive_menu(profile_info)
            return
        
        if args.profile_pic or args.all:
            tool.download_profile_pic(args.username, output_dir)
        
        if args.posts or args.all:
            count = args.posts or 10
            tool.download_posts(args.username, count, output_dir)
        
        if args.reels or args.all:
            count = args.reels or 5
            tool.download_reels(args.username, count, output_dir)
        
        if args.stories or args.all:
            tool.download_stories(args.username, output_dir)
        
        if not any([args.profile_pic, args.posts, args.reels, args.stories, args.all]):
            tool.print_profile_info(profile_info)
    
    HackerStyle.print_success("Mission accomplished! 🏴‍☠️")

if __name__ == "__main__":
    main()
