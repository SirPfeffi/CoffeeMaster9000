from peewee import *
from datetime import datetime
import os
from playhouse.migrate import SqliteMigrator, migrate

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
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    role = CharField(default="user")
    balance_cents = IntegerField(default=0)
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=True)

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
    kind = CharField(default="legacy")
    coffee_count = IntegerField(default=0)
    unit_price_cents = IntegerField(default=0)
    kg_bought = IntegerField(null=True)
    reference = CharField(null=True)
    metadata_json = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now)


class AdminUser(BaseModel):
    username = CharField(unique=True)
    password_hash = CharField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    last_login_at = DateTimeField(null=True)


class Setting(BaseModel):
    key = CharField(unique=True)
    value = TextField()
    updated_at = DateTimeField(default=datetime.now)


class BackupRun(BaseModel):
    target = CharField()
    status = CharField()
    retries = IntegerField(default=0)
    details = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)


class MachineEvent(BaseModel):
    source = CharField()
    event_type = CharField()
    count = IntegerField(default=1)
    details = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)


def _column_exists(table_name: str, column_name: str) -> bool:
    return any(column.name == column_name for column in db.get_columns(table_name))


def _safe_add_column(table_name: str, column_name: str, field):
    if not _column_exists(table_name, column_name):
        migrator = SqliteMigrator(db)
        migrate(migrator.add_column(table_name, column_name, field))


def _ensure_user_schema():
    _safe_add_column("user", "username", CharField(null=True))
    _safe_add_column("user", "first_name", CharField(null=True))
    _safe_add_column("user", "last_name", CharField(null=True))
    _safe_add_column("user", "role", CharField(default="user"))
    _safe_add_column("user", "is_active", BooleanField(default=True))
    db.execute_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_username_unique "
        "ON user(username) WHERE username IS NOT NULL;"
    )


def _ensure_transaction_schema():
    _safe_add_column("transaction", "kind", CharField(default="legacy"))
    _safe_add_column("transaction", "coffee_count", IntegerField(default=0))
    _safe_add_column("transaction", "unit_price_cents", IntegerField(default=0))
    _safe_add_column("transaction", "kg_bought", IntegerField(null=True))
    _safe_add_column("transaction", "reference", CharField(null=True))
    _safe_add_column("transaction", "metadata_json", TextField(null=True))


def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([User, Transaction, AdminUser, Setting, BackupRun, MachineEvent], safe=True)
    _ensure_user_schema()
    _ensure_transaction_schema()
