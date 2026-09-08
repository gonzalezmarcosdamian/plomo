"""Separa un fragmento de audio en bombo, bajo y armonia con Demucs.

Por que existe: transcribir sobre la mezcla completa no funciona y esta medido.
La banda de 30-110 Hz de un tema de progressive contiene el bajo tanto como el
bombo, asi que el detector de golpes dispara con cada nota del bajo — en Afrika
daba 43 golpes irregulares donde hay 32 parejos. Lo mismo con la altura: pyin
sobre la mezcla sigue los armonicos del pad, no la fundamental del bajo, y
devolvia 23% de notas fuera de tonalidad en un tema que no se sale nunca.

Separando primero, cada transcriptor ve una senial limpia y las dos tecnicas
pasan a funcionar como corresponde.

Demucs vive en `.venv-demucs`, un entorno aparte. No es capricho: demucs arrastra
numpy<2 y el entorno principal tiene numpy 2.4.4, asi que instalarlo al lado
romperia librosa y todos los scripts de analisis. Se lo llama por subproceso.

Uso:
    python scripts/separar.py "<archivo.mp3>" --desde 180 --compases 8
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import librosa
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
PYTHON_DEMUCS = RAIZ / ".venv-demucs" / "Scripts" / "python.exe"
CACHE = RAIZ / "postproduction" / "stems"
MODELO = "htdemucs"

# Se separa un poco mas de lo que se va a transcribir. Demucs decide con el
# contexto alrededor, y un fragmento cortado justo en el limite se degrada en
# los bordes — que es exactamente donde estan el primer y el ultimo compas.
MARGEN_S = 10.0

FALTA = f"""
  Demucs no esta instalado en {PYTHON_DEMUCS}

    uv venv .venv-demucs --python 3.11
    uv pip install --python .venv-demucs torch torchaudio --index-url https://download.pytorch.org/whl/cu124
    uv pip install --python .venv-demucs demucs
"""


def separar(archivo: Path, desde: float, duracion: float,
            forzar: bool = False) -> dict[str, Path]:
    """Devuelve {'drums': ..., 'bass': ..., 'other': ...} para el fragmento.

    El resultado queda cacheado por (archivo, desde, duracion): separar es lo
    caro de todo el proceso y la transcripcion se va a correr muchas veces
    encima del mismo fragmento mientras se ajustan los detectores.
    """
    if not PYTHON_DEMUCS.exists():
        raise SystemExit(FALTA)

    nombre = f"{archivo.stem[:40].strip()}_{int(desde)}_{int(duracion)}"
    nombre = "".join(c if c.isalnum() or c in "-_" else "_" for c in nombre)
    salida = CACHE / MODELO / nombre
    stems = {n: salida / f"{n}.wav" for n in ("drums", "bass", "other")}
    if not forzar and all(p.exists() for p in stems.values()):
        print(f"  stems en cache: {salida}")
        return stems

    CACHE.mkdir(parents=True, exist_ok=True)
    recorte = CACHE / f"{nombre}.wav"
    inicio = max(0.0, desde - MARGEN_S)
    y, sr = librosa.load(archivo, sr=44100, mono=False,
                         offset=inicio, duration=duracion + 2 * MARGEN_S)
    sf.write(recorte, y.T if y.ndim > 1 else y, sr)
    print(f"  recorte: {recorte.name} ({y.shape[-1] / sr:.0f}s)")

    print(f"  separando con {MODELO}... (la primera vez baja el modelo)")
    r = subprocess.run(
        [str(PYTHON_DEMUCS), "-m", "demucs", "-n", MODELO,
         "--segment", "7", "-o", str(CACHE), str(recorte)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        raise SystemExit("  demucs fallo")

    faltantes = [n for n, p in stems.items() if not p.exists()]
    if faltantes:
        raise SystemExit(f"  demucs no dejo los stems {faltantes} en {salida}")
    print(f"  stems: {salida}")
    return stems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--desde", type=float, default=180.0)
    ap.add_argument("--compases", type=int, default=8)
    ap.add_argument("--bpm", type=float, default=121.0)
    ap.add_argument("--forzar", action="store_true", help="ignora el cache")
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")
    dur = args.compases * 4 * 60.0 / args.bpm + 4.0
    for nombre, ruta in separar(args.archivo, args.desde, dur, args.forzar).items():
        print(f"    {nombre:6} {ruta}")


if __name__ == "__main__":
    main()
