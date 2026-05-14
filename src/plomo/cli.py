"""Plomo CLI - DJ IA Project automation entrypoint."""
import sys
import json
from pathlib import Path

import click

from . import config
from .rekordbox_db import RekordboxDB, RekordboxRunningError
from .cue_engine import analyze_track, apply_cues_v8


@click.group()
def main():
    """Plomo - DJ IA Project automation toolkit."""


@main.command()
def stats():
    """Mostrar estado de la colección: tracks, BPM distribution, gaps."""
    import sqlcipher3
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    total = con.execute(
        "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0"
    ).fetchone()[0]
    cued = con.execute(
        "SELECT COUNT(DISTINCT ContentID) FROM djmdCue"
    ).fetchone()[0]
    playlists = con.execute(
        "SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0"
    ).fetchone()[0]

    click.echo(f"📊 Colección Rekordbox")
    click.echo(f"  Total tracks: {total}")
    click.echo(f"  Tracks cueados: {cued}")
    click.echo(f"  Playlists: {playlists}")

    # BPM distribution
    bpm_dist = con.execute("""
        SELECT
          CASE
            WHEN BPM < 11800 THEN '<118 BPM (Outro)'
            WHEN BPM BETWEEN 11800 AND 12200 THEN '118-122 BPM (Warmup)'
            WHEN BPM BETWEEN 12200 AND 12500 THEN '122-125 BPM (Sweet)'
            WHEN BPM BETWEEN 12500 AND 12800 THEN '125-128 BPM (Build)'
            WHEN BPM BETWEEN 12800 AND 13000 THEN '128-130 BPM (Peak)'
            ELSE '>130 BPM (Hard)'
          END AS range_,
          COUNT(*)
        FROM djmdContent WHERE rb_local_deleted=0 AND BPM > 0
        GROUP BY range_ ORDER BY MIN(BPM)
    """).fetchall()
    click.echo("\n  Distribución BPM:")
    for r, c in bpm_dist:
        click.echo(f"    {r:<25} {c:>4}")

    con.close()


@main.command()
@click.option('--dry-run', is_flag=True, help='Solo mostrar qué se haría')
@click.option('--files', multiple=True, type=click.Path(exists=True),
              help='Archivos específicos a procesar (override Downloads scan)')
