"""Configuration loaded from .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Rekordbox
REKORDBOX_DB_PATH = Path(os.getenv("REKORDBOX_DB_PATH",
    r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\master.db"))
REKORDBOX_XML_PATH = Path(os.getenv("REKORDBOX_XML_PATH",
    r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\masterPlaylists6.xml"))
SQLCIPHER_KEY = os.getenv("SQLCIPHER_KEY",
    "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497")

# Music library
MUSIC_LIBRARY_ROOT = Path(os.getenv("MUSIC_LIBRARY_ROOT",
    r"C:\Users\gonza\Documents\Music"))
MUSIC_NEW_FOLDER = Path(os.getenv("MUSIC_NEW_FOLDER",
    r"C:\Users\gonza\Documents\Music\2026\Nuevos\Inbox"))
DOWNLOADS_FOLDER = Path(os.getenv("DOWNLOADS_FOLDER",
    r"C:\Users\gonza\Downloads"))

# Backups
BACKUP_FOLDER = Path(os.getenv("BACKUP_FOLDER",
    r"C:\Users\gonza\Music\plomo\outputs"))
BACKUP_RETENTION = int(os.getenv("BACKUP_RETENTION", "10"))

# OneDrive no se usa (2026-10-19, ver CLAUDE.md). Con la cuota llena dejo 62 GB
# como placeholders que nunca subio, y un .env viejo volveria a llenarlo sin que
# nadie lo note. Se corta aca, antes de que cualquier script escriba una ruta.
for _nombre, _ruta in (("MUSIC_LIBRARY_ROOT", MUSIC_LIBRARY_ROOT),
                       ("MUSIC_NEW_FOLDER", MUSIC_NEW_FOLDER),
                       ("BACKUP_FOLDER", BACKUP_FOLDER)):
    if "onedrive" in str(_ruta).lower():
        raise RuntimeError(f"{_nombre} apunta adentro de OneDrive ({_ruta}). "
                           "OneDrive no se usa: corregir el .env.")

BACKUP_FOLDER.mkdir(parents=True, exist_ok=True)

# Spotify
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
