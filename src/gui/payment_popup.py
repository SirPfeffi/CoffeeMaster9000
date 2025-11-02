from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

class PaymentPopup(Popup):
    def __init__(self, user, manager, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Einzahlung für {user.name}"
        self.size_hint = (0.8, 0.5)
        self.auto_dismiss = False

        self.user = user
        self.manager = manager

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.input_amount = TextInput(hint_text="Betrag eingeben (€)", multiline=False, input_filter='float', font_size=24)
        layout.add_widget(self.input_amount)

        self.message = Label(text="", font_size=18)
        layout.add_widget(self.message)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_ok = Button(text="Einzahlen", on_press=self.deposit)
        btn_cancel = Button(text="Abbrechen", on_press=self.dismiss)
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)

        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def deposit(self, instance):
        try:
            amount = float(self.input_amount.text)
            if amount <= 0:
                self.message.text = "Bitte einen positiven Betrag eingeben!"
                return
            new_balance = self.manager.deposit(self.user, amount)
            self.message.text = f"Neuer Kontostand: {new_balance:.2f} €"
        except ValueError:
            self.message.text = "Ungültiger Betrag!"
