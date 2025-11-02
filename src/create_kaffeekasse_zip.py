import os, zipfile

base_dir = "kaffeekasse_v1"
os.makedirs(f"{base_dir}/core", exist_ok=True)
os.makedirs(f"{base_dir}/gui", exist_ok=True)

# Hauptdateien
files = {
    f"{base_dir}/main.py": """import threading
from kivy.app import App
from kivy.clock import Clock
from gui.main_screen import MainScreen
from core.rfid_manager import RFIDReader

class KaffeeKasseApp(App):
    def build(self):
        self.title = "Kaffeekasse"
        self.screen = MainScreen()
        self.rfid = RFIDReader(callback=self.on_card_detected)
        threading.Thread(target=self.rfid.run, daemon=True).start()
        return self.screen

    def on_card_detected(self, uid: str):
        Clock.schedule_once(lambda dt: self.screen.display_card(uid))

if __name__ == '__main__':
    KaffeeKasseApp().run()
""",
    f"{base_dir}/core/rfid_manager.py": """from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time

class RFIDReader:
    def __init__(self, callback):
        self.reader = SimpleMFRC522()
        self.callback = callback
        self.running = True

    def run(self):
        print("[RFID] Reader gestartet. Bitte Karte auflegen...")
        while self.running:
            try:
                id, text = self.reader.read_no_block()
                if id:
                    uid = str(id)
                    print(f"[RFID] Karte erkannt: {uid}")
                    self.callback(uid)
                    time.sleep(2)
            except Exception as e:
                print(f"[RFID] Fehler: {e}")
                time.sleep(1)
        GPIO.cleanup()

    def stop(self):
        self.running = False
""",
    f"{base_dir}/gui/main_screen.py": """from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

class MainScreen(BoxLayout):
    message = StringProperty("Bitte Karte auflegen …")
    user_name = StringProperty("")
    balance = StringProperty("")

    def display_card(self, uid: str):
        self.user_name = f"UID: {uid}"
        self.balance = "Guthaben: 0.00 €"
        self.message = "Karte erkannt!"
""",
    f"{base_dir}/gui/app.kv": """<MainScreen>:
    orientation: "vertical"
    padding: 40
    spacing: 20

    Label:
        text: root.message
        font_size: '32sp'
        halign: 'center'
        valign: 'middle'

    Label:
        text: root.user_name
        font_size: '28sp'
        halign: 'center'

    Label:
        text: root.balance
        font_size: '28sp'
        halign: 'center'

    Button:
        text: "Kaffee buchen"
        font_size: '24sp'
        size_hint_y: None
        height: 80
        on_press: root.message = "Noch nicht implementiert"

    Button:
        text: "Beenden"
        font_size: '24sp'
        size_hint_y: None
        height: 80
        on_press: app.stop()
""",
    f"{base_dir}/requirements.txt": "kivy==2.3.0\nmfrc522==0.0.7\nspidev==3.6\n",
    f"{base_dir}/README_Inbetriebnahme.txt": """# Kaffeekasse v1 – Inbetriebnahme

## Installation
1. Raspberry Pi OS (Bookworm/Bullseye) installieren.
2. SPI aktivieren:
   sudo raspi-config → Interfacing Options → SPI → Enable
3. Abhängigkeiten:
   sudo apt update
   sudo apt install python3-pip python3-kivy python3-spidev
   pip install -r requirements.txt

## RC522 Anschluss
| RC522 Pin | Raspberry Pi Pin |
|------------|------------------|
| SDA        | GPIO8 (CE0)      |
| SCK        | GPIO11 (SCLK)    |
| MOSI       | GPIO10 (MOSI)    |
| MISO       | GPIO9 (MISO)     |
| GND        | GND              |
| RST        | GPIO25           |
| 3.3V       | 3.3V             |

## Start
python3 main.py

Nach dem Start zeigt der Bildschirm „Bitte Karte auflegen…“.  
Beim Auflegen einer Karte wird die UID angezeigt.
"""
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

zip_name = f"{base_dir}.zip"
with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
    for path in files.keys():
        z.write(path, arcname=os.path.relpath(path, base_dir))

print(f"ZIP-Paket erstellt: {zip_name}")
