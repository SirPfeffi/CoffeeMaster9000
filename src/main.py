import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from gui.main_screen import MainScreen
from gui.admin_screen import AdminScreen
from gui.user_management_screen import UserManagementScreen
from core.rfid_manager import RFIDManager
from core.account_manager import AccountManager
from db.models import init_db
import logging

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

kivy.require("2.3.0")
Window.fullscreen = 'auto'

class KaffeeKasseApp(App):
    def build(self):
        # Datenbank initialisieren
        init_db()
        logger.info("Datenbank initialisiert")
        
        # KV-Dateien laden
        Builder.load_file("gui/main_screen.kv")
        Builder.load_file("gui/admin_screen.kv")
        
        # ScreenManager erstellen
        sm = ScreenManager()
        
        # Screens erstellen und hinzufügen
        self.main_screen = MainScreen(name='main')
        self.admin_screen = AdminScreen(name='admin')
        self.user_management_screen = UserManagementScreen(name='user_management')
        
        sm.add_widget(self.main_screen)
        sm.add_widget(self.admin_screen)
        sm.add_widget(self.user_management_screen)
        
        # RFID Manager initialisieren (nur einmal!)
        self.rfid_manager = RFIDManager()
        
        if self.rfid_manager.is_hardware_available():
            logger.info("RFID-Hardware erkannt")
            self.rfid_manager.set_callback(self.on_rfid_scan)
            Clock.schedule_interval(lambda dt: self.rfid_manager.check_for_card(), 0.5)
        else:
            logger.info("Kein RFID-Hardware. Simulationsmodus aktiv.")
        
        return sm

    def on_rfid_scan(self, uid: str):
        """Callback für RFID-Scan - leitet an aktuellen Screen weiter"""
        logger.info(f"RFID gescannt: {uid}")
        # An den main_screen weiterleiten
        self.main_screen.on_rfid(uid)

if __name__ == "__main__":
    KaffeeKasseApp().run()