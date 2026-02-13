from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import logging

from core.config import CONFIG
from db.models import Transaction, User, db

logger = logging.getLogger(__name__)


class AccountManager:
    """Handles account and transaction operations."""

    def __init__(self):
        self._last_booking_by_uid = {}

    def euro_str_to_cents(self, value) -> int:
        """Convert euro string/number to cents."""
        try:
            raw = str(value).replace(",", ".")
            decimal_value = Decimal(raw).quantize(Decimal("0.01"))
            return int(decimal_value * 100)
        except (InvalidOperation, ValueError) as exc:
            logger.error("Invalid amount: %s", exc)
            raise ValueError(f"Invalid amount: {value}")

    def _split_name(self, name: str):
        parts = [part for part in name.strip().split() if part]
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])

    def _generate_username(self, first_name: str, last_name: str) -> str:
        base = f"{first_name}.{last_name}".strip(".").lower()
        base = "".join(ch if ch.isalnum() or ch == "." else "_" for ch in base)
        if not base:
            base = "user"
        candidate = base
        counter = 1
        while User.select().where(User.username == candidate).exists():
            counter += 1
            candidate = f"{base}{counter}"
        return candidate

    def _enforce_booking_cooldown(self, user: User):
        now = datetime.now()
        last_booking = self._last_booking_by_uid.get(user.rfid_uid)
        if last_booking and (now - last_booking).total_seconds() < CONFIG.booking_cooldown_seconds:
            raise ValueError(
                f"Please wait {CONFIG.booking_cooldown_seconds} seconds before booking again."
            )
        self._last_booking_by_uid[user.rfid_uid] = now

    def create_user(self, rfid_uid: str, name: str, initial_cents: int = 0, is_admin: bool = False):
        """Create a user if RFID is unknown, otherwise return existing user."""
        first_name, last_name = self._split_name(name)
        username = self._generate_username(first_name, last_name)

        with db.atomic():
            user, created = User.get_or_create(
                rfid_uid=rfid_uid,
                defaults={
                    "name": name,
                    "first_name": first_name or None,
                    "last_name": last_name or None,
                    "username": username,
                    "role": "admin" if is_admin else "user",
                    "balance_cents": initial_cents,
                    "is_admin": is_admin,
                    "is_active": True,
                },
            )

        if created:
            logger.info("Created user: %s (%s)", name, rfid_uid)
        else:
            logger.warning("User with RFID %s already exists", rfid_uid)
        return user

    def get_user_by_uid(self, rfid_uid: str):
        try:
            return User.get(User.rfid_uid == rfid_uid)
        except User.DoesNotExist:
            logger.warning("User with UID %s not found", rfid_uid)
            return None

    def get_user_by_username(self, username: str):
        try:
            return User.get(User.username == username)
        except User.DoesNotExist:
            return None

    def get_all_users(self):
        return User.select().where(User.is_active == True).order_by(User.name)

    def book_coffee(self, user: User, amount_euro=None, count: int = 1, enforce_cooldown: bool = True):
        """Book coffee; negative balances are allowed by design."""
        if count < 1 or count > CONFIG.max_coffees_per_booking:
            raise ValueError(f"Count must be between 1 and {CONFIG.max_coffees_per_booking}.")

        unit_price_cents = (
            self.euro_str_to_cents(amount_euro) if amount_euro is not None else CONFIG.coffee_price_cents
        )
        total_cents = unit_price_cents * count

        with db.atomic():
            user = User.get_by_id(user.id)
            if enforce_cooldown:
                self._enforce_booking_cooldown(user)
            user.balance_cents -= total_cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=-total_cents,
                description=f"Kaffee x{count}",
                kind="coffee",
                coffee_count=count,
                unit_price_cents=unit_price_cents,
            )

        logger.info("Booked coffee for %s: %d x %0.2f EUR", user.name, count, unit_price_cents / 100.0)
        return user

    def deposit(self, user: User, amount_euro):
        """Legacy manual top-up without kg metadata."""
        cents = self.euro_str_to_cents(amount_euro)
        if cents <= 0:
            raise ValueError("Deposit amount must be positive")

        with db.atomic():
            user = User.get_by_id(user.id)
            user.balance_cents += cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=cents,
                description="Einzahlung",
                kind="topup_manual",
            )
        logger.info("Deposited %0.2f EUR for %s", cents / 100.0, user.name)
        return user

    def topup_by_beans(self, user: User, kg: int, amount_euro, allow_zero: bool = True):
        if kg < 1 or kg > CONFIG.max_topup_kg:
            raise ValueError(f"Kg must be between 1 and {CONFIG.max_topup_kg}.")

        cents = self.euro_str_to_cents(amount_euro)
        if cents < 0:
            raise ValueError("Amount cannot be negative.")
        if cents == 0 and not allow_zero:
            raise ValueError("Amount cannot be zero.")
        if cents > CONFIG.max_topup_cents:
            raise ValueError(f"Amount cannot exceed {CONFIG.max_topup_cents / 100.0:.2f} EUR.")

        now = datetime.now()
        duplicate_window_start = now - timedelta(seconds=CONFIG.duplicate_topup_window_seconds)
        duplicate_exists = (
            Transaction.select()
            .where(
                (Transaction.user == user)
                & (Transaction.kind == "topup_beans")
                & (Transaction.amount_cents == cents)
                & (Transaction.kg_bought == kg)
                & (Transaction.timestamp >= duplicate_window_start)
            )
            .exists()
        )
        if duplicate_exists:
            raise ValueError("Potential duplicate top-up detected.")

        metadata = {"source": "beans", "kg": kg}
        with db.atomic():
            user = User.get_by_id(user.id)
            user.balance_cents += cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=cents,
                description=f"Bohnenkauf {kg} kg",
                kind="topup_beans",
                kg_bought=kg,
                reference="beans",
                metadata_json=json.dumps(metadata),
            )

        logger.info("Bean top-up for %s: %d kg, %0.2f EUR", user.name, kg, cents / 100.0)
        return user

    def add_correction(self, user: User, amount_euro, reason: str, reference: str = None):
        cents = self.euro_str_to_cents(amount_euro)
        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise ValueError("Correction reason is required.")

        with db.atomic():
            user = User.get_by_id(user.id)
            user.balance_cents += cents
            user.save()
            Transaction.create(
                user=user,
                amount_cents=cents,
                description=f"Korrektur: {clean_reason}",
                kind="correction",
                reference=reference,
            )

        logger.info("Correction for %s: %+0.2f EUR", user.name, cents / 100.0)
        return user

    def add_maintenance_entry(self, user: User, amount_euro, reason: str, affects_balance: bool = False):
        cents = self.euro_str_to_cents(amount_euro)
        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise ValueError("Maintenance reason is required.")
        if cents < 0:
            raise ValueError("Maintenance amount must be positive.")

        with db.atomic():
            user = User.get_by_id(user.id)
            if affects_balance:
                user.balance_cents -= cents
                user.save()
            Transaction.create(
                user=user,
                amount_cents=-cents,
                description=f"Maintenance: {clean_reason}",
                kind="maintenance",
                reference="maintenance",
            )

        logger.info("Maintenance entry for %s: -%0.2f EUR", user.name, cents / 100.0)
        return user

    def get_user_transactions(self, user: User, limit: int = 10):
        return (
            Transaction.select()
            .where(Transaction.user == user)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )

    def get_last_transactions(self, user: User, limit: int = 5):
        return self.get_user_transactions(user=user, limit=limit)

    def update_user(
        self,
        user: User,
        name: str = None,
        is_admin: bool = None,
        username: str = None,
        role: str = None,
        is_active: bool = None,
    ):
        with db.atomic():
            user = User.get_by_id(user.id)
            if name is not None:
                user.name = name
                first_name, last_name = self._split_name(name)
                user.first_name = first_name or None
                user.last_name = last_name or None
            if is_admin is not None:
                user.is_admin = is_admin
            if username is not None:
                existing = self.get_user_by_username(username)
                if existing and existing.id != user.id:
                    raise ValueError("Username already exists.")
                user.username = username
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active
            user.save()
        logger.info("Updated user: %s", user.name)
        return user

    def delete_user(self, user: User):
        """Legacy compatibility method: soft-delete via deactivation."""
        with db.atomic():
            user = User.get_by_id(user.id)
            user.is_active = False
            user.save()
        logger.info("Deactivated user: %s", user.name)
