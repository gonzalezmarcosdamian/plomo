"""Busca los tracks del ultimo Warung de Hernan en la DB de Rekordbox."""
import os
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

tracks = [
    ("Agent GEX", "Slipstream"),
    ("Tonaco", "Alnilam"),
    ("Makebo", "Back to the Roots"),
    ("Diana Miro", "Underwater"),
    ("Caribou", "Your Love Will Set You Free"),
    ("Chromatics", "Shadow"),
    ("CHVRCHES", "Clearest Blue"),
    ("David August", "Epikur"),
    ("Depeche Mode", "Going Backwards"),
    ("Depeche Mode", "I Feel Love"),
    ("Donna Summer", "Dusk Till Dawn"),
    ("Donna Summer", "I Feel Love"),
    ("Lloydbarwood", "Echoes Through You"),
    ("D-Nox Andre Moret", "Don't Leave Me"),
    ("Ezequiel Arias", "Psychodelia"),
    ("Gill Noris", "Forme"),
    ("Gorje Hewek", "Calinerie"),
    ("Gorkiz Fernando Olaya", "Sirius"),
    ("Gorkiz", "Black Sun"),
    ("Guy Gerber", "Timing"),
    ("Guy J", "Dizzy Moments"),
    ("Der Dritte Raum", "Hale Bopp"),
    ("Hans Zimmer", "Time"),
    ("Joe Goddard", "Music Is The Answer"),
    ("Juan Ibanez", "Kingdom of Dreams"),
    ("K Loveski Federico Monachesi", "Check a Change"),
    ("Kolsch", "All That Matters"),
    ("Kostya Outta", "Seguro"),
    ("Luciano Scheffer", "The Speech"),
    ("Gai Barone", "All I Need"),
    ("Marco Bailey Tom Hades", "Stars and Shines"),
    ("Edone", "Misery"),
    ("Moby", "The Last Day"),
    ("Guy Mantzur", "Moments Becoming Endless Time"),
    ("Oliver Weiter", "Room821"),
    ("Ossie", "Holyland"),
    ("Laurent Garnier", "Our Future"),
    ("Andre Moret", "Out of Control"),
    ("Phonique", "For the Time Being"),
    ("Radiohead", "Arpeggi"),
    ("Sasha", "In a State"),
    ("Lorenzo Balzarini", "Sail to the Moon"),
    ("Kevin Van Reeken", "Sax Talk"),
    ("Sebastian Busto", "December"),
    ("Sebastian Leger", "Ashes in the Wind"),
    ("Solomun", "Never Sleep Again"),
    ("Dilby", "Soul Drive"),
    ("Hot Tuneik", "Soul on Fire"),
    ("Nora En Pure", "Spring Embers"),
    ("Ruben Karapetyan", "State of Progression"),
    ("Radio Slave", "Strobe Queen"),
    ("Tame Impala", "Not My World"),
    ("Be Svendsen", "The Bar Tender"),
    ("Chemical Brothers", "Out of Control"),
    ("The MFA", "The Difference It Makes"),
    ("The Verve", "Bittersweet Symphony"),
    ("The XX", "Tides"),
    ("Trancefeld", "Echoes Within Silence"),
    ("Underworld", "Dark and Long"),
    ("Pachanga Boys", "Time"),
    ("Way Out West", "Tuesday Maybe"),
    ("Weval", "Are You Real"),
    ("WhoMadeWho", "Never Alone"),
]

found = []
not_found = []

for artist, title in tracks:
    # Buscar por titulo (mas confiable que por artista con nombres compuestos)
    rows = con.execute("""
        SELECT c.ID, c.Title, a.Name FROM djmdContent c
        JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE LOWER(c.Title) LIKE ? AND c.rb_local_deleted=0
        LIMIT 3
    """, (f"%{title.lower()}%",)).fetchall()

    if rows:
        # Tomar el primero
        found.append((artist, title, rows[0][1], rows[0][2]))
    else:
        not_found.append((artist, title))

print(f"EN TU LIBRERIA ({len(found)}/{len(tracks)}):")
for orig_artist, orig_title, db_title, db_artist in found:
    print(f"  + {db_artist} - {db_title}")

print(f"\nNO ENCONTRADOS ({len(not_found)}):")
for a, t in not_found:
    print(f"  - {a} - {t}")

con.close()
