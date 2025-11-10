from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.properties import StringProperty
from core.account_manager import AccountManager
from db.models import User
import logging

logger = logging.getLogger(__name__)

class UserManagementScreen(Screen):
    """Screen zur Verwaltung von Benutzern (nur für Admins)"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.am = AccountManager()
        self.current_admin = None
        self.build_ui()
    
    def build_ui(self):
        """Erstellt die UI"""
        main_layout = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(12))
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(60))
        title = Label(
            text="Benutzerverwaltung",
            font_size='24sp',
            bold=True,
            color=(0.12, 0.12, 0.12, 1)
        )
        header.add_widget(title)
        main_layout.add_widget(header)
        
        # ScrollView für Benutzerliste
        scroll = ScrollView(size_hint=(1, 1))
        self.user_list_layout = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        self.user_list_layout.bind(minimum_height=self.user_list_layout.setter('height'))
        scroll.add_widget(self.user_list_layout)
        main_layout.add_widget(scroll)
        
        # Zurück-Button
        back_btn = Button(
            text="Zurück",
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_release=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def on_pre_enter(self):
        """Wird aufgerufen bevor der Screen angezeigt wird"""
        self.load_users()
    
    def load_users(self):
        """Lädt alle Benutzer und zeigt sie an"""
        self.user_list_layout.clear_widgets()
        
        try:
            users = self.am.get_all_users()
            
            for user in users:
                user_box = self.create_user_widget(user)
                self.user_list_layout.add_widget(user_box)
                
        except Exception as e:
            logger.exception("Fehler beim Laden der Benutzer: %s", e)
    
    def create_user_widget(self, user):
        """Erstellt ein Widget für einen Benutzer"""
        box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Canvas für Hintergrund
        from kivy.graphics import Color, RoundedRectangle
        with box.canvas.before:
            Color(1, 1, 1, 1)
            box.rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[8,])
        
        box.bind(pos=lambda inst, val: setattr(inst.rect, 'pos', val))
        box.bind(size=lambda inst, val: setattr(inst.rect, 'size', val))
        
        # Benutzer-Info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        name_label = Label(
            text=user.name,
            font_size='18sp',
            bold=True,
            color=(0.1, 0.1, 0.1, 1),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        info_layout.add_widget(name_label)
        
        details = f"Guthaben: {user.balance:.2f} € | UID: {user.rfid_uid[:8]}..."
        if user.is_admin:
            details += " | ADMIN"
        
        details_label = Label(
            text=details,
            font_size='14sp',
            color=(0.4, 0.4, 0.4, 1),
            halign='left',
            valign='middle'
        )
        details_label.bind(size=details_label.setter('text_size'))
        info_layout.add_widget(details_label)
        
        box.add_widget(info_layout)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=dp(5))
        
        edit_btn = Button(
            text="Bearbeiten",
            background_normal='',
            background_color=(0.2, 0.6, 0.86, 1),
            size_hint_x=0.5
        )
        edit_btn.bind(on_release=lambda x: self.edit_user(user))
        button_layout.add_widget(edit_btn)
        
        delete_btn = Button(
            text="Löschen",
            background_normal='',
            background_color=(0.839, 0.153, 0.157, 1),
            size_hint_x=0.5
        )
        delete_btn.bind(on_release=lambda x: self.confirm_delete_user(user))
        button_layout.add_widget(delete_btn)
        
        box.add_widget(button_layout)
        
        return box
    
    def edit_user(self, user):
        """Öffnet Dialog zum Bearbeiten eines Benutzers"""
        dialog = EditUserDialog(user=user, on_save_callback=self.save_user_changes)
        dialog.open()
    
    def save_user_changes(self, user, new_name, is_admin):
        """Speichert Änderungen an einem Benutzer"""
        try:
            self.am.update_user(user, name=new_name, is_admin=is_admin)
            logger.info("Benutzer aktualisiert: %s", new_name)
            self.load_users()  # Liste neu laden
        except Exception as e:
            logger.exception("Fehler beim Aktualisieren des Benutzers: %s", e)
    
    def confirm_delete_user(self, user):
        """Bestätigungsdialog zum Löschen eines Benutzers"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        label = Label(
            text=f"Möchtest du {user.name} wirklich löschen?\n\nAlle Transaktionen werden ebenfalls gelöscht!",
            size_hint_y=None,
            height=dp(80)
        )
        content.add_widget(label)
        
        button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        popup = Popup(
            title="Benutzer löschen?",
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        
        cancel_btn = Button(
            text="Abbrechen",
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1)
        )
        cancel_btn.bind(on_release=popup.dismiss)
        button_layout.add_widget(cancel_btn)
        
        delete_btn = Button(
            text="Löschen",
            background_normal='',
            background_color=(0.839, 0.153, 0.157, 1)
        )
        delete_btn.bind(on_release=lambda x: self.delete_user(user, popup))
        button_layout.add_widget(delete_btn)
        
        content.add_widget(button_layout)
        popup.open()
    
    def delete_user(self, user, popup):
        """Löscht einen Benutzer"""
        try:
            self.am.delete_user(user)
            logger.info("Benutzer gelöscht: %s", user.name)
            popup.dismiss()
            self.load_users()  # Liste neu laden
        except Exception as e:
            logger.exception("Fehler beim Löschen des Benutzers: %s", e)
            popup.dismiss()
    
    def go_back(self, instance):
        """Kehrt zum Admin-Screen zurück"""
        if self.manager:
            self.manager.current = 'admin'


