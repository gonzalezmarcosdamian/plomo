"""
Organiza TODA la biblioteca en playlists por Estilo + Energia + Camelot.

Estructura creada:
  Por Posicion de Set/
    [POOL] Warmup     E:1-3.9
    [POOL] Build      E:4-5.4
    [POOL] Mid        E:5.5-6.4
    [POOL] Peak       E:6.5-7.9
    [POOL] Peak+      E:8.0+

  Por Estilo/
    Progressive/
      [WARMUP]  [BUILD]  [MID]  [PEAK]  [PEAK+]
    House/
      [WARMUP]  [BUILD]  [MID]  [PEAK]
    Techno/
      [WARMUP]  [MID]  [PEAK]
    Organic/
      [WARMUP]  [MID]  [PEAK]
    Otros/
      [MID]  [PEAK]

Tracks sin energy: se les asigna proxy por BPM antes de organizar.
BPM proxy:
  < 120  -> E:3.5 (warmup)
  120-121 -> E:5.0 (mid)
  122-123 -> E:5.5 (mid-high)
  124-125 -> E:6.0 (high)
  126+   -> E:6.5 (peak)

Dentro de cada playlist: ordenados por Camelot wheel (1A..12B) luego BPM.

Uso:
  python scripts/build_collection.py
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

# ─── Configuracion ────────────────────────────────────────────────────────────

ENERGY_BUCKETS = [
    ("[WARMUP]", 0.0,  3.9),
    ("[BUILD]",  4.0,  5.4),
    ("[MID]",    5.5,  6.4),
    ("[PEAK]",   6.5,  7.9),
    ("[PEAK+]",  8.0, 99.0),
]

# Mapeo de generos de RB a categorias de DJ
GENRE_STYLE = {
    "Progressive House":            "Progressive",
    "Melodic House & Techno":       "Progressive",
    "Melodic Techno":               "Progressive",
    "House":                        "House",
    "Deep House":                   "House",
    "Afro House":                   "House",
    "Nu Disco / Disco":             "House",
    "Funky House":                  "House",
    "Bass House":                   "House",
    "Tech House":                   "House",
    "Techno (Peak Time / Driving)": "Techno",
    "Techno (Peak Time / Driving / Hard)": "Techno",
    "Techno":                       "Techno",
    "Hard Techno":                  "Techno",
    "Organic House":                "Organic",
    "Organic House / Downtempo":    "Organic",
    "Downtempo":                    "Organic",
    "Ambient / Drone":              "Organic",
}

STYLES = ["Progressive", "House", "Techno", "Organic", "Otros"]

# BPM proxy para tracks sin energy
def bpm_to_energy(bpm: float) -> float:
    if bpm < 118: return 2.5
    if bpm < 120: return 3.5
    if bpm < 122: return 5.0
    if bpm < 124: return 5.5
    if bpm < 126: return 6.0
    return 6.5

# Camelot sort order
CAMELOT_ORDER = [
    "1A","2A","3A","4A","5A","6A","7A","8A","9A","10A","11A","12A",
    "1B","2B","3B","4B","5B","6B","7B","8B","9B","10B","11B","12B",
]

NOTATION_MAP = {
    "AM":"8A","EM":"9A","BM":"10A","F#M":"11A","GBM":"11A",
    "DBM":"12A","C#M":"12A","ABM":"1A","G#M":"1A","EBM":"2A",
    "D#M":"2A","BBM":"3A","A#M":"3A","FM":"4A","CM":"5A","GM":"6A","DM":"7A",
    "C":"8B","G":"9B","D":"10B","A":"11B","E":"12B","B":"1B",
    "F#":"2B","GB":"2B","DB":"3B","C#":"3B","AB":"4B","G#":"4B",
    "EB":"5B","D#":"5B","BB":"6B","A#":"6B","F":"7B",
}

def camelot_idx(key_str: str) -> int:
    k = (key_str or "").strip().upper()
    if k in CAMELOT_ORDER:
        return CAMELOT_ORDER.index(k)
    normalized = k.replace("MIN","M").replace("MAJ","").replace("MINOR","M").replace("MAJOR","")
    if normalized in NOTATION_MAP:
        return CAMELOT_ORDER.index(NOTATION_MAP[normalized])
    return 99

def sort_key(t):
    return (camelot_idx(t["key"]), t["bpm"])

# ─── DB helpers ───────────────────────────────────────────────────────────────

def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con

def safe_id() -> str:
    return str(random.randint(1500000000, 4000000000))

def get_or_create_folder(con, name: str, parent_id: str | None, ts: str) -> str:
    q = "SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND rb_local_deleted=0"
    row = con.execute(q, (name,)).fetchone()
    if row:
        return row[0]
    pid = safe_id()
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Name,Attribute,ParentID,UUID,rb_data_status,rb_local_data_status,
         rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
        VALUES(?,?,1,?,?,0,0,0,0,NULL,1,?,?)""",
        (pid, name, parent_id, str(uuid_lib.uuid4()), ts, ts))
    return pid

