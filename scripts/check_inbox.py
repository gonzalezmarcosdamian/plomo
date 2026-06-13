import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))

inbox = con.execute("SELECT COUNT(*) FROM djmdContent WHERE FolderPath LIKE '%Inbox%' AND rb_local_deleted=0").fetchone()[0]
inbox_no_e = con.execute("SELECT COUNT(*) FROM djmdContent WHERE FolderPath LIKE '%Inbox%' AND rb_local_deleted=0 AND (Commnt IS NULL OR Commnt NOT LIKE 'E:%')").fetchone()[0]
print('Inbox en DB:', inbox, '| Sin energy:', inbox_no_e)

# Check genres available
genres = con.execute("""
    SELECT g.Name, COUNT(*) as cnt
    FROM djmdContent c
    LEFT JOIN djmdGenre g ON g.ID = c.GenreID
    WHERE c.rb_local_deleted=0
    GROUP BY g.Name ORDER BY cnt DESC LIMIT 15
""").fetchall()
print('\nGeneros:')
for g, cnt in genres:
    print(f'  {cnt:4} | {g or "Sin genero"}')