class EditUserDialog(Popup):
    """Dialog zum Bearbeiten eines Benutzers"""
    
    def __init__(self, user, on_save_callback, **kwargs):
        self.user = user
        self.on_save_callback = on_save_callback
        
        super().__init__(
            title=f"Benutzer bearbeiten: {user.name}",
            size_hint=(0.8, 0.5),
            auto_dismiss=False,
            **kwargs
        )
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Name Input
        name_label = Label(
            text="Name:",
            size_hint_y=None,
            height=dp(30),
            font_size='14sp'
        )
        layout.add_widget(name_label)
        
        self.name_input = TextInput(
            text=user.name,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size='16sp'
        )
        layout.add_widget(self.name_input)
        
        # Admin Checkbox (simple Button Toggle)
        admin_layout = BoxLayout(size_hint_y=None, height=dp(50))
        admin_label = Label(text="Admin-Rechte:", font_size='14sp')
        admin_layout.add_widget(admin_label)
        
        self.admin_btn = Button(
            text="JA" if user.is_admin else "NEIN",
            background_normal='',
            background_color=(0.102, 0.737, 0.612, 1) if user.is_admin else (0.5, 0.5, 0.5, 1),
            size_hint_x=0.3
        )
        self.admin_btn.bind(on_release=self.toggle_admin)
        admin_layout.add_widget(self.admin_btn)
        
        layout.add_widget(admin_layout)
        
        # Info
        info_label = Label(
            text=f"UID: {user.rfid_uid}\nGuthaben: {user.balance:.2f} €",
            size_hint_y=None,
            height=dp(50),
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(info_label)
        
        # Buttons
        button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(
            text="Abbrechen",
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1)
        )
        cancel_btn.bind(on_release=self.dismiss)
        button_layout.add_widget(cancel_btn)
        
        save_btn = Button(
            text="Speichern",
            background_normal='',
            background_color=(0.102, 0.737, 0.612, 1)
        )
        save_btn.bind(on_release=self.save)
        button_layout.add_widget(save_btn)
        
        layout.add_widget(button_layout)
        
        self.content = layout
    
    def toggle_admin(self, instance):
        """Toggle Admin-Status"""
        is_admin = self.admin_btn.text == "JA"
        self.admin_btn.text = "NEIN" if is_admin else "JA"
        self.admin_btn.background_color = (0.5, 0.5, 0.5, 1) if is_admin else (0.102, 0.737, 0.612, 1)
    
    def save(self, instance):
        """Speichert die Änderungen"""
        new_name = self.name_input.text.strip()
        
        if not new_name:
            logger.warning("Name darf nicht leer sein")
            return
        
        is_admin = self.admin_btn.text == "JA"
        
        self.on_save_callback(self.user, new_name, is_admin)
        self.dismiss()