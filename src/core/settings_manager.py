from datetime import datetime

from core.config import CONFIG
from db.models import Setting


class SettingsManager:
    def _get_setting(self, key: str):
        try:
            return Setting.get(Setting.key == key).value
        except Setting.DoesNotExist:
            return None

    def _set_setting(self, key: str, value: str):
        setting, _ = Setting.get_or_create(key=key, defaults={"value": value})
        setting.value = value
        setting.updated_at = datetime.now()
        setting.save()

    def get_bool(self, key: str, default: bool) -> bool:
        value = self._get_setting(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def set_bool(self, key: str, value: bool):
        self._set_setting(key, "1" if value else "0")

    def get_registration_policy(self):
        return {
            "allow_self_registration": self.get_bool("allow_self_registration", CONFIG.allow_self_registration),
            "rfid_reassignment_admin_only": self.get_bool(
                "rfid_reassignment_admin_only",
                CONFIG.rfid_reassignment_admin_only,
            ),
        }
