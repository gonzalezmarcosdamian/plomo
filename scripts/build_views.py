"""Arbol de carpetas navegable, construido con hardlinks sobre el deposito.

La doctrina: el disco guarda, no organiza. Los archivos viven en su carpeta por
fecha de ingreso y no se mueven nunca — asi ningun path de Rekordbox se rompe.
La organizacion vive aca: un arbol descartable hecho con hardlinks que no ocupan
espacio ni duplican nada. Ocho vistas — rol de set, energia, genero, key, BPM,
sello, mas dos que no salen de ningun tag:

  Lo que tocan los de referencia — cruza la coleccion contra los 40 setlists de
      data/setlists/ y agrupa por DJ. Contesta "de lo que tengo, que toca
      Cattaneo" sin depender de la memoria.
  Sin usar en ningun set — los que nunca entraron a un set, agrupados por rol,
      que es lo que hace falta para decidir donde meterlos.

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
import json
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
from plomo.matching import clave  # noqa: E402

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


# Los generos vienen del tag de Beatport y son 47 cadenas distintas para unas
# nueve cosas reales: "Melodic House", "Melodic House & Techno", "Melodic House /
# Techno" y "Melodic House & Techno |" son lo mismo, y hay un "Deep Hose" con el
# typo incluido. Navegar 47 carpetas no es navegar. Se mapea a familias; lo que
# no matchea cae en "9 Otros" y aparece en el reporte para poder sumarlo.
FAMILIAS = [
    ("1 Progressive House", ("progressive house", "progressive")),
    ("2 Melodic House & Techno", ("melodic house", "melodic techno", "melodic")),
    ("3 Organic & Downtempo", ("organic", "downtempo", "ambient", "electronica",
                               "chill", "balearic")),
    ("4 Afro House", ("afro",)),
    ("5 Deep & House", ("deep house", "deep hose", "house", "tech house",
                        "future house", "bass house", "electro house")),
    ("6 Techno", ("techno",)),
    ("7 Indie Dance & Nu Disco", ("indie dance", "nu disco", "disco")),
    ("8 Trance & Breaks", ("trance", "breaks", "breakbeat", "uk bass",
                           "drum & bass", "dubstep")),
]


def _familia(genero: str) -> str:
    g = (genero or "").strip().lower()
    if not g:
        return "9 Otros"
    for nombre, claves in FAMILIAS:
        if any(k in g for k in claves):
            return nombre
    return "9 Otros"


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


def _cargar_referencia() -> dict[str, set[str]]:
    """{clave_de_track: {DJs que lo tocaron}} desde data/setlists/.

    Esta vista no existia hasta que el corpus de referencia tuvo 40 setlists.
    Contesta la pregunta que antes habia que contestar de memoria: "de lo que
    tengo, que toca Cattaneo". Es la unica vista que no sale de un tag.
    """
    carpeta = Path(__file__).resolve().parent.parent / "data" / "setlists"
    if not carpeta.exists():
        return {}
    out: dict[str, set[str]] = {}
    for f in carpeta.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        dj = d.get("dj", "?")
        for t in d.get("tracks", []):
            if t.get("es_id"):
                continue
            k = clave(t.get("artist", ""), t.get("title", ""))
            if k:
                out.setdefault(k, set()).add(dj)
    return out


def _cargar_sin_usar() -> set[str]:
    """Claves de los tracks que no entraron en ningun set ni se tocaron nunca."""
    f = Path(__file__).resolve().parent.parent / "data" / "pool.json"
    if not f.exists():
        return set()
    return {clave(t["artist"], t["title"])
            for t in json.loads(f.read_text(encoding="utf-8")) if not t.get("usado")}


REFERENCIA: dict[str, set[str]] = {}
SIN_USAR: set[str] = set()


def _referencia(t: dict) -> str | None:
    djs = REFERENCIA.get(clave(t["artist"], t["title"]))
    if not djs:
        return None
    # Un track que tocaron varios va en la carpeta del que mas peso tiene para
    # este proyecto; duplicarlo en cinco carpetas haria la vista ilegible.
    return _sano(sorted(djs)[0])


def _sin_usar(t: dict) -> str | None:
    if clave(t["artist"], t["title"]) not in SIN_USAR:
        return None
    return _rol(t) or "0 Sin energia"


VISTAS = {
    "rol": ("Por rol", _rol),
    "energia": ("Por energia", _energia),
    "genero": ("Por genero", lambda t: _familia(t["genre"])),
    "key": ("Por key", lambda t: t["key"] if t["key"] != "?" else None),
    "bpm": ("Por BPM", _bpm),
    "sello": ("Por sello", lambda t: _sano(t["label"]) if t["label"] else None),
    "referencia": ("Lo que tocan los de referencia", _referencia),
    "sin-usar": ("Sin usar en ningun set", _sin_usar),
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


def _preparar_indices() -> None:
    global REFERENCIA, SIN_USAR
    REFERENCIA = _cargar_referencia()
    SIN_USAR = _cargar_sin_usar()


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

    _preparar_indices()
    if REFERENCIA:
        print(f"corpus de referencia: {len(REFERENCIA)} tracks distintos en "
              f"data/setlists/  |  sin usar en ningun set: {len(SIN_USAR)}")

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
