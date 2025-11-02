import shutil
import os
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, db_path: str, usb_path: str = "/media/usb", network_path: str = None):
        """
        db_path: Pfad zur SQLite-Datenbank
        usb_path: USB-Stick Pfad
        network_path: optionaler Netzwerkpfad (z. B. Samba)
        """
        self.db_path = Path(db_path)
        self.usb_path = Path(usb_path)
        self.network_path = Path(network_path) if network_path else None

    def backup_to_usb(self):
        if not self.usb_path.exists():
            raise FileNotFoundError(f"USB-Stick nicht gefunden unter {self.usb_path}")
        backup_file = self.usb_path / f"kaffeekasse_backup_{datetime.now().strftime('%Y%m%d')}.db"
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def backup_to_network(self):
        if not self.network_path:
            raise ValueError("Kein Netzwerkpfad konfiguriert.")
        if not self.network_path.exists():
            raise FileNotFoundError(f"Netzwerkpfad nicht erreichbar: {self.network_path}")
        backup_file = self.network_path / f"kaffeekasse_backup_{datetime.now().strftime('%Y%m%d')}.db"
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def backup_all(self):
        results = {}
        try:
            results["usb"] = self.backup_to_usb()
        except Exception as e:
            results["usb"] = f"Fehler: {e}"

        if self.network_path:
            try:
                results["network"] = self.backup_to_network()
            except Exception as e:
                results["network"] = f"Fehler: {e}"

        return results
