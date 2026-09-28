# -*- coding: utf-8 -*-
"""Pule una grabacion de consola hasta dejarla publicable, y deja escrito que le hizo.

POR QUE
-------
El master del 2026-09-23 solo corrigio loudness y true peak: bajo la ganancia a
-14 LUFS y listo. Eso dejo adentro dos defectos medidos que un cambio de ganancia
no toca —4146 muestras pegadas al tope y contenido infrasonico que corre el cero
hasta -0.017 en el minuto 12— y dejo los diez segundos de silencio digital del
arranque. "Puli el master a nivel publicable" (el DJ, 2026-09-28).

QUE HACE, EN ORDEN, Y POR QUE CADA COSA
--------------------------------------
1. Recorta el silencio de punta y cola. La consola graba antes de que suene nada.
   El recorte queda en el informe: el desfase con el video del telefono (19.14 s
   en la del 23) se mide desde el arranque de la consola, y cambia.
2. Declip: spline cubica sobre las rachas pegadas al tope, con los vecinos sanos.
   Las rachas son de 1 a 9 muestras; en las de una sola no hay pico que
   reconstruir, asi que cambia pocas muestras y poco. Es prolijidad, no rescate.
   Va antes que cualquier filtro: filtrado, un tope plano deja de ser plano y ya
   no se encuentra.
3. Pasa-altos a 10 Hz, de fase cero. Saca lo infrasonico, que no se escucha y se
   come headroom. No es un offset de la consola —es cero en casi todo el set y
   -0.017 donde hay mas sub— asi que restar la media no alcanza.
4. Ganancias por tramo (opcional, `--ganancias`): puntos (segundo, dB) con rampas
   lineales entre ellos. Para nivelar temas que entraron mas bajos. Los puntos
   salen de medir contra los originales, no del oido del script.
5. Normaliza a -14 LUFS integrados. YouTube baja lo que viene mas fuerte y NO
   sube lo que viene mas bajo: -14 es el nivel donde no se pierde nada.
6. True peak con 4x de sobremuestreo. Si pasa el techo, ABORTA: a -14 no deberia
   pasar nunca, y si pasa hay algo mal que un limitador taparia.
7. 48 kHz / 24 bits, que es lo que usa el video.

Lo que NO hace: EQ, compresion ni ensanche. Los movimientos de EQ y filtro del DJ
son la mezcla, no defectos.

USO
---
    python scripts/pulir_master.py grabaciones/2026-09-23_set_consola_REC001.wav
    python scripts/pulir_master.py <wav> --ganancias data/video/ganancias.json --salida <wav>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
import soxr
from scipy.interpolate import CubicSpline
from scipy.signal import butter, resample_poly, sosfiltfilt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LUFS_OBJETIVO = -14.0
TECHO_DBTP = -1.0
SR_SALIDA = 48000
UMBRAL_SILENCIO_DB = -60.0
COLA_S = 2.0               # aire despues de que la musica termina
FUNDIDO_ENTRADA_S = 0.02   # evita el click si la musica arranca de golpe
FUNDIDO_SALIDA_S = 1.5
CORTE_SUBSONICO_HZ = 10.0
VECINOS_DECLIP = 6


def db(x: float) -> float:
    return float(20 * np.log10(max(x, 1e-12)))


def true_peak(x: np.ndarray, sr: int) -> float:
    """Pico con 4x de sobremuestreo, por bloques: el set entero a 4x son 5 GB."""
    bloque, solape = 30 * sr, 64
    pico = 0.0
    for i in range(0, len(x), bloque):
        tramo = x[max(0, i - solape): i + bloque + solape]
        pico = max(pico, float(np.abs(resample_poly(tramo, 4, 1, axis=0)).max()))
    return db(pico)


def recortar(x: np.ndarray, sr: int) -> tuple[np.ndarray, float, float]:
    """Saca el silencio digital de punta y cola. Devuelve el audio y los segundos recortados."""
    umbral = 10 ** (UMBRAL_SILENCIO_DB / 20)
    sonando = np.where(np.abs(x).max(axis=1) > umbral)[0]
    ini = int(sonando[0])
    fin = min(len(x), int(sonando[-1]) + int(COLA_S * sr))
    return x[ini:fin].copy(), ini / sr, (len(x) - fin) / sr


def declip(x: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Reconstruye las rachas pegadas al tope. Devuelve copia, rachas y muestras cambiadas."""
    y = x.copy()
    umbral = np.abs(x).max() * 0.99995
    rachas = cambiadas = 0
    for c in range(x.shape[1]):
        s = x[:, c]
        malo = np.abs(s) >= umbral
        borde = np.diff(np.concatenate([[0], malo.astype(np.int8), [0]]))
        for a, b in zip(np.where(borde == 1)[0], np.where(borde == -1)[0]):
            lo, hi = max(0, a - VECINOS_DECLIP), min(len(s), b + VECINOS_DECLIP)
            idx = np.r_[lo:a, b:hi]
            idx = idx[~malo[idx]]
            if len(idx) < 4:
                continue
            curva = CubicSpline(idx, s[idx])(np.arange(a, b))
            # lo reconstruido nunca queda por debajo de lo grabado
            nuevo = np.sign(s[a]) * np.maximum(np.abs(curva), np.abs(s[a:b]))
            cambiadas += int((nuevo != s[a:b]).sum())
            y[a:b, c] = nuevo
            rachas += 1
    return y, rachas, cambiadas


