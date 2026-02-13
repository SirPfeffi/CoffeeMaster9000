import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WE8Status:
    enabled: bool
    configured: bool
    connected: bool
    message: str
    last_checked_at: datetime
    brew_counter: Optional[int] = None


class WE8Client:
    """Best-effort WE8 connectivity wrapper.

    This implementation is intentionally non-blocking for core functionality:
    if WE8 is unavailable, all methods return a status without raising fatal errors.
    """

    def __init__(
        self,
        enabled: bool = False,
        host: str = "",
        port: int = 80,
        timeout_seconds: float = 2.0,
        simulate: bool = False,
    ):
        self.enabled = enabled
        self.host = (host or "").strip()
        self.port = int(port)
        self.timeout_seconds = float(timeout_seconds)
        self.simulate = bool(simulate)
        self._simulated_counter = 0

    @property
    def configured(self) -> bool:
        return bool(self.host)

    def status(self) -> WE8Status:
        now = datetime.now()
        if not self.enabled:
            return WE8Status(
                enabled=False,
                configured=self.configured,
                connected=False,
                message="WE8 integration disabled.",
                last_checked_at=now,
            )
        if self.simulate:
            return WE8Status(
                enabled=True,
                configured=True,
                connected=True,
                message="WE8 simulation mode active.",
                last_checked_at=now,
                brew_counter=self._simulated_counter,
            )
        if not self.configured:
            return WE8Status(
                enabled=True,
                configured=False,
                connected=False,
                message="WE8 host not configured.",
                last_checked_at=now,
            )

        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds):
                pass
            return WE8Status(
                enabled=True,
                configured=True,
                connected=True,
                message="WE8 reachable.",
                last_checked_at=now,
            )
        except OSError as exc:
            return WE8Status(
                enabled=True,
                configured=True,
                connected=False,
                message=f"WE8 unreachable: {exc}",
                last_checked_at=now,
            )

    def read_brew_counter(self) -> Optional[int]:
        """Placeholder for real WE8 protocol integration.

        In simulation mode we increment locally to validate end-to-end plumbing.
        """
        if not self.enabled:
            return None
        if self.simulate:
            self._simulated_counter += 1
            return self._simulated_counter
        return None
