"""Mide la FORMA de un tema: donde empieza y termina cada seccion, en compases.

Por que existe: el proyecto ya sabe medir el groove —cuantas notas por compas
lleva cada capa, donde cae el bajo respecto del bombo— pero todo eso se mide
sobre un fragmento de ocho compases elegido por pico de energia. Sirve para
escribir un loop y no dice absolutamente nada sobre como se ordena un tema
entero: cuanto dura la intro de DJ, en que compas se cae el bombo, cuantos
compases tiene el drop, cuanto se deja al final para mezclar.

Y esa es justamente la parte que no conviene inventar. Un loop que suena bien es
una opinion defendible; la duracion de una intro de DJ no es una opinion, es una
convencion que la pista impone y que se puede contar.

Como lo mide. Tres bandas por compas sobre el tema entero:

    bombo     30-120 Hz     dice si la seccion tiene pulso
    cuerpo    200-2000 Hz   dice si hay armonia y bajo
    brillo    4-11 kHz      dice si hay hats, arpegios y aire

Con eso alcanza para clasificar cada compas sin transcribir nada:

    BAJADA    sin bombo                       (el breakdown)
    GROOVE    bombo, poco brillo              (la intro y la salida de DJ)
    TEMA      bombo y cuerpo, brillo medio
    DROP      bombo, cuerpo y brillo, todo    (el pico)

Los umbrales son cuantiles del propio tema y no numeros absolutos: un tema
mezclado bajo y uno mezclado fuerte tienen la misma forma, y compararlos contra
un umbral fijo diria que el primero no tiene drop.

Uso:
    python scripts/estructura.py "<mp3>"
    python scripts/estructura.py --tocados 6
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from plomo import config  # noqa: E402
from plomo.matching import clave  # noqa: E402

DEPOSITO = config.MUSIC_LIBRARY_ROOT / "Biblioteca"
SR = 22050
BANDAS = {"bombo": (30, 120), "cuerpo": (200, 2000), "brillo": (4000, 11000)}


def _energia(y: np.ndarray, lo: float, hi: float, muestras_x_compas: int) -> np.ndarray:
    """Energia media de esa banda, un valor por compas."""
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    f = librosa.fft_frequencies(sr=SR, n_fft=2048)
    banda = S[(f >= lo) & (f < hi)].mean(axis=0)
    porc = muestras_x_compas / 512
    n = int(len(banda) / porc)
    return np.array([banda[int(i * porc):int((i + 1) * porc)].mean()
                     for i in range(n)])


def _clasificar(b: np.ndarray, c: np.ndarray, br: np.ndarray) -> list[str]:
    """Una etiqueta por compas, con umbrales sacados del propio tema."""
    hay_bombo = b > np.quantile(b, 0.85) * 0.42
    cuerpo_alto = c > np.quantile(c, 0.55)
    brillo_alto = br > np.quantile(br, 0.62)
    fuera = []
    for i in range(len(b)):
        if not hay_bombo[i]:
            fuera.append("BAJADA")
        elif brillo_alto[i] and cuerpo_alto[i]:
            fuera.append("DROP")
        elif cuerpo_alto[i]:
            fuera.append("TEMA")
        else:
            fuera.append("GROOVE")
    return fuera


def _suavizar(etiquetas: list[str], ventana: int = 4) -> list[str]:
    """Una seccion dura al menos cuatro compases.

    Sin esto la clasificacion parpadea compas a compas y devuelve cuarenta
    'secciones' de un compas, que no es la forma del tema sino el ruido de la
    medicion. Cuatro compases es la frase mas corta que existe en este genero.
    """
    fuera = list(etiquetas)
    for i in range(0, len(fuera) - ventana + 1, ventana):
        tramo = fuera[i:i + ventana]
        gana = max(set(tramo), key=tramo.count)
        fuera[i:i + ventana] = [gana] * ventana
    return fuera


def _bloques(etiquetas: list[str]) -> list[tuple[int, int, str]]:
    fuera = []
    ini = 0
    for i in range(1, len(etiquetas) + 1):
        if i == len(etiquetas) or etiquetas[i] != etiquetas[ini]:
            fuera.append((ini, i, etiquetas[ini]))
            ini = i
    return fuera


def medir(archivo: Path) -> dict | None:
    y, _ = librosa.load(archivo, sr=SR)
    crudo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=SR)[0])[0])
    while crudo < 100:
        crudo *= 2
    while crudo > 145:
        crudo /= 2
    x_compas = int(round(SR * 4 * 60.0 / crudo))
    bandas = {n: _energia(y, lo, hi, x_compas) for n, (lo, hi) in BANDAS.items()}
    n = min(len(v) for v in bandas.values())
    et = _suavizar(_clasificar(*(bandas[k][:n] for k in
                                 ("bombo", "cuerpo", "brillo"))))
    return {"archivo": archivo.stem, "bpm": crudo, "compases": n,
            "minutos": len(y) / SR / 60.0, "bloques": _bloques(et)}


def _mostrar(d: dict) -> None:
    print(f"\n  {d['archivo'][:70]}")
    print(f"  {d['bpm']:.0f} BPM · {d['compases']} compases · {d['minutos']:.1f} min\n")
    for ini, fin, et in d["bloques"]:
        if fin - ini < 4:
            continue
        print(f"   {ini + 1:>4}-{fin:<5} {fin - ini:>3} compases  {et:<7} "
              f"{'#' * ((fin - ini) // 2)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path, nargs="?")
    ap.add_argument("--tocados", type=int, help="los N mas tocados de la historia")
    args = ap.parse_args()

    objetivos: list[Path] = []
    if args.archivo:
        objetivos = [args.archivo]
    elif args.tocados:
        from medir_arreglos import _buscar, _partir
        mas = json.loads((RAIZ / "data" / "mi_sonido.json").read_text(encoding="utf-8"))
        indice = {clave(*_partir(p.stem)): p for p in DEPOSITO.rglob("*.mp3")}
        for t in mas["mas_sonados"]:
            if len(objetivos) >= args.tocados:
                break
            f = _buscar(t["artist"], t["title"], indice)
            if f:
                objetivos.append(f)
    else:
        sys.exit("dame un archivo o --tocados N")

    medidos = []
    for f in objetivos:
        try:
            d = medir(f)
        except Exception as e:                       # noqa: BLE001
            print(f"  - {f.stem[:50]}: {e}")
            continue
        medidos.append(d)
        _mostrar(d)

    if len(medidos) < 2:
        return
    print("\n\n  === lo que se repite ===\n")
    intros, bajadas, drops, largos = [], [], [], []
    for d in medidos:
        largos.append(d["minutos"])
        bl = [b for b in d["bloques"] if b[1] - b[0] >= 4]
        if bl and bl[0][2] in ("GROOVE", "TEMA"):
            intros.append(bl[0][1] - bl[0][0])
        bajadas += [b[1] - b[0] for b in bl if b[2] == "BAJADA"]
        drops += [b[1] - b[0] for b in bl if b[2] == "DROP"]
    def m(v, k):
        return f"{statistics.median(v):.0f}" if v else "-"
    print(f"   duracion           {statistics.median(largos):.1f} min")
    print(f"   intro de DJ        {m(intros, 0)} compases   ({len(intros)} temas)")
    print(f"   bajadas            {m(bajadas, 0)} compases   ({len(bajadas)} en total)")
    print(f"   drops              {m(drops, 0)} compases   ({len(drops)} en total)")
    print()


if __name__ == "__main__":
    main()
