"""Arbol de carpetas navegable, construido con hardlinks sobre el deposito.

La doctrina: el disco guarda, no organiza. Los archivos viven en su carpeta por
fecha de ingreso y no se mueven nunca — asi ningun path de Rekordbox se rompe.
La organizacion vive aca: un arbol descartable por rol de set, energia, genero,
key, BPM y sello, hecho con hardlinks que no ocupan espacio ni duplican nada.

Se puede borrar entero y regenerar sin consecuencias. Eso es lo que lo hace util:
cambiar de opinion sobre como ver la coleccion no cuesta nada.

Vive fuera de OneDrive a proposito: OneDrive convierte archivos en placeholders
en la nube y trata mal los hardlinks.

Uso:
    python scripts/build_views.py --dry          # que haria
    python scripts/build_views.py                # regenerar
    python scripts/build_views.py --m3u          # ademas playlists .m3u8
    python scripts/build_views.py --solo rol energia
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

RAIZ_VISTAS = Path(os.getenv("VIEWS_ROOT", r"C:\Users\gonza\Music\Vistas"))
MARCA = ".plomo-vistas"  # sin este archivo el script se niega a borrar la raiz
ENERGY_RE = re.compile(r"E:(\d+(?:\.\d+)?)")
MIN_TRACKS_SELLO = 5

# Roles de set. Los cortes salen de la escala de energia del proyecto y del uso
# real: lo que abre, lo que construye, lo que sostiene, lo que rompe.
ROLES = [
    (0.0, 3.5, "1 Apertura"),
    (3.5, 5.5, "2 Construccion"),
    (5.5, 6.5, "3 Meseta"),
    (6.5, 7.5, "4 Peak"),
    (7.5, 99.0, "5 Detonante"),
]


def _sano(nombre: str) -> str:
    """Nombre de carpeta valido en Windows."""
    n = re.sub(r'[<>:"/\\|?*]', "-", nombre).strip(" .")
    return n[:80] or "sin dato"


def cargar_tracks() -> list[dict]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    rows = con.execute(
        """
        SELECT c.FolderPath, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt,
               l.Name, g.Name
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        LEFT JOIN djmdKey   k ON k.ID = c.KeyID
        LEFT JOIN djmdLabel l ON l.ID = c.LabelID
        LEFT JOIN djmdGenre g ON g.ID = c.GenreID
        WHERE c.rb_local_deleted = 0 AND c.FolderPath IS NOT NULL
          -- Los demos y one-shots que trae Pioneer no son musica: aparecian en
          -- las vistas como "E--- 0 7A - NOISE.wav" y ensuciaban los conteos.
          AND c.FolderPath NOT LIKE '%/PioneerDJ/%'
        """
    ).fetchall()
    con.close()

    out = []
    for folder, artist, title, bpm_raw, key, commnt, label, genre in rows:
        m = ENERGY_RE.search(commnt or "")
        out.append({
            "path": Path(folder),
            "artist": artist or "?", "title": title or "?",
            "bpm": (bpm_raw or 0) / 100,
            "key": key or "?",
            "energy": float(m.group(1)) if m else None,
            "label": label or "", "genre": genre or "",
        })
    return out


# -- definicion de las vistas ----------------------------------------------
def _rol(t: dict) -> str | None:
    if t["energy"] is None:
        return "0 Sin energia"
    for lo, hi, nombre in ROLES:
        if lo <= t["energy"] < hi:
            return nombre
    return None


def _energia(t: dict) -> str | None:
    if t["energy"] is None:
        return None
    lo = int(t["energy"] // 2) * 2
    return f"E{lo}-{lo + 2}"


def _bpm(t: dict) -> str | None:
    if not t["bpm"]:
        return None
    lo = int(t["bpm"] // 2) * 2
    return f"{lo}-{lo + 2}"


VISTAS = {
    "rol": ("Por rol", _rol),
    "energia": ("Por energia", _energia),
    "genero": ("Por genero", lambda t: _sano(t["genre"]) if t["genre"] else None),
    "key": ("Por key", lambda t: t["key"] if t["key"] != "?" else None),
    "bpm": ("Por BPM", _bpm),
    "sello": ("Por sello", lambda t: _sano(t["label"]) if t["label"] else None),
}


def _prefijo(t: dict) -> str:
    """Prefijo que hace util el orden alfabetico de la carpeta."""
    e = f"E{t['energy']:.1f}" if t["energy"] is not None else "E---"
    return f"{e} {t['bpm']:.0f} {t['key']} - "


# -- enlazado ---------------------------------------------------------------
class Enlazador:
    """Hardlink, con caida a symlink y despues a copia-no. Reporta que uso."""

    def __init__(self, dry: bool) -> None:
        self.dry = dry
        self.metodo = "hardlink"
        self.ok = 0
        self.fallos: list[str] = []

    def enlazar(self, origen: Path, destino: Path) -> bool:
        if self.dry:
            self.ok += 1
            return True
        if destino.exists():
            return True
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(origen, destino)
            self.ok += 1
            return True
        except OSError:
            pass
        try:
            os.symlink(origen, destino)
            self.metodo = "symlink"
            self.ok += 1
            return True
        except OSError as e:
            self.fallos.append(f"{origen.name}: {e}")
            return False


def limpiar(raiz: Path, dry: bool) -> None:
    """Borra el arbol de vistas. Se niega si no encuentra la marca."""
    if not raiz.exists():
        return
    if not (raiz / MARCA).exists():
        sys.exit(
            f"ABORTADO: {raiz} existe pero no tiene el archivo {MARCA}.\n"
            "Este script solo borra arboles que el mismo creo. Si esa carpeta es\n"
            "tuya, elegi otra raiz con la variable de entorno VIEWS_ROOT.")
    if dry:
        print(f"  [dry] borraria el arbol existente en {raiz}")
        return
    for hijo in raiz.iterdir():
        if hijo.name == MARCA:
            continue
        shutil.rmtree(hijo) if hijo.is_dir() else hijo.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--m3u", action="store_true",
                    help="ademas de los enlaces, escribe una playlist .m3u8 por grupo")
    ap.add_argument("--solo", nargs="+", choices=sorted(VISTAS),
                    help="regenerar solo estas vistas")
    ap.add_argument("--raiz", type=Path, default=RAIZ_VISTAS)
    args = ap.parse_args()

    if "onedrive" in str(args.raiz).lower():
        print("AVISO: la raiz esta dentro de OneDrive. OneDrive convierte archivos\n"
              "       en placeholders y trata mal los hardlinks. Conviene otra raiz.\n")

    tracks = cargar_tracks()
    existentes = [t for t in tracks if t["path"].exists()]
    faltantes = len(tracks) - len(existentes)
    print(f"{len(tracks)} tracks en la DB, {len(existentes)} con archivo en disco"
          + (f", {faltantes} con path roto" if faltantes else ""))
    if faltantes:
        print("  (los de path roto se saltean — para arreglarlos: scripts/fix_missing_paths.py)")

    limpiar(args.raiz, args.dry)
    if not args.dry:
        args.raiz.mkdir(parents=True, exist_ok=True)
        (args.raiz / MARCA).write_text(
            "Arbol generado por scripts/build_views.py. Se borra y regenera entero.\n"
            "No guardes nada tuyo aca.\n", encoding="utf-8")

    enl = Enlazador(args.dry)
    seleccion = args.solo or list(VISTAS)
    total_grupos = 0

    for clave in seleccion:
        carpeta, fn = VISTAS[clave]
        grupos: dict[str, list[dict]] = defaultdict(list)
        for t in existentes:
            g = fn(t)
            if g:
                grupos[g].append(t)

        if clave == "sello":
            grupos = {k: v for k, v in grupos.items() if len(v) >= MIN_TRACKS_SELLO}

        print(f"\n  {carpeta:<14} {len(grupos):3d} grupos, "
              f"{sum(len(v) for v in grupos.values())} enlaces")
        total_grupos += len(grupos)
        for grupo, ts in sorted(grupos.items()):
            destino_dir = args.raiz / carpeta / _sano(grupo)
            for t in ts:
                enl.enlazar(t["path"], destino_dir / (_prefijo(t) + t["path"].name))
            if args.m3u and not args.dry:
                destino_dir.mkdir(parents=True, exist_ok=True)
                (destino_dir / f"{_sano(grupo)}.m3u8").write_text(
                    "#EXTM3U\n" + "\n".join(str(t["path"]) for t in ts),
                    encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"{'simulado' if args.dry else 'creado'}: {enl.ok} enlaces en "
          f"{total_grupos} carpetas  ({enl.metodo})")
    print(f"raiz: {args.raiz}")
    if enl.fallos:
        print(f"\n{len(enl.fallos)} fallos — ni hardlink ni symlink funcionaron.")
        for f in enl.fallos[:5]:
            print(f"  {f}")
        print("Correr con --m3u: las playlists .m3u8 funcionan siempre y "
              "Rekordbox las lee igual.")


if __name__ == "__main__":
    main()