def get_or_create_playlist(con, name: str, parent_id: str, ts: str) -> str:
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND ParentID=? AND Attribute=0 AND rb_local_deleted=0",
        (name, parent_id)
    ).fetchone()
    if row:
        return row[0]
    pid = safe_id()
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Name,Attribute,ParentID,UUID,rb_data_status,rb_local_data_status,
         rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
        VALUES(?,?,0,?,?,0,0,0,0,NULL,1,?,?)""",
        (pid, name, parent_id, str(uuid_lib.uuid4()), ts, ts))
    return pid

def fill_playlist(con, playlist_id: str, tracks: list[dict], ts: str):
    con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (playlist_id,))
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    for i, t in enumerate(tracks, 1):
        max_usn += 1
        con.execute("""INSERT INTO djmdSongPlaylist
            (ID,PlaylistID,ContentID,TrackNo,UUID,
             rb_data_status,rb_local_data_status,rb_local_deleted,
             rb_local_synced,usn,rb_local_usn,created_at,updated_at)
            VALUES(?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), playlist_id, t["id"], i, str(uuid_lib.uuid4()), max_usn, ts, ts))

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    con = db_connect()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load all tracks
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt,
               COALESCE(k.ScaleName,'?') as key_nm,
               COALESCE(g.Name,'') as genre
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        LEFT JOIN djmdKey k ON k.ID = c.KeyID
        LEFT JOIN djmdGenre g ON g.ID = c.GenreID
        WHERE c.rb_local_deleted = 0
    """).fetchall()

    def parse_energy(commnt, bpm):
        if commnt and "E:" in commnt:
            try:
                return float(commnt.split("|")[0].replace("E:","").strip())
            except ValueError:
                pass
        return bpm_to_energy(bpm)

    tracks_all = []
    for cid, artist, title, bpm_raw, commnt, key_nm, genre in rows:
        bpm = (bpm_raw or 12200) / 100
        energy = parse_energy(commnt, bpm)
        style = GENRE_STYLE.get(genre, "Otros")
        tracks_all.append({
            "id": str(cid),
            "artist": artist or "?",
            "title": title or "?",
            "bpm": bpm,
            "energy": energy,
            "key": key_nm,
            "style": style,
            "genre": genre,
        })

    print(f"Total tracks: {len(tracks_all)}")

    # ── Por Posicion de Set (POOLS GLOBALES) ──────────────────────────────────
    pos_folder_row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name='Por Posicion de Set' AND rb_local_deleted=0 LIMIT 1"
    ).fetchone()
    if not pos_folder_row:
        print("WARN: No encontre carpeta 'Por Posicion de Set'")
        pos_folder_id = get_or_create_folder(con, "Por Posicion de Set", None, ts)
    else:
        pos_folder_id = pos_folder_row[0]

    print("\n=== POOLS GLOBALES (Por Posicion de Set) ===")
    for label, e_min, e_max in ENERGY_BUCKETS:
        pool_tracks = sorted(
            [t for t in tracks_all if e_min <= t["energy"] <= e_max],
            key=sort_key
        )
        pl_id = get_or_create_playlist(con, label, pos_folder_id, ts)
        fill_playlist(con, pl_id, pool_tracks, ts)
        print(f"  {label:<12} {len(pool_tracks):>4} tracks")

    # ── Por Estilo (carpeta nueva) ─────────────────────────────────────────────
    estilo_folder_id = get_or_create_folder(con, "Por Estilo", None, ts)

    print("\n=== POR ESTILO ===")
    for style in STYLES:
        style_tracks = [t for t in tracks_all if t["style"] == style]
        if not style_tracks:
            continue

        style_folder_id = get_or_create_folder(con, style, estilo_folder_id, ts)

        for label, e_min, e_max in ENERGY_BUCKETS:
            bucket = sorted(
                [t for t in style_tracks if e_min <= t["energy"] <= e_max],
                key=sort_key
            )
            if not bucket:
                continue
            pl_name = f"{style} {label}"
            pl_id = get_or_create_playlist(con, pl_name, style_folder_id, ts)
            fill_playlist(con, pl_id, bucket, ts)
            print(f"  {pl_name:<30} {len(bucket):>4} tracks")

    con.commit()
    con.close()
    print("\nHecho. Abri Rekordbox y hace sync al pen.")

if __name__ == "__main__":
    main()
