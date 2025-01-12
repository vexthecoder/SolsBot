import time
import threading
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, KeyCode
import json
import os

class AutoClicker:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.running = False
        self.program_running = True
        self.mouse = Controller()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def load_config(self, config_path):
        with open(config_path, "r") as file:
            config = json.load(file)
        self.delay = (int(config.get("autoclicker_delay_minutes", 0)) * 60 +
                      int(config.get("autoclicker_delay_seconds", 0)) +
                      int(config.get("autoclicker_delay_milliseconds", 0)) / 1000.0)
        self.button = Button.left
        self.start_stop_key = KeyCode(char=config.get("autoclicker_hotkey", "Delete"))
        self.stop_key = KeyCode(char='b')  # You can change this to another key if needed
        self.fixed_position = (int(config.get("autoclicker_x_coord", 0)), int(config.get("autoclicker_y_coord", 0))) if config.get("autoclicker_fixed_location", False) else None

    def start_clicking(self):
        self.running = True

    def stop_clicking(self):
        self.running = False

    def exit(self):
        self.stop_clicking()
        self.program_running = False

    def run(self):
        while self.program_running:
            while self.running:
                if self.fixed_position:
                    self.mouse.position = self.fixed_position
                self.mouse.click(self.button)
                time.sleep(self.delay)
            time.sleep(0.1)

    def on_press(self, key):
        if key == self.start_stop_key:
            if self.running:
                self.stop_clicking()
            else:
                self.start_clicking()
        elif key == self.stop_key:
            self.exit()
            return False

    def start_listener(self):
        with Listener(on_press=self.on_press) as listener:
            listener.join()