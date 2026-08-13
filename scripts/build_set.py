"""
Construye / reconstruye un set en Rekordbox DB a partir de un target JSON.

Debe correrse DESPUES de:
  1. plan_set.py --batch  (genero el batch)
  2. muzpa_download.py --batch ...  (descargo)
  3. import_all.py + Rekordbox import + post_import.py  (importo a la DB)

Uso:
  python scripts/build_set.py 16          # construye set 16
  python scripts/build_set.py 16 --dry    # muestra el orden sin escribir
  python scripts/build_set.py --all       # construye todos los sets con target JSON
"""
import sys
import json
import random
import uuid as uuid_lib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.set_builder import SetConfig, Movement, build_set
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

SETS_ARMADOS_PARENT = "1975667623"

TARGETS_DIR = Path(__file__).parent.parent / "data" / "set_targets"
SETS_LOG = Path(__file__).parent.parent / "docs" / "sets_log.md"


def safe_id() -> str:
    return str(random.randint(1500000000, 4000000000))


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    return con


class AmbiguousPlaylistError(Exception):
    """Mas de una playlist comparte el mismo numero de set."""


def find_playlist(con, set_num: int) -> tuple[str, str] | None:
    rows = con.execute(
        "SELECT ID, Name FROM djmdPlaylist WHERE Name LIKE ? AND rb_local_deleted=0"
        " ORDER BY Name",
        (f"{set_num}.%",)
    ).fetchall()
    if not rows:
        return None
    if len(rows) > 1:
        # Antes devolvia rows[0] sin ORDER BY: con numeros duplicados podia
        # reconstruir —y borrar— el set equivocado.
        nombres = "\n".join(f"    - {r[1]}" for r in rows)
        raise AmbiguousPlaylistError(
            f"El numero {set_num} corresponde a {len(rows)} playlists:\n{nombres}\n"
            f"  Renombra las que sobren para que el numero sea unico."
        )
    return (rows[0][0], rows[0][1])


