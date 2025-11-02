from kivy.uix.boxlayout import BoxLayout
from gui.payment_screen import PaymentPopup
from gui.transaction_popup import TransactionPopup
from gui.stats_popup import StatsPopup
from core.backup_manager import BackupManager

LANGS = {
    "DE": {"coffee": "☕ Kaffee buchen", "deposit": "💶 Einzahlung", "transactions": "📜 Letzte Buchungen", "stats": "📊 Statistik"},
    "EN": {"coffee": "☕ Book Coffee", "deposit": "💶 Deposit", "transactions": "📜 Last Transactions", "stats": "📊 Statistics"}
}

class MainScreen(BoxLayout):
    current_lang = "DE"
    manager = None
    message = ""

    def load_account(self, uid):
        user = self.manager.get_user_by_uid(uid)
        if not user:
            user = self.manager.create_user(uid)
        self.current_user = user
        self.ids.label_user.text = f"{user.name}: {user.balance:.2f}€"

    def book_coffee(self):
        if self.manager.book_coffee(self.current_user):
            self.load_account(self.current_user.rfid_uid)

    def open_payment(self):
        PaymentPopup(user=self.current_user, manager=self.manager).open()

    def open_transactions(self):
        TransactionPopup(user=self.current_user, manager=self.manager).open()

    def open_stats(self):
        StatsPopup(account_manager=self.manager).open()

    def switch_language(self):
        self.current_lang = "EN" if self.current_lang=="DE" else "DE"
        # update button texts here...
        self.ids.coffee_btn.text = LANGS[self.current_lang]["coffee"]
        self.ids.deposit_btn.text = LANGS[self.current_lang]["deposit"]
        self.ids.transactions_btn.text = LANGS[self.current_lang]["transactions"]
        self.ids.stats_btn.text = LANGS[self.current_lang]["stats"]

    def perform_backup(self):
        bm = BackupManager(db_path="db/kaffeekasse.db", usb_path="/media/usb", network_path="//192.168.1.100/kaffeekasse")
        result = bm.backup_all()
        self.ids.label_message.text = "\n".join([f"{k}: {v}" for k,v in result.items()])