def curva_de_ganancia(puntos: list[list[float]], n: int, sr: int, inicio_s: float) -> np.ndarray:
    """Ganancia lineal por muestra desde puntos (segundo del ORIGINAL, dB)."""
    t = np.arange(n) / sr + inicio_s
    seg = [p[0] for p in puntos]
    gdb = [p[1] for p in puntos]
    return 10 ** (np.interp(t, seg, gdb) / 20)


def fundir(x: np.ndarray, sr: int) -> np.ndarray:
    y = x.copy()
    ne, ns = int(FUNDIDO_ENTRADA_S * sr), int(FUNDIDO_SALIDA_S * sr)
    y[:ne] *= np.linspace(0, 1, ne)[:, None]
    y[-ns:] *= (np.cos(np.linspace(0, np.pi, ns)) * 0.5 + 0.5)[:, None]
    return y


def medir(x: np.ndarray, sr: int) -> dict:
    tope = np.abs(x).max()
    return {
        "lufs": round(pyln.Meter(sr).integrated_loudness(x), 2),
        "pico_dbfs": round(db(tope), 2),
        "true_peak_dbtp": round(true_peak(x, sr), 2),
        "muestras_al_tope": int((np.abs(x) >= tope * 0.99995).sum()),
        "dc": [round(float(v), 5) for v in x.mean(axis=0)],
        "duracion_s": round(len(x) / sr, 2),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--salida", help="por defecto <nombre>_master_youtube.wav al lado del original")
    ap.add_argument("--ganancias", help="JSON con {'puntos': [[segundo, dB], ...]} en tiempo del original")
    ap.add_argument("--lufs", type=float, default=LUFS_OBJETIVO)
    a = ap.parse_args()

    origen = Path(a.wav)
    salida = Path(a.salida) if a.salida else origen.with_name(
        origen.stem.replace("_consola_REC001", "") + "_master_youtube.wav")
    if salida.resolve() == origen.resolve():
        sys.exit("la salida no puede pisar el original")

    x, sr = sf.read(origen, dtype="float64", always_2d=True)
    antes = medir(x, sr)
    print(f"original: {antes}")

    x, recorte_ini, recorte_fin = recortar(x, sr)
    # el declip va ANTES del filtro: despues del filtro las crestas ya no son planas
    x, rachas, cambiadas = declip(x)
    x = sosfiltfilt(butter(2, CORTE_SUBSONICO_HZ, "highpass", fs=sr, output="sos"), x, axis=0)
    print(f"recorte {recorte_ini:.2f} s al principio y {recorte_fin:.2f} s al final; "
          f"declip {rachas} rachas, {cambiadas} muestras cambiadas")

    puntos = None
    if a.ganancias:
        puntos = json.loads(Path(a.ganancias).read_text(encoding="utf-8"))["puntos"]
        x = x * curva_de_ganancia(puntos, len(x), sr, recorte_ini)[:, None]
        print(f"ganancias por tramo: {len(puntos)} puntos")

    x = fundir(x, sr)
    lufs = pyln.Meter(sr).integrated_loudness(x)
    x = x * 10 ** ((a.lufs - lufs) / 20)
    x = soxr.resample(x, sr, SR_SALIDA, quality="VHQ")

    despues = medir(x, SR_SALIDA)
    print(f"master:   {despues}")
    if despues["true_peak_dbtp"] > TECHO_DBTP:
        sys.exit(f"true peak {despues['true_peak_dbtp']} dBTP pasa el techo de {TECHO_DBTP}: "
                 "no se escribe. A este nivel no deberia pasar; revisar las ganancias.")

    sf.write(salida, x, SR_SALIDA, subtype="PCM_24")
    informe = {
        "origen": str(origen), "salida": str(salida),
        "antes": antes, "despues": despues,
        "recorte_inicio_s": round(recorte_ini, 3), "recorte_fin_s": round(recorte_fin, 3),
        "declip": {"rachas": rachas, "muestras_cambiadas": cambiadas},
        "subsonico_hz": CORTE_SUBSONICO_HZ, "ganancias": puntos,
        "lufs_objetivo": a.lufs, "techo_dbtp": TECHO_DBTP, "sr": SR_SALIDA,
    }
    salida.with_suffix(".json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {salida}\n-> {salida.with_suffix('.json')}")


if __name__ == "__main__":
    main()
