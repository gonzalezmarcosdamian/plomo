"""Chequea tracks de artistas estilo Marsh/Ferry Corsten en la libreria."""
import os, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

artists_to_check = [
    'Marsh', 'Ferry Corsten', 'Jody Wisternoff', 'Nick Warren', 'Way Out West',
    'Quivver', 'James Grant', 'Luke Chable', 'Simon Berry', 'Guy J',
    'Rauschhaus', 'Kasper Koman', 'John Digweed', 'Sasha', 'Joris Voorn',
    'GMJ', 'Matter', 'Fur Coat', 'D-Nox', 'Stiv Hey', 'Robert Babicz',
    'Lee Burridge', 'Lost Desert', 'Hermanez', 'Innellea', 'Khen',
    'Massane', 'Lexer', 'Rafael Cerato', 'Navar', 'Tim Green',
]

print('=== TRACKS EN LIBRERIA — MARSH STYLE ===\n')
found = []
for artist in artists_to_check:
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt
        FROM djmdContent c
        JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE c.rb_local_deleted=0 AND LOWER(a.Name) LIKE LOWER(?)
        ORDER BY c.BPM
    """, (f'%{artist.split()[0]}%',)).fetchall()
    if rows:
        print(f'{artist} ({len(rows)} tracks):')
        for cid, db_artist, title, bpm, commnt in rows[:6]:
            m = re.match(r'E:([\d.]+)', commnt or '')
            e_str = f'E:{m.group(1)}' if m else 'E:?  '
            bpm_str = str(bpm // 100) if bpm else '?'
            print(f'  {e_str}  {bpm_str}bpm | {title[:55]}')
            found.append((cid, db_artist, title, bpm, commnt))
        if len(rows) > 6:
            print(f'  ... +{len(rows)-6} mas')
        print()

print(f'Total tracks encontrados: {len(found)}')
con.close()
