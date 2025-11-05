# src/core/database.py
from peewee import SqliteDatabase
import os

# SQLite-Datei im Projektverzeichnis
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coffee.db")

# Peewee-DB-Objekt
db = SqliteDatabase(DB_PATH)


def initialize_database(models):
    """Erstellt Tabellen, falls sie noch nicht existieren."""
    with db:
        db.create_tables(models, safe=True)