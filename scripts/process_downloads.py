"""Pipeline completo: backup, mover, importar y cuear tracks de Downloads."""
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
from mutagen.id3 import ID3, TIT2, TPE1
import sqlcipher3


DOWNLOADS = config.DOWNLOADS_FOLDER
DEST = config.MUSIC_NEW_FOLDER
DEST.mkdir(parents=True, exist_ok=True)


def get_bpm_from_file(path: Path) -> float:
    try:
        tags = ID3(path)
        bpm_tag = tags.get("TBPM")
        if bpm_tag:
            return float(str(bpm_tag))
    except Exception:
        pass
    return 122.0


def parse_filename(stem: str) -> tuple[str, str]:
    """Return (artist, title) from 'Artist - Title [Label]' format."""
    stem = re.sub(r"\s*\[[^\]]*\]$", "", stem).strip()
    parts = stem.split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "Unknown", stem


def main():
    tracks = sorted(list(DOWNLOADS.glob("*.mp3")) + list(DOWNLOADS.glob("*.flac")))
    print(f"Tracks a procesar: {len(tracks)}")
    for t in tracks:
        print(f"  {t.name}")

    if not tracks:
        print("Nada que procesar.")
        return

    print()
    print("Abriendo DB (backup automático)...")

    with RekordboxDB() as db:
        print("✅ Backup OK — Rekordbox no está corriendo")
        print()

        now = datetime.now()
        results = []

        for i, src in enumerate(tracks, 1):
            print(f"[{i}/{len(tracks)}] {src.name}")

            bpm = get_bpm_from_file(src)
            artist, title = parse_filename(src.stem)

            # Mover a destino
            dest_file = DEST / src.name
            if not dest_file.exists():
                shutil.copy2(src, dest_file)
                print(f"  → Copiado a {DEST.name}\\{src.name}")
            else:
                print(f"  → Ya existe en destino")

            # Analizar con librosa
            print(f"  Analizando audio (BPM={bpm:.1f})...")
            cues = analyze_track(str(dest_file), known_bpm=bpm)
            if cues is None:
                print(f"  ⚠️  Track muy corto, salteando")
                continue

            bd_str = f"{cues.breakdown:.1f}s" if cues.breakdown else "—"
            dr_str = f"{cues.drop:.1f}s" if cues.drop else "—"
            print(
                f"  M1={cues.first_beat:.1f}s  M2={cues.bass_in:.1f}s  "
                f"BD={bd_str}  DROP={dr_str}  OUT={cues.outro:.1f}s"
            )

            # Insertar en djmdContent via API oficial de pyrekordbox
            # ArtistName es un association proxy — se setea después del flush
            content = db.db.add_content(dest_file, Title=title, BPM=int(bpm * 100))
            db.db.session.flush()
            content_id = content.ID

            # Setear artista via add_artist (crea si no existe)
            try:
                artist_obj = db.db.add_artist(artist)
                db.db.session.flush()
                content.ArtistID = artist_obj.ID
                db.db.session.flush()
            except Exception:
                pass

            # Aplicar cues v8
            n = apply_cues_v8(db.db, content_id, cues)
            print(f"  ✅ {n} markers insertados")

            results.append(
                {"file": src.name, "artist": artist, "title": title, "bpm": bpm}
            )

        db.db.session.commit()

    # Integrity check post-commit
    print()
    print("Verificando integridad DB...")
    with RekordboxDB() as db2:
        result = db2.integrity_check()
        print(f"DB integrity: {result}")

    print()
    print("=== RESUMEN ===")
    for r in results:
        print(f"  ✅ {r['artist']} - {r['title']} (BPM={r['bpm']:.0f})")

    print()
    print("=== MATCH DE PLAYLISTS ===")
    print("Cattaneo Style v1/v2/v3 / Cattaneo Short:")
    cattaneo = [r for r in results if "cattaneo" in r["file"].lower()]
    for r in cattaneo:
        print(f"  ★ {r['artist']} - {r['title']}")

    anjuna = [r for r in results if "anjunadeep" in r["file"].lower()]
    if anjuna:
        print("Progressive House / DJ - Main Progressive:")
        for r in anjuna:
            print(f"  ★ {r['artist']} - {r['title']}")


if __name__ == "__main__":
    main()
