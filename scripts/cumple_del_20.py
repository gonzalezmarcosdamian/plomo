"""Pipeline completo: mover de Downloads, importar, cuear y crear playlist 'Cumple del 20'."""
import sys
import re
import shutil
import random
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB, RekordboxRunningError
from plomo.cue_engine import analyze_track, apply_cues_v8
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import sqlcipher3

PLAYLIST_NAME = "Cumple del 20"
DOWNLOADS = config.DOWNLOADS_FOLDER
DEST = config.MUSIC_NEW_FOLDER
DEST.mkdir(parents=True, exist_ok=True)


def get_bpm(path: Path) -> float:
    try:
        if path.suffix.lower() == ".mp3":
            tags = MP3(path).tags
            t = tags.get("TBPM") or tags.get("BPM")
            if t:
                return float(str(t).split("\n")[0])
        elif path.suffix.lower() == ".flac":
            tags = FLAC(path)
            if "BPM" in tags:
                return float(tags["BPM"][0])
    except Exception:
        pass
    return 122.0


def parse_filename(stem: str) -> tuple[str, str]:
    stem = re.sub(r"\s*\[[^\]]*\]$", "", stem).strip()
    parts = stem.split(" - ", 1)
    return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else ("Unknown", stem)


def safe_id() -> str:
    return str(random.randint(1500000000, 4000000000))


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_playlist(con, name: str, content_ids: list) -> str:
    pl_id = safe_id()
    pl_uuid = str(uuid_lib.uuid4())
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    usn = max_usn + 1
    ts = now_str()

    con.execute("""
        INSERT INTO djmdPlaylist
          (ID, Seq, Name, ImagePath, Attribute, ParentID, SmartList, UUID,
           rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
           usn, rb_local_usn, created_at, updated_at)
        VALUES (?,?,?,NULL,0,'296109753',NULL,?,0,0,0,0,NULL,?,?,?)
    """, (pl_id, 0, name, pl_uuid, usn, ts, ts))

    max_sp_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    for i, cid in enumerate(content_ids, 1):
        sp_id = safe_id()
        sp_uuid = str(uuid_lib.uuid4())
        max_sp_usn += 1
        con.execute("""
            INSERT INTO djmdSongPlaylist
              (ID, PlaylistID, ContentID, TrackNo, UUID,
               rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
               usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
        """, (sp_id, pl_id, str(cid), i, sp_uuid, max_sp_usn, ts, ts))

    return pl_id


def main():
    tracks = sorted(list(DOWNLOADS.glob("*.mp3")) + list(DOWNLOADS.glob("*.flac")))
    print(f"Tracks encontrados en Downloads: {len(tracks)}")
    for t in tracks:
        print(f"  {t.name}")

    if not tracks:
        print("Nada que procesar.")
        return

    print(f"\nDestino: {DEST}")
    print("Abriendo DB (backup automático)...")

    with RekordboxDB() as db:
        print("✅ Pre-flight OK — Rekordbox no corre")
        print("✅ Backup creado\n")

        content_ids = []

        for i, src in enumerate(tracks, 1):
            print(f"[{i}/{len(tracks)}] {src.name}")
            bpm = get_bpm(src)
            artist, title = parse_filename(src.stem)

            # 1. Mover a destino
            dest_file = DEST / src.name
            if dest_file.exists():
                print(f"  → Ya existe en destino")
            else:
                shutil.move(str(src), str(dest_file))
                print(f"  → Movido a {DEST.name}/{src.name}")

            # 2. Importar a DB via pyrekordbox
            try:
                content = db.db.add_content(dest_file, Title=title, BPM=int(bpm * 100))
                db.db.session.flush()
                content_id = content.ID
                try:
                    artist_obj = db.db.add_artist(artist)
                    db.db.session.flush()
                    content.ArtistID = artist_obj.ID
                    db.db.session.flush()
                except Exception:
                    pass
                print(f"  DB ID: {content_id} | {artist} — {title} (BPM={bpm:.0f})")
            except Exception as e:
                print(f"  ⚠️  add_content falló: {e} — buscando por filename...")
                # fallback: buscar por filename en DB
                import sqlcipher3 as sc
                con_tmp = sc.connect(str(config.REKORDBOX_DB_PATH))
                con_tmp.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
                row = con_tmp.execute(
                    "SELECT ID FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0",
                    (dest_file.name,)
                ).fetchone()
                con_tmp.close()
                if row:
                    content_id = row[0]
                    print(f"  → Encontrado en DB: ID={content_id}")
                else:
                    print(f"  ❌ No encontrado en DB, salteando cues")
                    continue

            content_ids.append(content_id)

            # 3. Analizar audio + cues v8
            print(f"  Analizando audio (BPM={bpm:.1f})...")
            cues = analyze_track(str(dest_file), known_bpm=bpm)
            if cues is None:
                print(f"  ⚠️  Track muy corto, salteando cues")
                continue
            n = apply_cues_v8(db.db, content_id, cues)
            print(f"  ✅ {n} markers | M1={cues.first_beat:.1f}s M2={cues.bass_in:.1f}s OUT={cues.outro:.1f}s")

        db.db.session.commit()

        # 4. Crear playlist "Cumple del 20"
        print(f"\n=== Creando playlist '{PLAYLIST_NAME}' con {len(content_ids)} tracks ===")
        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
        pl_id = create_playlist(con, PLAYLIST_NAME, content_ids)
        con.commit()
        con.close()
        print(f"✅ Playlist creada — ID={pl_id}")

        # 5. Actualizar masterPlaylists6.xml
        db.add_node_to_xml(int(pl_id), 296109753)  # bajo "Pro DJ Library"
        print(f"✅ XML actualizado")

    # 6. Integrity check
    print("\nVerificando integridad DB...")
    with RekordboxDB() as db2:
        result = db2.integrity_check()
        print(f"DB integrity: {result}")

    print(f"\n=== LISTO ===")
    print(f"  Tracks procesados: {len(content_ids)}")
    print(f"  Playlist: '{PLAYLIST_NAME}' (ID={pl_id})")
    print(f"  Abrí Rekordbox para ver los cambios.")

    return content_ids, tracks


if __name__ == "__main__":
    main()