def create_playlist(con, name: str) -> str:
    pl_id = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    ts = now_str()
    con.execute("""INSERT INTO djmdPlaylist
        (ID, Seq, Name, ImagePath, Attribute, ParentID, SmartList, UUID,
         rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
         usn, rb_local_usn, created_at, updated_at)
        VALUES (?,0,?,NULL,0,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (pl_id, name, SETS_ARMADOS_PARENT, str(uuid_lib.uuid4()), max_usn + 1, ts, ts))
    return pl_id


def load_target(set_num: int) -> dict | None:
    path = TARGETS_DIR / f"set_{set_num:02d}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_tracks(con, target: dict) -> list[dict]:
    """
    Para cada track en target['tracks']:
    - Si tiene content_id: lo usa directamente
    - Si no: busca en djmdContent por artist + title
    Retorna lista de tracks con content_id resuelto y metadata real de la DB.
    """
    resolved = []
    for t in target.get("tracks", []):
        cid = t.get("content_id")

        KEY_JOIN = "LEFT JOIN djmdKey k ON k.ID = c.KeyID"
        KEY_COL = "COALESCE(k.ScaleName, '?')"

        if not cid:
            artist = t.get("artist", "")
            title = t.get("title", "")
            rows = con.execute(f"""
                SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt, {KEY_COL}
                FROM djmdContent c
                LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
                {KEY_JOIN}
                WHERE c.rb_local_deleted = 0
                  AND LOWER(c.Title) LIKE LOWER(?)
                  AND LOWER(COALESCE(a.Name,'')) LIKE LOWER(?)
            """, (f"%{title}%", f"%{artist.split()[0]}%")).fetchall()

            if not rows:
                rows = con.execute(f"""
                    SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt, {KEY_COL}
                    FROM djmdContent c
                    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
                    {KEY_JOIN}
                    WHERE c.rb_local_deleted=0 AND LOWER(c.Title) LIKE LOWER(?)
                """, (f"%{title}%",)).fetchall()

            if not rows:
                print(f"  [warn] No encontrado en DB: {artist} - {title}")
                continue

            cid = str(rows[0][0])
            db_artist = rows[0][1] or artist
            db_title = rows[0][2] or title
            bpm_raw = rows[0][3] or 12200
            commnt = rows[0][4] or ""
            db_key = rows[0][5] or "?"
        else:
            row = con.execute(f"""
                SELECT a.Name, c.Title, c.BPM, c.Commnt, {KEY_COL}
                FROM djmdContent c
                LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
                {KEY_JOIN}
                WHERE c.ID=? AND c.rb_local_deleted=0
            """, (str(cid),)).fetchone()
            if not row:
                print(f"  [warn] content_id {cid} no encontrado en DB")
                continue
            db_artist, db_title, bpm_raw, commnt, db_key = row
            db_artist = db_artist or t.get("artist", "?")
            db_title = db_title or t.get("title", "?")
            bpm_raw = bpm_raw or 12200
            db_key = db_key or "?"

        # Energy: from Commnt if available, else BPM proxy
        def _bpm_proxy(b: float) -> float:
            if b < 118: return 2.5
            if b < 120: return 3.5
            if b < 122: return 5.0
            if b < 124: return 5.5
            if b < 126: return 6.0
            return 6.5

        bpm_val = (bpm_raw or 12200) / 100
        energy = t.get("energy", _bpm_proxy(bpm_val))
        if commnt and "E:" in commnt:
            try:
                energy = float(commnt.split("|")[0].replace("E:", "").strip())
            except ValueError:
                energy = _bpm_proxy(bpm_val)

        resolved.append({
            "id": str(cid),
            "artist": db_artist,
            "title": db_title,
            "bpm": bpm_raw / 100,
            "energy": energy,
            "key": db_key,
        })

    return resolved


def rebuild_playlist(con, playlist_id: str, tracks: list[dict], ts: str) -> int:
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    # Soft delete, no DELETE fisico: el sync por USN del pen necesita el
    # tombstone para enterarse de que la fila se fue. Sin esto el pen acumula
    # las entradas viejas y aparecen duplicados en las playlists exportadas.
    for (row_id,) in con.execute(
        "SELECT ID FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0",
        (playlist_id,),
    ).fetchall():
        max_usn += 1
        con.execute(
            "UPDATE djmdSongPlaylist SET rb_local_deleted=1, rb_local_synced=0,"
            " rb_local_usn=?, updated_at=? WHERE ID=?",
            (max_usn, ts, row_id),
        )
    for i, t in enumerate(tracks, 1):
        max_usn += 1
        con.execute("""
            INSERT INTO djmdSongPlaylist
              (ID, PlaylistID, ContentID, TrackNo, UUID,
               rb_data_status, rb_local_data_status, rb_local_deleted,
               rb_local_synced, usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
        """, (safe_id(), playlist_id, t["id"], i,
              str(uuid_lib.uuid4()), max_usn, ts, ts))
    return len(tracks)


def print_tracklist(tracks: list[dict], name: str) -> None:
    print(f"\n{name} ({len(tracks)} tracks):")
    for i, t in enumerate(tracks, 1):
        print(f"  {i:>2}. E:{t['energy']:.1f} {t['bpm']:.0f}bpm {str(t.get('key','?')):<4} | "
              f"{t['artist'][:18]:18} — {t['title'][:36]}")


def update_sets_log(set_num: int, name: str, tracks: list[dict], target: dict) -> None:
    """Agrega o actualiza la entrada del set en docs/sets_log.md."""
    SETS_LOG.parent.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    duration_h = target.get("duration_h", "?")
    bpm_range = target.get("bpm_range", ["?", "?"])

    # Contar origenes
    in_library = sum(1 for t in target.get("tracks", []) if t.get("content_id"))
    total = len(tracks)

    section = f"\n## Set {set_num:02d}. {name}\n"
    section += f"**Armado:** {date_str}  \n"
    section += f"**Duracion:** {duration_h}h  \n"
    section += f"**Tracks:** {total}  \n"
    section += f"**BPM range:** {bpm_range[0]}-{bpm_range[1]}  \n"
    section += "\n| # | Artist | Title | BPM | E |\n"
    section += "|---|--------|-------|-----|---|\n"
    for i, t in enumerate(tracks, 1):
        section += f"| {i} | {t['artist']} | {t['title']} | {t['bpm']:.0f} | {t['energy']:.1f} |\n"
    section += "\n"

    # Leer log existente
    if SETS_LOG.exists():
        content = SETS_LOG.read_text(encoding="utf-8")
    else:
        content = "# Sets Log\n\nDocumento vivo — sets armados por fecha.\n"

    # Reemplazar entrada existente o agregar nueva
    marker = f"## Set {set_num:02d}."
    if marker in content:
        # Encontrar y reemplazar la seccion existente
        start = content.index(marker)
        # Buscar el proximo ## o fin
        next_section = content.find("\n## ", start + 1)
        if next_section == -1:
            content = content[:start] + section.lstrip("\n")
        else:
            content = content[:start] + section.lstrip("\n") + content[next_section:]
    else:
        content += section

    SETS_LOG.write_text(content, encoding="utf-8")
    print(f"\nsets_log.md actualizado: Set {set_num:02d}")


def build_one(set_num: int, dry: bool = False) -> None:
    target = load_target(set_num)
    if not target:
        print(f"ERROR: No existe data/set_targets/set_{set_num:02d}.json")
        return

    con = db_connect()
    playlist = find_playlist(con, set_num)
    new_playlist = False

    if not playlist:
        pl_name = target.get("name", f"{set_num}. Set")
        print(f"  [info] Playlist no encontrada — creando: {pl_name}")
        with RekordboxDB() as db:
            pl_id = create_playlist(con, pl_name)
            con.commit()
            db.add_node_to_xml(int(pl_id), int(SETS_ARMADOS_PARENT))
        new_playlist = True
    else:
        pl_id, pl_name = playlist

    print(f"\n{'='*60}")
    print(f"BUILD SET {set_num}: {pl_name}")

    # Resolver tracks desde DB
    tracks = resolve_tracks(con, target)
    if not tracks:
        print("ERROR: No se pudo resolver ningun track")
        con.close()
        return

    # Diversidad de artistas: max 3 tracks del mismo artista
    max_per_artist = target.get("max_per_artist", 3)
    from collections import Counter
    artist_count: Counter = Counter()
    filtered = []
    for t in tracks:
        primary = t["artist"].split(",")[0].strip().split("&")[0].strip()
        if artist_count[primary] < max_per_artist:
            filtered.append(t)
            artist_count[primary] += 1
        else:
            print(f"  [div] Removido (max {max_per_artist}/artista): {t['artist']} - {t['title']}")
    tracks = filtered

    # Ordenar con el algoritmo de movimientos si hay config
    movements_cfg = target.get("movements")
    if target.get("keep_order"):
        # El orden del JSON es curaduria humana: se respeta tal cual.
        # El algoritmo optimiza energia + Camelot, pero no ve las razones
        # de un bajon deliberado de BPM o de sostener una key tres tracks.
        print("  [keep_order] Se respeta el orden del target, sin reordenar")
    elif movements_cfg:
        movements = [
            Movement(
                m["name"],
                m["e_min"], m["e_max"], m.get("e_center", (m["e_min"] + m["e_max"]) / 2),
                m["fraction"],
                anchor_ids=m.get("anchor_ids", [])
            )
            for m in movements_cfg
        ]
        set_config = SetConfig(name=pl_name, movements=movements)
        tracks = build_set(tracks, set_config)
    else:
        # Fallback: ordenar por energia (arco progresivo simple)
        tracks = sorted(tracks, key=lambda t: t["energy"])

    print_tracklist(tracks, pl_name)

    if dry:
        print("\n[DRY RUN] No se escribio nada en la DB")
        con.close()
        return

    ts = now_str()
    n = rebuild_playlist(con, pl_id, tracks, ts)
    con.commit()
    con.close()

    print(f"\nPlaylist reconstruida: {n} tracks")
    update_sets_log(set_num, pl_name, tracks, target)
    print("Listo. Abri Rekordbox y hace sync al pen.")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(__doc__)
        return

    dry = "--dry" in sys.argv

    if sys.argv[1] == "--all":
        targets = sorted(TARGETS_DIR.glob("set_*.json"))
        if not targets:
            print("No hay targets en data/set_targets/")
            return
        for f in targets:
            num = int(f.stem.replace("set_", ""))
            build_one(num, dry=dry)
        return

    try:
        set_num = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: '{sys.argv[1]}' no es un numero de set valido")
        return

    build_one(set_num, dry=dry)


if __name__ == "__main__":
    main()
