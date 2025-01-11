import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re, os, sys, json, threading, time, pyautogui, webbrowser, requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import threading

from pynput import mouse, keyboard
from PIL import ImageGrab, Image, ImageDraw, ImageTk
from modules.discord_bot import start_bot
from modules.server_sniper import start_script, stop_script, pause_script
 
class DiscordMacroUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SolsBot UI | Pre-v1")
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
        self.setup_settings_tab()
        self.setup_credits_tab()
        self.auto_resize()

        # Variable for eon1 record and replay custom path 
        self.listener = None
        self.record_thread = None
        self.replay_thread = None
        self.is_replaying = False
        self.current_page = 0
        self.sub_paths = [f"Sub-Path {i + 1}" for i in range(8)]
        
        # item scheduler:
        self.scheduler_entries = []
        self.entry_vars = []
        self.entry_widgets = []
        self.available_items = ["Strange Controller", "Biome Randomizer", "Lucky Potion", "Speed Potion", 
                                "Fortune Potion I", "Fortune Potion II", "Fortune Potion III", 
                                "Haste Potion I", "Haste Potion II", "Haste Potion III", "Warp Potion",
                                 "Transcendant Potion", "Heavenly Potion I", "Heavenly Potion II", 
                                "Merchant Teleport", "Oblivion Potion", "Pump King's Blood"]
        
        #~ assign buttons:
        self.coord_vars = {}
        
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

            self.system_message("Settings imported successfully! Please restart the macro to take effect :3")
        except Exception as e:
            self.system_message(f"Error importing settings: {str(e)}")
        
    #?? Start and stop macro loop goober ##
    #& what kind of this fr*nch keyboard .-.
    
    def get_key_bindings(self):
        azerty_keyboard = self.config.get("AZERTY_Keyboard", False)
        if azerty_keyboard:
            return {'record_start': 'o', 'record_stop': 'p', 'replay_start': 'l', 'replay_stop': 'm'}
        return {'record_start': '[', 'record_stop': ']', 'replay_start': ';', 'replay_stop': "'"}

    def start_key_listener(self):
        def on_press(key):
            try:
                start_key = self.config.get("start_key", "F1")
                pause_key = self.config.get("pause_key", "F2")
                stop_key = self.config.get("stop_key", "F3")

                if hasattr(key, 'char') and key.char == start_key.lower():
                    start_script()
                elif hasattr(key, 'char') and key.char == pause_key.lower():
                    pause_script()
                elif hasattr(key, 'char') and key.char == stop_key.lower():
                    stop_script()
            except Exception as e:
                print(f"Error handling key press: {e}")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    
    def load_from_json(self):
        try:
            with open("config.json", "r") as file:
                data = json.load(file)
                self.scheduler_entries = data.get("item_scheduler", [])
                
                for entry in self.scheduler_entries:
                    entry.setdefault("item", self.available_items[0])
                    entry.setdefault("quantity", 1)
                    entry.setdefault("frequency", 1)
                    entry.setdefault("frequency_unit", "Minutes")
                    entry.setdefault("biome", "Any")

        except (FileNotFoundError, json.JSONDecodeError):
            self.scheduler_entries = [
                {"item": self.available_items[0], "quantity": 1, "frequency": 1, "frequency_unit": "Minutes", "biome": "Any"}
            ]

        self.refresh_itemscheduler_ui()

    def save_to_json(self):
        try:
            try:
                with open("config.json", "r") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}

            data["item_scheduler"] = self.scheduler_entries

            with open("config.json", "w") as file:
                json.dump(data, file, indent=4)

        except Exception as e:
            print(f"Error saving to config.json: {e}")
    
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
        else:
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
                "name": "Misc.",
                "buttons": {
                    "Open Chat Button": "open_chat_button_location",
                    "Chat Box (Upper Most Left Corner)": "chat_box_location"
                }
            }
        ]

        self.current_page = 0  # Start on the first page
        self.coord_vars = {}

        # Save and navigation buttons
        navigation_frame = ttk.Frame(self.assign_menu_window)
        navigation_frame.grid(row=10, column=0, columnspan=4, pady=10)

        self.prev_button = ttk.Button(navigation_frame, text="Previous", command=self.prev_page)
        self.prev_button.grid(row=0, column=0, padx=5)
        
        self.next_button = ttk.Button(navigation_frame, text="Next", command=self.next_page)
        self.next_button.grid(row=0, column=1, padx=5)

        save_button = ttk.Button(navigation_frame, text="Save", command=self.save_coordinates)
        save_button.grid(row=0, column=2, padx=5)


        self.display_current_page()

    def open_help_window1(self):
        help_window1 = tk.Toplevel(self.root)
        help_window1.title("Help Window")
        help_window1.geometry("630x300")

        help_window1_info = """
        There is no info to give for this page.
        """
        tk.Label(help_window1, text="Help", font=("Helvetica", 14, "bold")).pack(pady=10)
        tk.Label(help_window1, text=help_window1_info, justify="left", anchor="w").pack(padx=10, pady=10, fill="both", expand=True)
        ttk.Button(help_window1, text="Close", command=help_window1.destroy).pack(pady=10)
        
    def open_help_window2(self):
        help_window2 = tk.Toplevel(self.root)
        help_window2.title("Help Window | Discord")
        help_window2.geometry("630x300")

        help_window2_info = """
        How to setup the Webhook tab.
        1. Enable Webhook: Check this box to enable the webhook functionality.
        2. Webhook URL: Enter your Discord webhook URL here.
        3. Discord User ID (Pings): Enter the Discord User ID for pings.
        4. Discord User/Role ID Glitch Biome Ping: Enter the User/Role ID for glitch biome pings.
        """

        tk.Label(help_window2, text="Help", font=("Helvetica", 14, "bold")).pack(pady=10)
        tk.Label(help_window2, text=help_window2_info, justify="left", anchor="w").pack(padx=10, pady=10, fill="both", expand=True)
        ttk.Button(help_window2, text="Close", command=help_window2.destroy).pack(pady=10)

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

    def display_current_page(self):
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

    def prev_page(self):
        self.current_page -= 1
        self.display_current_page()

    def next_page(self):
        self.current_page += 1
        self.display_current_page()
    

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
    
    def navigate_paths(self, direction):
        new_page = self.current_page + direction
        if 0 <= new_page <= (len(self.sub_paths) - 1) // 4:
            self.current_page = new_page
            self.update_displayed_paths()
    
    def find_file(self, base_path, filename):
        for root, _, files in os.walk(base_path):
            if filename in files:
                return os.path.join(root, filename)
        return None
        
    def setup_tabs(self):
        self.tab_control = ttk.Notebook(self.root)
        
        # Define notebook
        self.info_tab = ttk.Frame(self.tab_control)
        self.discord_tab = ttk.Frame(self.tab_control)
        self.serversniper_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)
        self.credits_tab = ttk.Frame(self.tab_control)

        # Add tabs to the notebook
        self.tab_control.add(self.info_tab, text="Info")
        self.tab_control.add(self.discord_tab, text="Discord")
        self.tab_control.add(self.serversniper_tab, text="Server Sniper")
        self.tab_control.add(self.settings_tab, text="Settings")
        self.tab_control.add(self.credits_tab, text="Credits")
        self.tab_control.pack(expand=1, fill="both")

    def setup_info_tab(self):
        main_frame = ttk.Frame(self.info_tab)
        main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Info Frame
        info_frame = ttk.LabelFrame(main_frame, text="Information")
        info_frame.grid(column=0, row=0, padx=(5, 10), pady=5, sticky="nw")

        # Information Label
        self.info_label = ttk.Label(info_frame, text="Thanks for using SolsBot.\nThis page is mostly info on how to set up the app.\nIf you are still confused, please feel free to ask in my DMs (vexthecoder).\nYou may also click the Help button on each tab for more information.")
        self.info_label.grid(column=0, row=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Assign Menu Button
        self.assign_menu_button = ttk.Button(info_frame, text="Assign Menu Buttons", command=self.open_assign_menu_window)
        self.assign_menu_button.grid(column=0, row=2, sticky="w", padx=5, pady=5)

        # Bottom Frame
        self.bottom_frame = ttk.Frame(self.root, padding=3)
        self.bottom_frame.pack(fill="x")

        # Help Button
        self.help_button = ttk.Button(self.bottom_frame, text="Help", command=self.open_help_window1)
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
        /rejoin - Rejoin your private server
        /screenshot - Sends a screenshot of whatever is on the screen
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
