"""Lee BPM/key/energy de los 26 tracks del Warung recien importados."""
import os; from dotenv import load_dotenv; load_dotenv()
import sqlcipher3, re

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

titles = [
    "Alnilam", "Back To The Roots", "Your Love Will Set You Free", "Shadow",
    "Epikur", "I Feel Loved", "Don't Leave Me", "Psychodelia",
    "Calinerie", "Timing", "Dizzy Moments", "Hale Bopp",
    "Music Is The Answer", "Kingdom of Dreams", "Check-a-Change", "All that Matters",
    "Seguro", "Misery", "Never Sleep Again", "Soul on Fire",
    "Spring Embers", "Strobe Queen", "The Bar Tender", "Out of control",
    "Time", "Never Alone"
]

print(f"{'#':<3} {'BPM':<6} {'E':<5} {'Key':<8} {'Title'}")
print("-"*80)
for i, title in enumerate(titles, 1):
    row = con.execute("""
        SELECT c.Title, a.Name, c.BPM, c.Commnt
        FROM djmdContent c JOIN djmdArtist a ON c.ArtistID=a.ID
        WHERE LOWER(c.Title) LIKE ? AND c.rb_local_deleted=0
        ORDER BY c.ID DESC LIMIT 1
    """, (f"%{title.lower()}%",)).fetchone()
    if row:
        t, artist, bpm, commnt = row
        # Extraer energy del Commnt
        m = re.search(r'E:([\d.]+)', commnt or '')
        energy = float(m.group(1)) if m else '?'
        # Extraer key si está en commnt
        km = re.search(r'K:([^\|]+)', commnt or '')
        key = km.group(1).strip() if km else '-'
        print(f"{i:<3} {str(bpm or '?'):<6} {str(energy):<5} {key:<8} {artist} - {t[:45]}")
    else:
        print(f"{i:<3} {'?':<6} {'?':<5} {'?':<8} NO ENCONTRADO: {title}")
con.close()
