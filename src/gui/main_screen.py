from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from core.account_manager import AccountManager
import logging

logger = logging.getLogger(__name__)

class MainScreen(Screen):
    current_user_name = StringProperty("Bitte Karte scannen")
    current_user_balance = StringProperty("")
    feedback = StringProperty("")
    feedback_color = StringProperty("")  # '#a6e6a6' oder '#f7a6a6'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.am = AccountManager()
        self._auto_return_ev = None
        self._last_user = None  # Peewee User-Objekt oder None

    def on_rfid(self, uid: str):
        """Callback für RFID-Scan"""
        logger.info("RFID detected: %s", uid)
        user = self.am.get_user_by_uid(uid)
        
        if not user:
            self.show_feedback(f"Unbekannte Karte: {uid}", error=True)
            return

        # Admin-Benutzer -> zum Admin-Screen wechseln
        if user.is_admin:
            self.show_feedback("Admin-Modus aktiviert", success=True, timeout=1)
            Clock.schedule_once(lambda dt: self.switch_to_admin(user), 1)
            return

        # Normaler Benutzer: laden und anzeigen
        self.load_user(user)

    def load_user(self, user):
        """Lädt Benutzerdaten und zeigt sie an"""
        self._last_user = user
        self.current_user_name = user.name
        self.current_user_balance = f"{user.balance:.2f} €"
        self.show_feedback(f"Willkommen, {user.name}", success=True)

    def load_user_by_uid(self, uid: str):
        """Lädt Benutzer anhand UID (für Simulation)"""
        user = self.am.get_user_by_uid(uid)
        if user:
            self.on_rfid(uid)
        else:
            self.show_feedback(f"Unbekannte UID: {uid}", error=True)

    def book_coffee(self):
        """Bucht einen Kaffee für den aktuellen Benutzer"""
        user = self._last_user
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.book_coffee(user)
            # Benutzer neu laden um aktuellen Balance zu haben
            user = self.am.get_user_by_uid(user.rfid_uid)
            self._last_user = user
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Kaffee gebucht", success=True)
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Error booking coffee: %s", e)
            self.show_feedback(str(e), error=True)

    def deposit(self, amount_str):
        """Bucht eine Einzahlung für den aktuellen Benutzer"""
        user = self._last_user
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.deposit(user, amount_str)
            # Benutzer neu laden
            user = self.am.get_user_by_uid(user.rfid_uid)
            self._last_user = user
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Einzahlung erfolgreich", success=True)
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Error during deposit: %s", e)
            self.show_feedback(str(e), error=True)

    def show_feedback(self, message, success=False, error=False, timeout=3):
        """Zeigt Feedback-Nachricht an"""
        self.feedback = message
        if success:
            self.feedback_color = "#a6e6a6"
        elif error:
            self.feedback_color = "#f7a6a6"
        else:
            self.feedback_color = ""
        if timeout and timeout > 0:
            Clock.schedule_once(lambda dt: self.clear_feedback(), timeout)

    def clear_feedback(self):
        """Löscht die Feedback-Nachricht"""
        self.feedback = ""
        self.feedback_color = ""

    def schedule_return(self, seconds=5):
        """Plant automatische Rückkehr zum Startbildschirm"""
        if self._auto_return_ev:
            try:
                self._auto_return_ev.cancel()
            except Exception:
                pass
        self._auto_return_ev = Clock.schedule_once(lambda dt: self.reset_screen(), seconds)

    def reset_screen(self):
        """Setzt den Screen zurück"""
        self.current_user_name = "Bitte Karte scannen"
        self.current_user_balance = ""
        self.feedback = ""
        self.feedback_color = ""
        self._last_user = None

    def switch_to_admin(self, user):
        """Wechselt zum Admin-Screen"""
        if self.manager:
            admin_screen = self.manager.get_screen('admin')
            admin_screen.current_admin = user
            self.manager.current = 'admin'