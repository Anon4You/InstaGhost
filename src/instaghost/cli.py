"""Command-line interface: argument parsing and the interactive flow."""

import argparse
import sys

from . import __version__
from .auth import LoginManager
from .client import InstaGhost
from .config import DEFAULT_OUTPUT_DIR
from .output import Colors, HackerStyle


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
        print(f"InstaGhost v{__version__}")
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
    output_dir = args.output or DEFAULT_OUTPUT_DIR

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
