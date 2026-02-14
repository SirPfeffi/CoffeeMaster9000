from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen
import logging
import os

from core.account_manager import AccountManager
from core.config import CONFIG
from core.fun_content_manager import FunContentManager
from core.i18n import DEFAULT_LANG, SUPPORTED_LANGS, translate
from core.registration_manager import RegistrationManager
from gui.user_registration_dialog import UserRegistrationDialog

logger = logging.getLogger(__name__)


class MainScreen(Screen):
    current_user_name = StringProperty("")
    current_user_balance = StringProperty("")
    recent_bookings = StringProperty("")
    balance_notice = StringProperty("")
    feedback = StringProperty("")
    feedback_color = StringProperty("")
    feedback_rgba = ListProperty([1, 1, 1, 0])
    coffee_count = NumericProperty(1)
    selected_kg = NumericProperty(1)
    fun_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.am = AccountManager()
        self.registration = RegistrationManager()
        self._auto_return_ev = None
        self._last_user = None
        self.gui_lang = os.environ.get("COFFEEMASTER_GUI_LANG", DEFAULT_LANG)
        if self.gui_lang not in SUPPORTED_LANGS:
            self.gui_lang = DEFAULT_LANG
        self.fun_content = FunContentManager(
            lang=self.gui_lang,
            include_types=("fact", "joke"),
            max_length=120,
        )
        self.current_user_name = self.tr("gui.scan_card")
        self.rotate_fun_text(force=True)
        self._fun_rotation_ev = Clock.schedule_interval(lambda dt: self.rotate_fun_text(), 30)

    def tr(self, key: str, fallback: str = None) -> str:
        return translate(key, self.gui_lang, fallback=fallback or key)

    def rotate_fun_text(self, force: bool = False):
        if force or self._last_user is None:
            self.fun_text = self.fun_content.next_text() or self.tr("gui.fun_fallback")

    def on_rfid(self, uid: str):
        logger.info("RFID detected: %s", uid)
        user = self.am.get_user_by_uid(uid)
        if not user:
            self.show_registration_dialog(uid)
            return

        if user.is_admin:
            self.show_feedback(self.tr("gui.admin_mode_enabled"), success=True, timeout=1)
            Clock.schedule_once(lambda dt: self.switch_to_admin(user), 1)
            return

        self.load_user(user)

    def load_user(self, user):
        self._last_user = user
        self.coffee_count = 1
        self.selected_kg = 1
        self._refresh_user_context()
        self.show_feedback(self.tr("gui.welcome_user").format(name=user.name), success=True, timeout=2)
        self.fun_text = ""

    def load_user_by_uid(self, uid: str):
        self.on_rfid(uid)

    def load_user_by_uid_and_clear(self, text_input_widget):
        uid = text_input_widget.text.strip()
        text_input_widget.text = ""
        if uid:
            self.load_user_by_uid(uid)

    def increase_coffee_count(self):
        if self.coffee_count < CONFIG.max_coffees_per_booking:
            self.coffee_count += 1

    def decrease_coffee_count(self):
        if self.coffee_count > 1:
            self.coffee_count -= 1

    def _build_balance_notice(self, balance_cents: int) -> str:
        if balance_cents <= CONFIG.critical_balance_threshold_cents:
            return self.tr("gui.balance_critical")
        if balance_cents < CONFIG.low_balance_threshold_cents:
            return self.tr("gui.balance_negative")
        return ""

    def _refresh_user_context(self):
        user = self._last_user
        if not user:
            return

        current = self.am.get_user_by_uid(user.rfid_uid)
        if not current:
            return
        self._last_user = current

        self.current_user_name = current.name
        self.current_user_balance = f"{current.balance:.2f} EUR"
        self.balance_notice = self._build_balance_notice(current.balance_cents)

        tx = self.am.get_last_transactions(current, limit=5)
        lines = []
        for item in tx:
            ts = item.timestamp.strftime("%d.%m. %H:%M")
            eur = item.amount_cents / 100.0
            lines.append(f"{ts} | {item.description} | {eur:+.2f} EUR")
        self.recent_bookings = "\n".join(lines) if lines else self.tr("gui.no_bookings")

    def set_selected_kg(self, kg: int):
        if 1 <= int(kg) <= CONFIG.max_topup_kg:
            self.selected_kg = int(kg)

    def book_coffee(self):
        user = self._last_user
        if not user:
            self.show_feedback(self.tr("gui.no_user_loaded"), error=True)
            return

        try:
            self.am.book_coffee(user, count=int(self.coffee_count))
            self._refresh_user_context()
            self.show_feedback(self.tr("gui.booking_success"), success=True, timeout=4)
            self.schedule_return(10)
        except Exception as exc:
            logger.exception("Error booking coffee: %s", exc)
            self.show_feedback(str(exc), error=True)

    def deposit(self, amount_str):
        user = self._last_user
        if not user:
            self.show_feedback(self.tr("gui.no_user_loaded"), error=True)
            return
        try:
            self.am.deposit(user, amount_str)
            self._refresh_user_context()
            self.show_feedback(self.tr("gui.deposit_success"), success=True, timeout=4)
            self.schedule_return(10)
        except Exception as exc:
            logger.exception("Error during deposit: %s", exc)
            self.show_feedback(str(exc), error=True)

    def submit_bean_topup(self, amount_str):
        user = self._last_user
        if not user:
            self.show_feedback(self.tr("gui.no_user_loaded"), error=True)
            return
        try:
            self.am.topup_by_beans(
                user=user,
                kg=int(self.selected_kg),
                amount_euro=amount_str,
            )
            self._refresh_user_context()
            self.show_feedback(self.tr("gui.beans_topup_success"), success=True, timeout=4)
            self.schedule_return(10)
        except Exception as exc:
            logger.exception("Error during bean top-up: %s", exc)
            self.show_feedback(str(exc), error=True)

    def submit_bean_topup_and_clear(self, text_input_widget):
        amount = text_input_widget.text
        self.submit_bean_topup(amount)
        text_input_widget.text = ""

    def show_feedback(self, message, success=False, error=False, timeout=3):
        self.feedback = message
        if success:
            self.feedback_color = "#a6e6a6"
            self.feedback_rgba = [0.65, 0.95, 0.65, 1]
        elif error:
            self.feedback_color = "#f7a6a6"
            self.feedback_rgba = [0.97, 0.65, 0.65, 1]
        else:
            self.feedback_color = ""
            self.feedback_rgba = [1, 1, 1, 0]
        if timeout and timeout > 0:
            Clock.schedule_once(lambda dt: self.clear_feedback(), timeout)

    def clear_feedback(self):
        self.feedback = ""
        self.feedback_color = ""
        self.feedback_rgba = [1, 1, 1, 0]

    def schedule_return(self, seconds=5):
        if self._auto_return_ev:
            try:
                self._auto_return_ev.cancel()
            except Exception:
                pass
        self._auto_return_ev = Clock.schedule_once(lambda dt: self.reset_screen(), seconds)

    def reset_screen(self):
        self.current_user_name = self.tr("gui.scan_card")
        self.current_user_balance = ""
        self.recent_bookings = ""
        self.balance_notice = ""
        self.feedback = ""
        self.feedback_color = ""
        self.feedback_rgba = [1, 1, 1, 0]
        self._last_user = None
        self.coffee_count = 1
        self.selected_kg = 1
        self.rotate_fun_text(force=True)

    def switch_to_admin(self, user):
        if self.manager:
            admin_screen = self.manager.get_screen("admin")
            admin_screen.current_admin = user
            self.manager.current = "admin"

    def show_registration_dialog(self, uid):
        policy = self.registration.settings.get_registration_policy()
        if not policy["allow_self_registration"]:
            self.show_feedback(self.tr("gui.self_registration_disabled"), error=True, timeout=5)
            return

        users = self.registration.list_users_for_linking()
        can_link = not policy["rfid_reassignment_admin_only"]
        dialog = UserRegistrationDialog(
            uid=uid,
            users=users,
            can_link=can_link,
            on_submit_callback=self.register_new_user,
        )
        dialog.open()

    def register_new_user(self, uid, mode, full_name=None, user_id=None):
        try:
            user = self.registration.register_or_link_unknown_uid(
                uid=uid,
                mode=mode,
                actor_is_admin=False,
                full_name=full_name,
                user_id=user_id,
            )
            logger.info("Unknown UID handled by mode=%s", mode)
            self.show_feedback(self.tr("gui.welcome_user").format(name=user.name), success=True)
            self.load_user(user)
        except Exception as exc:
            logger.exception("Fehler bei der Registrierung: %s", exc)
            self.show_feedback(str(exc), error=True)
