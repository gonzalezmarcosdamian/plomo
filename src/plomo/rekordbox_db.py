"""Rekordbox SQLCipher DB wrapper with safety nets.

Encapsula:
- Backup automático antes de cada cambio
- Pre-flight check: rekordbox.exe no debe estar corriendo
- IDs 32-bit safe
- USN incremental
- masterPlaylists6.xml NODE auto-update
- DB integrity check
"""
import shutil
import time
import random
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import psutil
import sqlcipher3
from pyrekordbox.db6 import (
    Rekordbox6Database, DjmdContent, DjmdPlaylist,
    DjmdSongPlaylist, DjmdCue, DjmdKey, ContentCue
)

from . import config


class RekordboxRunningError(Exception):
    """Rekordbox.exe está corriendo - no se puede modificar la DB."""


class RekordboxDB:
    """Context manager seguro para tocar master.db."""

    def __init__(self, db_path: Optional[Path] = None, key: Optional[str] = None):
        self.db_path = db_path or config.REKORDBOX_DB_PATH
        self.xml_path = config.REKORDBOX_XML_PATH
        self.key = key or config.SQLCIPHER_KEY
        self.db: Optional[Rekordbox6Database] = None
        self._backup_path: Optional[Path] = None

    def __enter__(self):
        self._preflight_check()
        self._backup()
        self.db = Rekordbox6Database(path=str(self.db_path), key=self.key)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type is None:
                # Success: just close
                self.db.close()
            else:
                # Error: rollback + restore backup
                try:
                    self.db.session.rollback()
                except Exception:
                    pass
                self.db.close()
                if self._backup_path and self._backup_path.exists():
                    print(f"⚠️  Error during DB operation, restoring {self._backup_path.name}")
                    shutil.copy2(self._backup_path, self.db_path)

    def _preflight_check(self) -> None:
        """Verifica que rekordbox.exe NO esté corriendo."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'rekordbox' in proc.info['name'].lower():
                raise RekordboxRunningError(
                    f"Rekordbox is running (PID {proc.pid}). "
                    f"Close it via System Tray → Quit before continuing."
                )

    def _backup(self) -> None:
        """Crea backup de DB + XML antes de cualquier write."""
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._backup_path = config.BACKUP_FOLDER / f"master.db.backup-{ts}"
        shutil.copy2(self.db_path, self._backup_path)
        if self.xml_path.exists():
            shutil.copy2(self.xml_path, config.BACKUP_FOLDER / f"masterPlaylists6.xml.backup-{ts}")
        self._rotate_backups()

    def _rotate_backups(self) -> None:
        """Mantener últimos N backups (config.BACKUP_RETENTION)."""
        backups = sorted(
            config.BACKUP_FOLDER.glob("master.db.backup-*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old in backups[config.BACKUP_RETENTION:]:
            old.unlink()

    def integrity_check(self) -> str:
        """PRAGMA integrity_check. Returns 'ok' if all good."""
        con = sqlcipher3.connect(str(self.db_path))
        con.execute(f"PRAGMA key = '{self.key}'")
        result = con.execute("PRAGMA integrity_check").fetchone()[0]
        con.close()
        return result

    @staticmethod
    def safe_id() -> str:
        """Generate 32-bit safe ID (Rekordbox UI compatibility)."""
        return str(random.randint(1500000000, 4000000000))

    def get_max_usn(self, table: str = "djmdPlaylist") -> int:
        """Read MAX(rb_local_usn) for incremental USN assignment."""
        con = sqlcipher3.connect(str(self.db_path))
        con.execute(f"PRAGMA key = '{self.key}'")
        result = con.execute(f"SELECT MAX(rb_local_usn) FROM {table}").fetchone()[0]
        con.close()
        return result or 0

    def add_node_to_xml(self, playlist_id_int: int, parent_id_int: int) -> None:
        """Append <NODE> entry to masterPlaylists6.xml.

        Required so Rekordbox UI loads the playlist tracks.
        """
        if not self.xml_path.exists():
            return
        new_pl_hex = format(playlist_id_int, '08X')
        parent_hex = format(parent_id_int, '08X')
        ts_ms = int(time.time() * 1000)
        new_node = (
            f'    <NODE Id="{new_pl_hex}" ParentId="{parent_hex}" '
            f'Attribute="0" Timestamp="{ts_ms}" Lib_Type="0" CheckType="0"/>\n'
        )
        xml = self.xml_path.read_text()
        xml = xml.replace("  </PLAYLISTS>", new_node + "  </PLAYLISTS>")
        self.xml_path.write_text(xml)
