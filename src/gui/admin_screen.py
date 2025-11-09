from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from db.models import User, Transaction
from peewee import fn

class AdminScreen(Screen):
    stats_text = StringProperty("")

    def on_pre_enter(self):
        # build simple stats
        total_users = User.select().count()
        total_transactions = Transaction.select().count()
        total_balance = User.select(fn.SUM(User.balance_cents)).scalar() or 0
        self.stats_text = f"Users: {total_users}\nTransactions: {total_transactions}\nTotal Balance: {total_balance/100:.2f} €"
