from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from db.models import User, Transaction
from peewee import fn
from core.account_manager import AccountManager
import logging

logger = logging.getLogger(__name__)

class AdminScreen(Screen):
    stats_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_admin = None
        self.am = AccountManager()

    def on_pre_enter(self):
        """Wird aufgerufen bevor der Screen angezeigt wird"""
        self.update_stats()

    def update_stats(self):
        """Aktualisiert die Statistiken"""
        try:
            total_users = User.select().count()
            total_transactions = Transaction.select().count()
            total_balance = User.select(fn.SUM(User.balance_cents)).scalar() or 0
            
            admin_name = self.current_admin.name if self.current_admin else "Unbekannt"
            
            self.stats_text = (
                f"Admin: {admin_name}\n\n"
                f"Benutzer: {total_users}\n"
                f"Transaktionen: {total_transactions}\n"
                f"Gesamtguthaben: {total_balance/100:.2f} €"
            )
        except Exception as e:
            logger.exception("Fehler beim Laden der Statistiken: %s", e)
            self.stats_text = "Fehler beim Laden der Statistiken"

    def show_user_management(self):
        """Zeigt Benutzerverwaltung an"""
        if self.manager:
            user_mgmt_screen = self.manager.get_screen('user_management')
            user_mgmt_screen.current_admin = self.current_admin
            self.manager.current = 'user_management'
        logger.info("Benutzerverwaltung aufgerufen")

    def show_balance_overview(self):
        """Zeigt Kassensaldo-Übersicht an"""
        # TODO: Implementierung
        logger.info("Kassensaldo-Übersicht aufgerufen")
        pass

    def book_deposit(self):
        """Bucht manuelle Einzahlung"""
        # TODO: Implementierung
        logger.info("Einzahlung buchen aufgerufen")
        pass

    def cancel_transaction(self):
        """Storniert eine Fehlbuchung"""
        # TODO: Implementierung
        logger.info("Stornierung aufgerufen")
        pass

    def return_to_main(self):
        """Kehrt zum Hauptbildschirm zurück"""
        if self.manager:
            main_screen = self.manager.get_screen('main')
            main_screen.reset_screen()
            self.manager.current = 'main'
        self.current_admin = None