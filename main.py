import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys, json, threading, webbrowser, requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import threading

from pynput import mouse, keyboard
from PIL import ImageGrab, Image, ImageDraw, ImageTk
from modules.discord_bot import start_bot
from modules.server_sniper import start_script, stop_script, pause_script
from modules.autoclicker import AutoClicker
from pynput.keyboard import KeyCode
from pynput.mouse import Button

class DiscordMacroUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SolsBot UI | v1.0.2")
        self.root.configure(bg="#2C2F33")
        self.dark_mode = True

        self.running_event = threading.Event()
        self.running_event.set()
        
        # theme
        theme_path = os.path.join("modules/Azure-ttk-theme-2.1.0", "azure.tcl")
        self.root.tk.call("source", theme_path)
        self.root.tk.call("set_theme", "dark")

        # design
        style = ttk.Style()
        style.configure("TLabelFrame", padding=10, font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10), padding=(6, 4))
        style.configure("TCheckbutton", font=("Helvetica", 10), padding=(6, 4))
        style.configure("TRadiobutton", font=("Helvetica", 10))
        style.configure("Switch.TCheckbutton", font=("Helvetica", 10), padding=5)
        self.center_window()
        
        #config and config path
        self.config_path = "config.json"
        self.config = self.load_config()

        # initialize/start the discord bot
        if self.config.get("DiscordBot_Enabled", 0):
            threading.Thread(target=start_bot, args=(self.running_event,), daemon=True).start()

        # UI
        self.setup_tabs()
        self.setup_info_tab()
        self.setup_discord_tab()
        self.setup_serversniper_tab()
        if self.config.get("developer", False):
            self.setup_autoclicker_tab()
        self.setup_settings_tab()
        self.setup_credits_tab()
        self.auto_resize()

        #~ assign buttons:
        self.coord_vars = {}

        #~ check for updates
        self.check_for_updates()

    def show_update_popup(self, root, current_version, latest_version):
        update_window = tk.Toplevel(root)
        update_window.title("Update Available")
        update_window.geometry("400x200")
        update_window.attributes("-topmost", True)

        ttk.Label(update_window, text="A new update is available!", font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(update_window, text=f"Current Version: {current_version}", font=("Helvetica", 12)).pack(pady=5)
        ttk.Label(update_window, text=f"Latest Version: {latest_version}", font=("Helvetica", 12)).pack(pady=5)

        button_frame = ttk.Frame(update_window)
        button_frame.pack(pady=20)

        update_button = ttk.Button(button_frame, text="Update", command=lambda: [webbrowser.open("https://github.com/vexthecoder/SolsBot/releases/latest"), update_window.destroy()])
        update_button.grid(row=0, column=0, padx=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=update_window.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    def check_for_updates(self):
        update_num = requests.get("https://raw.githubusercontent.com/vexthecoder/SolsBot/main/version").text.strip()
        if update_num != "v1.0.2":
            current_version = "v1.0.2"
            latest_version = update_num
            if latest_version != current_version:
                self.show_update_popup(self.root, current_version, latest_version)

    def system_message(self, message):
        messagebox.showinfo("Discord Macro UI", message)

    def load_config(self):
        try:
            with open(self.config_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def update_config(self, key, value, default=None):
        if key not in self.config:
            self.config[key] = value if default is None else default
        else:
            self.config[key] = value
        self.save_config()

    def save_config(self):
        with open(self.config_path, "w") as file:
            json.dump(self.config, file, indent=4)

    def update_item_spot(self, index, var):
        item_spots = self.config.get("Sub_ItemSpot", [0] * 8)
        item_spots[index] = var.get()
        self.update_config("Sub_ItemSpot", item_spots)
        
    def import_settings(self):
        file_path = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=(("Config File", "config.json"), ("JSON Files", "*.json"), ("All Files", "*.*"))
        )
        if not file_path:
            return
        try:
            with open(file_path, "r") as file:
                imported_config = json.load(file)
            self.config.update(imported_config)
            self.save_config()

            self.system_message("Settings imported successfully! Please restart the macro to apply the changes.")
        except Exception as e:
            self.system_message(f"Settings | Error importing settings: {str(e)}")
    
    def get_key_bindings(self):
        azerty_keyboard = self.config.get("AZERTY_Keyboard", False)
        if azerty_keyboard:
            return {'record_start': 'o', 'record_stop': 'p', 'replay_start': 'l', 'replay_stop': 'm'}
        return {'record_start': '[', 'record_stop': ']', 'replay_start': ';', 'replay_stop': "'"}

    def start_key_listener(self):
        def on_press(key):
            try:
                start_key = self.config.get("start_key", "F4")
                pause_key = self.config.get("pause_key", "F5")
                stop_key = self.config.get("stop_key", "F6")

                if hasattr(key, 'char') and key.char == start_key.lower():
                    start_script()
                elif hasattr(key, 'char') and key.char == pause_key.lower():
                    pause_script()
                elif hasattr(key, 'char') and key.char == stop_key.lower():
                    stop_script()
            except Exception as e:
                print(f"Server Sniper | Error handling key press: {e}")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    
    ## ~ DISCORD BOT ## 

    def toggle_discordbot_enabled(self):
        if self.enable_discordbot.get() == 1 and not self.discordbot_token_entry.get():
            messagebox.showwarning("Discord Bot Disabled", "Please enter a valid Discord Bot Token before enabling.")
            self.enable_discordbot.set(0)
            return
        self.update_config("DiscordBot_Enabled", self.enable_discordbot.get())
     
    ##* Check PS link format *##
    def validate_and_save_ps_link(self, event=None):
        link = self.server_link_var.get()
        if self.is_valid_ps_link(link):
            self.config["PrivateServerLink"] = link
            with open(self.config_path, "w") as config_file:
                json.dump(self.config, config_file, indent=4)
        if link != "" and not self.is_valid_ps_link(link):
            messagebox.showerror("Error", "Invalid link format. Please correct it.")

    def is_valid_ps_link(self, link):
        if link.startswith("https://www.roblox.com/share?") and "code=" in link and "type=Server" in link:
            return True
        if link.startswith("https://www.roblox.com/games/") and "privateServerLinkCode=" in link:
            return True
        return False
        
    ##! Assign Button ##
    def open_assign_menu_window(self):
        self.assign_menu_window = tk.Toplevel(self.root)
        self.assign_menu_window.title("Assign Ingame Buttons Coordinates")
        self.assign_menu_window.geometry("560x580")
        self.assign_menu_window.attributes("-topmost", True)
        
        self.sections = [
            {
                "name": "Misc",
                "buttons": {
                    "Open/Close Chat Button": "chat_button_location",
                    "Play Button (Main Menu)": "play_button_location"
                }
            }
        ]

        self.current_page = 0  # Start on the first page
        self.coord_vars = {}

        # Save and navigation buttons
        navigation_frame = ttk.Frame(self.assign_menu_window)
        navigation_frame.grid(row=10, column=0, columnspan=4, pady=10)

        save_button = ttk.Button(navigation_frame, text="Save", command=self.save_coordinates)
        save_button.grid(row=0, column=0, padx=5)

        close_button = ttk.Button(navigation_frame, text="Close", command=self.assign_menu_window.destroy)
        close_button.grid(row=0, column=1, padx=5)

        self.assign_ingame_buttons_display_current_page()

    def assign_ingame_buttons_display_current_page(self):
        for widget in self.assign_menu_window.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()

        start_index = self.current_page * 2
        end_index = min(start_index + 2, len(self.sections))
        current_sections = self.sections[start_index:end_index]

        for section_index, section in enumerate(current_sections):
            section_frame = ttk.LabelFrame(
                self.assign_menu_window, 
                text=section["name"], 
                padding=(10, 5)
            )
            section_frame.grid(
                row=section_index, 
                column=0, 
                columnspan=4, 
                padx=10, 
                pady=10, 
                sticky="w"
            )

            for index, (label_text, config_key) in enumerate(section["buttons"].items()):
                label = ttk.Label(section_frame, text=f"{label_text}:")
                label.grid(row=index, column=0, padx=10, pady=5, sticky="w")

                # Initialize coordinate variables
                coords = self.config.get(config_key, [0, 0])
                x_var = tk.IntVar(value=coords[0])
                y_var = tk.IntVar(value=coords[1])
                self.coord_vars[config_key] = (x_var, y_var)

                # X and Y coordinate entries
                x_entry = ttk.Entry(section_frame, textvariable=x_var, width=6)
                x_entry.grid(row=index, column=1, padx=5, pady=5)

                y_entry = ttk.Entry(section_frame, textvariable=y_var, width=6)
                y_entry.grid(row=index, column=2, padx=5, pady=5)

                assign_button = ttk.Button(
                    section_frame, 
                    text="Assign Click",
                    command=lambda key=config_key: self.start_capture_thread(key)
                )
                assign_button.grid(row=index, column=3, padx=5, pady=5)

        self.prev_button["state"] = "normal" if self.current_page > 0 else "disabled"
        self.next_button["state"] = "normal" if start_index + 2 < len(self.sections) else "disabled"

    def open_help_window(self):
        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("Help Window")

        self.help_info = [
            {
                "type": "release",
                "title": "Help | Discord",
                "subtitle1": "Discord Bot",
                "content1": (
                    "Follow the tutorial to create your discord bot and paste the token into the \"Discord Bot Token\" space.\n"
                    "Make sure to enable EVERY privileged gateway intent or the bot will not work."
                ),
                "link1": "https://www.youtube.com/watch?v=-m-Z7Wav-fM",
                "subtitle2": "Webhook",
                "content2": (
                    "Follow the tutorial to create a discord webhook and paste the webhook URL into the \"Webhook URL\" space."
                ),
                "link2": "https://youtu.be/fKksxz2Gdnc?t=13&si=7FdMdJW6SNqSMZ4N",
                "geometry": "675x410"
            },
            {
                "type": "release",
                "title": "Help | Server Sniper",
                "subtitle1": "Authorization Key",
                "content1": (
                    "1. Activate developer tools on your discord client by pressing Ctrl + Shift + I and navigate to \"Network\" tab\n"
                    "2. Enable Fetch/XHR\n"
                    "3. Click on any channel from any server\n"
                    "4. Click on the messages?limit=50 option\n"
                    "5. Right click and copy as fetch, paste into a notepad\n"
                    "6. Copy the text in the authorization field, it should start with MTA\n"
                    "7. Paste it into the Authorization Key field in the Server Sniper config editor"
                ),
                "subtitle2": "Channel Link",
                "content2": (
                    "1. Go to any discord server and right click the channel you want to monitor and \nsnipe servers from, click copy link\n"
                    "2. Paste that link into the Channel Link field in the Server Sniper config editor"
                ),
                "geometry": "690x450"
            },
            {
                "type": "developer",
                "title": "Help | Auto Clicker",
                "subtitle1": "Hotkey",
                "content1": (
                    "Enter the hotkey you want to use to start the auto clicker."
                ),
                "subtitle2": "Interval",
                "content2": (
                    "Enter the interval in milliseconds, seconds, and/or minutes between each click."
                ),
                "subtitle3": "Location",
                "content3": (
                    "Click the Assign Location button and click on the location on your screen where you want the auto clicker to click."
                ),
                "geometry": "690x365"
            },
            {
                "type": "release",
                "title": "Help | Settings",
                "subtitle1": "Private Server Link",
                "content1": (
                    "1. Go to the private server you want to join\n"
                    "2. Copy the link from the URL bar\n"
                    "3. Paste it into the Private Server Link field in the Settings tab\n"
                    "Note: Private Server link MUST be formatted like this: \n"
                    "https://www.roblox.com/games/1234567890/game_name?privateServerLinkCode=ABC123\n"
                    "You can find this link by opening your private server share URL and\n"
                    "copying the link from the URL bar."
                ),
                "subtitle2": "Assign Menu Buttons",
                "content2": (
                    "1. Click the Assign Menu Buttons button\n"
                    "2. Click the Assign Click button next to the button you want to assign\n"
                    "3. Click on the location on your screen where the button is located\n"
                    "4. Repeat for all buttons\n"
                    "5. Click Save"
                ),
                "subtitle3": "External Macro",
                "content3": (
                    "The Start, Pause, and Stop keys are used to control an additional \n"
                    "external macro you might have running.\n"
                    "These keybinds MUST be set to use the /start, /pause, and /stop \n"
                    "commands in the discord bot."
                ),
                "geometry": "695x600"
            }
        ]

        self.current_page = 0  # Start on the first page

        # Navigation Frame
        navigation_frame = ttk.Frame(self.help_window)
        navigation_frame.grid(row=10, column=0, columnspan=4, pady=10)

        self.prev_button = ttk.Button(navigation_frame, text="Previous", command=self.prev_page)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.next_button = ttk.Button(navigation_frame, text="Next", command=self.next_page)
        self.next_button.grid(row=0, column=1, padx=5)

        close_button = ttk.Button(navigation_frame, text="Close", command=self.help_window.destroy)
        close_button.grid(row=0, column=2, padx=5)

        self.display_current_page()

    def display_current_page(self):
        for widget in self.help_window.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()

        while self.current_page < len(self.help_info) and self.help_info[self.current_page]["type"] == "developer" and not self.config.get("developer", False):
            self.current_page += 1

        if self.current_page >= len(self.help_info):
            self.current_page = len(self.help_info) - 1

        start_index = self.current_page
        end_index = min(start_index + 1, len(self.help_info))
        current_sections = self.help_info[start_index:end_index]

        for section_index, section in enumerate(current_sections):
            section_frame = ttk.LabelFrame(
                self.help_window, 
                text=section["title"], 
                padding=(10, 5)
            )
            section_frame.grid(
                row=section_index, 
                column=0, 
                columnspan=4, 
                padx=10, 
                pady=10, 
                sticky="w"
            )

            if "subtitle1" in section and "content1" in section:
                subtitle1_frame = ttk.LabelFrame(section_frame, text=section["subtitle1"], padding=(5, 5))
                subtitle1_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
                content1_label = ttk.Label(subtitle1_frame, text=section["content1"], wraplength=600, justify="left")
                content1_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
                if "link1" in section:
                    link1_button = ttk.Button(subtitle1_frame, text="Open Tutorial", command=lambda url=section["link1"]: webbrowser.open(url))
                    link1_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")

            if "subtitle2" in section and "content2" in section:
                subtitle2_frame = ttk.LabelFrame(section_frame, text=section["subtitle2"], padding=(5, 5))
                subtitle2_frame.grid(row=1, column=0, padx=10, pady=5, sticky="w")
                content2_label = ttk.Label(subtitle2_frame, text=section["content2"], wraplength=600, justify="left")
                content2_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
                if "link2" in section:
                    link2_button = ttk.Button(subtitle2_frame, text="Open Tutorial", command=lambda url=section["link2"]: webbrowser.open(url))
                    link2_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")

            if "subtitle3" in section and "content3" in section:
                subtitle3_frame = ttk.LabelFrame(section_frame, text=section["subtitle3"], padding=(5, 5))
                subtitle3_frame.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                content3_label = ttk.Label(subtitle3_frame, text=section["content3"], wraplength=600, justify="left")
                content3_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.prev_button["state"] = "normal" if self.current_page > 0 else "disabled"
        self.next_button["state"] = "normal" if start_index + 1 < len(self.help_info) else "disabled"

        # Adjust window size based on content
        if current_sections:
            self.help_window.geometry(current_sections[0]["geometry"])

    def prev_page(self):
        self.current_page -= 1
        while self.current_page >= 0 and self.help_info[self.current_page]["type"] == "developer" and not self.config.get("developer", False):
            self.current_page -= 1
        self.display_current_page()

    def next_page(self):
        self.current_page += 1
        while self.current_page < len(self.help_info) and self.help_info[self.current_page]["type"] == "developer" and not self.config.get("developer", False):
            self.current_page += 1
        self.display_current_page()

    def edit_config_menu(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Edit Config")
        config_window.geometry("635x440")

        # Server Sniper Frame
        serversniper_frame = ttk.LabelFrame(config_window, text="Server Sniper Config")
        serversniper_frame.grid(column=0, row=0, padx=(5, 10), pady=5, sticky="nw")

        # Channel Link Entry
        self.channel_link_label = ttk.Label(serversniper_frame, text="Channel Link:")
        self.channel_link_label.grid(column=0, row=0, sticky="w", padx=5, pady=5)
        self.channel_link_entry = ttk.Entry(serversniper_frame, width=50)
        self.channel_link_entry.grid(column=1, row=0, sticky="w", padx=5, pady=5)
        self.channel_link_entry.insert(0, self.config.get("discord_channel_link", ""))

        # Authorization Key Entry
        self.authorization_key_label = ttk.Label(serversniper_frame, text="Authorization Key:")
        self.authorization_key_label.grid(column=0, row=1, sticky="w", padx=5, pady=5)
        self.authorization_key_entry = ttk.Entry(serversniper_frame, width=50)
        self.authorization_key_entry.grid(column=1, row=1, sticky="w", padx=5, pady=5)
        self.authorization_key_entry.insert(0, self.config.get("authorization_key", ""))

        # Keywords Entry
        self.keywords_label = ttk.Label(serversniper_frame, text="Keywords:")
        self.keywords_label.grid(column=0, row=2, sticky="w", padx=5, pady=5)
        self.keywords_entry = ttk.Entry(serversniper_frame, width=50)
        self.keywords_entry.grid(column=1, row=2, sticky="w", padx=5, pady=5)
        self.keywords_entry.insert(0, self.config.get("keywords", ""))
        

        # Sniping Speed
        self.sniping_speed_label = ttk.Label(serversniper_frame, text="Sniping Speed:")
        self.sniping_speed_label.grid(column=0, row=3, sticky="w", padx=5, pady=5)
        self.sniping_speed_var = tk.StringVar(value=self.config.get("serversniper_speed", "Normal"))

        def on_speed_change():
            speed = self.sniping_speed_var.get()
            if speed == "Fast":
                messagebox.showwarning("Warning", "Using 'Fast' speed could get your account locked.")
            elif speed == "Very Fast":
                messagebox.showwarning("Warning", "Using 'Very Fast' speed could get your account locked or even deleted.")
            self.update_config("serversniper_speed", speed)

        self.normal_speed_radio = ttk.Radiobutton(serversniper_frame, text="Normal", variable=self.sniping_speed_var, value="Normal", command=on_speed_change)
        self.normal_speed_radio.grid(column=1, row=3, sticky="w", padx=5, pady=5)

        self.fast_speed_radio = ttk.Radiobutton(serversniper_frame, text="Fast", variable=self.sniping_speed_var, value="Fast", command=on_speed_change)
        self.fast_speed_radio.grid(column=1, row=3, sticky="w", padx=100, pady=5)

        self.very_fast_speed_radio = ttk.Radiobutton(serversniper_frame, text="Very Fast", variable=self.sniping_speed_var, value="Very Fast", command=on_speed_change)
        self.very_fast_speed_radio.grid(column=1, row=3, sticky="w", padx=175, pady=5)

        # Notifications
        self.notifications_var = tk.BooleanVar(value=self.config.get("enable_notifications", False))
        self.notifications_checkbox = ttk.Checkbutton(
            serversniper_frame,
            text="Enable Notifications",
            variable=self.notifications_var,
            command=lambda: self.update_config("enable_notifications", self.notifications_var.get())
        )
        self.notifications_checkbox.grid(column=0, row=5, padx=5, pady=5, sticky="w")

        # Keybinds
        self.start_key_label = ttk.Label(serversniper_frame, text="Start Key:")
        self.start_key_label.grid(column=0, row=6, sticky="w", padx=5, pady=5)
        self.start_key_entry = ttk.Entry(serversniper_frame, width=10)
        self.start_key_entry.grid(column=1, row=6, sticky="w", padx=5, pady=5)
        self.start_key_entry.insert(0, self.config.get("start_key", "F4"))

        self.pause_key_label = ttk.Label(serversniper_frame, text="Pause Key:")
        self.pause_key_label.grid(column=0, row=7, sticky="w", padx=5, pady=5)
        self.pause_key_entry = ttk.Entry(serversniper_frame, width=10)
        self.pause_key_entry.grid(column=1, row=7, sticky="w", padx=5, pady=5)
        self.pause_key_entry.insert(0, self.config.get("pause_key", "F5"))

        self.stop_key_label = ttk.Label(serversniper_frame, text="Stop Key:")
        self.stop_key_label.grid(column=0, row=8, sticky="w", padx=5, pady=5)
        self.stop_key_entry = ttk.Entry(serversniper_frame, width=10)
        self.stop_key_entry.grid(column=1, row=8, sticky="w", padx=5, pady=5)
        self.stop_key_entry.insert(0, self.config.get("stop_key", "F6"))

        # Save On Focus Out
        self.channel_link_entry.bind("<FocusOut>", lambda e: self.update_config("discord_channel_link", self.channel_link_entry.get()))
        self.authorization_key_entry.bind("<FocusOut>", lambda e: self.update_config("authorization_key", self.authorization_key_entry.get()))
        self.keywords_entry.bind("<FocusOut>", lambda e: self.update_config("keywords", self.keywords_entry.get()))
        self.start_key_entry.bind("<FocusOut>", lambda e: self.update_config("start_key", self.start_key_entry.get()))
        self.pause_key_entry.bind("<FocusOut>", lambda e: self.update_config("pause_key", self.pause_key_entry.get()))
        self.stop_key_entry.bind("<FocusOut>", lambda e: self.update_config("stop_key", self.stop_key_entry.get()))

        navigation_frame = ttk.Frame(config_window)
        navigation_frame.grid(row=10, column=0, columnspan=4, pady=5)
        ttk.Button(navigation_frame, text="Close", command=config_window.destroy).pack(pady=5)

    def start_capture_thread(self, config_key):
        capture_thread = threading.Thread(target=self.capture_mouse_position, args=(config_key,))
        capture_thread.daemon = True
        capture_thread.start()


    def capture_mouse_position(self, config_key):
        if hasattr(self, "capture_window") and self.capture_window.winfo_exists():
            return

        self.capture_window = tk.Toplevel(self.root)
        self.capture_window.attributes("-fullscreen", True)
        self.capture_window.attributes("-alpha", 0.3)
        self.capture_window.config(cursor="cross")

        def on_click(event):
            x, y = event.x_root, event.y_root
            x_var, y_var = self.coord_vars[config_key]
            x_var.set(x)
            y_var.set(y)
            print(f"Captured coordinates for {config_key}: ({x}, {y})")
            self.capture_window.destroy()
            del self.capture_window

        self.capture_window.bind("<Button-1>", on_click)

    def save_coordinates(self):
        for config_key, (x_var, y_var) in self.coord_vars.items():
            self.config[config_key] = [x_var.get(), y_var.get()]

        self.save_config()
        self.assign_menu_window.destroy()
        
    def setup_tabs(self):
        self.tab_control = ttk.Notebook(self.root)
        
        # Define and add tabs to notebook
        self.info_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.info_tab, text="Info")

        self.discord_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.discord_tab, text="Discord")

        self.serversniper_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.serversniper_tab, text="Server Sniper")

        if self.config.get("developer", False):
            self.autoclicker_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.autoclicker_tab, text="Auto Clicker")

        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")

        self.credits_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.credits_tab, text="Credits")

        self.tab_control.pack(expand=1, fill="both")

    def setup_info_tab(self):
        main_frame = ttk.Frame(self.info_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Info Frame
        info_frame = ttk.LabelFrame(main_frame, text="Information")
        info_frame.grid(column=0, row=0, padx=(5, 10), pady=5, sticky="nw")

        # Information Label
        self.info_label = ttk.Label(info_frame, text="Thanks for using SolsBot.", font=("Helvetica", 14, "bold"))
        self.info_label.grid(column=0, row=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Navigation Info Label
        self.navigation_info_label = ttk.Label(info_frame, text="Use the tabs above to navigate through different sections of the GUI.", wraplength=400)
        self.navigation_info_label.grid(column=0, row=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Detailed Navigation Info
        self.detailed_navigation_info_label = ttk.Label(info_frame, text=(
            "Info: Provides general information and navigation tips.\n"
            "Discord: Configure the Discord bot and webhook settings.\n"
            "Server Sniper: Snipe private servers.\n"
            # "Auto Clicker: Automatically click at a specified interval.\n"
            "Settings: Adjust general settings.\n"
            "Credits: View credits and contributors."
        ), wraplength=400, justify="left")
        self.detailed_navigation_info_label.grid(column=0, row=2, columnspan=2, sticky="w", padx=5, pady=5)

        # Bottom Frame
        self.bottom_frame = ttk.Frame(self.root, padding=3)
        self.bottom_frame.pack(fill="x")

        # Help Button
        self.help_button = ttk.Button(self.bottom_frame, text="Help", command=self.open_help_window)
        self.help_button.grid(row=0, column=0, padx=5, sticky="e")

        # Dark Mode Switch
        self.dark_mode_switch = ttk.Checkbutton(self.bottom_frame, text="Dark Mode", style="Switch.TCheckbutton", command=self.toggle_dark_mode)
        self.dark_mode_switch.state(['!alternate'])
        self.dark_mode_switch.grid(row=0, column=10, sticky="e", padx=5)

    def setup_discord_tab(self):
        main_frame = ttk.Frame(self.discord_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Webhook URL
        webhook_frame = ttk.LabelFrame(main_frame, text="Webhook URL")
        webhook_frame.grid(column=0, row=3, padx=(5, 10), pady=5, sticky="nw")
        self.webhook_url_label = ttk.Label(webhook_frame, text="Webhook URL:")
        self.webhook_url_label.grid(column=0, row=3, sticky="w", padx=5, pady=5)
        self.webhook_url_entry = ttk.Entry(webhook_frame, width=50)
        self.webhook_url_entry.grid(column=1, row=3, sticky="w", padx=5, pady=5)
        self.webhook_url_entry.insert(0, self.config.get("WebhookLink", ""))

        # Discord Bot Frame
        discordbot_frame = ttk.LabelFrame(main_frame, text="Discord Bot")
        discordbot_frame.grid(column=0, row=0, padx=(5, 10), pady=5, sticky="nw")

        # Enable Discord Bot Checkbox
        self.enable_discordbot = tk.IntVar(value=self.config.get("DiscordBot_Enabled", 0))
        self.enable_discordbot_checkbox = ttk.Checkbutton(discordbot_frame, text="Enable Discord Bot", variable=self.enable_discordbot,
                                                    command=self.toggle_discordbot_enabled)
        self.enable_discordbot_checkbox.grid(column=0, row=0, columnspan=2, sticky="w")

        # Discord User ID
        self.discordbot_userid_label = ttk.Label(discordbot_frame, text="Your Discord ID:")
        self.discordbot_userid_label.grid(column=0, row=1, sticky="w", padx=5, pady=2)
        self.discordbot_userid_entry = ttk.Entry(discordbot_frame, width=25)
        self.discordbot_userid_entry.grid(column=1, row=1, sticky="w", padx=5, pady=2)
        self.discordbot_userid_entry.insert(0, self.config.get("DiscordBot_UserID", ""))

        # Discord Token Entry (without validation)
        self.discordbot_token_label = ttk.Label(discordbot_frame, text="Discord Bot Token:")
        self.discordbot_token_label.grid(column=0, row=2, sticky="w", padx=5, pady=2)
        self.discordbot_token_entry = ttk.Entry(discordbot_frame, width=25)
        self.discordbot_token_entry.grid(column=1, row=2, sticky="w", padx=5, pady=2)
        self.discordbot_token_entry.insert(0, self.config.get("DiscordBot_Token", ""))

        # Command Info Button
        discordbot_cmd_info = ttk.Button(discordbot_frame, text="Command Info", command=self.discordbot_cmd_info_popup)
        discordbot_cmd_info.grid(column=1, row=0, padx=5, pady=2)

        # Update inputs directly on focus out
        self.discordbot_token_entry.bind("<FocusOut>", lambda e: self.update_config("DiscordBot_Token", self.discordbot_token_entry.get()))
        self.discordbot_userid_entry.bind("<FocusOut>", lambda e: self.update_config("DiscordBot_UserID", self.discordbot_userid_entry.get()))
        self.webhook_url_entry.bind("<FocusOut>", lambda e: self.update_config("WebhookLink", self.webhook_url_entry.get()))

    def discordbot_cmd_info_popup(self):
        discordbot_info = tk.Toplevel(self.root)
        discordbot_info.title("Discord Bot Commands")
        discordbot_info.geometry("630x300")

        discordbot_commands = """
        /start - Starts an external macro
        /stop - Stops an external macro
        /pause - Toggles pause for an external macro
        /ping - Gets the bot's latency (response time)
        /screenshot - Sends a screenshot of whatever is on the screen
        /chat <message> - Sends a message to the roblox chat
        """
        tk.Label(discordbot_info, text="Discord Bot Commands", font=("Helvetica", 14, "bold")).pack(pady=10)
        tk.Label(discordbot_info, text=discordbot_commands, justify="left", anchor="w").pack(padx=10, pady=10, fill="both", expand=True)
        ttk.Button(discordbot_info, text="Close", command=discordbot_info.destroy).pack(pady=10)

    def setup_serversniper_tab(self):
        main_frame = ttk.Frame(self.serversniper_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Main Frame
        sniper_frame = ttk.LabelFrame(main_frame, text="Server Sniper")
        sniper_frame.grid(column=0, row=0, padx=(5, 10), pady=5, sticky="nw")
    
        start_button = ttk.Button(sniper_frame, text="Start Script", command=self.start_script_with_status)
        start_button.grid(column=0, row=0, padx=5, pady=5)

        pause_button = ttk.Button(sniper_frame, text="Pause Script", command=self.pause_script_with_status)
        pause_button.grid(column=1, row=0, padx=5, pady=5)

        stop_button = ttk.Button(sniper_frame, text="Stop Script", command=self.stop_script_with_status)
        stop_button.grid(column=2, row=0, padx=5, pady=5)

        edit_config_button = ttk.Button(sniper_frame, text="Edit Configuration", command=self.edit_config_menu)
        edit_config_button.grid(column=3, row=0, padx=5, pady=5)

        self.serversniper_status = ttk.Label(sniper_frame, text="Status: ", font=("Helvetica", 12, "bold"))
        self.serversniper_status.grid(column=0, row=1, padx=5, pady=5, sticky="w")

        self.status_value = ttk.Label(sniper_frame, text="Stopped", font=("Helvetica", 12, "bold"), foreground="red")
        self.status_value.grid(column=1, row=1, padx=5, pady=5, sticky="w")

        # Sniped Message Frame
        sniped_message_frame = ttk.LabelFrame(main_frame, text="Last Sniped Message:")
        sniped_message_frame.grid(column=0, row=2, padx=(5, 10), pady=5, sticky="nw")

        self.recent_message_text = tk.Text(sniped_message_frame, height=4, width=50, wrap="word")
        self.recent_message_text.grid(column=0, row=3, columnspan=4, padx=5, pady=5)
        self.recent_message_text.config(state=tk.DISABLED)
        self.recent_message_text.tag_configure("bold", font=("Helvetica", 10, "bold"))

        start_key = self.config.get("start_key", "F4")
        pause_key = self.config.get("pause_key", "F5")
        stop_key = self.config.get("stop_key", "F6")

        self.root.bind(f"<{start_key}>", lambda e: self.start_script_with_status())
        self.root.bind(f"<{pause_key}>", lambda e: self.pause_script_with_status())
        self.root.bind(f"<{stop_key}>", lambda e: self.stop_script_with_status())

    def start_script_with_status(self):
        start_script(self.update_status, self.update_recent_message)

    def pause_script_with_status(self):
        pause_script(self.update_status)

    def stop_script_with_status(self):
        stop_script(self.update_status)

    def update_status(self, status):
        if status == "Running":
            self.status_value.config(text="Running", foreground="green")
        elif status == "Paused":
            self.status_value.config(text="Paused", foreground="yellow")
        else:
            self.status_value.config(text="Stopped", foreground="red")

    def update_recent_message(self, username, message):
        self.recent_message_text.config(state=tk.NORMAL)
        self.recent_message_text.delete(1.0, tk.END)
        self.recent_message_text.insert(tk.END, f"{username}:\n", "bold")
        self.recent_message_text.insert(tk.END, f"{message}")
        self.recent_message_text.config(state=tk.DISABLED)
        self.recent_message_text.see(tk.END)

    def setup_autoclicker_tab(self):
        main_frame = ttk.Frame(self.autoclicker_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Hotkey Frame
        self.hotkey_frame = ttk.LabelFrame(main_frame, text="Hotkey")
        self.hotkey_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Hotkey Configuration
        ttk.Label(self.hotkey_frame, text="Hotkey:").grid(row=0, column=0, padx=10, pady=5)
        self.hotkey_entry = ttk.Entry(self.hotkey_frame, width=10)
        self.hotkey_entry.grid(row=0, column=1, padx=5, pady=5)
        self.hotkey_entry.insert(0, self.config.get("autoclicker_hotkey", "F7"))
        self.hotkey_entry.bind("<FocusOut>", lambda e: self.update_config("autoclicker_hotkey", self.hotkey_entry.get()))

        # Delay Frame
        self.delay_frame = ttk.LabelFrame(main_frame, text="Delay")
        self.delay_frame.grid(column=0, row=1, padx=10, pady=10, sticky="nw")

        # Delay Input Boxes
        ttk.Label(self.delay_frame, text="Minutes:").grid(row=0, column=0, padx=10, pady=5)
        self.delay_minutes = ttk.Entry(self.delay_frame, width=5)
        self.delay_minutes.grid(row=0, column=1, padx=5, pady=5)
        self.delay_minutes.insert(0, self.config.get("autoclicker_delay_minutes", "0"))
        self.delay_minutes.bind("<FocusOut>", lambda e: self.update_config("autoclicker_delay_minutes", self.delay_minutes.get()))

        ttk.Label(self.delay_frame, text="Seconds:").grid(row=1, column=0, padx=10, pady=5)
        self.delay_seconds = ttk.Entry(self.delay_frame, width=5)
        self.delay_seconds.grid(row=1, column=1, padx=5, pady=5)
        self.delay_seconds.insert(0, self.config.get("autoclicker_delay_seconds", "1"))
        self.delay_seconds.bind("<FocusOut>", lambda e: self.update_config("autoclicker_delay_seconds", self.delay_seconds.get()))

        ttk.Label(self.delay_frame, text="Milliseconds:").grid(row=2, column=0, padx=10, pady=5)
        self.delay_milliseconds = ttk.Entry(self.delay_frame, width=5)
        self.delay_milliseconds.grid(row=2, column=1, padx=5, pady=5)
        self.delay_milliseconds.insert(0, self.config.get("autoclicker_delay_milliseconds", "0"))
        self.delay_milliseconds.bind("<FocusOut>", lambda e: self.update_config("autoclicker_delay_milliseconds", self.delay_milliseconds.get()))

        # Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Auto Clicker Status")
        status_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=10, sticky="nw")

        self.autoclicker_status = ttk.Label(status_frame, text="Status: ", font=("Helvetica", 12, "bold"))
        self.autoclicker_status.grid(column=0, row=0, padx=5, pady=5, sticky="w")

        self.status_value = ttk.Label(status_frame, text="Off", font=("Helvetica", 12, "bold"), foreground="red")
        self.status_value.grid(column=1, row=0, padx=5, pady=5, sticky="w")

        # Location Frame
        self.location_frame = ttk.LabelFrame(main_frame, text="Location")
        self.location_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nw")

        # Fixed Location Option
        self.fixed_location_var = tk.BooleanVar(value=self.config.get("autoclicker_fixed_location", False))
        self.fixed_location_checkbox = ttk.Checkbutton(self.location_frame, text="Fixed Location", variable=self.fixed_location_var)
        self.fixed_location_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.fixed_location_checkbox.bind("<FocusOut>", lambda e: self.update_config("autoclicker_fixed_location", self.fixed_location_var.get()))

        self.assign_button = ttk.Button(self.location_frame, text="Assign Click", command=self.ac_start_capture_thread)
        self.assign_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.x_coord_label = ttk.Label(self.location_frame, text="X Coord:")
        self.y_coord_label = ttk.Label(self.location_frame, text="Y Coord:")
        self.x_coord_entry = ttk.Entry(self.location_frame, width=10)
        self.y_coord_entry = ttk.Entry(self.location_frame, width=10)

        self.x_coord_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.x_coord_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.x_coord_entry.insert(0, self.config.get("autoclicker_x_coord", "0"))
        self.x_coord_entry.bind("<FocusOut>", lambda e: self.update_config("autoclicker_x_coord", self.x_coord_entry.get()))

        self.y_coord_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.y_coord_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.y_coord_entry.insert(0, self.config.get("autoclicker_y_coord", "0"))
        self.y_coord_entry.bind("<FocusOut>", lambda e: self.update_config("autoclicker_y_coord", self.y_coord_entry.get()))

        # Control Frame
        self.control_frame = ttk.LabelFrame(main_frame, text="Controls")
        self.control_frame.grid(row=2, column=1, columnspan=2, pady=10)

        # Control Buttons
        self.start_button = ttk.Button(self.control_frame, text="Start", command=self.toggle_autoclicker)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(self.control_frame, text="Stop", command=self.toggle_autoclicker)
        self.stop_button.grid(row=0, column=1, padx=5)

        self.update_autoclicker_status()

    def ac_start_capture_thread(self):
        capture_thread = threading.Thread(target=self.ac_capture_mouse_position)
        capture_thread.daemon = True
        capture_thread.start()

    def ac_capture_mouse_position(self):
        if hasattr(self, "capture_window") and self.capture_window.winfo_exists():
            return

        self.capture_window = tk.Toplevel(self.root)
        self.capture_window.attributes("-fullscreen", True)
        self.capture_window.attributes("-alpha", 0.3)
        self.capture_window.config(cursor="cross")

        def on_click(event):
            self.x_coord_entry.delete(0, tk.END)
            self.x_coord_entry.insert(0, event.x)
            self.y_coord_entry.delete(0, tk.END)
            self.y_coord_entry.insert(0, event.y)
            self.capture_window.destroy()

        self.capture_window.bind("<Button-1>", on_click)

    def update_autoclicker_status(self):
        status = "On" if hasattr(self, 'autoclicker') and self.autoclicker.running else "Off"
        color = "green" if status == "On" else "red"
        self.status_value.config(text=status, foreground=color)

    def toggle_autoclicker(self):
        if hasattr(self, 'autoclicker') and self.autoclicker.running:
            self.stop_autoclicker()
        else:
            self.start_autoclicker()

    def start_autoclicker(self):
        delay = (int(self.delay_minutes.get() or 0) * 60 +
                 int(self.delay_seconds.get() or 0) +
                 int(self.delay_milliseconds.get() or 0) / 1000.0)
        fixed_position = (int(self.x_coord_entry.get()), int(self.y_coord_entry.get())) if self.fixed_location_var.get() else None

        self.update_config("autoclicker_delay_minutes", self.delay_minutes.get())
        self.update_config("autoclicker_delay_seconds", self.delay_seconds.get())
        self.update_config("autoclicker_delay_milliseconds", self.delay_milliseconds.get())
        self.update_config("autoclicker_hotkey", self.hotkey_entry.get())
        self.update_config("autoclicker_fixed_location", self.fixed_location_var.get())
        self.update_config("autoclicker_x_coord", self.x_coord_entry.get())
        self.update_config("autoclicker_y_coord", self.y_coord_entry.get())

        config_path = "config.json"
        self.autoclicker = AutoClicker(config_path)
        self.autoclicker.start_listener()
        self.update_autoclicker_status()

    def stop_autoclicker(self):
        if hasattr(self, 'autoclicker'):
            self.autoclicker.exit()
        self.update_autoclicker_status()

    def setup_settings_tab(self):
        main_frame = ttk.Frame(self.settings_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)
        general_frame = ttk.LabelFrame(main_frame, text="General")
        general_frame.grid(column=0, row=0, padx=5, pady=5, sticky="nw")

        # Private Server Link
        ttk.Label(general_frame, text="Private Server Link:").grid(column=0, row=0, padx=5, pady=5, sticky="w")
        self.server_link_var = tk.StringVar(value=self.config.get("PrivateServerLink", ""))
        self.server_link_entry = ttk.Entry(general_frame, textvariable=self.server_link_var, width=50)
        self.server_link_entry.grid(column=1, row=0, padx=5, pady=5, sticky="w")
        self.server_link_entry.bind("<FocusOut>", self.validate_and_save_ps_link)

        macro_frame = ttk.LabelFrame(main_frame, text="External Macro")
        macro_frame.grid(column=0, row=3, padx=5, pady=5, sticky="nw")

        # External Macro Keybinds
        ttk.Label(macro_frame, text="Start Key:").grid(column=0, row=3, padx=5, pady=5, sticky="w")
        self.macro_start_key_var = tk.StringVar(value=self.config.get("macro_start_key", "F1"))
        self.macro_start_key_entry = ttk.Entry(macro_frame, textvariable=self.macro_start_key_var, width=10)
        self.macro_start_key_entry.grid(column=1, row=3, padx=5, pady=5, sticky="w")
        self.macro_start_key_entry.bind("<FocusOut>", lambda e: self.update_config("macro_start_key", self.macro_start_key_entry.get()))

        ttk.Label(macro_frame, text="Pause Key:").grid(column=2, row=3, padx=5, pady=5, sticky="w")
        self.macro_pause_key_var = tk.StringVar(value=self.config.get("macro_pause_key", "F2"))
        self.macro_pause_key_entry = ttk.Entry(macro_frame, textvariable=self.macro_pause_key_var, width=10)
        self.macro_pause_key_entry.grid(column=3, row=3, padx=5, pady=5, sticky="w")
        self.macro_pause_key_entry.bind("<FocusOut>", lambda e: self.update_config("macro_pause_key", self.macro_pause_key_entry.get()))

        ttk.Label(macro_frame, text="Stop Key:").grid(column=4, row=3, padx=5, pady=5, sticky="w")
        self.macro_stop_key_var = tk.StringVar(value=self.config.get("macro_stop_key", "F3"))
        self.macro_stop_key_entry = ttk.Entry(macro_frame, textvariable=self.macro_stop_key_var, width=10)
        self.macro_stop_key_entry.grid(column=5, row=3, padx=5, pady=5, sticky="w")
        self.macro_stop_key_entry.bind("<FocusOut>", lambda e: self.update_config("macro_stop_key", self.macro_stop_key_entry.get()))
        
        import_button = ttk.Button(general_frame, text="Import Settings", command=self.import_settings)
        import_button.grid(column=0, row=4, padx=5, pady=5, sticky="w")

        # Assign Menu Button
        self.assign_menu_button = ttk.Button(general_frame, text="Assign Menu Buttons", command=self.open_assign_menu_window)
        self.assign_menu_button.grid(column=1, row=4, sticky="w", padx=5, pady=5)
    
    def setup_credits_tab(self):
        main_frame = ttk.Frame(self.credits_tab)
        main_frame.pack(expand=1, fill="both", padx=5, pady=5)
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Creator Section
        creator_frame = ttk.LabelFrame(main_frame, text="The Creator")
        creator_frame.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        creator_frame.grid_columnconfigure(0, weight=1)

        creator_image = Image.open("images/vexthecoder.png")
        creator_image = creator_image.resize((50, 50), Image.LANCZOS)
        creator_photo = ImageTk.PhotoImage(creator_image)
        
        creator_image_label = ttk.Label(creator_frame, image=creator_photo)
        creator_image_label.image = creator_photo 
        creator_image_label.grid(column=0, row=0, padx=5, pady=5, sticky="n")

        creator_label = ttk.Label(creator_frame, text="vex\n'Dumbass Developer'", justify="center", font=("Helvetica", 9))
        creator_label.grid(column=0, row=1, padx=5, pady=5, sticky="n")

        # Inspired by Section
        inspired_frame = ttk.LabelFrame(main_frame, text="Inspired by")
        inspired_frame.grid(column=1, row=0, padx=5, pady=5, sticky="nsew")
        inspired_frame.grid_columnconfigure(0, weight=1)

        noteab_image = Image.open("images/noteab.png")
        noteab_image = noteab_image.resize((50, 50), Image.LANCZOS)
        noteab_photo = ImageTk.PhotoImage(noteab_image)
        
        noteab_image_label = ttk.Label(inspired_frame, image=noteab_photo)
        noteab_image_label.image = noteab_photo
        noteab_image_label.grid(column=0, row=0, padx=5, pady=5, sticky="n")

        inspired_label = ttk.Label(inspired_frame, text="Noteab\n'Ordinary Solo Developer'", justify="center", font=("Helvetica", 9))
        inspired_label.grid(column=0, row=1, padx=5, pady=5, sticky="n")

        # Other
        other_frame = ttk.LabelFrame(main_frame, text="Other")
        other_frame.grid(column=0, row=1, padx=5, pady=5, sticky="nsew", columnspan=2)
        
        discord_link = ttk.Label(other_frame, text="My Roblox Profile (pls follow)", foreground="#1E90FF", cursor="hand2", font=("Helvetica", 9))
        discord_link.grid(column=0, row=0, padx=5, pady=5, sticky="w")
        discord_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.roblox.com/users/682980257/profile"))

        github_link = ttk.Label(other_frame, text="Visit the source code on GitHub!", foreground="#1E90FF", cursor="hand2", font=("Helvetica", 9))
        github_link.grid(column=0, row=1, padx=5, pady=5, sticky="w")
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/vexthecoder/SolsBot"))


        extras_button = ttk.Button(other_frame, text="Extras Credit", command=self.show_extras_credit)
        extras_button.grid(column=0, row=2, padx=5, pady=5, sticky="w")

    def show_extras_credit(self):
        extras_window = tk.Toplevel(self.root)
        extras_window.title("Extras Credit")
        extras_window.geometry("450x450")

        contributors_frame = ttk.LabelFrame(extras_window, text="Contributors (Development)")
        contributors_frame.pack(fill="both", expand=True, padx=10, pady=10)

        contributors = [
            "vexthecoder -",
            "Everything",
            "",
            "Noteab -",
            "Original Source Code"
        ]

        for contributor in contributors:
            ttk.Label(contributors_frame, text=contributor).pack(pady=2)
        
        testers_frame = ttk.LabelFrame(extras_window, text="SolsBot Testers")
        testers_frame.pack(fill="both", expand=True, padx=10, pady=10)

        testers = [
            "vexthecoder - vex"
        ]

        for tester in testers:
            ttk.Label(testers_frame, text=tester).pack(pady=2)
        
    def toggle_dark_mode(self):
        current_geometry = self.root.geometry()
        
        if self.dark_mode:
            self.root.tk.call("set_theme", "light")
            self.root.configure(bg="#FFFFFF")
            self.dark_mode_switch.config(text="Light Mode")
        else:
            self.root.tk.call("set_theme", "dark")
            self.root.configure(bg="#2C2F33")
            self.dark_mode_switch.config(text="Dark Mode")
        
        self.root.geometry(current_geometry)
        self.dark_mode = not self.dark_mode
        
    def auto_resize(self):
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}")
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"+{x}+{y}")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = DiscordMacroUI(root)
    root.mainloop()
