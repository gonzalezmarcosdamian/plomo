"""
Energy score calculation for DJ tracks.

Score 0-10 based on cue timing analysis:
- BPM weight
- Intro tightness (how fast the bass kicks in)
- Breakdown tension (duration of breakdown before drop)
- Peak section length (post-drop energy)
- Drop presence bonus

Scale:
  0-2  → Warmup / ambient / cena
  3-4  → Build / early set
  5-6  → Mid set / progressive groove
  7-8  → Peak zone
  9-10 → Peak+ / peak hour
"""
from __future__ import annotations


def calculate_energy(
    bpm: float,
    bass_in_ms: int | None,
    breakdown_ms: int | None,
    drop_ms: int | None,
    outro_ms: int | None,
    track_length_ms: int | None,
) -> float:
    score = 0.0

    # BPM component (0-3): 118→0, 126→3
    bpm_score = min(3.0, max(0.0, (bpm - 118) / 8 * 3))
    score += bpm_score

    # Intro tightness (0-2): bass kicks in fast = energetic
    if bass_in_ms is not None and bass_in_ms > 100:
        intro_s = bass_in_ms / 1000
        # 0s→2pts, 30s→1.5pts, 60s→1pt, 120s→0pts
        intro_score = max(0.0, 2.0 - intro_s / 60)
        score += intro_score
    else:
        score += 1.0  # unknown = neutral

    # Breakdown tension (0-2.5): longer breakdown = more tension/release
    if breakdown_ms is not None and drop_ms is not None and drop_ms > breakdown_ms:
        breakdown_dur_s = (drop_ms - breakdown_ms) / 1000
        # 30s→0.8, 60s→1.5, 90s→2.0, 120s→2.5
        breakdown_score = min(2.5, breakdown_dur_s / 48)
        score += breakdown_score
    elif breakdown_ms is None and drop_ms is None:
        pass  # no breakdown/drop = ambient, no bonus

    # Drop presence bonus (0-1)
    if drop_ms is not None:
        score += 1.0

    # Peak section length (0-1.5): long post-drop section = high energy
    if drop_ms is not None and outro_ms is not None and outro_ms > drop_ms:
        peak_dur_s = (outro_ms - drop_ms) / 1000
        # 60s→0.5, 120s→1.0, 180s→1.5
        peak_score = min(1.5, peak_dur_s / 120)
        score += peak_score

    return round(min(10.0, max(0.0, score)), 1)


def energy_label(score: float) -> str:
    if score < 2.5:
        return "ambient"
    elif score < 4.0:
        return "warmup"
    elif score < 5.5:
        return "build"
    elif score < 7.0:
        return "mid"
    elif score < 8.5:
        return "peak"
    else:
        return "peak+"


def reorder_by_energy_and_camelot(
    tracks: list[dict],
    key_field: str = "key",
    energy_field: str = "energy",
    bpm_field: str = "bpm",
) -> list[dict]:
    """
    Reorder tracks optimizing both Camelot flow and energy progression.

    Energy target curve: ramp up to 75% of set, slight cool-down at end.
    Each step penalizes:
    - Camelot distance > 1 hop
    - Deviation from target energy at that position
    - BPM jumps > 3 BPM
    """
    from .camelot import distance as camelot_distance

    if not tracks:
        return tracks

    n = len(tracks)
    remaining = list(tracks)
    ordered = []

    # Energy target at position i (0-indexed): ramp to 75%, cool to end
    def target_energy(i: int) -> float:
        t = i / max(n - 1, 1)
        peak_t = 0.75
        if t <= peak_t:
            return 2.0 + (t / peak_t) * 6.0   # 2→8
        else:
            decay = (t - peak_t) / (1 - peak_t)
            return 8.0 - decay * 3.0            # 8→5

    # Start with lowest energy track
    remaining.sort(key=lambda t: t.get(energy_field, 5))
    current = remaining.pop(0)
    ordered.append(current)

    while remaining:
        pos = len(ordered)
        te = target_energy(pos)

        def score(candidate: dict) -> float:
            cam = camelot_distance(
                current.get(key_field, "?"),
                candidate.get(key_field, "?")
            )
            energy_dev = abs(candidate.get(energy_field, 5) - te)
            bpm_dev = abs(candidate.get(bpm_field, 122) - current.get(bpm_field, 122)) / 2
            # weights: camelot most important, then energy, then bpm
            return cam * 3.0 + energy_dev * 1.5 + bpm_dev

        remaining.sort(key=score)
        current = remaining.pop(0)
        ordered.append(current)

    return ordered
