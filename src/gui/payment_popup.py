from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from core.account_manager import AccountManager
import logging

logger = logging.getLogger(__name__)

class PaymentPopup(Popup):
    message = StringProperty("")

    def __init__(self, uid=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Einzahlung"
        self.size_hint = (0.9, 0.5)
        self.auto_dismiss = False
        self.uid = uid
        self.am = AccountManager()

    def on_open(self):
        pass

    def submit(self, amount_str):
        try:
            if not self.uid:
                self.message = "Keine Karte ausgewählt"
                return
            user = self.am.get_user_by_uid(self.uid)
            if not user:
                self.message = "Benutzer nicht gefunden"
                return
            self.am.deposit(user, amount_str)
            self.message = f"Einzahlung {amount_str} € erfolgreich"
            self.dismiss()
        except Exception as e:
            logger.exception("Fehler bei Einzahlung: %s", e)
            self.message = str(e)
