import logging
import os

import kivy
from kivy.config import Config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

kivy.require("2.3.1")
keyboard_mode = os.environ.get("COFFEEMASTER_KIVY_KEYBOARD_MODE", "dock").strip().lower()
if keyboard_mode not in {"system", "dock", "multi", "systemanddock", "systemandmulti"}:
    logger.warning("Invalid COFFEEMASTER_KIVY_KEYBOARD_MODE=%s; fallback to dock", keyboard_mode)
    keyboard_mode = "dock"
Config.set("kivy", "keyboard_mode", keyboard_mode)
Config.set("kivy", "keyboard_layout", os.environ.get("COFFEEMASTER_KIVY_KEYBOARD_LAYOUT", "qwertz"))
# Prevent duplicate touch events from touch+mouse emulation on kiosk screens.
Config.set(
    "input",
    "mouse",
    os.environ.get("COFFEEMASTER_KIVY_MOUSE_INPUT", "mouse,disable_on_activity"),
)

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from core.machine_sync_manager import MachineSyncManager
from core.rfid_manager import RFIDManager
from db.models import init_db
from gui.admin_screen import AdminScreen
from gui.main_screen import MainScreen
from gui.user_management_screen import UserManagementScreen

Window.fullscreen = os.environ.get("COFFEEMASTER_KIVY_FULLSCREEN", "auto")


class KaffeeKasseApp(App):
    def build(self):
        init_db()
        logger.info("Database initialized")

        Builder.load_file("gui/main_screen.kv")
        Builder.load_file("gui/admin_screen.kv")

        sm = ScreenManager()
        self.main_screen = MainScreen(name="main")
        self.admin_screen = AdminScreen(name="admin")
        self.user_management_screen = UserManagementScreen(name="user_management")

        sm.add_widget(self.main_screen)
        sm.add_widget(self.admin_screen)
        sm.add_widget(self.user_management_screen)

        self.rfid_manager = RFIDManager()
        if self.rfid_manager.is_hardware_available():
            logger.info("RFID hardware detected")
            self.rfid_manager.set_callback(self.on_rfid_scan)
            Clock.schedule_interval(lambda dt: self.rfid_manager.check_for_card(), 0.5)
        else:
            logger.info("No RFID hardware detected. Running in simulation mode.")

        self.machine_sync = MachineSyncManager.from_env()
        if self.machine_sync.enabled:
            logger.info("WE8 sync enabled")
            Clock.schedule_interval(lambda dt: self.poll_machine_sync(), 30)
        else:
            logger.info("WE8 sync disabled")

        return sm

    def on_rfid_scan(self, uid: str):
        logger.info("RFID scanned: %s", uid)
        self.main_screen.on_rfid(uid)

    def poll_machine_sync(self):
        events = self.machine_sync.poll_once()
        for event in events:
            logger.info("Machine sync event: %s", event)


if __name__ == "__main__":
    KaffeeKasseApp().run()
