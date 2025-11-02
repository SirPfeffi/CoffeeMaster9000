from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


class PaymentPopup(Popup):
    user = ObjectProperty(None)
    account_manager = ObjectProperty(None)
    parent_screen = ObjectProperty(None)

    def add_digit(self, digit):
        self.ids.amount_input.text += str(digit)

    def clear_input(self):
        self.ids.amount_input.text = ""

    def confirm_payment(self):
        text = self.ids.amount_input.text
        if not text:
            self.parent_screen.message = "Bitte Betrag eingeben."
            return
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            self.parent_screen.message = "Ungültiger Betrag!"
            return
        new_balance = self.account_manager.deposit(self.user, amount)
        self.parent_screen.balance = f"Guthaben: {new_balance:.2f} €"
        self.parent_screen.message = f"{amount:.2f} € eingezahlt 💶"
        self.dismiss()
