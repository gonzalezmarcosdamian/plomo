"""Ingenieria inversa de un track: la receta de produccion en numeros.

Convierte "quiero que suene como Vuarambon" en algo perseguible: estructura por
compases, curva de energia, balance espectral, ancho estereo por banda, LUFS y
densidad de eventos.

Mide senal, no intencion. No detecta acordes ni instrumentos, y la segmentacion
es una heuristica sobre presencia de kick: en material sin kick claro (organic,
downtempo, ambient) el reporte lo dice en vez de inventar secciones.

Uso:
    python scripts/reverse_engineer.py "track.mp3"
    python scripts/reverse_engineer.py referencia.mp3 --contra propio.mp3
    python scripts/reverse_engineer.py track.mp3 --json data/recetas/nombre.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402
import librosa  # noqa: E402
import pyloudnorm  # noqa: E402
from scipy.signal import butter, sosfiltfilt  # noqa: E402

SR = 44100
BEATS_POR_COMPAS = 4
# Bandas de analisis. El sub y el bajo son donde se decide si un kick suena
# anclado o flotante; el aire define cuanto "brilla" la produccion.
BANDAS = {"sub": (20, 60), "bajo": (60, 250), "medio": (250, 2000), "aire": (2000, 16000)}
KICK_BANDA = (30, 120)
MIN_COMPASES_SECCION = 4
# Un compas cuenta con kick si su energia grave supera esta fraccion del p90 del
# track. Empirico: por debajo de 0.30 los breakdowns con pad grave dan falso
# positivo; por encima de 0.45 se parte el drop en pedazos.
UMBRAL_KICK = 0.35


@dataclass
class Seccion:
    tipo: str
    compas_inicio: int
    compases: int
    seg_inicio: float
    seg_dur: float
    energia: float
    densidad: float


@dataclass
class Receta:
    archivo: str
    duracion_seg: float
    bpm: float
    compases: int
    lufs: float
    rango_dinamico_db: float
    pico_dbfs: float
    balance: dict[str, float]
    ancho: dict[str, float]
    secciones: list[Seccion] = field(default_factory=list)
    curva_energia: list[float] = field(default_factory=list)
    confiable: bool = True
    aviso: str = ""


# -- utilidades -------------------------------------------------------------
def _bandpass(x: np.ndarray, lo: float, hi: float, sr: int) -> np.ndarray:
    ny = sr / 2
    hi = min(hi, ny * 0.99)
    sos = butter(4, [lo / ny, hi / ny], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def _energia_por_compas(x: np.ndarray, bordes: np.ndarray) -> np.ndarray:
    """RMS de cada compas, dado el vector de muestras donde arranca cada uno."""
    return np.array([
        float(np.sqrt(np.mean(x[a:b] ** 2))) if b > a else 0.0
        for a, b in zip(bordes[:-1], bordes[1:])
    ])


def _etiquetar(tramos: list[tuple[bool, int, int]], total: int) -> list[str]:
    """Nombra cada tramo segun donde cae y si tiene kick.

    La logica es la del algoritmo de cues v8: el breakdown es el tramo sin kick
    mas largo del medio del track, y el drop es el kick que vuelve despues.
    """
    sin_kick_medio = [
        (i, largo) for i, (hay, ini, largo) in enumerate(tramos)
        if not hay and 0.15 < (ini + largo / 2) / total < 0.85
    ]
    i_break = max(sin_kick_medio, key=lambda x: x[1])[0] if sin_kick_medio else -1

    nombres = []
    visto_kick = False
    for i, (hay, ini, largo) in enumerate(tramos):
        fin_rel = (ini + largo) / total
        if i == i_break:
            nombres.append("breakdown")
        elif not hay and not visto_kick:
            nombres.append("intro")
        elif not hay and fin_rel > 0.9:
            nombres.append("outro")
        elif not hay:
            nombres.append("respiro")
        elif i_break >= 0 and i == i_break + 1:
            nombres.append("drop")
        elif not visto_kick:
            nombres.append("groove")
        else:
            nombres.append("groove" if i < i_break or i_break < 0 else "salida")
        if hay:
            visto_kick = True
    return nombres


# -- analisis ---------------------------------------------------------------
def analizar(path: Path) -> Receta:
    y, sr = librosa.load(str(path), sr=SR, mono=False)
    if y.ndim == 1:
        y = np.vstack([y, y])
    mono = y.mean(axis=0)
    dur = len(mono) / sr

    bpm, beats = librosa.beat.beat_track(y=mono, sr=sr, units="samples")
    bpm = float(np.atleast_1d(bpm)[0])

    # Bordes de compas. Si el beat tracking falla, se cae a una grilla fija
    # derivada del BPM: peor, pero no rompe el analisis.
    if len(beats) > BEATS_POR_COMPAS * 2:
        bordes = beats[::BEATS_POR_COMPAS]
    else:
        paso = int(sr * 60 / max(bpm, 60) * BEATS_POR_COMPAS)
        bordes = np.arange(0, len(mono), paso)
    bordes = np.append(bordes, len(mono))
    n_compases = len(bordes) - 1

    grave = _bandpass(mono, *KICK_BANDA, sr)
    e_grave = _energia_por_compas(grave, bordes)
    e_total = _energia_por_compas(mono, bordes)

    ref = np.percentile(e_grave, 90) or 1e-9
    hay_kick = e_grave > UMBRAL_KICK * ref
    # Un track sin contraste grave (todo o nada) no se puede segmentar asi.
    contraste = float(np.percentile(e_grave, 90) / (np.percentile(e_grave, 10) + 1e-9))
    confiable = contraste > 2.5

    # tramos consecutivos de igual estado, descartando los muy cortos
    tramos: list[tuple[bool, int, int]] = []
    i = 0
    while i < n_compases:
        j = i
        while j < n_compases and hay_kick[j] == hay_kick[i]:
            j += 1
        largo = j - i
        estado = bool(hay_kick[i])
        # Un tramo corto no es una seccion: lo absorbe el anterior. Y si al
        # absorberlo el siguiente queda con el mismo estado que el anterior,
        # tambien se funden — si no, salen tres "groove" seguidos que en
        # realidad son uno solo.
        if tramos and (largo < MIN_COMPASES_SECCION or tramos[-1][0] == estado):
            hay, ini, l0 = tramos[-1]
            tramos[-1] = (hay, ini, l0 + largo)
        else:
            tramos.append((estado, i, largo))
        i = j

    onsets = librosa.onset.onset_detect(y=mono, sr=sr, units="samples")
    nombres = _etiquetar(tramos, n_compases)
    secciones = []
    for (hay, ini, largo), nombre in zip(tramos, nombres):
        a, b = int(bordes[ini]), int(bordes[min(ini + largo, n_compases)])
        n_on = int(((onsets >= a) & (onsets < b)).sum())
        secciones.append(Seccion(
            tipo=nombre, compas_inicio=ini + 1, compases=largo,
            seg_inicio=round(a / sr, 1), seg_dur=round((b - a) / sr, 1),
            energia=round(float(np.mean(e_total[ini:ini + largo])), 5),
            densidad=round(n_on / max(largo, 1), 2),
        ))

    # balance espectral
    S = np.abs(librosa.stft(mono, n_fft=4096))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    total_e = float((S ** 2).sum()) or 1e-9
    balance = {}
    for nombre, (lo, hi) in BANDAS.items():
        m = (freqs >= lo) & (freqs < hi)
        balance[nombre] = round(float((S[m] ** 2).sum()) / total_e * 100, 1)

    # ancho estereo por banda: correlacion L/R. 1.0 = mono, 0 = descorrelacionado
    ancho = {}
    for nombre, (lo, hi) in BANDAS.items():
        L = _bandpass(y[0], lo, hi, sr)
        Rr = _bandpass(y[1], lo, hi, sr)
        if L.std() < 1e-9 or Rr.std() < 1e-9:
            ancho[nombre] = 1.0
        else:
            ancho[nombre] = round(float(np.corrcoef(L, Rr)[0, 1]), 3)

    # loudness
    medidor = pyloudnorm.Meter(sr)
    lufs = float(medidor.integrated_loudness(y.T))
    ventana = int(sr * 3)
    cortos = [
        medidor.integrated_loudness(y.T[k:k + ventana])
        for k in range(0, max(len(mono) - ventana, 1), ventana)
    ]
    cortos = [c for c in cortos if np.isfinite(c)]
    rango = round(float(np.percentile(cortos, 95) - np.percentile(cortos, 10)), 1) if cortos else 0.0
    pico = round(float(20 * np.log10(np.max(np.abs(y)) + 1e-12)), 1)

    emax = float(e_total.max()) or 1e-9
    return Receta(
        archivo=path.name, duracion_seg=round(dur, 1), bpm=round(bpm, 1),
        compases=n_compases, lufs=round(lufs, 1), rango_dinamico_db=rango,
        pico_dbfs=pico, balance=balance, ancho=ancho, secciones=secciones,
        curva_energia=[round(float(v / emax), 3) for v in e_total],
        confiable=confiable,
        aviso="" if confiable else (
            "poco contraste en la banda grave: la segmentacion por presencia de "
            "kick no es confiable en este material. Leer las secciones con pinzas."),
    )


# -- salida -----------------------------------------------------------------
def _sparkline(vals: list[float], ancho: int = 60) -> str:
    if not vals:
        return ""
    chars = " .:-=+*#%@"
    paso = max(len(vals) / ancho, 1)
    out = []
    for k in range(min(ancho, len(vals))):
        tramo = vals[int(k * paso):max(int((k + 1) * paso), int(k * paso) + 1)]
        v = sum(tramo) / len(tramo)
        out.append(chars[min(int(v * (len(chars) - 1)), len(chars) - 1)])
    return "".join(out)


def imprimir(r: Receta) -> None:
    print(f"\n{'=' * 74}")
    print(f"{r.archivo}")
    print(f"  {r.duracion_seg / 60:.1f} min   {r.bpm} BPM   {r.compases} compases")
    if r.aviso:
        print(f"  AVISO: {r.aviso}")

    print(f"\n  LOUDNESS   {r.lufs} LUFS integrado   rango {r.rango_dinamico_db} dB"
          f"   pico {r.pico_dbfs} dBFS")
    print("  BALANCE    " + "   ".join(f"{k} {v:>4.1f}%" for k, v in r.balance.items()))
    print("  ANCHO      " + "   ".join(f"{k} {v:>5.2f}" for k, v in r.ancho.items())
          + "     (1.00 = mono)")
    if r.ancho.get("sub", 1) < 0.85:
        print("             el sub no es mono: en un sistema grande se cancela.")

    print(f"\n  ESTRUCTURA ({len(r.secciones)} secciones)")
    print(f"  {'seccion':<11} {'compas':>7} {'largo':>6} {'min':>6} {'dur':>6}"
          f" {'energia':>8} {'onsets/c':>9}")
    for s in r.secciones:
        print(f"  {s.tipo:<11} {s.compas_inicio:>7} {s.compases:>6} "
              f"{s.seg_inicio / 60:>6.1f} {s.seg_dur:>5.0f}s {s.energia:>8.4f} "
              f"{s.densidad:>9.2f}")

    print(f"\n  CURVA      |{_sparkline(r.curva_energia)}|")


def comparar(a: Receta, b: Receta) -> None:
    print(f"\n{'=' * 74}\nCOMPARACION   {a.archivo}   vs   {b.archivo}\n")
    filas = [
        ("BPM", a.bpm, b.bpm, ""),
        ("duracion min", round(a.duracion_seg / 60, 1), round(b.duracion_seg / 60, 1), ""),
        ("compases", a.compases, b.compases, ""),
        ("LUFS", a.lufs, b.lufs, "mas alto = mas comprimido"),
        ("rango dB", a.rango_dinamico_db, b.rango_dinamico_db, "mas alto = mas dinamico"),
        ("secciones", len(a.secciones), len(b.secciones), ""),
    ]
    for k, (lo, hi) in BANDAS.items():
        filas.append((f"{k} %", a.balance[k], b.balance[k], f"{lo}-{hi} Hz"))
    for k in BANDAS:
        filas.append((f"ancho {k}", a.ancho[k], b.ancho[k], "1.00 = mono"))

    print(f"  {'':<14} {'referencia':>11} {'propio':>11} {'delta':>9}   nota")
    for nombre, va, vb, nota in filas:
        try:
            d = f"{vb - va:+.2f}"
        except TypeError:
            d = ""
        print(f"  {nombre:<14} {va:>11} {vb:>11} {d:>9}   {nota}")

    print(f"\n  CURVAS")
    print(f"    ref    |{_sparkline(a.curva_energia)}|")
    print(f"    propio |{_sparkline(b.curva_energia)}|")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("track", type=Path)
    ap.add_argument("--contra", type=Path, help="segundo track para comparar")
    ap.add_argument("--json", type=Path, help="guarda la receta")
    args = ap.parse_args()

    if not args.track.exists():
        sys.exit(f"no existe: {args.track}")

    print(f"analizando {args.track.name} ...", flush=True)
    ra = analizar(args.track)
    imprimir(ra)

    rb = None
    if args.contra:
        if not args.contra.exists():
            sys.exit(f"no existe: {args.contra}")
        print(f"\nanalizando {args.contra.name} ...", flush=True)
        rb = analizar(args.contra)
        imprimir(rb)
        comparar(ra, rb)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        doc = {"referencia": asdict(ra)}
        if rb:
            doc["contra"] = asdict(rb)
        args.json.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"\n  receta -> {args.json}")


if __name__ == "__main__":
    main()
