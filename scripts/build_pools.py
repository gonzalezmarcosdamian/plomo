"""
Crea/actualiza playlists POOL organizadas por nivel de energia y key Camelot.
Usa TODA la libreria activa.

Pools creados (en carpeta "Por Posicion de Set"):
  [POOL] Warmup     E: 1.0 - 3.9
  [POOL] Build      E: 4.0 - 5.4
  [POOL] Mid        E: 5.5 - 6.4
  [POOL] Peak       E: 6.5 - 7.9
  [POOL] Peak+      E: 8.0+
  [POOL] Sin Energy (tracks sin calcular)

Dentro de cada pool: ordenados por Camelot (1A..12A, 1B..12B), luego BPM.

Uso:
  python scripts/build_pools.py
"""
import sys
import random
import uuid as uuid_lib
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
import sqlcipher3

POOL_FOLDER_NAME = "Por Posicion de Set"

POOLS = [
    ("[POOL] Warmup",     0.0,  3.9),
    ("[POOL] Build",      4.0,  5.4),
    ("[POOL] Mid",        5.5,  6.4),
    ("[POOL] Peak",       6.5,  7.9),
    ("[POOL] Peak+",      8.0, 99.0),
]

CAMELOT_ORDER = [
    "1A","2A","3A","4A","5A","6A","7A","8A","9A","10A","11A","12A",
    "1B","2B","3B","4B","5B","6B","7B","8B","9B","10B","11B","12B",
]

def camelot_sort_key(key_str: str) -> int:
    k = (key_str or "").strip().upper()
    if k in CAMELOT_ORDER:
        return CAMELOT_ORDER.index(k)
    # Convert music notation to Camelot
    NOTATION_MAP = {
        "AM": "8A", "EM": "9A", "BM": "10A", "F#M": "11A", "GBM": "11A",
        "DBM": "12A", "C#M": "12A", "ABM": "1A", "G#M": "1A", "EBM": "2A",
        "D#M": "2A", "BBM": "3A", "A#M": "3A", "FM": "4A", "CM": "5A",
        "GM": "6A", "DM": "7A",
        "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B",
        "B": "1B", "F#": "2B", "GB": "2B", "DB": "3B", "C#": "3B",
        "AB": "4B", "G#": "4B", "EB": "5B", "D#": "5B", "BB": "6B",
        "A#": "6B", "F": "7B",
    }
    normalized = k.replace("MIN", "M").replace("MAJ", "").replace("MINOR","M").replace("MAJOR","")
    if normalized in NOTATION_MAP:
        return CAMELOT_ORDER.index(NOTATION_MAP[normalized])
    return 99  # unknowns at end


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def safe_id() -> str:
    return str(random.randint(1500000000, 4000000000))


def find_or_create_folder(con, name: str, parent: str) -> str:
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND rb_local_deleted=0 LIMIT 1",
        (name,)
    ).fetchone()
    if row:
        return row[0]
    pid = safe_id()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con.execute("""INSERT INTO djmdPlaylist
        (ID, Name, Attribute, ParentID, UUID, rb_data_status, rb_local_data_status,
         rb_local_deleted, rb_local_synced, usn, rb_local_usn, created_at, updated_at)
        VALUES (?,?,1,?,?,0,0,0,0,NULL,1,?,?)""",
        (pid, name, parent, str(uuid_lib.uuid4()), ts, ts))
    return pid


def find_or_create_playlist(con, name: str, parent: str) -> str:
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=0 AND rb_local_deleted=0 LIMIT 1",
        (name,)
    ).fetchone()
    if row:
        return row[0]
    pid = safe_id()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con.execute("""INSERT INTO djmdPlaylist
        (ID, Name, Attribute, ParentID, UUID, rb_data_status, rb_local_data_status,
         rb_local_deleted, rb_local_synced, usn, rb_local_usn, created_at, updated_at)
        VALUES (?,?,0,?,?,0,0,0,0,NULL,1,?,?)""",
        (pid, name, parent, str(uuid_lib.uuid4()), ts, ts))
    return pid


