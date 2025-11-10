from peewee import *
from datetime import datetime
import os

# Sicherstellen, dass das data-Verzeichnis existiert
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "coffee.db")
db = SqliteDatabase(DB_PATH, pragmas={"foreign_keys": 1})

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    rfid_uid = CharField(unique=True)
    name = CharField()
    balance_cents = IntegerField(default=0)
    is_admin = BooleanField(default=False)

    @property
    def balance(self) -> float:
        return self.balance_cents / 100.0

    def deposit_cents(self, cents: int):
        self.balance_cents += cents
        self.save()

class Transaction(BaseModel):
    user = ForeignKeyField(User, backref="transactions", on_delete="CASCADE")
    amount_cents = IntegerField()
    description = CharField()
    timestamp = DateTimeField(default=datetime.now)

def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([User, Transaction], safe=True)