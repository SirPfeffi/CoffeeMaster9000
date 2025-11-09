import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition

# Eigene Module
from gui.mainscreen import MainScreen
from gui.adminscreen import AdminScreen
from core.rfid_manager import RFIDManager
from core.account_manager import AccountManager

# Setup
kivy.require("2.3.0")
Window.size = (800, 480)

class CoffeeMasterApp(App):
    def build(self):

        # KV-Dateien laden
        #Builder.load_file("src/gui/theme.kv")
        
        root = Builder.load_file("src/gui/main.kv")

        #Builder.load_file("src/gui/mainscreen.kv")
        #Builder.load_file("src/gui/adminscreen.kv")
            
        #screen_manager = root.ids.screenmanager

        #self.mainscreen = MainScreen(name="mainscreen")    # <-- MANUELLE ERSTELLUNG
        #self.adminscreen = AdminScreen(name="adminscreen")  # <-- MANUELLE ERSTELLUNG

        #screen_manager.add_widget(self.mainscreen)       # <-- HINZUFÜGEN
        #screen_manager.add_widget(self.adminscreen)      # <-- HINZUFÜGEN

        #screen_manager.current = "mainscreen"

        #root.theme = root.ids.theme

        # Manager für Logik
        self.account_manager = AccountManager()
        self.rfid_manager = RFIDManager()
        self.rfid_manager.set_callback(self.on_rfid_scan)
        Clock.schedule_interval(lambda dt: self.rfid_manager.check_for_card(), 0.5)

        return root

    def on_rfid_scan(self, uid: str):
        print(f"RFID gescannt: {uid}")
        # Beispielhafte Admin-UIDs
        admin_uids = ["ADMIN1234", "04A1B2C3D4"]

        if uid in admin_uids:
            print("→ Adminmodus aktiviert")
            self.root.current = "adminscreen"
        else:
            self.root.get_screen("mainscreen").load_account(uid)

    def switch_to_main(self):
        self.root.current = "mainscreen"


if __name__ == "__main__":
    CoffeeMasterApp().run()
