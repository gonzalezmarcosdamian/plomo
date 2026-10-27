"""Los cues de un tema puestos con la misma estructura que usa la mezcla.

POR QUE
-------
"Los cues que estamos poniendo, tienen que ser con la misma tecnica que mezclamos los sets no?" y,
de las dos opciones, "1 como el que mezcla que lo veo joya cada vez que escucho" (el DJ, 2026-10-27).
Medido en el 159 y el 157 ese dia: el Mix-IN coincidia siempre, pero 62 a 82% de los Mix-OUT caian
fuera de frase y un tercio de los breakdowns estaba a 8 compases o mas de donde mezcla el motor.
`cue_engine.analyze_track` cuenta compases desde el segundo 0 a BPM fijo, sin la grilla de
Rekordbox; `mezcla.medir` mide compas por compas SOBRE la grilla y lleva todo a frase. Aca los
cues salen de `medir`, asi el CDJ y la mezcla miran los mismos puntos.

Se escribe con el mismo layout (`cue_engine.layout_v9`, `apply_cues_v8_direct`): cambia donde
caen los cues, no cuales son.
"""
from __future__ import annotations

import numpy as np

from plomo.cue_engine import CueAnalysis, _bar_medio, layout_v9
from plomo.mezcla import Estructura

# los comentarios que escribe el engine; cualquier otro cue lo puso el DJ a mano
NOMBRES_DEL_ENGINE = frozenset(m.nombre for m in layout_v9(CueAnalysis(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))


def _t(compases: np.ndarray, compas: int) -> float:
    return float(compases[min(max(compas, 0), len(compases) - 1)])


def cues_de_estructura(compases: np.ndarray, e: Estructura, medios: np.ndarray | None = None) -> CueAnalysis:
    """Los segundos de cada cue, desde los compases que mide la mezcla sobre la grilla.

    `compases`: el tiempo de cada primer tiempo de compas (Tema.compases).
    `medios`: energia de medios por compas, para el Medio; sin ella no se pone.
    """
    inicio_tramo = e.drop if e.drop is not None else (e.breakdown[1] if e.breakdown else None)
    medio = None
    if medios is not None and inicio_tramo is not None:
        bar = _bar_medio(inicio_tramo, e.mix_out(), medios)
        medio = _t(compases, bar) if bar is not None else None
    return CueAnalysis(
        first_beat=_t(compases, 0),
        bass_in=_t(compases, e.bass_in),
        breakdown=_t(compases, e.breakdown[0]) if e.breakdown else None,
        drop=_t(compases, e.drop) if e.drop is not None else None,
        drop_mid=medio,
        outro=_t(compases, e.mix_out()),
    )


def medios_por_compas(y: np.ndarray, sr: int, compases: np.ndarray) -> np.ndarray:
    """RMS de 300 Hz a 3 kHz por compas de la grilla: el respiro que busca el Medio."""
    from scipy.signal import butter, sosfilt
    m = sosfilt(butter(4, [300, 3000], "bandpass", fs=sr, output="sos"), y)
    bordes = [int(t * sr) for t in compases] + [len(m)]
    return np.array([np.sqrt(np.mean(m[a:b] ** 2)) if b > a else 0.0 for a, b in zip(bordes[:-1], bordes[1:])])


def analizar(tema) -> CueAnalysis:
    """Mide el tema como la mezcla y devuelve sus cues. `tema` es un mezcla.Tema."""
    import librosa

    from plomo.mezcla import SR_ANALISIS, medir
    y = librosa.load(str(tema.archivo), sr=SR_ANALISIS, mono=True)[0]
    e = medir(tema, y)
    return cues_de_estructura(tema.compases, e, medios_por_compas(y, SR_ANALISIS, tema.compases))


def cues_a_mano(con, content_id: str) -> list[str]:
    """Los cues vivos del tema que no escribio el engine: los puso el DJ y no se pisan."""
    filas = con.execute("SELECT Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0",
                        (str(content_id),)).fetchall()
    return [f"{c or '(sin nombre)'} @ {ms / 1000:.1f}s" for c, ms in filas if (c or "") not in NOMBRES_DEL_ENGINE]
