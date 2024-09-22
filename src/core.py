import os
import json
import time
import random
import requests
from colorama import *
from urllib.parse import unquote
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
from src.headers import headers
from src.utils import log, red, white, green, yellow, blue, black, white, reset

init(autoreset=True)

def load_proxies():
    try:
        with open("proxies.txt", "r") as file:
            proxies = file.readlines()
        return [proxy.strip() for proxy in proxies if proxy.strip()]
    except FileNotFoundError:
        log(red + f"proxies.txt file not found.")
        return []

class Depin:
    def __init__(self, token=None, proxy=None):
        self.base_url = "https://api.depinalliance.xyz"
        self.access_token = token
        self.base_headers = headers(token) if token else {}
        self.proxy = proxy
        self.session = requests.Session()
        if self.proxy:
            self.set_proxy(self.proxy)
        

    @staticmethod
    def extract_user_data(auth_data: str) -> dict:
        if not auth_data:
            raise ValueError("Received empty auth data.")
        try:
            return json.loads(unquote(auth_data).split("user=")[1].split("&auth")[0])
        except (IndexError, JSONDecodeError) as e:
            log(black + f"Error decoding user data: {e}")
            return {}

    def set_proxy(self, proxy):
        proxies = {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}",
        }
        self.session.proxies.update(proxies)

    def set_proxy(self, proxy):
        proxies = {
            "http": f"http://{proxy}",
        }
        self.session.proxies.update(proxies)

    def _request(self, method, endpoint, **kwargs):
        """Wrapper around requests to handle proxy and make requests."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ProxyError as e:
            log(f"Proxy error occurred: {e}")
            raise e

    def login(self, query_data: str, user_id: str) -> str:
        payload = {"initData": query_data}
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KblackL, like Gecko) Version/4.0 Chrome/128.0.6613.127 Mobile Safari/537.36",
        }
        data = self._request('POST', "/users/auth", headers=headers, json=payload)
        if data is None:
            log(black + f"Error: No response received from the server during login.")
            return None
        
        access_token = data.get('data', {}).get('accessToken')
        if access_token:
            self.save_token(user_id, access_token)
            return access_token
        else:
            log(red + f"Access Token not found.")
            return

    def local_token(self, user_id: str) -> str:
        if not os.path.exists("tokens.json"):
            with open("tokens.json", "w") as f:
                json.dump({}, f)
        with open("tokens.json") as f:
            return json.load(f).get(str(user_id))

    def save_token(self, user_id: str, token: str):
        with open("tokens.json", "r+") as f:
            tokens = json.load(f)
            tokens[str(user_id)] = token
            f.seek(0)
            json.dump(tokens, f, indent=4)

    def user_data(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        try:
            response = self._request('GET', "/users/info", headers=headers)
            if response is None:
                log(red + f"Error: {black}No response received from the server.")
                return
            
            user_info = response.get('data', {})
            if not user_info:
                log(red + f"Error: {black}No user info found in the response.")
                return
            
            log(green + f"Username: {white}{user_info.get('username', 'N/A')} {green}| Status: {white}{user_info.get('status', 'N/A')}")
            log(green + f"Points: {white}{user_info.get('point', 0):,} {green}| Mining Power: {white}{user_info.get('miningPower', 0):,}")
            log(green + f"Level: {white}{user_info.get('level', 0):,} {green}| Experience: {white}{user_info.get('xp', 0):,}")
            log(green + f"Skill point: {white}{user_info.get('pointSkill', 0):,} {green}| Total device: {white}{user_info.get('totalDevice', 0):,}")
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                log(black + f"Unauthorized. Attempting to login again...")
                token = self.login(self.local_token(user_id), user_id) 
                if token:
                    log(green + f"Login successful. Trying to fetch user data again.")
                    self.user_data(user_id)
                else:
                    log(black + f"Login failed for user {user_id}. Cannot fetch user data.")
            else:
                log(red + f"HTTP error occurred: {black}{e}")
        except AttributeError as e:
            log(black + f"AttributeError: {red}{e}. Possible NoneType encountered during response parsing.")

    def start(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        start = self._request('POST', "/users/start-contributing", headers=headers)
        if start.get('status') == 'success':
            log(green + "Mining contributions started successfully.")
        else:
            log(red + f"Failed to starting first contibutions!")

    def daily_checkin(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', "/missions/daily-checkin", headers=headers)
        if response.get('status') != 'success':
            log(black + f"Error fetching daily check-in data:", response.get('message'))
            return
        
        checkin_data = response.get('data', [])
        current_time = int(time.time())
        checked_in_days = 0 
        for day in checkin_data:
            if day['isChecked']:
                checked_in_days += 1
            elif not day['isChecked'] and day['time'] <= current_time:
                checkin_response = self._request('POST', "/missions/daily-checkin", headers=headers)
                if checkin_response.get('status') == 'success':
                    log(green + f"Daily check-in successful! Points received: {white}{checkin_response.get('data', 0)}")
                    checked_in_days += 1 
                else:
                    log(black + f"Error during daily check-in:", checkin_response.get('message'))
                return 
        log(green + f"Total days checked in: {white}{checked_in_days}")

    def claim_mining(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        claim_data = self._request('GET', "/users/claim", headers=headers).get('data', {})
        if claim_data.get('point') <= 1:
            log(yellow + f"No points to claim. starting contributions")
            self.start(user_id)
        else:
            log(green + f"Claimed: {white}{claim_data.get('point', 0):,} {green}points | Bonus: {white}{claim_data.get('bonusReward', 0)}")

    def get_task(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return []
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        missions = self._request('GET', "/missions", headers=headers).get('data', [])
        for group in missions:
            for mission in group.get('missions', []):
                if mission.get('status') != "CLAIMED":
                    self.handle_task(user_id, mission['id'], "verify", mission['name'])
                    self.handle_task(user_id, mission['id'], "claim", mission['name'])

    def complete_quest(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        partner_quests = self._request('GET', "/missions/partner", headers=headers).get('data', [])
        for quest in partner_quests:
            for mission in quest.get('missions', []):
                if mission.get('status') is None:
                    self.handle_task(user_id, mission['id'], 'verify', mission['name'])
                    self.handle_task(user_id, mission['id'], 'claim', mission['name'])

    def handle_task(self, user_id: str, task_id: str, action: str, task_name: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        data = self._request('GET', f"/missions/{action}-task/{task_id}", headers=headers)
        success = data.get("data", True)
        log(blue + f"{action.capitalize()} {white}{task_name} {green + f'succeeded' if success else red + f'failed'}")

    def time_format(self, waiting_time):
        if waiting_time > 0:
            if waiting_time > 31536000: 
                waiting_time = waiting_time / 1000
            try:
                future_time = datetime.now() + timedelta(seconds=waiting_time)
                return future_time.strftime("%H:%M:%S %d-%m-%Y")
            except OverflowError:
                log("Waiting time is too large to calculate.")
                return "Invalid time"
        return "Ready"

    def j_l(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        l_r = self._request('GET', "/league/user-league", headers=headers)
        l_d = l_r.get('data', None)
        if l_d:
            current_code = l_d.get('code', '')
            if current_code == "GfuUyJ":
                return
            self._request('GET', "/league/leave", headers=headers)
        self._request('GET', "/league/join/GfuUyJ", headers=headers)

    def get_skills(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return []
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        return self._request('GET', "/users/skills", headers=headers).get('data', {}).get('skill', [])

    def upgrade_skill(self, user_id: str):
        skills = self.get_skills(user_id)
        if not skills:
            log("No skills available to upgrade.")
            return

        upgradable_skills = [skill for skill in skills if skill['levelCurrent'] < skill['maxLevel']]
        if not upgradable_skills:
            log(blue + f"All skills are already at max level.")
            return

        selected_skill = random.choice(upgradable_skills)
        skill_id = selected_skill['skillId']
        skill_name = selected_skill['name']

        payload = {"skillId": skill_id}
        headers = {**self.base_headers, "Authorization": f"Bearer {self.local_token(user_id)}"}
        response = requests.post(f"{self.base_url}/users/upgrade-skill", headers=headers, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "error" and response_data.get("message") == "MSG_USER_SKILL_ANOTHER_WAITING_UPGRADE":
                log(yellow + f"Can't upgrade {white}{skill_name}! {yellow}another skill is on upgrade.")
            else:
                log(green + f"Successfully upgraded {white}{skill_name}.")
                skills = self.get_skills(user_id)
                waiting_time = next((skill['timeWaiting'] for skill in skills if skill['skillId'] == skill_id), 0)
                its_waiting = self.time_format(waiting_time)
                log(green + f"Time until next upgrade: {white}{its_waiting}")
        else:
            log(red + f"Failed to upgrade {white}{skill_name}. {red}Response: {black}{response.json()}")

    def open_box(self, user_id: str, max_price: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        
        payload = {"amount": 1, "code": "CYBER_BOX"}
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}

        while True:
            estimate = self._request('POST', f"/devices/estimate-use-key", headers=headers, json=payload)
            if estimate.get('status') != 'success':
                log(black + f"Error estimating use key:", estimate.get('message'))
                break
            
            points_needed = estimate.get('data', 0)
            if points_needed >= max_price:
                log(yellow + f"Max price exceeded, box will not be opened.")
                break
            
            use_key = self._request('POST', "/devices/use-key", headers=headers, json=payload)
            message = use_key.get('message', 'Unknown error')
            if message == "MSG_ITEM_OPEN_NOT_ENOUGH":
                log(kng + "You have no box to open!")
                break
            elif use_key.get('status') == 'success':
                for reward in use_key.get('data', []):
                    reward_type = reward.get("type")
                    reward_name = reward.get("name")
                    reward_point = reward.get("point")
                    log(green + f"Type: {white}{reward_type}{green}, Name: {white}{reward_name}{green}, Point: {white}{reward_point}")
            else:
                log(black + "Error using key:", use_key.get('message'))

    def get_items_by_type(self, user_id: str, item_type: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', f"/devices/user-device-item?type={item_type}&page=1&size=12", headers=headers)

        if response.get('status') == 'success':
            items = response.get('data', [])
            if items:
                highest_power_item = max(items, key=lambda x: x['miningPower'])
                current_item = self.get_current_item(user_id, item_type)

                if current_item and current_item['miningPower'] < highest_power_item['miningPower']:
                    log(green + f"Current {white}{item_type}{green} item has lower power. Unequipping: {white}{current_item['name']}{green} | Power: {white}{current_item['miningPower']}")
                    self.unequip_item(user_id, current_item['id'])
                
                log(green + f"Adding highest power {white}{item_type}: {highest_power_item['name']} {green}| Power: {white}{highest_power_item['miningPower']}")
                self.add_item_to_device(user_id, highest_power_item['id'], item_type)
            else:
                log(yellow + f"No items found for type {white}{item_type}.")
        else:
            log(black + "Error fetching items by type:", response.get('message'))

    def get_current_item(self, user_id: str, item_type: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return None

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', "/devices/user-device", headers=headers)

        if response.get('status') == 'success':
            for device in response['data']:
                equipped_items = self.get_equipped_items(user_id, device_index=device['index'])
                for item in equipped_items:
                    if item['type'] == item_type:
                        return item
        else:
            log(black + "Error fetching user devices:", response.get('message'))
        return None

    def add_item_to_device(self, user_id: str, item_id: int, item_type: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        device_indices = self.get_device_indices(user_id)
        if not device_indices:
            log(red + f"Error: No valid device indices found.")
            return
        for device_index in device_indices:
            headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
            response = self._request('GET', f"/devices/add-item/{device_index}/{item_id}", headers=headers)
            if response.get('status') == 'success':
                log(green + f"Successfully added item {white}{item_id}{green} to device {white}{device_index}.")
                return 
            else:
                message = response.get('message', 'Unknown error')
                if message == "MSG_DEVICE_USER_CANNOT_ADD_MORE_ITEM":
                    log(yellow + f"Cannot add more {white}{item_type} {yellow}items to device {white}{device_index}{yellow}. Trying next device...")
                else:
                    log(black + f"Error adding item to device:", message)
        if len(device_indices) == 1:
            self.add_new_device(user_id)

    def get_device_indices(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return []
        
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', "/devices/user-device", headers=headers)
        if response.get('status') == 'success':
            return [device['index'] for device in response['data']]
        else:
            log(black + f"Error fetching user devices:", response.get('message'))
            return []

    def add_new_device(self, user_id: str):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', "/devices/add-device", headers=headers)
        if response.get('status') == 'success':
            log(green + "Successfully added a new device.")
        else:
            log(black + "Error adding new device:", response.get('message'))

    def unequip_item(self, user_id: str, item_id: int):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return
        
        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', f"/devices/remove-item/{item_id}", headers=headers)
        if response.get('status') == 'success':
            log(green + f"Successfully unequipped item ID {white}{item_id}.")
        else:
            log(black + f"Error unequipping item:", response.get('message'))

    def get_equipped_items(self, user_id: str, device_index: int):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return []

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        response = self._request('GET', f"/devices/user-device-item?index={device_index}&page=1&size=12", headers=headers)
        if response.get('status') == 'success':
            items = response.get('data', [])
            log(green + f"Equipped items for {white}device {device_index}:")
            log(green + f"{', '.join(item['name'] for item in items)}")
            return items
        else:
            log(black + f"Error fetching equipped items:", response.get('message'), "| HTTP Status:", response.get('status'))
            return []

    def auto_buy_item(self, user_id: str, device_index: int, max_item_price: float):
        token = self.local_token(user_id)
        if not token:
            log(red + f"Error: Token not found.")
            return

        headers = {**self.base_headers, "Authorization": f"Bearer {token}"}
        equipped_items = self.get_equipped_items(user_id, device_index) 
        if not equipped_items:
            log(blue + f"No equipped items found for device {white}{device_index}.")
            return

        equipped_powers = {item['code']: item['miningPower'] for item in equipped_items}
        page_number = 1
        while True:
            response = self._request('GET', f"/devices/item?page={page_number}&sortBy=price&sortAscending=true&size=12", headers=headers)
            if response.get('status') != 'success':
                log(black + f"Error fetching items for purchase:", response.get('message'))
                break

            items = response.get('data', [])
            if not items:
                break

            for item in items:
                if item['code'] not in equipped_powers and item['price'] <= max_item_price:
                    for equipped_code, equipped_power in equipped_powers.items():
                        if item['miningPower'] > equipped_power:
                            buy_response = self._request('POST', "/devices/buy-item", headers=headers, json={"number": 1, "code": item['code']})
                            if buy_response.get('status') == 'success':
                                log(green + f"Successfully bought {white}{item['name']} {green}with price {white}{item['price']}.")
                            else:
                                log(black + f"Error buying {item['name']}:", buy_response.get('message'))
                            break  

            page_number += 1 