def rebuild_pool(con, playlist_id: str, tracks: list[dict], ts: str):
    con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (playlist_id,))
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    for i, t in enumerate(tracks, 1):
        max_usn += 1
        con.execute("""INSERT INTO djmdSongPlaylist
            (ID, PlaylistID, ContentID, TrackNo, UUID,
             rb_data_status, rb_local_data_status, rb_local_deleted,
             rb_local_synced, usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), playlist_id, t["id"], i, str(uuid_lib.uuid4()), max_usn, ts, ts))


def main():
    con = db_connect()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Find parent folder "Por Posicion de Set"
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0 LIMIT 1",
        (POOL_FOLDER_NAME,)
    ).fetchone()
    if not row:
        print(f"ERROR: Carpeta '{POOL_FOLDER_NAME}' no encontrada en DB")
        con.close()
        return
    parent_id = row[0]

    # Load all active tracks with energy + key
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt,
               COALESCE(k.ScaleName, '?') as key_name
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        LEFT JOIN djmdKey k ON k.ID = c.KeyID
        WHERE c.rb_local_deleted = 0
          -- Los demos y one-shots de Pioneer no son musica y sin este
          -- filtro terminan en los pools de armado con datos inventados.
          AND c.FolderPath NOT LIKE '%/PioneerDJ/%'
    """).fetchall()

    print(f"Total tracks: {len(rows)}")

    # Parse energy from Commnt
    def parse_energy(commnt: str) -> float | None:
        if not commnt or "E:" not in commnt:
            return None
        try:
            return float(commnt.split("|")[0].replace("E:", "").strip())
        except ValueError:
            return None

    # Bucket into pools
    buckets: dict[str, list[dict]] = {name: [] for name, _, _ in POOLS}
    no_energy = []

    for cid, artist, title, bpm_raw, commnt, key_name in rows:
        energy = parse_energy(commnt)
        # Sin inventar: `bpm_raw or 12200` le ponia 122 BPM a lo que no tiene
        # BPM, y `energy or 5.0` le ponia E:5.0 a lo que no tiene energia. Con
        # eso, cuatro one-shots del sampler de Pioneer entraban al pool [MID]
        # como si fueran tracks de 122 BPM y energia media. Un dato inventado
        # que se ve igual que uno medido es peor que un dato faltante.
        t = {
            "id": str(cid),
            "artist": artist or "?",
            "title": title or "?",
            "bpm": (bpm_raw / 100) if bpm_raw else None,
            "energy": energy,
            "key": key_name,
        }
        if not t["bpm"]:
            no_energy.append(t)
            continue
        if energy is None:
            no_energy.append(t)
            continue
        for pool_name, e_min, e_max in POOLS:
            if e_min <= energy <= e_max:
                buckets[pool_name].append(t)
                break

    # Sort each bucket by Camelot key then BPM
    def sort_key(t):
        return (camelot_sort_key(t["key"]), t["bpm"])

    for pool_name in buckets:
        buckets[pool_name].sort(key=sort_key)

    no_energy.sort(key=sort_key)

    # Create/update playlists
    for pool_name, _, _ in POOLS:
        tracks = buckets[pool_name]
        pl_id = find_or_create_playlist(con, pool_name, parent_id)
        rebuild_pool(con, pl_id, tracks, ts)
        print(f"  {pool_name}: {len(tracks)} tracks")

    # Sin energy pool
    no_e_id = find_or_create_playlist(con, "[POOL] Sin Energy", parent_id)
    rebuild_pool(con, no_e_id, no_energy, ts)
    print(f"  [POOL] Sin Energy: {len(no_energy)} tracks")

    con.commit()
    con.close()

    total = sum(len(v) for v in buckets.values()) + len(no_energy)
    print(f"\nTotal pools: {total} tracks organizados")
    print("Abri Rekordbox y hace sync al pen.")


if __name__ == "__main__":
    main()