def analyze(dry_run: bool, files: tuple):
    """Procesar nuevos tracks en Downloads: mover, importar, cuear."""
    import shutil
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    import sqlcipher3
    from pyrekordbox.db6 import Rekordbox6Database, DjmdContent

    if files:
        new_files = [Path(f) for f in files]
    else:
        downloads = config.DOWNLOADS_FOLDER
        if not downloads.exists():
            click.echo(f"❌ Downloads folder no existe: {downloads}")
            sys.exit(1)
        new_files = list(downloads.glob("*.mp3")) + list(downloads.glob("*.flac"))

    click.echo(f"🎵 Encontrados {len(new_files)} archivos")
    if not new_files:
        click.echo("  Nada que procesar.")
        return

    if dry_run:
        for f in new_files:
            click.echo(f"  [DRY] {f.name}")
        return

    config.MUSIC_NEW_FOLDER.mkdir(parents=True, exist_ok=True)

    try:
        with RekordboxDB() as db:
            click.echo("  ✅ Pre-flight OK — Rekordbox no corre")
            click.echo("  ✅ Backup creado")

            for src in new_files:
                click.echo(f"\n  ▶ {src.name}")

                # 1. Leer BPM de ID3
                bpm = 122.0
                try:
                    if src.suffix.lower() == '.mp3':
                        audio = MP3(src)
                        bpm_tag = audio.tags.get('TBPM') or audio.tags.get('BPM')
                        if bpm_tag:
                            bpm = float(str(bpm_tag).split('\n')[0])
                    elif src.suffix.lower() == '.flac':
                        audio = FLAC(src)
                        if 'BPM' in audio:
                            bpm = float(audio['BPM'][0])
                except Exception:
                    pass
                click.echo(f"     BPM: {bpm:.1f}")

                # 2. Mover a carpeta Music/Nuevos/YYYY-MM
                dest = config.MUSIC_NEW_FOLDER / src.name
                if dest.exists():
                    click.echo(f"     ⚠️  Ya existe en destino, saltando movida")
                else:
                    shutil.move(str(src), str(dest))
                    click.echo(f"     📁 Movido → {dest.parent.name}/{dest.name}")

                # 3. Buscar track en DB por path
                con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
                con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
                path_variants = [str(dest).replace('\\', '/'), str(dest)]
                content_id = None
                for pv in path_variants:
                    row = con.execute(
                        "SELECT ID FROM djmdContent WHERE FolderPath=? AND rb_local_deleted=0",
                        (pv,)
                    ).fetchone()
                    if row:
                        content_id = row[0]
                        break
                    # buscar por filename
                    row = con.execute(
                        "SELECT ID FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0",
                        (dest.name,)
                    ).fetchone()
                    if row:
                        content_id = row[0]
                        break
                con.close()

                if not content_id:
                    click.echo(f"     ⚠️  Track no encontrado en DB — importalo en Rekordbox primero")
                    continue

                # Actualizar FolderPath al destino real (fix post-move)
                con2 = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
                con2.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
                con2.execute(
                    "UPDATE djmdContent SET FolderPath=? WHERE ID=?",
                    (str(dest).replace("\\", "/"), content_id)
                )
                con2.commit()
                con2.close()

                click.echo(f"     🔍 ContentID: {content_id}")

                # 4. Análisis de audio + cues v8
                click.echo(f"     🎧 Analizando audio (cue engine v8)...")
                cues = analyze_track(str(dest), known_bpm=bpm)
                if not cues:
                    click.echo(f"     ⚠️  Track muy corto, saltando cues")
                    continue

                click.echo(f"     M1 first_beat: {cues.first_beat:.2f}s")
                click.echo(f"     M2 bass_in:    {cues.bass_in:.2f}s")
                if cues.breakdown:
                    click.echo(f"     M3 breakdown:  {cues.breakdown:.2f}s")
                if cues.drop:
                    click.echo(f"     M4 drop:       {cues.drop:.2f}s")
                click.echo(f"     M5 outro:      {cues.outro:.2f}s")

                # 5. Escribir cues en DB
                n = apply_cues_v8(db.db, content_id, cues)
                click.echo(f"     ✅ {n} markers escritos en DB")

    except RekordboxRunningError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)


@main.command()
@click.option('--style', type=click.Choice(['vuarambon', 'cattaneo', 'eze-arias', 'main-prog']),
              required=True)
@click.option('--duration', type=int, default=60, help='Duración en minutos')
def playlist(style: str, duration: int):
    """Generar set por estilo (vuarambon, cattaneo, eze-arias, main-prog)."""
    click.echo(f"🎧 Playlist style={style} duration={duration}min")
    click.echo("   ⚠️  TODO: portar lógica de scripts/find_vuarambon.py + create_vuarambon_pl.py")


@main.command()
def backup():
    """Backup manual de master.db + masterPlaylists6.xml."""
    try:
        with RekordboxDB() as db:
            click.echo(f"✅ Backup creado en {config.BACKUP_FOLDER}")
    except RekordboxRunningError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)


@main.command()
def verify():
    """Integrity check + reportar inconsistencias."""
    try:
        with RekordboxDB() as db:
            integrity = db.integrity_check()
            click.echo(f"DB integrity: {integrity}")
            if integrity != 'ok':
                click.echo("❌ DB corrupta. Restaurar backup desde outputs/", err=True)
                sys.exit(1)
            click.echo("✅ DB OK")
    except RekordboxRunningError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)


@main.command()
def watch():
    """Daemon: procesa Downloads automáticamente cuando aparece archivo nuevo."""
    click.echo("⚠️  TODO: implementar con watchdog. Ver scripts/watcher.py")


if __name__ == "__main__":
    main()
