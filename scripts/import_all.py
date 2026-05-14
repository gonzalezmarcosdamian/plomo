"""
Pipeline completo para tracks nuevos en Downloads:
1. Mover a Music/Nuevos/YYYY-MM
2. Importar a Rekordbox DB (add_content o find by filename)
3. Fix artistas desde filename
4. Aplicar cues v8
5. Fix DeliveryControl = 'on'
6. Calcular energy score → Commnt
7. Copiar ANLZ al pen
"""
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
from plomo.energy import calculate_energy, energy_label
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import sqlcipher3

DOWNLOADS = config.DOWNLOADS_FOLDER
DEST = config.MUSIC_NEW_FOLDER
DEST.mkdir(parents=True, exist_ok=True)
PEN_SHARE = Path(r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\share")
PEN_ROOT = Path("D:/")


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


def safe_id(): return str(random.randint(1500000000, 4000000000))
def now_str(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_cue_timings(con, content_id: str) -> dict:
    cues = con.execute(
        "SELECT Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0",
        (content_id,)
    ).fetchall()
    result = {}
    for comment, in_msec in cues:
        if comment in ("Mix-IN First Beat", "M-First Beat"):
            result["first_beat"] = in_msec
        elif comment in ("Bass IN", "M-Bass IN"):
            result["bass_in"] = in_msec
        elif comment in ("Breakdown", "M-Breakdown"):
            result["breakdown"] = in_msec
        elif comment in ("DROP", "M-DROP"):
            result["drop"] = in_msec
        elif comment == "Mix-OUT":
            result["outro"] = in_msec
    return result


def copy_anlz_to_pen(con, content_id: str, title: str):
    row = con.execute(
        "SELECT AnalysisDataPath FROM djmdContent WHERE ID=?", (str(content_id),)
    ).fetchone()
    if not row or not row[0]:
        return False
    apath = row[0]
    rel = apath.lstrip("/")
    local_src = PEN_SHARE / rel
    pen_dst = PEN_ROOT / rel.replace("/", "\\")
    if not local_src.exists():
        return False
    if pen_dst.exists():
        return True
    pen_dst.parent.mkdir(parents=True, exist_ok=True)
    for f in local_src.parent.iterdir():
        shutil.copy2(f, pen_dst.parent / f.name)
    print(f"  ANLZ → pen: {title[:40]}")
    return True


def main():
    tracks = sorted(list(DOWNLOADS.glob("*.mp3")) + list(DOWNLOADS.glob("*.flac")))
    print(f"Tracks en Downloads: {len(tracks)}")
    for t in tracks:
        print(f"  {t.name}")

    if not tracks:
        print("Nada que procesar.")
        return

    ts = now_str()
    results = []

    # ── FASE 1: pyrekordbox — mover, importar, cues ──────────────────────────
    with RekordboxDB() as db:
        print("\n✅ Pre-flight OK | Backup creado\n")

        for i, src in enumerate(tracks, 1):
            print(f"[{i}/{len(tracks)}] {src.name}")
            bpm = get_bpm(src)
            artist, title = parse_filename(src.stem)

            # Mover a destino
            dest_file = DEST / src.name
            if not dest_file.exists():
                shutil.move(str(src), str(dest_file))
                print(f"  → Movido a {DEST.name}/")
            else:
                if src.exists():
                    src.unlink()
                print(f"  → Ya existía, duplicado removido de Downloads")

            # Importar a DB via pyrekordbox
            content_id = None
            is_new = False
            try:
                content = db.db.add_content(dest_file, Title=title, BPM=int(bpm * 100))
                db.db.session.flush()
                content_id = str(content.ID)
                try:
                    artist_obj = db.db.add_artist(artist)
                    db.db.session.flush()
                    content.ArtistID = artist_obj.ID
                    db.db.session.flush()
                except Exception:
                    pass
                is_new = True
            except Exception:
                # fallback: buscar por filename
                con_tmp = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
                con_tmp.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
                row = con_tmp.execute(
                    "SELECT ID FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0",
                    (dest_file.name,)
                ).fetchone()
                con_tmp.close()
                if row:
                    content_id = str(row[0])
                else:
                    print(f"  ❌ No se pudo importar")
                    continue

            print(f"  ID={content_id} ({'nuevo' if is_new else 'existente'}) | {artist} — {title} | BPM={bpm:.0f}")

            # Cues v8
            print(f"  Analizando audio...")
            cues = analyze_track(str(dest_file), known_bpm=bpm)
            if cues:
                n = apply_cues_v8(db.db, int(content_id), cues)
                print(f"  ✅ {n} markers | M1={cues.first_beat:.1f}s M2={cues.bass_in:.1f}s OUT={cues.outro:.1f}s")
            else:
                print(f"  ⚠️  Track muy corto, sin cues")

            results.append({"id": content_id, "artist": artist, "title": title, "bpm": bpm, "dest": dest_file})

        db.db.session.commit()
        print(f"\n  {len(results)} tracks importados y cueados")

    # ── FASE 2: sqlcipher3 — fix metadata + energy ───────────────────────────
    print("\n=== Fix metadata + energy scores ===")
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    for r in results:
        cid = r["id"]
        artist = r["artist"]
        dest_file = r["dest"]
        bpm = r["bpm"]

        # Fix artista si falta
        a_check = con.execute("SELECT ArtistID FROM djmdContent WHERE ID=?", (cid,)).fetchone()
        if a_check and not a_check[0]:
            a_row = con.execute(
                "SELECT ID FROM djmdArtist WHERE Name=? AND rb_local_deleted=0", (artist,)
            ).fetchone()
            if a_row:
                aid = a_row[0]
            else:
                aid = safe_id()
                max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdArtist").fetchone()[0] or 0
                con.execute("""INSERT INTO djmdArtist
                    (ID,Name,rb_data_status,rb_local_data_status,rb_local_deleted,
                     rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                    VALUES (?,?,0,0,0,0,NULL,?,?,?)""",
                    (aid, artist, max_usn + 1, ts, ts))
            con.execute("UPDATE djmdContent SET ArtistID=? WHERE ID=?", (aid, cid))

        # Fix FolderPath + DeliveryControl
        folder = str(dest_file).replace("\\", "/")
        con.execute("""UPDATE djmdContent SET
            FolderPath=?, DeliveryControl='on', updated_at=? WHERE ID=?""",
            (folder, ts, cid))

        # Energy score
        row = con.execute("SELECT BPM, Length FROM djmdContent WHERE ID=?", (cid,)).fetchone()
        if row:
            bpm_val = (row[0] or 12200) / 100
            timings = get_cue_timings(con, cid)
            if timings:
                score = calculate_energy(
                    bpm=bpm_val,
                    bass_in_ms=timings.get("bass_in"),
                    breakdown_ms=timings.get("breakdown"),
                    drop_ms=timings.get("drop"),
                    outro_ms=timings.get("outro"),
                    track_length_ms=row[1],
                )
                label = energy_label(score)
                prev = (con.execute("SELECT Commnt FROM djmdContent WHERE ID=?", (cid,)).fetchone() or [""])[0] or ""
                if prev.startswith("E:"):
                    prev = prev.split("|", 1)[1].strip() if "|" in prev else ""
                new_commnt = f"E:{score}" + (f" | {prev}" if prev else "")
                con.execute("UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                            (new_commnt, ts, cid))
                print(f"  E:{score} [{label:7}] {r['artist']} — {r['title']}")

    con.commit()

    # ── FASE 3: copiar ANLZ al pen ───────────────────────────────────────────
    if (PEN_ROOT / "PIONEER").exists():
        print("\n=== Copiando ANLZ al pen ===")
        for r in results:
            copy_anlz_to_pen(con, r["id"], r["title"])
    else:
        print("\n  Pen no conectado — conectalo antes del sync")

    con.close()

    # ── Integrity check ──────────────────────────────────────────────────────
    with RekordboxDB() as db2:
        print(f"\nDB integrity: {db2.integrity_check()}")

    print(f"\n=== LISTO — {len(results)} tracks procesados ===")
    for r in results:
        print(f"  ✅ {r['artist']} — {r['title']} (BPM={r['bpm']:.0f})")
    print("\nAbrí Rekordbox y hacé sync.")


if __name__ == "__main__":
    main()
