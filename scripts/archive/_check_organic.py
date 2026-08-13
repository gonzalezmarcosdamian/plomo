import sys, os; sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3
KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")
rows = con.execute("""
    SELECT p.Name, COUNT(*) as n
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID=p.ID
    WHERE p.Name LIKE '%Organic%' AND p.rb_local_deleted=0
    GROUP BY p.ID ORDER BY p.Name
""").fetchall()
print("Playlists Organic en DB:")
for name, n in rows:
    print(f"  [{n}] {name}")
con.close()
