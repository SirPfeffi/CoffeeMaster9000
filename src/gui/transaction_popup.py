from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

class TransactionPopup(Popup):
    def __init__(self, user, manager, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Letzte Buchungen von {user.name}"
        self.size_hint = (0.9, 0.7)
        self.auto_dismiss = True

        transactions = manager.get_last_transactions(user, limit=10)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        if transactions:
            for t in transactions:
                label = Label(text=f"{t.timestamp.strftime('%d.%m.%Y %H:%M')} | {t.description} | {t.amount:+.2f} €",
                              size_hint_y=None, height=30)
                grid.add_widget(label)
        else:
            grid.add_widget(Label(text="Keine Buchungen vorhanden", size_hint_y=None, height=30))

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        self.add_widget(layout)
