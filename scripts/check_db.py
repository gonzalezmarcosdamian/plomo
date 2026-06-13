import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))
r = con.execute('PRAGMA integrity_check').fetchone()
print('Integridad:', r[0])
t = con.execute('SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0').fetchone()[0]
p = con.execute('SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0').fetchone()[0]
print(f'Tracks: {t} | Playlists: {p}')
con.close()
