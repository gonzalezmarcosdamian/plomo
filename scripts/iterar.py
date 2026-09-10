"""El bucle: renderiza el tema propio, lo mide igual que a la referencia, y dice
que esta lejos y en que direccion.

Por que existe. Hasta hoy el ciclo era: yo cambio algo, el DJ escucha, dice una
frase, yo busco el numero que la explica. Cada vuelta costaba una escucha humana
y la mitad de las veces la frase apuntaba a otra cosa. Con `render.py` el audio
propio existe, y con `traducir.py` se mide con EL MISMO instrumento que la
referencia. Esto junta las dos y devuelve una tabla: cada dimension, el valor de
la referencia, el propio, y cuanto falta.

Lo que NO hace, y hay que decirlo: no decide que es bueno. Acercarse a la
referencia en todas las dimensiones a la vez no es el objetivo — es una copia.
El objetivo lo pone el DJ diciendo que referencia y que dimensiones importan;
esto solo evita que una iteracion crea que mejoro cuando se alejo.

Las mediciones de la referencia se cachean en `data/traducciones/`: separar con
Demucs es lo caro, y la referencia no cambia entre vueltas.

Uso:
    python scripts/iterar.py v2 --ref "<mp3 de referencia>" --desde 161
    python scripts/iterar.py v2 --ref "<mp3>" --desde 161 --ref-desde 283
    python scripts/iterar.py v2 --solo-medir postproduction/render/v2_161-176.wav --ref "<mp3>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from traducir import traducir  # noqa: E402

CACHE = RAIZ / "data" / "traducciones"

# Que se compara, de donde sale cada numero, y cuanto desvio es "bien".
#
# La tolerancia no es estetica: es el ruido de la medicion. Dos fragmentos
# distintos del MISMO tema difieren mas o menos esto, asi que una diferencia
# menor no distingue nada.
DIMENSIONES = [
    # (nombre,             camino en el dict,                       tolerancia, unidad)
    ("bombo x compas",     ("piezas", "bombo", "x_compas"),          0.3,  ""),
    ("clap x compas",      ("piezas", "clap", "x_compas"),           1.0,  ""),
    ("percusion x compas", ("piezas", "percusion", "x_compas"),      1.5,  ""),
    ("hat x compas",       ("piezas", "hat", "x_compas"),            1.5,  ""),
    ("bajo ataques",       ("piezas", "bajo", "x_compas"),           0.8,  ""),
    ("bajo suena",         ("piezas", "bajo", "cobertura"),          0.10, "%"),
    ("melodia ataques",    ("piezas", "melodia", "x_compas"),        0.8,  ""),
    ("melodia suena",      ("piezas", "melodia", "cobertura"),       0.10, "%"),
    ("aire suena",         ("piezas", "aire", "cobertura"),          0.10, "%"),
    ("sidechain bajo",     ("efectos", "bass", "sidechain_db"),      2.0,  "dB"),
    ("sidechain melodico", ("efectos", "other", "sidechain_db"),     2.0,  "dB"),
    ("cola bajo",          ("efectos", "bass", "cola_s"),            0.05, "s"),
    ("cola melodico",      ("efectos", "other", "cola_s"),           0.08, "s"),
    ("ancho bajo medios",  ("efectos", "bass", "ancho", "medios"),   0.10, ""),
    ("ancho melod medios", ("efectos", "other", "ancho", "medios"),  0.12, ""),
    ("ancho bat agudos",   ("efectos", "drums", "ancho", "agudos"),  0.15, ""),
    ("cresta bajo",        ("efectos", "bass", "cresta_db"),         2.0,  "dB"),
    ("cresta bateria",     ("efectos", "drums", "cresta_db"),        2.0,  "dB"),
]


def _saca(d: dict, camino: tuple) -> float | None:
    for k in camino:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return float(d) if isinstance(d, (int, float)) else None


def medir_cacheado(archivo: Path, desde: float | None) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    clave = f"{archivo.stem[:60]}__{int(desde) if desde is not None else 'auto'}"
    clave = "".join(c if c.isalnum() or c in "-_" else "_" for c in clave)
    destino = CACHE / f"{clave}.json"
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    d = traducir(archivo, desde)
    destino.write_text(json.dumps(d, indent=1, ensure_ascii=False, default=float),
                       encoding="utf-8")
    return d


def renderizar(version: str, desde: int, compases: int) -> Path:
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "render.py"), version,
                        "--desde", str(desde), "--compases", str(compases)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr.strip() or "  el render fallo")
    # el render puede haber arrancado un compas mas tarde: se toma el mas nuevo
    cands = sorted((RAIZ / "postproduction" / "render").glob(f"{version}_*.wav"),
                   key=lambda p: p.stat().st_mtime)
    return cands[-1]


def comparar(ref: dict, propio: dict) -> list[tuple[str, float | None, float | None, str]]:
    filas = []
    for nombre, camino, tol, unidad in DIMENSIONES:
        a, b = _saca(ref, camino), _saca(propio, camino)
        if a is None or b is None:
            filas.append((nombre, a, b, "?"))
            continue
        d = b - a
        if abs(d) <= tol:
            veredicto = "ok"
        elif d > 0:
            veredicto = "propio MAS alto"
        else:
            veredicto = "propio mas bajo"
        filas.append((nombre, a, b, veredicto))
    return filas


def _fmt(v: float | None, unidad: str) -> str:
    if v is None:
        return "   —"
    if unidad == "%":
        return f"{v:6.0%}"
    return f"{v:6.2f}{unidad}"


def mostrar(filas, ref_nombre: str, propio_nombre: str) -> None:
    print(f"\n  referencia: {ref_nombre[:60]}")
    print(f"  propio:     {propio_nombre[:60]}\n")
    print(f"  {'dimension':<20} {'referencia':>11} {'propio':>10}   veredicto")
    lejos = []
    for nombre, a, b, v in filas:
        marca = "  " if v == "ok" else "->"
        print(f"  {marca}{nombre:<18} {_fmt(a, ''):>11} {_fmt(b, ''):>10}   {v}")
        if v not in ("ok", "?"):
            lejos.append(nombre)
    print()
    if not lejos:
        print("  todo dentro de tolerancia. Eso no quiere decir que suene igual:")
        print("  quiere decir que ninguna de estas dieciocho cosas lo distingue.")
    else:
        print(f"  {len(lejos)} de {len(filas)} fuera de tolerancia: {', '.join(lejos)}")
        print("  Una por vez. Cambiar dos cosas y medir no dice cual de las dos hizo que.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--ref", type=Path, required=True, help="mp3 de referencia")
    ap.add_argument("--ref-desde", type=float, help="segundo de la referencia (auto: pico)")
    ap.add_argument("--desde", type=int, default=161, help="compas del tema propio")
    ap.add_argument("--compases", type=int, default=16)
    ap.add_argument("--solo-medir", type=Path, help="no renderiza: mide este WAV")
    args = ap.parse_args()

    if not args.ref.exists():
        sys.exit(f"no existe {args.ref}")
    ref = medir_cacheado(args.ref, args.ref_desde)
    propio_wav = args.solo_medir or renderizar(args.version, args.desde, args.compases)
    propio = traducir(propio_wav, 0.0)
    mostrar(comparar(ref, propio), ref["archivo"], propio_wav.name)


if __name__ == "__main__":
    main()
