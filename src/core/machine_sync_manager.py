import os
from datetime import datetime

from integrations.we8 import WE8Client
from db.models import MachineEvent, db


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class MachineSyncManager:
    def __init__(self, client: WE8Client):
        self.client = client
        self.last_polled_at = None
        self.last_brew_counter = None
        self.last_error = ""

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    @classmethod
    def from_env(cls):
        client = WE8Client(
            enabled=_env_bool("COFFEEMASTER_WE8_ENABLED", False),
            host=os.environ.get("COFFEEMASTER_WE8_HOST", ""),
            port=int(os.environ.get("COFFEEMASTER_WE8_PORT", "80")),
            timeout_seconds=float(os.environ.get("COFFEEMASTER_WE8_TIMEOUT_SECONDS", "2.0")),
            simulate=_env_bool("COFFEEMASTER_WE8_SIMULATE", False),
        )
        return cls(client=client)

    def status(self):
        status = self.client.status()
        return {
            "enabled": status.enabled,
            "configured": status.configured,
            "connected": status.connected,
            "message": status.message,
            "last_checked_at": status.last_checked_at,
            "last_polled_at": self.last_polled_at,
            "last_brew_counter": self.last_brew_counter,
            "last_error": self.last_error,
        }

    def poll_once(self):
        self.last_polled_at = datetime.now()
        try:
            counter = self.client.read_brew_counter()
            if counter is None:
                return []
            events = []
            if self.last_brew_counter is not None and counter > self.last_brew_counter:
                delta = counter - self.last_brew_counter
                event = {
                    "event": "coffee_brewed",
                    "delta": delta,
                    "counter": counter,
                    "timestamp": self.last_polled_at,
                }
                events.append(event)
                with db.atomic():
                    MachineEvent.create(
                        source="we8",
                        event_type="coffee_brewed",
                        count=delta,
                        details=str(event),
                    )
            self.last_brew_counter = counter
            self.last_error = ""
            return events
        except Exception as exc:
            self.last_error = str(exc)
            return []
