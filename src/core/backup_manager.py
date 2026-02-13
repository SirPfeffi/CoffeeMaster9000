from datetime import datetime
from pathlib import Path
import shutil
import sqlite3

from db.models import BackupRun


class BackupManager:
    def __init__(
        self,
        db_path: str,
        usb_path: str = "/media/usb",
        network_path: str = None,
        max_retries: int = 10,
    ):
        self.db_path = Path(db_path)
        self.usb_path = Path(usb_path)
        self.network_path = Path(network_path) if network_path else None
        self.max_retries = max_retries

    def _timestamped_filename(self) -> str:
        return f"kaffeekasse_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    def _consecutive_failures(self, target: str) -> int:
        count = 0
        runs = BackupRun.select().where(BackupRun.target == target).order_by(BackupRun.created_at.desc()).limit(100)
        for run in runs:
            if run.status == "success":
                break
            count += 1
        return count

    def _record_run(self, target: str, status: str, details: str = None):
        retries = 0 if status == "success" else self._consecutive_failures(target) + 1
        if status in {"failed", "alert"} and retries >= self.max_retries:
            status = "alert"
        BackupRun.create(
            target=target,
            status=status,
            retries=retries,
            details=details,
        )

    def _backup_to_target(self, target_name: str, target_path: Path):
        if not target_path.exists():
            raise FileNotFoundError(f"Backup target not found: {target_path}")
        backup_file = target_path / self._timestamped_filename()
        shutil.copy2(self.db_path, backup_file)
        self._record_run(target_name, "success", str(backup_file))
        return backup_file

    def backup_to_usb(self):
        try:
            return self._backup_to_target("usb", self.usb_path)
        except Exception as exc:
            self._record_run("usb", "failed", str(exc))
            raise

    def backup_to_network(self):
        if not self.network_path:
            raise ValueError("No network path configured.")
        try:
            return self._backup_to_target("network", self.network_path)
        except Exception as exc:
            self._record_run("network", "failed", str(exc))
            raise

    def backup_all(self):
        results = {}
        try:
            results["usb"] = self.backup_to_usb()
        except Exception as exc:
            results["usb"] = f"Error: {exc}"

        if self.network_path:
            try:
                results["network"] = self.backup_to_network()
            except Exception as exc:
                results["network"] = f"Error: {exc}"

        return results

    def recent_runs(self, limit: int = 30):
        return list(BackupRun.select().order_by(BackupRun.created_at.desc()).limit(limit))

    def _allowed_roots(self):
        roots = [self.usb_path.resolve()]
        if self.network_path:
            roots.append(self.network_path.resolve())
        return roots

    def _is_allowed_backup_file(self, candidate: Path) -> bool:
        candidate_resolved = candidate.resolve()
        for root in self._allowed_roots():
            if root in [candidate_resolved, *candidate_resolved.parents]:
                return True
        return False

    def list_backup_files(self):
        files = []
        targets = [("usb", self.usb_path)]
        if self.network_path:
            targets.append(("network", self.network_path))

        for target_name, target_path in targets:
            if not target_path.exists():
                continue
            for file in sorted(target_path.glob("kaffeekasse_backup_*.db"), reverse=True):
                stat = file.stat()
                files.append(
                    {
                        "target": target_name,
                        "path": str(file),
                        "name": file.name,
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime),
                    }
                )
        files.sort(key=lambda item: item["modified_at"], reverse=True)
        return files

    def preview_restore(self, backup_file_path: str):
        backup_file = Path(backup_file_path)
        if not backup_file.exists():
            raise FileNotFoundError("Backup file not found.")
        if not self._is_allowed_backup_file(backup_file):
            raise PermissionError("Backup file is outside allowed directories.")

        with sqlite3.connect(str(backup_file)) as conn:
            cursor = conn.cursor()
            user_count = cursor.execute("SELECT COUNT(*) FROM user").fetchone()[0]
            transaction_count = cursor.execute("SELECT COUNT(*) FROM \"transaction\"").fetchone()[0]
            newest_tx = cursor.execute(
                "SELECT MAX(timestamp) FROM \"transaction\""
            ).fetchone()[0]

        current_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        backup_size = backup_file.stat().st_size
        return {
            "backup_path": str(backup_file),
            "users": user_count,
            "transactions": transaction_count,
            "newest_transaction_timestamp": newest_tx,
            "current_db_size_bytes": current_size,
            "backup_db_size_bytes": backup_size,
        }

    def restore_from_backup(self, backup_file_path: str):
        backup_file = Path(backup_file_path)
        if not backup_file.exists():
            raise FileNotFoundError("Backup file not found.")
        if not self._is_allowed_backup_file(backup_file):
            raise PermissionError("Backup file is outside allowed directories.")

        pre_restore_file = self.db_path.parent / f"pre_restore_{self._timestamped_filename()}"
        if self.db_path.exists():
            shutil.copy2(self.db_path, pre_restore_file)

        shutil.copy2(backup_file, self.db_path)
        self._record_run("restore", "success", f"Restored from {backup_file}")
        return {"restored_from": str(backup_file), "pre_restore_backup": str(pre_restore_file)}
