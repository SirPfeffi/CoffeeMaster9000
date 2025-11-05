from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from core.account_manager import AccountManager
from core.rfid_manager import RFIDManager
import logging

logger = logging.getLogger(__name__)

class MainScreen(Screen):
    current_user_name = StringProperty("Bitte Karte scannen")
    current_user_balance = StringProperty("")
    feedback = StringProperty("")
    feedback_color = StringProperty("white")
    is_admin_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.am = AccountManager()
        self.rfid = RFIDManager()
        self.rfid.set_callback(self.on_rfid)
        # schedule periodic check only if hardware present
        Clock.schedule_interval(lambda dt: self.rfid.check_for_card(), 0.5)
        self._auto_return_ev = None

    def on_rfid(self, uid: str):
        logger.info("RFID erkannt: %s", uid)
        user = self.am.get_user_by_uid(uid)
        if not user:
            self.show_feedback(f"Unbekannte Karte: {uid}", error=True)
            return
        # check admin
        if getattr(user, "is_admin", False):
            self.is_admin_mode = True
            self.show_feedback("Admin-Modus aktiviert", timeout=5, success=True)
            # inform other parts via event
            self.dispatch("on_admin_activate", user)
            return
        # normal user
        self.load_user(user)

    def load_user(self, user):
        self.current_user_name = user.name
        self.current_user_balance = f"{user.balance:.2f} €"
        self.show_feedback(f"Willkommen, {user.name}", success=True)

    def book_coffee(self):
        # attempts to book coffee for current user
        # find user by name (safer to store current user id in real impl)
        users = self.am.db.execute_sql("SELECT id FROM user WHERE name = ?", (self.current_user_name,))
        # simple approach: fetch user object by name
        user = self.am.get_user_by_uid(self._last_uid) if hasattr(self, '_last_uid') else None
        if not user:
            # try to get by name
            user = self.am.get_user_by_uid(self.ids.get('uid_input').text) if 'uid_input' in self.ids else None
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.book_coffee(user)
            user = self.am.get_user_by_uid(user.rfid_uid)  # refresh
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Kaffee gebucht", success=True)
            # auto return to default after 5s
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Fehler beim Buchen")
            self.show_feedback(str(e), error=True)

    def deposit(self, amount_str):
        user = self.am.get_user_by_uid(self._last_uid) if hasattr(self, '_last_uid') else None
        if not user:
            self.show_feedback("Kein Benutzer geladen", error=True)
            return
        try:
            self.am.deposit(user, amount_str)
            user = self.am.get_user_by_uid(user.rfid_uid)
            self.current_user_balance = f"{user.balance:.2f} €"
            self.show_feedback("Einzahlung erfolgreich", success=True)
            self.schedule_return(5)
        except Exception as e:
            logger.exception("Fehler bei Einzahlung")
            self.show_feedback(str(e), error=True)

    def show_feedback(self, message, success=False, error=False, timeout=3):
        self.feedback = message
        if success:
            self.feedback_color = "#a6e6a6"  # light green
        elif error:
            self.feedback_color = "#f7a6a6"  # light red
        else:
            self.feedback_color = "white"
        # TODO: play sound if desired
        if timeout and timeout > 0:
            self.schedule_return(timeout)

    def schedule_return(self, seconds=5):
        if self._auto_return_ev:
            self._auto_return_ev.cancel()
        self._auto_return_ev = Clock.schedule_once(lambda dt: self.reset_screen(), seconds)

    def reset_screen(self):
        self.current_user_name = "Bitte Karte scannen"
        self.current_user_balance = ""
        self.feedback = ""
        self.feedback_color = "white"
        self.is_admin_mode = False

    # Kivy event for admin activation
    def on_admin_activate(self, user):
        pass

# register custom event
MainScreen.register_event_type('on_admin_activate')
