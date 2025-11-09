import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from gui.main_screen import MainScreen
from gui.admin_screen import MainScreen
from core.rfid_manager import RFIDManager
from core.account_manager import AccountManager

kivy.require("2.3.0")
#Window.size = (800, 480)
Window.size = 'auto'

class KaffeeKasseApp(App):
    def build(self):
        Builder.load_file("gui/mainscreen.kv")
        self.account_manager = AccountManager()
        self.main_screen = MainScreen()
        self.rfid_manager = RFIDManager()
        self.rfid_manager.set_callback(self.on_rfid_scan)
        Clock.schedule_interval(lambda dt: self.rfid_manager.check_for_card(), 0.5)
        return self.main_screen

    def on_rfid_scan(self, uid: str):
        print(f"RFID gescannt: {uid}")
        self.main_screen.load_account(uid)

if __name__ == "__main__":
    KaffeeKasseApp().run()