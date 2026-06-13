"""
Auditoria completa de la DB de Rekordbox + limpieza de duplicados.

Verifica:
  - Duplicados por titulo (mismo titulo, mismo artista)
  - Tracks huerfanos (en playlists pero borrados de djmdContent)
  - Tracks sin archivo en disco
  - Playlists vacias
  - Cues sin track padre
  - Entradas de djmdSongPlaylist con ContentID invalido

Uso:
  python scripts/db_audit.py          # auditoria + limpieza
  python scripts/db_audit.py --dry    # solo reporta, no modifica
"""
import sys
import os
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
import sqlcipher3

DRY = "--dry" in sys.argv


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    return con


def check_duplicates(con):
    """Detecta tracks con mismo titulo + artista. Conserva el que esta en mas playlists."""
    print("\n=== DUPLICADOS ===")

    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.FolderPath, c.rb_local_deleted
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
        ORDER BY c.Title, a.Name
    """).fetchall()

    # Agrupar por (titulo normalizado, artista normalizado)
    groups = defaultdict(list)
    for cid, artist, title, bpm, fpath, deleted in rows:
        if not title:
            continue
        key = (title.strip().lower(), (artist or "").strip().lower())
        groups[key].append((cid, artist, title, bpm, fpath))

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    if not duplicates:
        print("  Sin duplicados encontrados.")
        return 0

    print(f"  {len(duplicates)} grupos con duplicados:")
    total_removed = 0

    for (title_key, artist_key), tracks in sorted(duplicates.items()):
        # Contar cuantas playlists tiene cada uno
        playlist_counts = {}
        for cid, artist, title, bpm, fpath in tracks:
            cnt = con.execute(
                "SELECT COUNT(*) FROM djmdSongPlaylist WHERE ContentID=? AND rb_local_deleted=0",
                (str(cid),)
            ).fetchone()[0]
            playlist_counts[cid] = cnt

        # Conservar el que tiene mas playlists; empate: el de mayor ID (mas nuevo)
        keep_id = max(tracks, key=lambda t: (playlist_counts[t[0]], t[0]))[0]

        to_remove = [t for t in tracks if t[0] != keep_id]

        for cid, artist, title, bpm, fpath in to_remove:
            in_playlists = playlist_counts[cid]
            fname = Path(fpath).name if fpath else "?"
            print(f"  REMOVE [{cid}] {artist or '?'} - {title}")
            print(f"         playlists={in_playlists}  file={fname}")
            print(f"         KEEP  [{keep_id}] (playlists={playlist_counts[keep_id]})")

            if not DRY:
                # Soft delete: marcar como borrado
                con.execute(
                    "UPDATE djmdContent SET rb_local_deleted=1 WHERE ID=?",
                    (str(cid),)
                )
                # Remover de playlists
                con.execute(
                    "UPDATE djmdSongPlaylist SET rb_local_deleted=1 WHERE ContentID=?",
                    (str(cid),)
                )
                # Remover cues
                con.execute(
                    "UPDATE djmdCue SET rb_local_deleted=1 WHERE ContentID=?",
                    (str(cid),)
                )
            total_removed += 1

    print(f"\n  Total a eliminar: {total_removed} tracks duplicados")
    return total_removed


def check_orphan_playlist_entries(con):
    """Entradas en djmdSongPlaylist que apuntan a ContentID inexistente o borrado."""
    print("\n=== PLAYLIST ENTRIES HUERFANAS ===")

    rows = con.execute("""
        SELECT sp.ID, sp.PlaylistID, sp.ContentID, p.Name
        FROM djmdSongPlaylist sp
        LEFT JOIN djmdPlaylist p ON p.ID = sp.PlaylistID
        LEFT JOIN djmdContent c ON c.ID = sp.ContentID
        WHERE sp.rb_local_deleted = 0
          AND (c.ID IS NULL OR c.rb_local_deleted = 1)
    """).fetchall()

    if not rows:
        print("  Sin entradas huerfanas.")
        return 0

    print(f"  {len(rows)} entradas huerfanas:")
    for sp_id, pl_id, cid, pl_name in rows:
        print(f"  [{sp_id}] Playlist '{pl_name}' -> ContentID {cid} (no existe)")
        if not DRY:
            con.execute(
                "UPDATE djmdSongPlaylist SET rb_local_deleted=1 WHERE ID=?",
                (str(sp_id),)
            )

    return len(rows)


def check_missing_files(con):
    """Tracks cuyo archivo fisico no existe en disco."""
    print("\n=== ARCHIVOS FALTANTES ===")

    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.FolderPath
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
          AND c.FolderPath IS NOT NULL
    """).fetchall()

    missing = []
    for cid, artist, title, fpath in rows:
        if not fpath:
            continue
        # RB usa forward slashes, Windows necesita backslash
        local_path = Path(fpath.replace("/", os.sep))
        if not local_path.exists():
            missing.append((cid, artist, title, fpath))

    if not missing:
        print("  Todos los archivos existen en disco.")
        return 0

    print(f"  {len(missing)} tracks sin archivo:")
    for cid, artist, title, fpath in missing:
        print(f"  [{cid}] {artist or '?'} - {title}")
        print(f"         {fpath}")

    return len(missing)


