from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.metrics import dp
import logging

logger = logging.getLogger(__name__)

class UserRegistrationDialog(Popup):
    """Dialog zur Registrierung neuer Benutzer"""
    
    def __init__(self, uid, on_register_callback, **kwargs):
        self.uid = uid
        self.on_register_callback = on_register_callback
        
        super().__init__(
            title="Neue Karte erkannt",
            size_hint=(0.8, 0.6),
            auto_dismiss=False,
            **kwargs
        )
        
        # Layout erstellen
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Info-Text
        info_label = Label(
            text=f"Diese Karte ist noch nicht registriert.\n\nUID: {uid}\n\nMöchtest du dich als Benutzer hinzufügen?",
            size_hint_y=None,
            height=dp(100),
            font_size='16sp'
        )
        layout.add_widget(info_label)
        
        # Vorname Input
        vorname_label = Label(
            text="Vorname:",
            size_hint_y=None,
            height=dp(30),
            font_size='14sp'
        )
        layout.add_widget(vorname_label)
        
        self.vorname_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size='16sp'
        )
        layout.add_widget(self.vorname_input)
        
        # Nachname Input
        nachname_label = Label(
            text="Nachname:",
            size_hint_y=None,
            height=dp(30),
            font_size='14sp'
        )
        layout.add_widget(nachname_label)
        
        self.nachname_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size='16sp'
        )
        layout.add_widget(self.nachname_input)
        
        # Buttons
        button_layout = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        cancel_btn = Button(
            text="Abbrechen",
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1)
        )
        cancel_btn.bind(on_release=self.cancel)
        button_layout.add_widget(cancel_btn)
        
        register_btn = Button(
            text="Registrieren",
            background_normal='',
            background_color=(0.102, 0.737, 0.612, 1)
        )
        register_btn.bind(on_release=self.register)
        button_layout.add_widget(register_btn)
        
        layout.add_widget(button_layout)
        
        self.content = layout
        
        # Fokus auf Vorname setzen
        self.vorname_input.focus = True
    
    def register(self, instance):
        """Registriert den neuen Benutzer"""
        vorname = self.vorname_input.text.strip()
        nachname = self.nachname_input.text.strip()
        
        if not vorname or not nachname:
            # TODO: Fehler anzeigen
            logger.warning("Vor- oder Nachname fehlt")
            return
        
        full_name = f"{vorname} {nachname}"
        
        try:
            self.on_register_callback(self.uid, full_name)
            self.dismiss()
        except Exception as e:
            logger.exception("Fehler bei der Registrierung: %s", e)
            # TODO: Fehler-Dialog anzeigen
    
    def cancel(self, instance):
        """Bricht die Registrierung ab"""
        self.dismiss()