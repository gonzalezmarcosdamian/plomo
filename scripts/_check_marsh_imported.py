"""Verifica tracks nuevos del batch marsh-style importados."""
import os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

total = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
print(f"Total tracks en DB: {total}")

rows = con.execute("""
    SELECT a.Name, c.Title, c.BPM, c.Commnt
    FROM djmdContent c JOIN djmdArtist a ON c.ArtistID=a.ID
    WHERE c.rb_local_deleted=0
      AND (LOWER(a.Name) LIKE '%marsh%'
        OR LOWER(a.Name) LIKE '%ferry corsten%'
        OR LOWER(a.Name) LIKE '%analog trip%'
        OR LOWER(a.Name) LIKE '%andy moor%'
        OR LOWER(a.Name) LIKE '%dmitry molosh%')
    ORDER BY c.Commnt DESC, c.BPM
""").fetchall()

print("\n=== Tracks marsh-style en DB ===")
for artist, title, bpm, commnt in rows:
    m = re.match(r'E:([\d.]+)', commnt or '')
    e = f"E:{m.group(1)}" if m else "E:?  "
    bpm_str = str(bpm // 100) if bpm else "?"
    print(f"  {e}  {bpm_str:>3}bpm | {artist[:24]} - {title[:48]}")

con.close()
