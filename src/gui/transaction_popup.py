from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from db.models import Transaction, User
from datetime import datetime

class TransactionPopup(Popup):
    def __init__(self, user: User, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Transaktionen von {user.name}"
        self.size_hint = (0.95, 0.8)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        scroll = ScrollView()
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=6)
        container.bind(minimum_height=container.setter('height'))

        transactions = Transaction.select().where(Transaction.user == user).order_by(Transaction.timestamp.desc())
        if transactions:
            for t in transactions:
                ts = t.timestamp.strftime('%d.%m.%Y %H:%M')
                amount = t.amount_cents/100.0
                label = Label(text=f"{ts} | {t.description} | {amount:+.2f} €", size_hint_y=None, height=30)
                container.add_widget(label)
        else:
            container.add_widget(Label(text="Keine Buchungen vorhanden", size_hint_y=None, height=30))

        scroll.add_widget(container)
        layout.add_widget(scroll)
        btn = BoxLayout(size_hint_y=None, height=50)
        from kivy.uix.button import Button
        btn.add_widget(Button(text="Schließen", on_press=lambda *_: self.dismiss()))
        layout.add_widget(btn)
        self.add_widget(layout)
