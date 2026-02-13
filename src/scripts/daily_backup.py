import os

from core.backup_manager import BackupManager
from db.models import DB_PATH, init_db


def main():
    init_db()
    usb_path = os.environ.get("COFFEEMASTER_USB_BACKUP_PATH", "/media/usb")
    network_path = os.environ.get("COFFEEMASTER_NETWORK_BACKUP_PATH")
    db_path = os.environ.get("COFFEEMASTER_DB_PATH", DB_PATH)

    manager = BackupManager(
        db_path=db_path,
        usb_path=usb_path,
        network_path=network_path,
    )
    result = manager.backup_all()
    print(result)


if __name__ == "__main__":
    main()
