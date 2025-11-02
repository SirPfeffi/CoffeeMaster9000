from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

class StatsPopup(Popup):
    def __init__(self, account_manager, days=7, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Kaffeestatistik ({days} Tage)"
        self.size_hint = (0.9, 0.7)
        self.auto_dismiss = True

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        total = account_manager.get_total_coffee()
        layout.add_widget(Label(text=f"Gesamtanzahl gebuchter Kaffees: {total}", font_size=20))

        daily_counts = account_manager.get_daily_coffee_counts(days=days)

        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))

        for day, count in daily_counts.items():
            grid.add_widget(Label(text=f"{day}: {count} Kaffees", size_hint_y=None, height=30))

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        self.add_widget(layout)
