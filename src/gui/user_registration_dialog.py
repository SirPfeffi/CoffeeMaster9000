from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
import logging
import os

from core.i18n import DEFAULT_LANG, SUPPORTED_LANGS, translate

logger = logging.getLogger(__name__)


class UserRegistrationDialog(Popup):
    """Dialog for unknown RFID: create user or link existing user."""

    def __init__(
        self,
        uid,
        users,
        can_link=True,
        on_submit_callback=None,
        **kwargs,
    ):
        self.scanned_uid = uid
        self.users = users or []
        self.can_link = can_link
        self.on_submit_callback = on_submit_callback
        self.mode = "create"
        self.gui_lang = os.environ.get("COFFEEMASTER_GUI_LANG", DEFAULT_LANG)
        if self.gui_lang not in SUPPORTED_LANGS:
            self.gui_lang = DEFAULT_LANG

        super().__init__(
            title=self.tr("gui.registration_new_card"),
            size_hint=(0.85, 0.8),
            auto_dismiss=False,
            **kwargs,
        )

        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
        layout.add_widget(
            Label(
                text=self.tr("gui.registration_info").format(uid=uid),
                size_hint_y=None,
                height=dp(80),
                font_size="16sp",
            )
        )

        mode_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        self.create_btn = Button(text=self.tr("gui.registration_create"), background_normal="")
        self.link_btn = Button(text=self.tr("gui.registration_link"), background_normal="")
        self.create_btn.bind(on_release=lambda _: self.set_mode("create"))
        self.link_btn.bind(on_release=lambda _: self.set_mode("link"))
        mode_row.add_widget(self.create_btn)
        mode_row.add_widget(self.link_btn)
        layout.add_widget(mode_row)

        self.first_name_input = TextInput(
            hint_text=self.tr("gui.first_name"),
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
        self.last_name_input = TextInput(
            hint_text=self.tr("gui.last_name"),
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
        layout.add_widget(self.first_name_input)
        layout.add_widget(self.last_name_input)

        user_names = [f"{u.id}: {u.name}" for u in self.users]
        self.user_spinner = Spinner(
            text=self.tr("gui.select_user"),
            values=user_names,
            size_hint_y=None,
            height=dp(44),
        )
        layout.add_widget(self.user_spinner)

        button_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel_btn = Button(text=self.tr("gui.cancel"), background_normal="", background_color=(0.5, 0.5, 0.5, 1))
        submit_btn = Button(text=self.tr("gui.save"), background_normal="", background_color=(0.102, 0.737, 0.612, 1))
        cancel_btn.bind(on_release=self.cancel)
        submit_btn.bind(on_release=self.submit)
        button_row.add_widget(cancel_btn)
        button_row.add_widget(submit_btn)
        layout.add_widget(button_row)

        self.content = layout
        self.set_mode("create")
        self.first_name_input.focus = True

    def tr(self, key: str, fallback: str = None) -> str:
        return translate(key, self.gui_lang, fallback=fallback or key)

    def set_mode(self, mode: str):
        if mode == "link" and not self.can_link:
            return
        self.mode = mode
        is_create = mode == "create"
        self.first_name_input.disabled = not is_create
        self.last_name_input.disabled = not is_create
        self.user_spinner.disabled = is_create
        self.create_btn.background_color = (0.102, 0.737, 0.612, 1) if is_create else (0.4, 0.4, 0.4, 1)
        self.link_btn.background_color = (
            (0.2, 0.6, 0.86, 1) if (not is_create and self.can_link) else (0.4, 0.4, 0.4, 1)
        )

    def submit(self, _):
        if not self.on_submit_callback:
            self.dismiss()
            return

        try:
            if self.mode == "create":
                first_name = self.first_name_input.text.strip()
                last_name = self.last_name_input.text.strip()
                if not first_name or not last_name:
                    raise ValueError(self.tr("gui.first_last_required"))
                full_name = f"{first_name} {last_name}"
                self.on_submit_callback(self.scanned_uid, "create", full_name=full_name, user_id=None)
            else:
                selected = self.user_spinner.text.strip()
                if ":" not in selected:
                    raise ValueError(self.tr("gui.select_target_required"))
                user_id = int(selected.split(":", 1)[0].strip())
                self.on_submit_callback(self.scanned_uid, "link", full_name=None, user_id=user_id)
            self.dismiss()
        except Exception as exc:
            logger.exception("Registration dialog failed: %s", exc)

    def cancel(self, _):
        self.dismiss()
