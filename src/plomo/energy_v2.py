"""
Energy Score v2 — mejoras sobre v1.0

v1.1: bass_in=0 penalizado (no es "entra inmediatamente", es "no detectado")
v1.2: BPM de 30% → 15% del score total
v1.3: groove_ratio — fracción del track con kick activo (ancla vs flotante)
"""
from __future__ import annotations
import numpy as np


def calculate_energy_v2(
    bpm: float,
    bass_in_ms: int | None,
    breakdown_ms: int | None,
    drop_ms: int | None,
    outro_ms: int | None,
    track_length_ms: int | None,
    groove_ratio: float | None = None,
) -> float:

    score = 0.0

    # v1.2 — BPM: max 1.5 pts (antes 3.0)
    bpm_score = min(1.5, max(0.0, (bpm - 118) / 12 * 1.5))
    score += bpm_score

    # v1.1 — Intro: bass_in=0 o None → penalizar
    if bass_in_ms is not None and bass_in_ms > 500:
        intro_score = max(0.0, 2.0 - (bass_in_ms / 1000) / 60)
    elif bass_in_ms is None or bass_in_ms <= 100:
        intro_score = 0.3   # no detectado o ruido → penalizar
    else:
        intro_score = 1.0   # neutral
    score += intro_score

    # Breakdown tension (sin cambios)
    if breakdown_ms is not None and drop_ms is not None and drop_ms > breakdown_ms:
        breakdown_dur_s = (drop_ms - breakdown_ms) / 1000
        score += min(2.5, breakdown_dur_s / 48)

    # Drop presence (sin cambios)
    if drop_ms is not None:
        score += 1.0

    # Peak section (sin cambios)
    if drop_ms is not None and outro_ms is not None and outro_ms > drop_ms:
        peak_dur_s = (outro_ms - drop_ms) / 1000
        score += min(1.5, peak_dur_s / 120)

    # v1.3 — Groove ratio: 0-2 pts
    if groove_ratio is not None:
        score += min(2.0, groove_ratio * 2.5)

    return round(min(10.0, max(0.0, score)), 1)


def compute_groove_ratio(path: str, bpm: float) -> float:
    """
    Fracción del track con kick activo. 0=flotante, 1=anclado.
    Threshold: 70% de la media del kick — separa breakdowns (silencio)
    de secciones con groove real sin depender del percentile.
    """
    import librosa
    from scipy.signal import butter, filtfilt

    y, sr = librosa.load(path, sr=None, mono=True)
    hop = 512
    bar_s = 4 * 60 / bpm
    b, a = butter(4, [60 / (sr / 2), 200 / (sr / 2)], btype='band')
    y_kick = filtfilt(b, a, y)
    kick_rms = librosa.feature.rms(y=y_kick, hop_length=hop)[0]
    bar_frames = int(bar_s * sr / hop)
    n = len(kick_rms) // bar_frames
    kpb = np.array([kick_rms[i * bar_frames:(i + 1) * bar_frames].mean()
                    for i in range(n)])
    # Threshold absoluto: 70% de la media — bars en breakdown quedan muy por debajo
    threshold = np.mean(kpb) * 0.70
    return float((kpb > threshold).sum() / len(kpb))
