"""Copia clasificada de la biblioteca para pasarle a otra persona.

No es una vista ni un export al pen: es una COPIA REAL de archivos, pensada
para que alguien la arrastre a su pen y la use en otra PC. Por eso no usa
hardlinks (no sobreviven a otro disco) y por eso el nombre de cada archivo
lleva el dato adelante: energia, BPM y key. Del otro lado no hay Rekordbox
que los muestre.

Que entra: lo probado. El puntaje sale de senales reales de uso — cuantas
veces se toco, en cuantos sets entro, si esta en los pools que definen el
sonido propio. Un track que nunca se toco y nunca entro a un set no es
"bueno para mi": es inventario.

Como se ordena: por momento del set, con la misma escala de energia que usa
scripts/build_views.py. Las cuotas por carpeta existen para que ninguna
quede vacia — sin ellas la Meseta se come la mitad de la copia.

Uso:
    python scripts/exportar_copia.py --dry
    python scripts/exportar_copia.py --destino "C:\\Users\\gonza\\Music\\ParaAmiga"
    python scripts/exportar_copia.py --n 400 --acceso-directo
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

DESTINO_DEFAULT = Path(r"C:\Users\gonza\Music\ParaAmiga")
MARCA = ".plomo-copia"  # sin este archivo el script se niega a vaciar el destino
ENERGY_RE = re.compile(r"E:(\d+(?:\.\d+)?)")
SET_RE = re.compile(r"^\d\d[v0-9]*\.")  # '09.' y '09v2.' son el mismo set

# Momento del set. Los cortes son los de build_views.py: la misma escala en
# todos lados, o el vocabulario deja de significar algo.
MOMENTOS = [
    (0.0, 3.5, "01 Apertura", 40),
    (3.5, 5.5, "02 Construccion", 80),
    (5.5, 6.5, "03 Meseta", 100),
    (6.5, 7.5, "04 Peak", 75),
    (7.5, 99.0, "05 Detonantes", 25),
]

# Peso de cada senal de "esto me sirve a mi".
PESO_TOCADO = 3.0        # por reproduccion registrada en Rekordbox
PESO_SET = 1.0           # por set en el que entro
PESO_RATING = 0.5        # por estrella
POOLS_BONUS = {          # pools que son declaracion de criterio, no cajones
    "[POOL] Mi Sonido": 2.5,
    "Core (Tracks Pilares)": 3.0,
    "[POOL] Detonantes \u2014 E>=7.5 \u2014 uno o dos por set, al 70-85%": 1.0,
}

MAX_POR_ARTISTA = 5      # que no sea el showcase de tres manos


def _sano(nombre: str, largo: int = 90) -> str:
    n = re.sub(r'[<>:"/\\|?*]', "-", nombre)
    n = re.sub(r"\s+", " ", n).strip(" .")
    return n[:largo] or "sin dato"


def _artista_principal(artista: str) -> str:
    """Primer nombre de la lista. 'A, B, C' y 'A, D' son la misma mano."""
    return artista.split(",")[0].strip().lower() or "?"


def cargar() -> list[dict]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    filas = con.execute(
        """
        SELECT c.ID, c.FolderPath, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt,
               l.Name, g.Name, c.Rating, c.DJPlayCount
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        LEFT JOIN djmdKey    k ON k.ID = c.KeyID
        LEFT JOIN djmdLabel  l ON l.ID = c.LabelID
        LEFT JOIN djmdGenre  g ON g.ID = c.GenreID
        WHERE c.rb_local_deleted = 0 AND c.FolderPath IS NOT NULL
          AND c.FolderPath NOT LIKE '%/PioneerDJ/%'
        """
    ).fetchall()

    playlists = con.execute(
        "SELECT ID, Name FROM djmdPlaylist WHERE rb_local_deleted = 0"
    ).fetchall()
    ids_sets = {i for i, n in playlists if SET_RE.match(n or "")}
    ids_pool = {i: POOLS_BONUS[n] for i, n in playlists if n in POOLS_BONUS}

    n_sets: Counter = Counter()
    bonus_pool: dict = defaultdict(float)
    for pid, cid in con.execute(
        "SELECT PlaylistID, ContentID FROM djmdSongPlaylist WHERE rb_local_deleted = 0"
    ):
        if pid in ids_sets:
            n_sets[cid] += 1
        if pid in ids_pool:
            bonus_pool[cid] = max(bonus_pool[cid], ids_pool[pid])
    con.close()

    tracks = []
    for cid, folder, artista, titulo, bpm, key, commnt, sello, genero, rating, plays in filas:
        m = ENERGY_RE.search(commnt or "")
        if not m:
            continue  # sin energia no hay momento al que asignarlo
        origen = Path(folder)
        if not origen.exists():
            continue
        tocado = plays or 0
        sets = n_sets.get(cid, 0)
        puntaje = (PESO_TOCADO * tocado + PESO_SET * sets
                   + PESO_RATING * (rating or 0) + bonus_pool.get(cid, 0.0))
        tracks.append({
            "origen": origen,
            "artista": artista or "Desconocido",
            "titulo": titulo or origen.stem,
            "bpm": (bpm or 0) / 100,
            "key": key or "?",
            "energia": float(m.group(1)),
            "sello": sello or "",
            "genero": genero or "",
            "tocado": tocado,
            "sets": sets,
            "puntaje": puntaje,
        })
    return tracks


def momento(energia: float) -> str:
    for lo, hi, nombre, _ in MOMENTOS:
        if lo <= energia < hi:
            return nombre
    return MOMENTOS[-1][2]


def seleccionar(tracks: list[dict], total: int) -> dict:
    """Los mejores de cada momento, con tope por artista y cupo por carpeta."""
    escala = total / sum(c for *_, c in MOMENTOS)
    por_momento: dict = defaultdict(list)
    for t in tracks:
        if t["puntaje"] > 0:
            por_momento[momento(t["energia"])].append(t)

    elegidos: dict = {}
    usados: Counter = Counter()
    for _, _, nombre, cupo in MOMENTOS:
        objetivo = max(1, round(cupo * escala))
        candidatos = sorted(por_momento.get(nombre, []),
                            key=lambda t: (-t["puntaje"], -t["tocado"], t["artista"]))
        seleccion = []
        for t in candidatos:
            if len(seleccion) >= objetivo:
                break
            mano = _artista_principal(t["artista"])
            if usados[mano] >= MAX_POR_ARTISTA:
                continue
            usados[mano] += 1
            seleccion.append(t)
        # Si el tope por artista dejo la carpeta corta, se afloja: mejor un
        # artista repetido que una carpeta con la mitad de lo pedido.
        if len(seleccion) < objetivo:
            ya = {id(t) for t in seleccion}
            for t in candidatos:
                if len(seleccion) >= objetivo:
                    break
                if id(t) not in ya:
                    seleccion.append(t)
        elegidos[nombre] = seleccion
    return elegidos


def nombre_archivo(t: dict) -> str:
    prefijo = f"E{t['energia']:.1f} {t['bpm']:.0f} {t['key']}"
    return _sano(f"{prefijo} - {t['artista']} - {t['titulo']}") + t["origen"].suffix.lower()


def limpiar(destino: Path, dry: bool) -> None:
    if not destino.exists():
        return
    if not (destino / MARCA).exists():
        sys.exit(
            f"ABORTADO: {destino} existe y no tiene {MARCA}.\n"
            "Este script solo vacia carpetas que el mismo creo. Elegi otro --destino.")
    if dry:
        print(f"  [dry] vaciaria {destino}")
        return
    for hijo in destino.iterdir():
        if hijo.name != MARCA:
            shutil.rmtree(hijo) if hijo.is_dir() else hijo.unlink()


def acceso_directo(destino: Path) -> None:
    """Acceso directo en el escritorio, sin meter varios GB adentro de OneDrive."""
    casa = Path(os.path.expanduser("~"))
    escritorio = casa / "OneDrive" / "Escritorio"
    if not escritorio.exists():
        escritorio = casa / "Desktop"
    lnk = escritorio / f"{destino.name}.lnk"
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
          f"'{lnk}');$s.TargetPath='{destino}';$s.Save()")
    os.system(f'powershell -NoProfile -Command "{ps}"')
    print(f"acceso directo: {lnk}")


LEEME = """MUSICA \u2014 copia clasificada
==========================

