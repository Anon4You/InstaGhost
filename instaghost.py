#!/usr/bin/env python3

import instaloader
import argparse
import json
import sys
import os
import requests
import time
import threading
from datetime import datetime
from pathlib import Path

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
        # KEEPING YOUR ORIGINAL BANNER EXACTLY AS IS
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

class InstaGhost:
    def __init__(self):
        self.loader = instaloader.Instaloader()
        self.loader.save_metadata = False
        self.loader.download_video_thumbnails = False
        self.loader.compress_json = False
    
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
            
            if profile.is_private:
                HackerStyle.print_error("Private account - access denied")
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
            
            if profile.is_private:
                HackerStyle.print_error("Private account - access denied")
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
            
            if profile.is_private:
                HackerStyle.print_error("Private account - access denied")
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
            elif choice == '0':
                HackerStyle.print_success("Terminal session terminated. Stay stealthy! 🏴‍☠️")
                break
            else:
                HackerStyle.print_error("Invalid command. Try again.")

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
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    if args.help or not args.username:
        print(f"{Colors.BOLD}{Colors.CYAN}🛠️  INSTAGHOST COMMAND REFERENCE{Colors.RESET}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.RESET}")
        print(f"\n{Colors.GREEN}Usage:{Colors.RESET}")
        print(f"  python instaghost.py {Colors.YELLOW}<username>{Colors.RESET} {Colors.CYAN}[options]{Colors.RESET}")
        print(f"\n{Colors.GREEN}Options:{Colors.RESET}")
        print(f"  {Colors.YELLOW}-i, --interactive{Colors.RESET}  🖥️  Launch interactive terminal")
        print(f"  {Colors.YELLOW}-p, --profile-pic{Colors.RESET}  📸 Extract profile picture")
        print(f"  {Colors.YELLOW}-P, --posts{Colors.RESET}       📷 Download posts (specify count)")
        print(f"  {Colors.YELLOW}-r, --reels{Colors.RESET}       🎬 Download reels (specify count)")
        print(f"  {Colors.YELLOW}-s, --stories{Colors.RESET}     📖 Download stories")
        print(f"  {Colors.YELLOW}-a, --all{Colors.RESET}         🚀 Download all intelligence")
        print(f"  {Colors.YELLOW}-o, --output{Colors.RESET}      💾 Output directory")
        print(f"  {Colors.YELLOW}-h, --help{Colors.RESET}        📖 Show this help")
        print(f"\n{Colors.GREEN}Examples:{Colors.RESET}")
        print(f"  python instaghost.py {Colors.CYAN}username -i{Colors.RESET}")
        print(f"  python instaghost.py {Colors.CYAN}target -p -P 5{Colors.RESET}")
        print(f"  python instaghost.py {Colors.CYAN}user -a{Colors.RESET}")
        sys.exit(0)
    
    tool = InstaGhost()
    output_dir = args.output or "downloads"
    
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
