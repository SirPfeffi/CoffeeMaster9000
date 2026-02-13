import hashlib
import hmac
import os
from datetime import datetime

from db.models import AdminUser, db


def _hash_password(password: str, salt: bytes = None) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = encoded.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = _hash_password(password, salt=bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, encoded)


class AuthManager:
    def create_admin(self, username: str, password: str):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        password_hash = _hash_password(password)
        with db.atomic():
            admin, created = AdminUser.get_or_create(
                username=username,
                defaults={
                    "password_hash": password_hash,
                    "is_active": True,
                },
            )
            if not created:
                admin.password_hash = password_hash
                admin.is_active = True
                admin.save()
        return admin

    def verify_admin(self, username: str, password: str):
        username = (username or "").strip()
        if not username or not password:
            return None
        try:
            admin = AdminUser.get((AdminUser.username == username) & (AdminUser.is_active == True))
        except AdminUser.DoesNotExist:
            return None
        if not _verify_password(password, admin.password_hash):
            return None
        admin.last_login_at = datetime.now()
        admin.save()
        return admin
