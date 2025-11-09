# src/gui/main_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from core.account_manager import AccountManager
from core.rfid_manager import RFIDManager
import logging

logger = logging.getLogger(__name__)

class MainScreen(Screen):
    # Kivy-Event hier per Klassen-API definieren
    __events__ = ('on_admin_activate',)

    current_user_name = StringProperty("Bitte Karte scannen")
    current_user_balance = StringProperty("")
    feedback = StringProperty("")
    feedback_color = StringProperty("")  # '#a6e6a6' oder '#f7a6a6'
    is_admin_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.am = AccountManager()
        self.rfid = RFIDManager()
        self.rfid.set_callback(self.on_rfid)
        # nur alle 0.5s auf Karten prüfen (RFIDManager kann intern None haben)
        Clock.schedule_interval(lambda dt: self.rfid.check_for_card(), 0.5)
        self._auto_return_ev = None
        self._last_user = None  # Peewee User-Objekt oder None
        self.simulation_mode = False
        try:
            if self.rfid.is_hardware_available():
                Clock.schedule_interval(lambda dt: self.rfid.check_for_card(), 0.5)
            else:
                logger.info("No RFID hardware detected; simulation mode enabled.")
                self.simulation_mode = True
        except Exception:
            logger.exception("Error checking RFID hardware; enabling simulation.")
            self.simulation_mode = True

    def on_rfid(self, uid: str):
        logger.info("RFID detected: %s", uid)
        user = self.am.get_user_by_uid(uid)
        if not user:
            self.show_feedback(f"Unbekannte Karte: {uid}", error=True)
            return

        if getattr(user, "is_admin", False):
            self.is_admin_mode = True
            self._last_user = user
            self.show_feedback("Admin-Modus aktiviert", success=True, timeout=5)
            self.dispatch('on_admin_activate', user)
            return

        self.load_user(user)

        # Normaler Benutzer: laden und anzeigen
        self.load_user(user)

    def load_user(self, user):
        self._last_user = user
        self.current_user_name = user.name
        self.current_user_balance = f"{user.balance:.2f} €"
        self.show_feedback(f"Willkommen, {user.name}", success=True)

    def book_coffee(self):
        user = self._last_user
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.book_coffee(user)
            user = self.am.get_user_by_uid(user.rfid_uid)
            self._last_user = user
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Kaffee gebucht", success=True)
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Error booking coffee: %s", e)
            self.show_feedback(str(e), error=True)


    def deposit(self, amount_str):
        user = self._last_user
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.deposit(user, amount_str)
            user = self.am.get_user_by_uid(user.rfid_uid)
            self._last_user = user
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Einzahlung erfolgreich", success=True)
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Error during deposit: %s", e)
            self.show_feedback(str(e), error=True)

    def show_feedback(self, message, success=False, error=False, timeout=3):
        self.feedback = message
        if success:
            self.feedback_color = "#a6e6a6"
        elif error:
            self.feedback_color = "#f7a6a6"
        else:
            self.feedback_color = ""
        if timeout and timeout > 0:
            self.schedule_return(timeout)

    def schedule_return(self, seconds=5):
        if self._auto_return_ev:
            try:
                self._auto_return_ev.cancel()
            except Exception:
                pass
        self._auto_return_ev = Clock.schedule_once(lambda dt: self.reset_screen(), seconds)

    def reset_screen(self):
        self.current_user_name = "Bitte Karte scannen"
        self.current_user_balance = ""
        self.feedback = ""
        self.feedback_color = ""
        self.is_admin_mode = False
        self._last_user = None

    def on_textinput_focus(self, instance, value):
        if getattr(self, "simulation_mode", False) and not value:
            Clock.schedule_once(lambda dt: setattr(instance, "focus", True), 0.05)

    def on_admin_activate(self, user):
        logger.info("Admin activated: %s", getattr(user, "name", "unknown"))
        pass
