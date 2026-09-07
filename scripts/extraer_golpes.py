"""Extrae kicks, hats y claps reales de la biblioteca propia.

El kick de un track que Gonzalo toca cien veces es, literalmente, el sonido que
elige. Este script lo aisla y lo deja como .wav para que `render_sketch.py` lo
use en vez de sintetizar todo. Es el unico camino que rompe el techo de "la
maqueta suena a sintetizador": el arreglo ya esta bien, lo que falta es timbre,
y el timbre no se deduce de una plantilla — se agarra de una grabacion.

MATERIAL CON DERECHOS. Lo que sale de aca son fragmentos de grabaciones
comerciales ajenas. Un golpe de 300 ms es referencia de timbre para produccion
propia y para escuchar un boceto en esta maquina. NO es un sample para publicar,
distribuir ni meter en un track que sale a un sello. Si el uso cruza esa linea,
el golpe se reemplaza por uno propio o por uno con licencia. `data/samples/`
esta en .gitignore por esto mismo.

Las fuentes no se eligen al azar: por defecto salen de
`data/plantillas/lista_lo_tocado_meta.json`, ordenadas por veces reproducido.

Uso:
    python scripts/extraer_golpes.py --top 6
    python scripts/extraer_golpes.py --artista cendryma --por-clase 4
    python scripts/extraer_golpes.py "ruta/al/track.mp3" --salida data/samples/prueba
    python scripts/extraer_golpes.py --top 6 --clases kick hat
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import librosa  # noqa: E402

from plomo.golpes import (  # noqa: E402
    BLEED_ACEPTABLE_DB, CLASES, SR, Golpe, extraer_de_track,
)

LISTA_TOCADOS = RAIZ / "data" / "plantillas" / "lista_lo_tocado_meta.json"
SALIDA_BASE = RAIZ / "data" / "samples"


def _slug(texto: str) -> str:
    limpio = "".join(ch if ch.isalnum() else "_" for ch in texto.lower())
    return "_".join(p for p in limpio.split("_") if p)[:60]


def _fuentes(args) -> list[dict]:
    """Resuelve de que tracks se extrae, y deja constancia del criterio."""
    if args.track:
        return [{"artist": args.track.stem, "title": "", "path": str(args.track),
                 "veces": 0}]
    if not LISTA_TOCADOS.exists():
        sys.exit(f"no existe {LISTA_TOCADOS}; pasa un track suelto o corre "
                 "derive_template.py --tocados primero")
    meta = json.loads(LISTA_TOCADOS.read_text(encoding="utf-8"))
    if args.artista:
        aguja = args.artista.lower()
        meta = [m for m in meta if aguja in m["artist"].lower()]
        if not meta:
            sys.exit(f"ningun track tocado de '{args.artista}'")
    return sorted(meta, key=lambda m: -m["veces"])[:args.top]


def _reportar(golpes: list[Golpe]) -> None:
    """Imprime la separacion medida. Se reporta siempre, tambien cuando sale mal."""
    if not golpes:
        print("  no se extrajo nada")
        return
    print(f"\n  {'clase':<13} {'archivo':<18} {'bleed':>7} {'crudo':>7} "
          f"{'sub%':>6} {'centro':>7} {'ms':>5} {'seg':>7}")
    for g in golpes:
        marca = " " if g.limpio else "!"
        print(f"{marca} {g.clase:<13} {g.archivo:<18} {g.bleed_db:>6.1f}dB "
              f"{g.bleed_db_crudo:>6.1f}dB {g.sub_pct:>5.1f} {g.centroide_hz:>5.0f}Hz "
              f"{g.dur_ms:>5.0f} {g.segundo:>6.1f}s")
    sucios = [g for g in golpes if not g.limpio]
    print(f"\n  bleed = energia >300 Hz despues de 80 ms, relativa al pico del golpe."
          f"\n  limpio = {BLEED_ACEPTABLE_DB:.0f} dB o menos. "
          f"{len(golpes) - len(sucios)}/{len(golpes)} pasan.")
    if sucios:
        print(f"  ! {len(sucios)} traen demasiado encima (cola de bajo, hat del "
              "contratiempo, reverb).\n    Sirven para escuchar la forma, no como "
              "sonido definitivo.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("track", nargs="?", type=Path, help="un track suelto")
    ap.add_argument("--top", type=int, default=6,
                    help="cuantos de los mas tocados usar (default 6)")
    ap.add_argument("--artista", help="filtra los tocados por artista")
    ap.add_argument("--clases", nargs="+", default=list(CLASES), choices=list(CLASES))
    ap.add_argument("--por-clase", type=int, default=3,
                    help="cuantas variantes guardar de cada clase")
    ap.add_argument("--salida", type=Path, help="carpeta destino (default por track)")
    ap.add_argument("--sin-limpieza", action="store_true",
                    help="no apaga la cola de la banda alta del kick")
    args = ap.parse_args()

    fuentes = _fuentes(args)
    print(f"fuentes: {len(fuentes)} track(s)"
          + ("" if args.track else "  (los mas reproducidos de la biblioteca)"))

    todos: list[Golpe] = []
    for m in fuentes:
        ruta = Path(m["path"])
        if not ruta.exists():
            print(f"  falta {ruta.name}")
            continue
        etiqueta = f"{m['artist']} - {m['title']}".strip(" -") or ruta.stem
        destino = args.salida or SALIDA_BASE / _slug(etiqueta)
        print(f"\n{etiqueta}  ({m['veces']} reproducciones)" if m["veces"]
              else f"\n{etiqueta}")
        audio, _ = librosa.load(str(ruta), sr=SR, mono=True)
        golpes = extraer_de_track(audio, ruta.name, destino, args.clases,
                                  args.por_clase, not args.sin_limpieza)
        _reportar(golpes)
        _escribir_indice(destino, etiqueta, m, golpes)
        print(f"  -> {destino}")
        todos.extend(golpes)

    print(f"\n{len(todos)} golpes en total. Material de referencia, no para publicar.")


def _escribir_indice(destino: Path, etiqueta: str, meta: dict,
                     golpes: list[Golpe]) -> None:
    """De que track salio cada sample. Sin esto el material no es rastreable."""
    indice = {
        "origen": etiqueta,
        "archivo_fuente": meta["path"],
        "reproducciones": meta.get("veces", 0),
        "bpm": meta.get("bpm"),
        "key": meta.get("key"),
        "licencia": "material con derechos de terceros — referencia de timbre "
                    "para produccion propia, NO para publicar ni distribuir",
        "golpes": [g.como_dict() for g in golpes],
    }
    (destino / "PROCEDENCIA.json").write_text(
        json.dumps(indice, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
