from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from peewee import fn
import logging
import os

from core.account_manager import AccountManager
from core.i18n import DEFAULT_LANG, SUPPORTED_LANGS, translate
from core.settings_manager import SettingsManager
from db.models import Transaction, User

logger = logging.getLogger(__name__)


class AdminScreen(Screen):
    stats_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_admin = None
        self.am = AccountManager()
        self.settings = SettingsManager()
        self.gui_lang = os.environ.get("COFFEEMASTER_GUI_LANG", DEFAULT_LANG)
        if self.gui_lang not in SUPPORTED_LANGS:
            self.gui_lang = DEFAULT_LANG

    def tr(self, key: str, fallback: str = None):
        return translate(key, self.gui_lang, fallback=fallback or key)

    def on_pre_enter(self):
        self.update_stats()

    def update_stats(self):
        try:
            total_users = User.select().where(User.is_active == True).count()
            total_transactions = Transaction.select().count()
            total_balance = User.select(fn.SUM(User.balance_cents)).where(User.is_active == True).scalar() or 0
            admin_name = self.current_admin.name if self.current_admin else self.tr("gui.admin_unknown")
            policy = self.settings.get_registration_policy()

            self.stats_text = (
                f"{self.tr('gui.admin_label')}: {admin_name}\n\n"
                f"{self.tr('gui.users_label')}: {total_users}\n"
                f"{self.tr('gui.transactions_label')}: {total_transactions}\n"
                f"{self.tr('gui.total_balance_label')}: {total_balance/100:.2f} EUR\n"
                f"{self.tr('gui.self_registration_label')}: "
                f"{self.tr('gui.on') if policy['allow_self_registration'] else self.tr('gui.off')}\n"
                f"{self.tr('gui.rfid_reassign_admin_only_label')}: "
                f"{self.tr('gui.on') if policy['rfid_reassignment_admin_only'] else self.tr('gui.off')}"
            )
        except Exception as exc:
            logger.exception("Stats loading failed: %s", exc)
            self.stats_text = self.tr("gui.stats_loading_error")

    def show_user_management(self):
        if self.manager:
            user_mgmt_screen = self.manager.get_screen("user_management")
            user_mgmt_screen.current_admin = self.current_admin
            self.manager.current = "user_management"
        logger.info("User management opened")

    def _open_popup(self, title: str, message: str):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(Label(text=message))
        close_btn = Button(text=self.tr("gui.close"), size_hint_y=None, height=45)
        popup = Popup(title=title, content=layout, size_hint=(0.8, 0.6), auto_dismiss=False)
        close_btn.bind(on_release=popup.dismiss)
        layout.add_widget(close_btn)
        popup.open()

    def show_balance_overview(self):
        users = (
            User.select()
            .where(User.is_active == True)
            .order_by(User.balance_cents.asc())
            .limit(20)
        )
        lines = [f"{u.name}: {u.balance_cents/100.0:.2f} EUR" for u in users]
        message = "\n".join(lines) if lines else self.tr("gui.no_users_found")
        self._open_popup(self.tr("gui.balance_overview"), message)

    def book_deposit(self):
        policy = self.settings.get_registration_policy()
        self.settings.set_bool("allow_self_registration", not policy["allow_self_registration"])
        self.update_stats()
        state = self.tr("gui.enabled") if not policy["allow_self_registration"] else self.tr("gui.disabled")
        self._open_popup(self.tr("gui.policy"), self.tr("gui.self_registration_was_set_to").format(state=state))

    def cancel_transaction(self):
        self._open_popup(
            self.tr("gui.corrections"),
            self.tr("gui.direct_cancel_disabled"),
        )

    def return_to_main(self):
        if self.manager:
            main_screen = self.manager.get_screen("main")
            main_screen.reset_screen()
            self.manager.current = "main"
        self.current_admin = None
