"""Candidatos para el set marsh-style: driving emotional progressive 119-128 BPM, E>=5.5"""
import os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

rows = con.execute("""
    SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt, k.ScaleName
    FROM djmdContent c
    JOIN djmdArtist a ON c.ArtistID = a.ID
    LEFT JOIN djmdKey k ON c.KeyID = k.ID
    WHERE c.rb_local_deleted=0
      AND c.BPM BETWEEN 11900 AND 12800
      AND c.Commnt LIKE 'E:%'
    ORDER BY c.BPM, c.Commnt DESC
""").fetchall()

candidates = []
for cid, artist, title, bpm, commnt, key in rows:
    m = re.match(r'E:([\d.]+)', commnt or '')
    if not m:
        continue
    energy = float(m.group(1))
    if energy >= 5.5:
        candidates.append((cid, artist, title, bpm / 100, energy, key or '?'))

# Dedup por titulo+artista
seen = {}
for cid, artist, title, bpm, energy, key in candidates:
    k = (artist.lower()[:30], title.lower()[:40])
    if k not in seen or energy > seen[k][4]:
        seen[k] = (cid, artist, title, bpm, energy, key)

deduped = sorted(seen.values(), key=lambda x: (-x[4], x[3]))
print(f"Candidatos 119-128 BPM, E>=5.5: {len(deduped)}\n")
for cid, artist, title, bpm, energy, key in deduped:
    print(f"  E:{energy:.1f}  {bpm:.0f}bpm  {key:6} [{cid}] | {artist[:22]} - {title[:48]}")

con.close()