Las carpetas van en orden: de lo mas tranquilo a lo que rompe.

  01 Apertura      arrancar, fondo, nadie bailando todavia
  02 Construccion  ya se siente que va a algun lado
  03 Meseta        el cuerpo del set, donde se pasa mas tiempo
  04 Peak          lo alto
  05 Detonantes    los que rompen \u2014 uno o dos por noche, no mas

Cada archivo empieza con tres datos:

  E6.2 122 8A - Artista - Titulo.mp3
  ^^^^ ^^^ ^^
   |    |   +-- key en Camelot: los vecinos mezclan bien (8A con 7A, 9A u 8B).
   |    |       Saltar de 8A a 3A suena a choque.
   |    +------ BPM
   +----------- energia de 1 a 10, la escala con la que ordeno mis sets

Ordenando por nombre dentro de una carpeta quedan de menor a mayor energia.

Los .m3u8 son playlists: se abren con VLC, foobar2000, Rekordbox o Serato y
respetan el orden. Funcionan mientras el .m3u8 quede al lado de sus archivos.

INDICE.csv tiene todo en una tabla (Excel): artista, titulo, BPM, key,
energia, genero y sello.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", type=Path, default=DESTINO_DEFAULT)
    ap.add_argument("--n", type=int, default=320, help="cuantos tracks copiar")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--acceso-directo", action="store_true",
                    help="deja un .lnk en el escritorio apuntando al destino")
    args = ap.parse_args()

    if "onedrive" in str(args.destino).lower():
        print("AVISO: el destino esta dentro de OneDrive. Va a sincronizar varios GB\n"
              "       a la nube. Conviene una carpeta local y un acceso directo.\n")

    tracks = cargar()
    print(f"{len(tracks)} tracks con energia y archivo en disco")
    elegidos = seleccionar(tracks, args.n)

    limpiar(args.destino, args.dry)
    if not args.dry:
        args.destino.mkdir(parents=True, exist_ok=True)
        (args.destino / MARCA).write_text(
            "Carpeta generada por scripts/exportar_copia.py. Se vacia y regenera entera.\n",
            encoding="utf-8")

    filas_indice = []
    copiados = bytes_totales = 0
    for _, _, carpeta, _ in MOMENTOS:
        ts = elegidos.get(carpeta, [])
        ts.sort(key=lambda t: (t["energia"], t["bpm"]))
        rango = f"  E{ts[0]['energia']:.1f}-{ts[-1]['energia']:.1f}" if ts else ""
        print(f"  {carpeta:<18} {len(ts):3d} tracks{rango}")

        dir_destino = args.destino / carpeta
        nombres: list[str] = []
        for t in ts:
            base = nombre_archivo(t)
            nombre, n = base, 2
            while nombre in nombres:  # dos mezclas del mismo track existen
                nombre = f"{base[:-len(t['origen'].suffix)]} ({n}){t['origen'].suffix.lower()}"
                n += 1
            nombres.append(nombre)
            if not args.dry:
                dir_destino.mkdir(parents=True, exist_ok=True)
                shutil.copy2(t["origen"], dir_destino / nombre)
            copiados += 1
            bytes_totales += t["origen"].stat().st_size
            filas_indice.append({
                "momento": carpeta, "archivo": nombre, "artista": t["artista"],
                "titulo": t["titulo"], "bpm": f"{t['bpm']:.1f}", "key": t["key"],
                "energia": f"{t['energia']:.1f}", "genero": t["genero"],
                "sello": t["sello"], "veces_tocado": t["tocado"],
                "sets_en_los_que_entro": t["sets"],
            })
        if ts and not args.dry:
            (dir_destino / f"{carpeta}.m3u8").write_text(
                "#EXTM3U\n" + "\n".join(nombres) + "\n", encoding="utf-8")

    if not args.dry and filas_indice:
        (args.destino / "LEEME.txt").write_text(LEEME, encoding="utf-8")
        with (args.destino / "INDICE.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas_indice[0]))
            w.writeheader()
            w.writerows(filas_indice)
        (args.destino / "TODO.m3u8").write_text(
            "#EXTM3U\n" + "\n".join(f"{r['momento']}/{r['archivo']}" for r in filas_indice) + "\n",
            encoding="utf-8")
        if args.acceso_directo:
            acceso_directo(args.destino)

    print(f"\n{'=' * 60}")
    print(f"{'simulado' if args.dry else 'copiado'}: {copiados} tracks, "
          f"{bytes_totales / 1e9:.2f} GB")
    print(f"destino: {args.destino}")


if __name__ == "__main__":
    main()
