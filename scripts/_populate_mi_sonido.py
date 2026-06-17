"""
Agrega a [POOL] Mi Sonido todos los tracks de batch_mi_sonido.txt que estén en la DB.
Parsea lineas como: "Artist1 Artist2 - Title" o "Artist - Title"
"""
import os, re, random
from datetime import datetime
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('SQLCIPHER_KEY')
MI_SONIDO_ID = '3746304539'
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
BATCH_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'batch_mi_sonido.txt')

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Parsear batch file
tracks_to_find = []
with open(BATCH_FILE, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Separar por " - "
        if ' - ' in line:
            parts = line.split(' - ', 1)
            artist_raw = parts[0].strip()
            title_raw = parts[1].strip()
            tracks_to_find.append((artist_raw, title_raw))

print(f"Tracks en batch: {len(tracks_to_find)}")

found = []
not_found = []

for artist_raw, title_raw in tracks_to_find:
    # Intentar buscar por título exacto primero
    # El artista puede estar en cualquier orden o ser parcial
    title_q = f"%{title_raw.lower()}%"

    rows = con.execute("""
        SELECT c.ID, c.Title, a.Name FROM djmdContent c
        JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE LOWER(c.Title) LIKE ? AND c.rb_local_deleted=0
        ORDER BY c.ID LIMIT 5
    """, (title_q,)).fetchall()

    if not rows:
        not_found.append(f"{artist_raw} - {title_raw}")
        continue

    # Si hay varios, intentar filtrar por artista
    best = None
    for cid, ctitle, cartist in rows:
        # Tomar palabras del artista raw y ver si alguna matchea
        artist_words = re.findall(r'\w+', artist_raw.lower())
        cartist_lower = cartist.lower()
        if any(w in cartist_lower for w in artist_words if len(w) > 3):
            best = (cid, ctitle, cartist)
            break
    if not best:
        best = rows[0]  # primer resultado si no hay match de artista

    found.append(best)

print(f"Encontrados en DB: {len(found)}")
print(f"No encontrados: {len(not_found)}")

# Agregar a la playlist
added = 0
already = 0
for cid, ctitle, cartist in found:
    exists = con.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=? AND rb_local_deleted=0",
        (MI_SONIDO_ID, cid)
    ).fetchone()[0]
    if exists:
        already += 1
        continue

    tno = (con.execute(
        "SELECT MAX(TrackNo) FROM djmdSongPlaylist WHERE PlaylistID=?", (MI_SONIDO_ID,)
    ).fetchone()[0] or 0) + 1

    con.execute(
        "INSERT INTO djmdSongPlaylist (ID, PlaylistID, ContentID, TrackNo, rb_local_deleted, created_at, updated_at) VALUES (?,?,?,?,0,?,?)",
        (random.randint(100000000, 999999999), MI_SONIDO_ID, cid, tno, NOW, NOW)
    )
    con.commit()
    added += 1
    print(f"  + {cartist} - {ctitle}")

print(f"\nAgregados: {added} | Ya existian: {already} | No encontrados: {len(not_found)}")

if not_found:
    print("\n--- NO ENCONTRADOS EN DB (no descargados aun) ---")
    for t in not_found:
        print(f"  {t}")

con.close()
