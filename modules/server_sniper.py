import json
import requests
from collections import deque
from time import sleep
import webbrowser
import datetime
import re
import os
import sys
import threading
from pynput import keyboard

try:
    from win10toast import ToastNotifier # type: ignore
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

config = {}
running = False
paused = False
toaster = ToastNotifier() if TOAST_AVAILABLE else None

def show_notification(title, message):
    if TOAST_AVAILABLE and config.get('enable_notifications', '0') == '1':
        try:
            toaster.show_toast(title, message, duration=5)
        except Exception:
            pass

def read_config():
    config_name = '../config.json'

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(application_path, config_name)
    global config
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    
    if 'enable_notifications' not in config:
        config['enable_notifications'] = '1'
        save_config()

def save_config():
    config_name = '../config.json'

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(application_path, config_name)
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

def start_script(update_status_callback=None, update_recent_message_callback=None):
    global running, paused
    read_config()  # Ensure the config is read before checking values

    if not config.get("authorization_key") or not config.get("discord_channel_link"):
        print("Server Sniper | Error: Authorization Key and Discord Channel Link must be set in the configuration.")
        return

    if running:
        print("Server Sniper is already running.")
        return
    print("Server Sniper has started.")
    running = True
    paused = False
    if update_status_callback:
        update_status_callback("Running")
    threading.Thread(target=main, args=(update_recent_message_callback,), daemon=True).start()

def stop_script(update_status_callback=None):
    global running
    if not running:
        print("Server Sniper is not running.")
        return
    print("Server Sniper has stopped.")
    running = False
    if update_status_callback:
        update_status_callback("Stopped")

def pause_script(update_status_callback=None):
    global paused
    if not running:
        print("Server Sniper is not running.")
        return
    paused = not paused
    state = "Paused" if paused else "Running"
    print(f"Server Sniper is {state}.")
    if update_status_callback:
        update_status_callback(state)

def main(update_recent_message_callback=None):
    read_config()
    global config, running, paused
    
    keywords = [kw.strip().lower() for kw in config.get("keywords", "").split(",")]

    if config.get("serversniper_speed") == "2":
        show_notification("Warning!", "You have enabled Extremely Fast Autojoin! This option may lock or even ban your discord account!")
    elif config.get("serversniper_speed") == "1":
        show_notification("Warning!", "You have enabled Faster Autojoin! This option may lock your discord account!")
    
    messages = deque()

    if not config.get("authorization_key"):
        show_notification("Server Sniper | Error!", "Authorization Key Empty! Go to the Github README for instructions to get one.")
        return

    try:
        channel_id = re.search(r"[0-9]+/?$", config["discord_channel_link"]).group(0)
    except AttributeError:
        show_notification("Server Sniper | Error!", "Discord Channel Link Empty or Invalid!")
        return

    print("Server Sniper has resumed.")

    while running:
        if paused:
            sleep(1)
            continue
        try:
            response = requests.get(
                url=f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1",
                headers={
                    'Accept': 'application/json',
                    'Authorization': config["authorization_key"]
                }
            )
            response_json = response.json()

            if not response_json:
                print("Server Sniper | Error: Empty response from Discord API.")
                continue

            if isinstance(response_json, dict) and response_json.get("message") == "401: Unauthorized":
                show_notification("Server Sniper | ERROR!", "Authentication key invalid or timed out. Refresh the key.")
                return

            message = response_json[0]

            if message["id"] in messages:
                continue
            messages.append(message["id"])

            message_content = message.get("content", "").lower()

            matched_keyword = next((kw for kw in keywords if kw in message_content), None)

            if matched_keyword:
                links = re.findall(r'(https?://[^\s]+)', message.get("content", ""))
                link = None
                if links:
                    link = links[0]
                else:
                    for embed in message.get("embeds", []):
                        if "description" in embed:
                            embed_links = re.findall(r'(https?://[^\s]+)', embed["description"])
                            if embed_links:
                                link = embed_links[0]
                                break

                if not link:
                    print("No valid links found in the message. Skipping.")
                    continue

                if link.startswith("https://www.roblox.com/games/") and "15532962292" in link and "privateServerLinkCode=" in link or link.startswith("https://www.roblox.com/share?") and "code=" in link and "type=Server" in link:
                    timestamp = datetime.datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
                    duration = datetime.datetime.now(datetime.timezone.utc) - timestamp
                    duration_in_s = duration.total_seconds()
                    
                    if divmod(duration_in_s, 60)[0] < 4:
                        print(f"Server Link sniped with term \"{matched_keyword}\", joining: {link}")
                        print(f"Full Message: \"{message.get('content', '')}\"")
                        join_ps_link(link)
                        show_notification(
                            "Server Link Sniped!", 
                            f"Server Link sniped with the term \"{matched_keyword}\".Server Link: {link}"
                        )
                        if update_recent_message_callback:
                            username = message["author"]["username"]
                            formatted_message = message["content"]
                            update_recent_message_callback(username, formatted_message)
                    else:
                        print(f"Link is older than 4 minutes. Ignoring.")
                else:
                    print("Non-Sol's RNG link detected. Ignoring for safety.")

            while len(messages) > 10:
                messages.popleft()

        except Exception as e:
            print(f"Server Sniper | Error occurred: {e}")

        sleep(int(config.get("sleep_duration", 5)))

def join_ps_link(link):
    webbrowser.open(link)

start_key = config.get("start_key")
pause_key = config.get("pause_key")
stop_key = config.get("stop_key")

def on_press(key):
    try:
        if key == start_key:
            start_script()
        elif key == pause_key:
            pause_script()
        elif key == stop_key:
            stop_script()
    except Exception as e:
        print(f"Server Sniper | Error handling key press: {e}")

if __name__ == "__main__":
    if not TOAST_AVAILABLE:
        print("Win10toast library not found. Notifications will be console-only.")