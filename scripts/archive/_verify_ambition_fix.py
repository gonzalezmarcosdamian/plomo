import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

original_id = '57277028'
dup_playlists = ['3510738544', '2039131269', '3887003823', '2058305450', '3864232730']

print("Verificando playlists afectadas:")
ok = 0
for pl_id in dup_playlists:
    pl_name = con.execute("SELECT Name FROM djmdPlaylist WHERE ID=?", (pl_id,)).fetchone()
    has_orig = con.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=?",
        (pl_id, original_id)
    ).fetchone()[0]
    status = "OK" if has_orig else "FALTA"
    name = pl_name[0] if pl_name else pl_id
    print(f"  [{status}] {name}")
    if has_orig:
        ok += 1

total = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
print(f"\nTotal tracks en DB: {total}")
print(f"Playlists con original: {ok}/{len(dup_playlists)}")
con.close()
