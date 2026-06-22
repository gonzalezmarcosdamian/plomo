import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

con.execute("UPDATE djmdPlaylist SET Name='colorido progresive' WHERE Name='marsh' AND rb_local_deleted=0")
con.commit()

row = con.execute("SELECT ID, Name FROM djmdPlaylist WHERE Name='colorido progresive'").fetchone()
print("Renombrado:", row)
con.close()
