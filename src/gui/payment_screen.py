from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.lang import Builder
from core.account_manager import AccountManager
import logging

logger = logging.getLogger(__name__)
Builder.load_string('''
<PaymentScreen>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label:
            text: "Einzahlung (EUR)"
            bold: True
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(8)
        TextInput:
            id: amount_input
            hint_text: "z. B. 1.00"
            input_filter: 'float'
        Button:
            text: "Einzahlen"
            size_hint_x: None
            width: dp(120)
            on_press: root.do_deposit(amount_input.text)
''')

class PaymentScreen(BoxLayout):
    status = StringProperty("")

    def __init__(self, uid=None, **kwargs):
        super().__init__(**kwargs)
        self.uid = uid
        self.am = AccountManager()

    def do_deposit(self, amount_str):
        try:
            user = self.am.get_user_by_uid(self.uid)
            if not user:
                self.status = "Benutzer nicht gefunden"
                return
            self.am.deposit(user, amount_str)
            self.status = f"Einzahlung {amount_str} € erfolgreich"
        except Exception as e:
            logger.exception("Fehler bei Einzahlung")
            self.status = str(e)
