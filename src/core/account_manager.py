from decimal import Decimal, InvalidOperation
from db.models import User, Transaction, db
import logging

logger = logging.getLogger(__name__)

class AccountManager:
    """Verwaltet Benutzerkonten und Transaktionen"""
    
    def euro_str_to_cents(self, value) -> int:
        """Konvertiert Euro-String oder Float zu Cents"""
        try:
            d = Decimal(str(value)).quantize(Decimal("0.01"))
            return int(d * 100)
        except (InvalidOperation, ValueError) as e:
            logger.error("Ungültiger Betrag: %s", e)
            raise ValueError(f"Ungültiger Betrag: {value}")

    def create_user(self, rfid_uid: str, name: str, initial_cents: int = 0, is_admin: bool = False):
        """Erstellt einen neuen Benutzer"""
        with db.atomic():
            user, created = User.get_or_create(
                rfid_uid=rfid_uid,
                defaults={
                    "name": name,
                    "balance_cents": initial_cents,
                    "is_admin": is_admin
                },
            )
            if not created:
                logger.warning("Benutzer mit RFID %s existiert bereits", rfid_uid)
            else:
                logger.info("Benutzer erstellt: %s (%s)", name, rfid_uid)
            return user

    def get_user_by_uid(self, rfid_uid: str):
        """Gibt Benutzer anhand der RFID-UID zurück"""
        try:
            return User.get(User.rfid_uid == rfid_uid)
        except User.DoesNotExist:
            logger.warning("Benutzer mit UID %s nicht gefunden", rfid_uid)
            return None

    def get_all_users(self):
        """Gibt alle Benutzer zurück"""
        return User.select().order_by(User.name)

    def book_coffee(self, user: User, amount_euro="0.17"):
        """Bucht einen Kaffee für den Benutzer"""
        cents = self.euro_str_to_cents(amount_euro)
        with db.atomic():
            # Benutzer neu aus DB laden um Race Conditions zu vermeiden
            user = User.get_by_id(user.id)
            if user.balance_cents - cents < 0:
                raise ValueError("Nicht genügend Guthaben.")
            user.balance_cents -= cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=-cents,
                description="Kaffee"
            )
        logger.info("Kaffee gebucht für %s (%.2f €)", user.name, cents / 100.0)

    def deposit(self, user: User, amount_euro):
        """Bucht eine Einzahlung für den Benutzer"""
        cents = self.euro_str_to_cents(amount_euro)
        if cents <= 0:
            raise ValueError("Einzahlungsbetrag muss positiv sein")
        
        with db.atomic():
            user = User.get_by_id(user.id)
            user.balance_cents += cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=cents,
                description="Einzahlung"
            )
        logger.info("Einzahlung %.2f € für %s", cents / 100.0, user.name)

    def get_user_transactions(self, user: User, limit: int = 10):
        """Gibt die letzten Transaktionen eines Benutzers zurück"""
        return (Transaction
                .select()
                .where(Transaction.user == user)
                .order_by(Transaction.timestamp.desc())
                .limit(limit))

    def update_user(self, user: User, name: str = None, is_admin: bool = None):
        """Aktualisiert Benutzerdaten"""
        with db.atomic():
            user = User.get_by_id(user.id)
            if name is not None:
                user.name = name
            if is_admin is not None:
                user.is_admin = is_admin
            user.save()
        logger.info("Benutzer aktualisiert: %s", user.name)
        return user

    def delete_user(self, user: User):
        """Löscht einen Benutzer (und alle Transaktionen via CASCADE)"""
        user_name = user.name
        with db.atomic():
            user.delete_instance()
        logger.info("Benutzer gelöscht: %s", user_name)