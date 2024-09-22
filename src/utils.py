import os
import json
import time
from datetime import datetime
from colorama import *

# Define colors
red = Fore.LIGHTRED_EX
white = Fore.LIGHTWHITE_EX
green = Fore.LIGHTGREEN_EX
yellow = Fore.LIGHTYELLOW_EX
blue = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL
black = Fore.LIGHTBLACK_EX

# Global variable to store the last log message
last_log_message = None


def _banner():
    """Displays the application banner."""
    banner = r"""
  ____           _   _              __  __
 |  _ \    ___  | | | |_    __ _    \ \/ /
 | | | |  / _ \ | | | __|  / _` |    \  / 
 | |_| | |  __/ | | | |_  | (_| |    /  \ 
 |____/   \___| |_|  \__|  \__,_|   /_/\_\
"""
    print(Fore.GREEN + Style.BRIGHT + banner + Style.RESET_ALL)
    print(green + " DePin Alliance Telegram Bot")
    log_line()


def _clear():
    """Clears the terminal."""
    os.system("cls" if os.name == "nt" else "clear")


def read_config():
    """Reads and returns the configuration from the config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), "../config.json")
    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        log(red + "Config file not found!")
        return {}
    except json.JSONDecodeError as e:
        log(red + f"Error parsing config file: {e}")
        return {}


def log(message, *args, **kwargs):
    """Logs a message with a timestamp, preventing duplicate messages."""
    global last_log_message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flush = kwargs.pop("flush", False)
    end = kwargs.pop("end", "\n")

    # Only print the log if it's different from the last one
    full_message = message + " " + " ".join(map(str, args))
    if full_message != last_log_message:
        print(f"[{current_time}] {full_message}", flush=flush, end=end)
        last_log_message = full_message


def log_line():
    """Logs a separator line."""
    print(white + "~" * 60)


def countdown_timer(seconds):
    """Displays a countdown timer in HH:MM:SS format."""
    while seconds:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        print(f"{white}please wait until {h:02}:{m:02}:{s:02} ", flush=True, end="\r")
        time.sleep(1)
        seconds -= 1
    print(f"{white}Timer completed!                          ", flush=True)
