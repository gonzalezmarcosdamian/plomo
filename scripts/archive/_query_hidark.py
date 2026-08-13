import os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# BPM va x100, energia en Commnt como "E:5.7"
rows = con.execute("""
    SELECT c.ID, a.Name, c.Title, c.BPM,
           c.Commnt,
           k.ScaleName
    FROM djmdContent c
    JOIN djmdArtist a ON c.ArtistID = a.ID
    LEFT JOIN djmdKey k ON c.KeyID = k.ID
    WHERE c.rb_local_deleted=0
      AND c.BPM BETWEEN 12000 AND 12700
      AND c.Commnt LIKE 'E:%'
    ORDER BY c.BPM
""").fetchall()

# Parsear energia y filtrar
candidates = []
for cid, artist, title, bpm, commnt, key in rows:
    m = re.match(r'E:([\d.]+)', commnt or '')
    if not m:
        continue
    energy = float(m.group(1))
    if energy >= 4.8:
        candidates.append((cid, artist, title, bpm / 100, energy, key or '?'))

# Dedup por titulo+artista (keep highest energy)
seen = {}
for cid, artist, title, bpm, energy, key in candidates:
    k = (artist.lower()[:30], title.lower()[:40])
    if k not in seen or energy > seen[k][4]:
        seen[k] = (cid, artist, title, bpm, energy, key)

deduped = sorted(seen.values(), key=lambda x: (-x[4], x[3]))
print(f"Candidatos hidark (120-127 BPM, E>=4.8): {len(deduped)}")
for cid, artist, title, bpm, energy, key in deduped:
    print(f"  E:{energy:.1f}  {bpm:.0f}bpm  {key:6} | {artist} - {title[:55]}")

con.close()
