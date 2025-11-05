from decimal import Decimal, InvalidOperation
from peewee import SqliteDatabase
from db.models import User, Transaction, db
import logging

logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self):
        self.db = db

    def euro_str_to_cents(self, value) -> int:
        try:
            d = Decimal(str(value)).quantize(Decimal("0.01"))
            return int(d * 100)
        except InvalidOperation as e:
            logger.error("Ungültiger Betrag: %s", e)
            raise ValueError("Ungültiger Betrag")

    def create_user(self, rfid_uid: str, name: str, initial_cents: int = 0):
        with self.db.atomic():
            user, created = User.get_or_create(
                rfid_uid=rfid_uid,
                defaults={"name": name, "balance_cents": initial_cents},
            )
            if not created:
                logger.warning("Benutzer mit RFID %s existiert bereits", rfid_uid)
            return user

    def get_user_by_uid(self, rfid_uid: str):
        try:
            return User.get(User.rfid_uid == rfid_uid)
        except User.DoesNotExist:
            return None

    def book_coffee(self, user: User, amount_euro="0.17"):
        cents = self.euro_str_to_cents(amount_euro)
        with self.db.atomic():
            user = User.get_by_id(user.id)
            if user.balance_cents - cents < 0:
                raise ValueError("Nicht genügend Guthaben.")
            user.balance_cents -= cents
            user.save()
            Transaction.create(user=user, amount_cents=-cents, description="Kaffee")
        logger.info("Kaffee gebucht für %s (%.2f €)", user.name, cents / 100.0)

    def deposit(self, user: User, amount_euro):
        cents = self.euro_str_to_cents(amount_euro)
        with self.db.atomic():
            user.balance_cents += cents
            user.save()
            Transaction.create(user=user, amount_cents=cents, description="Einzahlung")
        logger.info("Einzahlung %.2f € für %s", cents / 100.0, user.name)