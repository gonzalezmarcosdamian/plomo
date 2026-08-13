import os; from dotenv import load_dotenv; load_dotenv()
import sqlcipher3
KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")
# Buscar Para Probar
rows = con.execute("SELECT ID, Name, ParentID FROM djmdPlaylist WHERE LOWER(Name) LIKE '%probar%' OR LOWER(Name) LIKE '%41%' OR LOWER(Name) LIKE '%42%' ORDER BY Name").fetchall()
for r in rows: print(r)
# Buscar hijos del ID conocido
print('\nHijos de 1975667623:')
rows2 = con.execute("SELECT ID, Name, Seq FROM djmdPlaylist WHERE ParentID='1975667623' AND rb_local_deleted=0 ORDER BY Seq").fetchall()
for r in rows2: print(r)
