# src/db/database.py
from peewee import SqliteDatabase
import os

# SQLite-Datei im Projektverzeichnis
# Erstellt automatisch das data-Verzeichnis falls es nicht existiert
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "coffee.db")

# Peewee-DB-Objekt
db = SqliteDatabase(DB_PATH, pragmas={"foreign_keys": 1})


def initialize_database(models):
    """Erstellt Tabellen, falls sie noch nicht existieren."""
    with db:
        db.create_tables(models, safe=True)