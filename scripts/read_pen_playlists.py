import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

try:
    from pyrekordbox.pdb import PioneerDatabase
    db = PioneerDatabase("D:/PIONEER/rekordbox/export.pdb")
    playlists = list(db.playlists.values()) if hasattr(db.playlists, 'values') else list(db.playlists)
    print(f"Playlists en pen ({len(playlists)}):")
    for pl in playlists:
        name = getattr(pl, 'name', getattr(pl, 'Name', str(pl)))
        print(f"  {name[:70]}")
except Exception as e:
    print(f"Error pdb: {e}")
    # Fallback: intentar leer raw
    import struct
    with open("D:/PIONEER/rekordbox/export.pdb", 'rb') as f:
        data = f.read(200)
    print(f"Raw header: {data[:32].hex()}")
    # Buscar strings legibles
    text = data.decode('utf-8', errors='replace')
    print(f"Text: {repr(text[:100])}")
