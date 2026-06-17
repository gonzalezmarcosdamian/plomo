"""Busca tracks de estilo organico en la libreria actual."""
import os, re; from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

ORGANIC_ARTISTS = [
    'Monolink', 'Hermanez', 'Lee Burridge', 'Lost Desert', 'Ben Bohmer', 'Ben Böhmer',
    'Nils Hoffmann', 'HVOB', 'Moderat', "N'to", 'Rodriguez Jr', 'Nora En Pure',
    'Bedouin', 'Bonobo', 'Jon Hopkins', 'Bicep', 'Floating Points',
    'Thandi Draai', 'Darque', 'Innellea', 'Monkey Safari', 'Apparat',
    'Lane 8', 'Recondite', 'Patrice Baumel', 'Patrice Bäumel',
    'Adam Port', 'Worakls', 'Worakls Orchestra', 'David August',
    'Stimming', 'Stephan Bodzin', 'Mathame', 'Tale of Us', 'Adriatique',
    'Sol Selectas', 'Butch', 'Cosmonaut',
]

results = []
for artist in ORGANIC_ARTISTS:
    rows = con.execute("""
        SELECT c.Title, a.Name, c.BPM, c.Commnt
        FROM djmdContent c JOIN djmdArtist a ON c.ArtistID=a.ID
        WHERE LOWER(a.Name) LIKE ? AND c.rb_local_deleted=0
        ORDER BY c.ID DESC
    """, (f"%{artist.lower()}%",)).fetchall()
    for t, a, bpm, commnt in rows:
        m = re.search(r'E:([\d.]+)', commnt or '')
        energy = float(m.group(1)) if m else None
        results.append((a, t, (bpm or 0)//100, energy))

# Filtrar por rango organico: BPM 110-124, energy < 6.5
organic = [(a, t, bpm, e) for a, t, bpm, e in results
           if 108 <= bpm <= 124 and (e is None or e < 6.5)]

print(f"Tracks organicos en libreria ({len(organic)}):")
for a, t, bpm, e in sorted(organic, key=lambda x: x[3] or 0):
    print(f"  {bpm}bpm E:{e or '?':4} | {a} - {t[:55]}")

con.close()
