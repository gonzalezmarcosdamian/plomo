import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))

rows = con.execute("""
    SELECT a.Name, c.Title, c.Commnt
    FROM djmdContent c
    LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
    WHERE c.rb_local_deleted=0 AND c.Commnt LIKE 'E:%'
      AND a.Name IN ('Maze 28','Rockka','Hobin Rude','Cendryma','Gai Barone')
    LIMIT 10
""").fetchall()
for r in rows:
    print(r[2][:10], '|', r[0], '-', r[1][:35])

total = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0 AND Commnt LIKE 'E:%'").fetchone()[0]
no_energy = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0 AND (Commnt IS NULL OR Commnt NOT LIKE 'E:%')").fetchone()[0]
print(f'Con energy: {total} | Sin energy: {no_energy}')
