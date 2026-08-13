import os; from dotenv import load_dotenv; load_dotenv()
import sqlcipher3
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{os.environ.get('SQLCIPHER_KEY')}'")
con.execute("PRAGMA cipher_compatibility=4")
rows = con.execute("SELECT ID, Name, Attribute FROM djmdPlaylist WHERE LOWER(Name) LIKE '%mi son%' OR LOWER(Name) LIKE '%pool%'").fetchall()
for r in rows:
    print(r)
