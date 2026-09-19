"""El juez: un veredicto contra las doce dimensiones que convergen.

Por que reemplaza a la tabla de veinte de `iterar.py`. Un agente midio la
dispersion de cada dimension entre referencias contra su tolerancia, y ademas
comparo el MISMO tema contra si mismo (Interlocutor a 283 s contra 310 s).
Resultado: seis de las veinte fallan cuando un tema se compara consigo mismo, o
tienen un rango entre referencias de 4 a 8 veces su tolerancia. Esas seis
describen al TEMA, no al genero, y perseguirlas es copiar a la referencia que
tocó esa semana.

    bajo ataques          rango entre refs 8.4x la tolerancia
    nivel melod vs bat    7.6x   (Tunnel -23.6 dB, Interlocutor -8.3)
    melodia ataques       5.6x
    sidechain bajo        5.3x   y falla contra si mismo
    bajo suena            4.0x   y falla contra si mismo
    melodia suena         falla contra si mismo

Quedan nueve invariantes de genero (rango < 1.5x tolerancia) mas tres
dimensiones nuevas que ninguna de las veinte contestaba:

    cresta espectral de bateria   span de 1.4 dB entre cuatro referencias:
                                  el invariante mas apretado del proyecto
    ocupacion del bus melodico    si el sonido tiene cuerpo o son tres senos
    variacion por compas          si algo CAMBIA (Tunnel 0.86, Panorama
                                  1.45, Closing Doors 2.46; el boceto 0.64)

Uso:
    python scripts/juzgar.py postproduction/render/v3_159-174.wav
    python scripts/juzgar.py <render.wav> --midi postproduction/bocetos/v3/drop
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import _banda  # noqa: E402
from timbre import medir as medir_timbre  # noqa: E402

SR = 22050
BPM = 123.0

# (nombre, minimo, maximo, unidad). Los rangos salen de medir Alex O'Rion
# "Tunnel", Jeremy Olander "Panorama", Khen "Closing Doors" e Interlocutor.
CONVERGENCIA = [
    ("bombo x compas",          3.7,  4.4,  ""),
    ("percusion x compas",      8.2,  9.4,  ""),
    ("hat x compas",            8.4, 10.3,  ""),
    ("aire suena",             0.94, 1.00,  "%"),
    ("cola bajo",              0.05, 0.06,  "s"),
    ("nivel bajo vs bat",      -6.5, -4.0, "dB"),
    ("cresta bateria",          9.1, 11.8, "dB"),
    ("cresta bajo",            13.0, 16.0, "dB"),
    ("sidechain melodico",     -9.6, -6.8, "dB"),
    ("cresta espectral bat",   17.4, 18.8, "dB"),
    ("ocupacion melodico",     0.44, 1.00,  "%"),
    ("variacion por compas",   0.85, 2.50,  ""),
]


def _huella(y: np.ndarray, x: int, c: int) -> np.ndarray | None:
    """La firma de un compas: ocho bandas en dB relativos mas el patron de ataque.

    Las dos mitades importan y por separado no alcanzan. Solo bandas: dos
    compases con el mismo contenido y distinto ritmo miden igual. Solo
    ataques: dos compases con el mismo ritmo y distinto instrumento tambien.

    Las bandas van en dB RELATIVOS al total del compas y no normalizadas a 1,
    y ahi esta la diferencia entre un instrumento que sirve y uno que miente.
    La primera version normalizaba y comparaba por coseno: daba "1 compas
    distinto de 16" para Alex O'Rion - Tunnel, que es obviamente falso. El
    coseno sobre espectros normalizados satura en 0.99 entre compases de
    cualquier tema. Se descubrio calibrando contra las referencias antes de
    usar el instrumento, que es el unico momento en que se puede descubrir.
    """
    seg = y[c * x:(c + 1) * x]
    if seg.size < x // 2:
        return None
    bordes = [30, 80, 150, 300, 700, 1500, 3000, 6000, 11000]
    niveles = np.array([np.sqrt((_banda(seg, SR, a, b) ** 2).mean())
                        for a, b in zip(bordes, bordes[1:])])
    niveles = 20 * np.log10(niveles / (niveles.sum() or 1.0) + 1e-9)
    env = librosa.onset.onset_strength(y=seg, sr=SR, hop_length=256)
    paso = max(1, len(env) // 16)
    ataques = np.array([env[i * paso:(i + 1) * paso].max() for i in range(16)])
    ataques = ataques / (ataques.max() or 1.0)
    # las dos escalas puestas a la par: 6 dB de cambio de banda pesa como un
    # tercio de ataque que aparece o desaparece
    return np.concatenate([niveles / 6.0, ataques * 3.0])


def variacion(y: np.ndarray, bpm: float = BPM, ventana: int = 16) -> float:
    """Cuanto se diferencia cada compas del mas parecido de los anteriores.

    Devuelve la MEDIANA de esas distancias, no un conteo con umbral: un umbral
    es una decision mas que calibrar, y la distancia ya separa sola.

    Calibrado sobre las referencias: Tunnel 0.86, Panorama 1.45, Closing Doors
    2.46. El boceto propio: 0.64 — mas bajo que las tres, que es "nada cambia"
    medido.
    """
    x = int(round(SR * 4 * 60.0 / bpm))
    n = min(ventana, len(y) // x)
    hs = [h for h in (_huella(y, x, c) for c in range(n)) if h is not None]
    if len(hs) < 4:
        return 0.0
    return float(np.median([
        min(float(np.linalg.norm(hs[i] - hs[j])) for j in range(i))
        for i in range(1, len(hs))]))


def juzgar(render: Path, previo: dict | None = None) -> dict:
    """Mide lo que se puede medir sobre el render solo, sin Demucs."""
    y, _ = librosa.load(render, sr=SR, mono=True)
    fuera = dict(previo or {})
    fuera["variacion por compas"] = variacion(y)
    # el timbre de la mezcla entera: sirve de tamiz aunque no separe buses
    t = medir_timbre(y, 150, 11000)
    if t:
        fuera["cresta espectral mezcla"] = t["cresta"]
        fuera["centroide mezcla"] = t["centroide"]
    return fuera


def mostrar(vals: dict) -> tuple[int, list[str]]:
    print(f"\n  {'dimension':<24} {'objetivo':>14} {'propio':>9}   veredicto")
    dentro, lejos = 0, []
    for nombre, lo, hi, u in CONVERGENCIA:
        v = vals.get(nombre)
        obj = (f"{lo:.0%}-{hi:.0%}" if u == "%" else f"{lo:g} a {hi:g}{u}")
        if v is None:
            print(f"    {nombre:<24} {obj:>14} {'—':>9}   sin medir")
            continue
        txt = f"{v:.0%}" if u == "%" else f"{v:.2f}"
        if lo <= v <= hi:
            dentro += 1
            print(f"    {nombre:<24} {obj:>14} {txt:>9}   ok")
        else:
            lejos.append((abs(v - (lo if v < lo else hi)) / max(abs(hi - lo), 1e-6), nombre))
            print(f"  ->{nombre:<24} {obj:>14} {txt:>9}   "
                  f"{'bajo' if v < lo else 'alto'}")
    n = sum(1 for x, *_ in CONVERGENCIA if vals.get(x) is not None)
    print(f"\n  {dentro} de {n} medidas dentro de rango"
          f" ({len(CONVERGENCIA)} dimensiones en total)")
    orden = [nombre for _, nombre in sorted(lejos, reverse=True)]
    if orden:
        print(f"  la mas lejos, que es la de la proxima vuelta: {orden[0]}")
        print(f"  despues: {', '.join(orden[1:4])}")
    return dentro, orden


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("render", type=Path)
    ap.add_argument("--previo", type=Path,
                    help="JSON con dimensiones ya medidas (de iterar.py)")
    ap.add_argument("--json", type=Path, help="guarda el resultado")
    args = ap.parse_args()
    if not args.render.exists():
        sys.exit(f"no existe {args.render}")
    previo = json.loads(args.previo.read_text(encoding="utf-8")) if args.previo else None
    vals = juzgar(args.render, previo)
    dentro, orden = mostrar(vals)
    if args.json:
        args.json.write_text(json.dumps(
            {"render": args.render.name, "valores": vals,
             "dentro": dentro, "orden_de_ataque": orden},
            indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  -> {args.json}")


if __name__ == "__main__":
    main()
