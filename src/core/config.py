import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppConfig:
    coffee_price_cents: int = int(os.environ.get("COFFEE_PRICE_CENTS", "17"))
    max_coffees_per_booking: int = int(os.environ.get("MAX_COFFEES_PER_BOOKING", "10"))
    booking_cooldown_seconds: int = int(os.environ.get("BOOKING_COOLDOWN_SECONDS", "5"))
    low_balance_threshold_cents: int = int(os.environ.get("LOW_BALANCE_THRESHOLD_CENTS", "0"))
    critical_balance_threshold_cents: int = int(os.environ.get("CRITICAL_BALANCE_THRESHOLD_CENTS", "-2500"))
    max_topup_kg: int = int(os.environ.get("MAX_TOPUP_KG", "5"))
    max_topup_cents: int = int(os.environ.get("MAX_TOPUP_CENTS", "10000"))
    duplicate_topup_window_seconds: int = int(os.environ.get("DUPLICATE_TOPUP_WINDOW_SECONDS", "60"))
    allow_self_registration: bool = _env_bool("ALLOW_SELF_REGISTRATION", True)
    rfid_reassignment_admin_only: bool = _env_bool("RFID_REASSIGNMENT_ADMIN_ONLY", False)


CONFIG = AppConfig()
