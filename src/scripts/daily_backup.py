from core.backup_manager import BackupManager

bm = BackupManager(
    db_path="/home/pi/kaffeekasse_v1/db/kaffeekasse.db",
    usb_path="/media/usb",
    network_path="//192.168.1.100/kaffeekasse"
)
result = bm.backup_all()
print(result)
