from core.account_manager import AccountManager
from core.settings_manager import SettingsManager
from db.models import User, db


class RegistrationManager:
    def __init__(self):
        self.am = AccountManager()
        self.settings = SettingsManager()

    def list_users_for_linking(self):
        return list(self.am.get_all_users())

    def resolve_scanned_uid(self, uid: str):
        return self.am.get_user_by_uid(uid)

    def register_or_link_unknown_uid(
        self,
        uid: str,
        mode: str,
        actor_is_admin: bool = False,
        full_name: str = None,
        user_id: int = None,
    ):
        existing = self.am.get_user_by_uid(uid)
        if existing:
            return existing

        policy = self.settings.get_registration_policy()
        if not policy["allow_self_registration"] and not actor_is_admin:
            raise PermissionError("Self-registration is disabled.")

        if mode == "create":
            clean_name = (full_name or "").strip()
            if not clean_name:
                raise ValueError("Name is required.")
            return self.am.create_user(rfid_uid=uid, name=clean_name, initial_cents=0, is_admin=False)

        if mode == "link":
            if policy["rfid_reassignment_admin_only"] and not actor_is_admin:
                raise PermissionError("RFID reassignment is admin-only.")
            if not user_id:
                raise ValueError("Target user is required.")
            target_user = User.get_or_none((User.id == int(user_id)) & (User.is_active == True))
            if not target_user:
                raise ValueError("Target user not found.")
            with db.atomic():
                target_user.rfid_uid = uid
                target_user.save()
            return target_user

        raise ValueError("Unsupported registration mode.")
