from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from db.models import User, Transaction
from peewee import fn
from datetime import timedelta, datetime

class StatsPopup(Popup):
    def __init__(self, days=7, **kwargs):
        super().__init__(**kwargs)
        self.title = "Statistiken"
        self.size_hint = (0.9, 0.8)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        total_users = User.select().count()
        total_transactions = Transaction.select().count()
        total_balance = User.select(fn.SUM(User.balance_cents)).scalar() or 0
        from kivy.uix.label import Label
        layout.add_widget(Label(text=f"Benutzer: {total_users}"))
        layout.add_widget(Label(text=f"Transaktionen: {total_transactions}"))
        layout.add_widget(Label(text=f"Gesamtguthaben: {total_balance/100:.2f} €"))

        today = datetime.now().date()
        for i in range(days):
            day = today - timedelta(days=i)
            count = Transaction.select().where((Transaction.description=="Kaffee") & (Transaction.timestamp.date()==day)).count()
            layout.add_widget(Label(text=f"{day.strftime('%d.%m.%Y')}: {count}"))

        from kivy.uix.button import Button
        layout.add_widget(Button(text="Schließen", size_hint_y=None, height=40, on_press=lambda *_: self.dismiss()))
        self.add_widget(layout)
