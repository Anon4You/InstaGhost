"""Terminal styling, status lines, and the loading spinner."""

import os
import sys
import threading
import time


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
        from . import __version__

        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")
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

{Colors.BLUE}{Colors.BOLD}{pad}InstaGhost v{__version__} - Instagram OSINT Tool{Colors.RESET}
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
    enabled = True  # gateways turn this off so captured output stays clean

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
        if not self.enabled:
            return
        self.running = True
        self.thread = threading.Thread(target=self.__animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
