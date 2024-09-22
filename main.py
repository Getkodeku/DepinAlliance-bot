import random
import requests
from colorama import *
from src.utils import log, log_line, countdown_timer, read_config, _banner, red, white, yellow, green, blue, black, reset, _clear
from src.core import Depin, load_proxies

config = read_config()
init(autoreset=True)

# Cached configuration settings
UPGRADE_SKILL = config.get('auto_upgrade_skill', False)
AUTO_TASK = config.get('auto_complete_task', False)
AUTO_OPEN_BOX = config.get('auto_open_box', False)
MAX_BOX_PRICE = config.get('auto_open_box_max_price', 0)
AUTO_BUY_ITEM = config.get('auto_buy_item', False)
MAX_ITEM_PRICE = config.get('auto_buy_item_max_price', 0)
DELAY = config.get('account_delay', 5)
LOOP_DELAY = config.get('countdown_loop', 3800)
USE_PROXY = config.get('use_proxy', False)
PROXIES = load_proxies() if USE_PROXY else None

def process_account(i, total_accounts, query_data):
    """Handles the processing of a single account."""
    proxy = random.choice(PROXIES) if PROXIES and USE_PROXY else None
    dep = Depin(proxy=proxy)

    log(green + f"Processing account {white}{i}/{total_accounts}")
    if proxy:
        log(green + f"Using proxy: {white}{proxy}")
        log(black + "~" * 38)

    user_data = dep.extract_user_data(query_data)
    user_id = user_data.get("id")
    if not user_id:
        log(red + "User ID not found in data.")
        return

    token = dep.local_token(user_id) or dep.login(query_data, user_id)
    if not token:
        log(red + f"Login failed for user ID: {white}{user_id}")
        return

    try:
        execute_user_actions(dep, user_id)
    except requests.exceptions.ProxyError as e:
        handle_proxy_error(e)
    except requests.exceptions.HTTPError as e:
        handle_http_error(e, query_data, user_id, dep)

def execute_user_actions(dep, user_id):
    """Executes various actions for the user account."""
    dep.user_data(user_id)
    dep.j_l(user_id)
    dep.daily_checkin(user_id)
    dep.claim_mining(user_id)

    device_indices = dep.get_device_indices(user_id)
    if not device_indices:
        log(black + f"No valid device indices found for user ID: {white}{user_id}")
        return
    device_index = device_indices[0]

    equipped_items = dep.get_equipped_items(user_id, device_index)
    if equipped_items is None:
        log(red + f"No equipped items found for user ID: {white}{user_id}")
        return

    if AUTO_OPEN_BOX:
        dep.open_box(user_id, MAX_BOX_PRICE)
    else:
        log(yellow + "Auto open cyber box is disabled!")

    for item_type in ["CPU", "GPU", "RAM", "STORAGE"]:
        dep.get_items_by_type(user_id, item_type)

    if AUTO_BUY_ITEM:
        dep.auto_buy_item(user_id, device_index, MAX_ITEM_PRICE)

    if UPGRADE_SKILL:
        dep.upgrade_skill(user_id)
    else:
        log(yellow + "Auto upgrade skill is disabled!")

    if AUTO_TASK:
        dep.get_task(user_id)
        dep.complete_quest(user_id)
    else:
        log(yellow + "Auto complete task is disabled!")

def handle_proxy_error(e):
    """Handles proxy-related errors."""
    log(red + f"Proxy error occurred: {e}")
    if "407" in str(e):
        log(blue + "Proxy authentication failed. Trying another proxy...")
        if PROXIES:
            proxy = random.choice(PROXIES)
            log(blue + f"Switching to new proxy: {white}{proxy}")
        else:
            log(red + "No more proxies available.")
    else:
        log(black + f"An error occurred: {black}{e}")

def handle_http_error(e, query_data, user_id, dep):
    """Handles HTTP errors during the execution."""
    if e.response.status_code == 401:
        log(blue + "Token expired or Unauthorized. Attempting to login again...")
        token = dep.login(query_data, user_id)
        if token:
            log(green + f"Re-login successful for user ID {white}{user_id}{green}. Continuing actions.")
        else:
            log(red + f"Re-login failed for user ID {white}{user_id}. Skipping this user.")
    else:
        log(black + f"HTTP error occurred: {black}{e}")

def main():
    try:
        with open("data.txt") as file:
            query_data_list = [data.strip() for data in file if data.strip()]
        if not query_data_list:
            raise ValueError("data.txt is empty or contains only empty lines.")
    except FileNotFoundError:
        log(red + "data.txt file not found.")
        return

    for i, query_data in enumerate(query_data_list, start=1):
        process_account(i, len(query_data_list), query_data)
        log_line()
        countdown_timer(DELAY)

    countdown_timer(LOOP_DELAY)

if __name__ == "__main__":
    _clear()
    _banner()
    while True:
        try:
            main()
        except KeyboardInterrupt:
            log(red + "Process interrupted by user.")
            exit(0)
