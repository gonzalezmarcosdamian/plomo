"""
Analiza tracks nuevos por artista: BPM, key, energy.
Muestra agrupado para decidir armado de sets.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

def bpm_proxy(bpm):
    if bpm < 118: return 2.5
    if bpm < 120: return 3.5
    if bpm < 122: return 5.0
    if bpm < 124: return 5.5
    if bpm < 126: return 6.0
    return 6.5

def get_energy(commnt, bpm):
    if commnt and "E:" in commnt:
        try:
            return float(commnt.split("|")[0].replace("E:", "").strip())
        except:
            pass
    return bpm_proxy(bpm)

def query_artist(artist_kw):
    rows = con.execute("""
        SELECT c.ID, COALESCE(a.Name,'?'), c.Title, c.BPM/100.0,
               COALESCE(k.ScaleName,'?'), c.Commnt
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        LEFT JOIN djmdKey k ON k.ID=c.KeyID
        WHERE c.rb_local_deleted=0
          AND LOWER(COALESCE(a.Name,'')) LIKE LOWER(?)
          AND c.BPM IS NOT NULL AND c.BPM > 0
        ORDER BY c.BPM, COALESCE(k.ScaleName,'?')
    """, (f"%{artist_kw}%",)).fetchall()
    return rows

ARTIST_GROUPS = [
    ("=== EMI GALVAN ===", ["Emi Galvan"]),
    ("=== KAMILO SANCLEMENTE ===", ["Kamilo Sanclemente"]),
    ("=== GREG OCHMAN / YOTTO ===", ["Greg Ochman", "Yotto", "Amir Telem"]),
    ("=== IGNACIO HERNANDEZ ===", ["Ignacio Hernandez"]),
    ("=== MAZE 28 ===", ["Maze 28"]),
    ("=== ROCKKA ===", ["Rockka"]),
    ("=== CENDRYMA ===", ["Cendryma"]),
    ("=== GAI BARONE ===", ["Gai Barone"]),
    ("=== HRAACH / ARMEN MIRAN ===", ["Hraach", "Armen Miran"]),
    ("=== DOWDEN ===", ["Dowden"]),
    ("=== DMITRY MOLOSH ===", ["Dmitry Molosh"]),
    ("=== GUY J ===", ["Guy J"]),
    ("=== HERNAN CATTANEO ===", ["Hernan Cattaneo"]),
    ("=== TOM PAVICICH ===", ["Tom Pavicich"]),
    ("=== DURANTE ===", ["Durante"]),
    ("=== NICOLAS RADA ===", ["Nicolas Rada"]),
    ("=== CENDRYMA COLLABS (Muuk, Dimas) ===", ["Muuk", "Dimas Mixon"]),
    ("=== SIMON VAURAMBON ===", ["Simon Vaurambon"]),
    ("=== DIGWEED ===", ["John Digweed"]),
    ("=== HOBIN RUDE ===", ["Hobin Rude"]),
    ("=== CHELAKHOV ===", ["Chelakhov"]),
    ("=== CARY CRANK ===", ["Cary Crank"]),
    ("=== TOM PAVICICH COLLABS (FAERO, Tirso) ===", ["FAERO", "Tirso Enriquez"]),
]

all_tracks = []

for header, artists in ARTIST_GROUPS:
    rows = []
    for a in artists:
        rows += query_artist(a)
    # deduplicate by ID
    seen = set()
    unique = []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0])
            unique.append(r)
    unique.sort(key=lambda r: (r[3], r[4]))

    if not unique:
        continue

    print(f"\n{header}")
    print(f"{'BPM':>5} {'Key':<6} {'E':>4}  {'Artist':<22} {'Title':<40}")
    print("-" * 80)
    for r in unique:
        cid, artist, title, bpm, key, commnt = r
        e = get_energy(commnt, bpm)
        print(f"{bpm:>5.1f} {key:<6} {e:>4.1f}  {artist[:22]:<22} {title[:40]}")
        all_tracks.append({"id": cid, "artist": artist, "title": title,
                           "bpm": bpm, "key": key, "energy": e})

# Key cluster summary
from collections import Counter
print("\n\n=== RESUMEN POR KEY (todos los tracks nuevos) ===")
key_counts = Counter(t["key"] for t in all_tracks)
for key, cnt in sorted(key_counts.items(), key=lambda x: -x[1]):
    print(f"  {key:<8} {cnt:>3} tracks")

print(f"\n=== BPM DISTRIBUTION ===")
bpm_buckets = Counter()
for t in all_tracks:
    bucket = int(t["bpm"])
    bpm_buckets[bucket] += 1
for bpm, cnt in sorted(bpm_buckets.items()):
    print(f"  {bpm} BPM:  {'#' * cnt} ({cnt})")

con.close()
