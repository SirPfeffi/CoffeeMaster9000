# SW

## Backend/General control

- Python for everything?

## Logging

- Set log level and log every action for it

## Database

(is it even needed?)

- SQL via SQLAlchemy package in Python?

## Frontend

### GUI

- QT?
- Python Tkinter/CustomTkinter (<https://customtkinter.tomschimansky.com/>)

### Webpage

#### FLASK?

ChatGPT-generated architecture

kaffeekasse/
│
├── main.py                       # Einstiegspunkt für das Gesamtsystem
│
├── gui/                          # Kivy-basierte Benutzeroberfläche
│   ├── __init__.py
│   ├── screens/
│   │   ├── main_screen.py        # Startansicht, RFID-Warten
│   │   ├── account_screen.py     # Kontoansicht (Guthaben, Aktionen)
│   │   ├── payment_screen.py     # Einzahlung
│   │   ├── stats_screen.py       # Statistiken & Kaffeefakten
│   │   └── admin_screen.py       # Adminfunktionen
│   ├── widgets/                  # Reusable UI-Komponenten
│   │   ├── keypad.py             # Zahlenfeld für Einzahlungen
│   │   └── dialogs.py            # Bestätigungs-/Fehlermeldungen
│   └── app.kv                    # Kivy Layout-Definitionen
│
├── core/                         # Geschäftslogik
│   ├── __init__.py
│   ├── rfid_manager.py           # Kommunikation mit RC522
│   ├── account_manager.py        # Guthaben, Buchungen, Validierung
│   ├── transaction_manager.py    # Transaktionslogik
│   ├── stats_manager.py          # Statistikberechnungen
│   └── facts_provider.py         # Kaffee-Fakten aus JSON o. API
│
├── db/                           # Datenhaltung
│   ├── __init__.py
│   ├── models.py                 # ORM-Klassen (User, Transaction, etc.)
│   ├── database.py               # SQLite-Verbindung, Initialisierung
│   ├── backup.py                 # Backup-Logik (USB & NAS)
│   └── seeds.py                  # Beispiel-Datensätze (Admin-Karte etc.)
│
├── web/                          # Admin-Webinterface (Flask)
│   ├── __init__.py
│   ├── app.py                    # Flask-Serverstart
│   ├── routes/
│   │   ├── users.py              # Benutzerverwaltung
│   │   ├── transactions.py       # Transaktionsansicht
│   │   ├── stats.py              # Statistiken
│   │   └── auth.py               # Admin-Login
│   ├── templates/                # HTML-Dateien
│   └── static/                   # CSS, JS, Icons
│
├── config/
│   ├── settings.py               # globale Einstellungen
│   ├── logging.yaml              # Logging-Konfiguration
│   └── locale/                   # Sprachdateien (de.json, en.json)
│
├── tests/
│   ├── test_db.py
│   ├── test_rfid.py
│   └── test_core_logic.py
│
└── requirements.txt              # Abhängigkeiten