def check_orphan_cues(con):
    """Cues cuyo ContentID no existe o esta borrado."""
    print("\n=== CUES HUERFANOS ===")

    rows = con.execute("""
        SELECT cue.ID, cue.ContentID
        FROM djmdCue cue
        LEFT JOIN djmdContent c ON c.ID = cue.ContentID
        WHERE cue.rb_local_deleted = 0
          AND (c.ID IS NULL OR c.rb_local_deleted = 1)
    """).fetchall()

    if not rows:
        print("  Sin cues huerfanos.")
        return 0

    print(f"  {len(rows)} cues huerfanos:")
    cue_ids = [r[0] for r in rows]
    for cue_id, cid in rows[:10]:
        print(f"  Cue [{cue_id}] -> ContentID {cid} (no existe)")
    if len(rows) > 10:
        print(f"  ... y {len(rows)-10} mas")

    if not DRY:
        for cue_id, _ in rows:
            con.execute(
                "UPDATE djmdCue SET rb_local_deleted=1 WHERE ID=?",
                (str(cue_id),)
            )

    return len(rows)


def check_empty_playlists(con):
    """Playlists sin tracks activos."""
    print("\n=== PLAYLISTS VACIAS ===")

    rows = con.execute("""
        SELECT p.ID, p.Name
        FROM djmdPlaylist p
        WHERE p.rb_local_deleted = 0
          AND p.Attribute = 0
          AND NOT EXISTS (
              SELECT 1 FROM djmdSongPlaylist sp
              WHERE sp.PlaylistID = p.ID AND sp.rb_local_deleted = 0
          )
    """).fetchall()

    if not rows:
        print("  Sin playlists vacias.")
        return 0

    print(f"  {len(rows)} playlists vacias:")
    for pl_id, name in rows:
        print(f"  [{pl_id}] {name}")

    return len(rows)


def check_tracks_without_cues(con):
    """Tracks activos que no tienen cues asignados."""
    print("\n=== TRACKS SIN CUES ===")

    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
          AND NOT EXISTS (
              SELECT 1 FROM djmdCue cue
              WHERE cue.ContentID = c.ID AND cue.rb_local_deleted = 0
          )
    """).fetchall()

    if not rows:
        print("  Todos los tracks tienen cues.")
        return 0

    print(f"  {len(rows)} tracks sin cues:")
    for cid, artist, title in rows[:20]:
        print(f"  [{cid}] {artist or '?'} - {title}")
    if len(rows) > 20:
        print(f"  ... y {len(rows)-20} mas")

    return len(rows)


def stats(con):
    """Estadisticas generales de la libreria."""
    print("\n=== ESTADISTICAS GENERALES ===")

    total = con.execute(
        "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0"
    ).fetchone()[0]
    with_energy = con.execute(
        "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0 AND Commnt LIKE 'E:%'"
    ).fetchone()[0]
    with_cues = con.execute("""
        SELECT COUNT(DISTINCT ContentID) FROM djmdCue WHERE rb_local_deleted=0
    """).fetchone()[0]
    playlists = con.execute(
        "SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0"
    ).fetchone()[0]
    total_playlist_entries = con.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE rb_local_deleted=0"
    ).fetchone()[0]

    print(f"  Tracks activos:          {total}")
    print(f"  Con energy score:        {with_energy} ({with_energy*100//total if total else 0}%)")
    print(f"  Con cues:                {with_cues} ({with_cues*100//total if total else 0}%)")
    print(f"  Playlists activas:       {playlists}")
    print(f"  Entradas en playlists:   {total_playlist_entries}")


def main():
    mode = "DRY RUN" if DRY else "WRITE MODE"
    print(f"DB Audit — {mode}")
    print(f"DB: {config.REKORDBOX_DB_PATH}")

    con = db_connect()

    stats(con)

    dup_removed = check_duplicates(con)
    orphan_sp = check_orphan_playlist_entries(con)
    missing_files = check_missing_files(con)
    orphan_cues = check_orphan_cues(con)
    empty_pl = check_empty_playlists(con)
    no_cues = check_tracks_without_cues(con)

    print("\n=== RESUMEN ===")
    print(f"  Duplicados eliminados:          {dup_removed}")
    print(f"  Playlist entries huerfanas:     {orphan_sp}")
    print(f"  Archivos faltantes en disco:    {missing_files}")
    print(f"  Cues huerfanos:                 {orphan_cues}")
    print(f"  Playlists vacias:               {empty_pl}")
    print(f"  Tracks sin cues:                {no_cues}")

    if not DRY and (dup_removed or orphan_sp or orphan_cues):
        con.commit()
        print("\nDB actualizada. Abri Rekordbox y hace sync al pen.")
    elif DRY:
        print("\n[DRY RUN] No se modifico nada.")
    else:
        print("\nDB sin cambios necesarios.")

    # Verificacion final de integridad
    result = con.execute("PRAGMA integrity_check").fetchone()
    print(f"\nIntegridad SQLite: {result[0]}")

    con.close()


if __name__ == "__main__":
    main()
