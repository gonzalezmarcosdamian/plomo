"""
Set Builder v2 — tres mejoras sobre el algoritmo greedy original.

Mejora 1: Tracks ancla
  El DJ marca 2-3 tracks como anclas del set. El algoritmo los ubica
  en los picos de cada movimiento y construye el resto a su alrededor.

Mejora 2: Movimientos (actos)
  El set se divide en 2-3 movimientos con arcos de energía independientes.
  Cada movimiento tiene su propio ramp-up, plateau y release.
  Los movimientos se conectan con tracks "pivote".

Mejora 3: Score de compatibilidad de transición
  Registra pares de tracks que funcionaron mal/bien en vivo.
  Penaliza las transiciones conocidas como problemáticas al ordenar.
"""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .camelot import distance as camelot_dist
from .energy import reorder_by_energy_and_camelot

FEEDBACK_FILE = Path(__file__).parent.parent.parent / "transition_feedback.json"


# ─────────────────────────────────────────────────────────────────────────────
# Tipos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Movement:
    """Un acto del set con su propio arco de energía."""
    name: str
    energy_start: float
    energy_peak: float
    energy_end: float
    duration_pct: float       # fracción del set total (0.0-1.0)
    anchor_ids: list[str] = field(default_factory=list)  # tracks ancla en este movimiento


@dataclass
class SetConfig:
    """Configuración completa de un set."""
    name: str
    movements: list[Movement]
    anchor_ids: list[str] = field(default_factory=list)  # anclas globales

    @classmethod
    def progressive_3h(cls, name: str) -> "SetConfig":
        """Arco estándar de 3 horas de progressive house."""
        return cls(
            name=name,
            movements=[
                Movement("Entrada",   2.0, 5.0, 3.5, 0.30),
                Movement("Meseta",    4.0, 7.5, 6.0, 0.45),
                Movement("Cierre",    6.0, 8.0, 5.0, 0.25),
            ]
        )

    @classmethod
    def romantic_1h(cls, name: str) -> "SetConfig":
        """Arco suave de 1 hora romántico/orgánico."""
        return cls(
            name=name,
            movements=[
                Movement("Ambient",  1.0, 3.5, 2.0, 0.40),
                Movement("Calido",   2.5, 5.5, 3.5, 0.40),
                Movement("Cierre",   3.0, 4.5, 1.5, 0.20),
            ]
        )

    @classmethod
    def techno_2h(cls, name: str) -> "SetConfig":
        """Arco de 2 horas de techno/peak."""
        return cls(
            name=name,
            movements=[
                Movement("Entrada",  6.0, 7.5, 6.5, 0.35),
                Movement("Peak",     7.0, 9.0, 7.5, 0.50),
                Movement("Cierre",   7.0, 8.0, 6.0, 0.15),
            ]
        )


# ─────────────────────────────────────────────────────────────────────────────
# Feedback de transiciones
# ─────────────────────────────────────────────────────────────────────────────

def load_feedback() -> dict:
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text())
    return {}


def save_feedback(feedback: dict) -> None:
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2))


def record_transition(from_id: str, to_id: str, score: int, note: str = "") -> None:
    """
    Registra feedback de una transición.
    score: -2 choca fuerte, -1 incómoda, 0 neutral, +1 buena, +2 perfecta
    """
    feedback = load_feedback()
    key = f"{from_id}→{to_id}"
    feedback[key] = {"score": score, "note": note, "from": from_id, "to": to_id}
    save_feedback(feedback)
    print(f"Feedback registrado: {key} = {score} ({note})")


def transition_penalty(from_id: str, to_id: str, feedback: dict) -> float:
    """Penalización por transición conocida como problemática. 0=neutral, >0=malo."""
    key = f"{from_id}→{to_id}"
    if key in feedback:
        score = feedback[key]["score"]
        if score < 0:
            return abs(score) * 2.0  # penalizar transitions negativas
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Builder principal
# ─────────────────────────────────────────────────────────────────────────────

def _target_energy_for_movement(position: float, mov: Movement) -> float:
    """
    Energía objetivo en una posición (0-1) dentro del movimiento.
    Curva: sube hasta 0.70, luego baja.
    """
    peak_pos = 0.70
    if position <= peak_pos:
        t = position / peak_pos
        return mov.energy_start + t * (mov.energy_peak - mov.energy_start)
    else:
        t = (position - peak_pos) / (1 - peak_pos)
        return mov.energy_peak - t * (mov.energy_peak - mov.energy_end)


def _assign_tracks_to_movement(
    tracks: list[dict],
    movement: Movement,
    n_tracks: int,
    feedback: dict,
) -> list[dict]:
    """
    Asigna n_tracks al movimiento respetando anclas, energía objetivo y
    feedback de transiciones.
    """
    if not tracks:
        return []

    # Separar anclas del movimiento
    anchors = [t for t in tracks if t["id"] in movement.anchor_ids]
    pool = [t for t in tracks if t not in anchors]

    # Posición pico: donde van las anclas
    anchor_position = 0.70

    # Calcular posiciones objetivo de energía para n_tracks
    target_energies = [
        _target_energy_for_movement(i / max(n_tracks - 1, 1), movement)
        for i in range(n_tracks)
    ]

    ordered = []
    remaining = list(pool)

    # Colocar anclas en la posición de pico
    if anchors:
        anchor_slot = int(anchor_position * n_tracks)
        # Antes del ancla: tracks con energía ascendente
        pre_count = anchor_slot
        post_count = n_tracks - anchor_slot - len(anchors)

        pre_pool = sorted(remaining, key=lambda t: t["energy"])[:pre_count * 2]
        ordered_pre = _greedy_order(pre_pool[:pre_count], feedback)

        post_pool = sorted(remaining, key=lambda t: -t["energy"])[:post_count * 2]
        ordered_post = _greedy_order(post_pool[:post_count], feedback,
                                      start_key=anchors[-1]["key"] if anchors else None)

        ordered = ordered_pre + anchors + ordered_post
    else:
        # Sin anclas: ordenar por energía objetivo + camelot
        ordered = _greedy_energy_camelot(remaining[:n_tracks], target_energies, feedback)

    return ordered[:n_tracks]


def _greedy_order(tracks: list[dict], feedback: dict,
                   start_key: Optional[str] = None) -> list[dict]:
    """Greedy por Camelot con penalización de transiciones conocidas."""
    if not tracks:
        return []
    remaining = list(tracks)
    remaining.sort(key=lambda t: t["energy"])
    ordered = [remaining.pop(0)]
    while remaining:
        current = ordered[-1]
        current_key = current["key"]
        current_id = current["id"]

        def score_next(t: dict) -> float:
            cam = camelot_dist(current_key, t["key"])
            bpm_diff = abs(current["bpm"] - t["bpm"]) / 2
            penalty = transition_penalty(current_id, t["id"], feedback)
            return cam * 3.0 + bpm_diff + penalty * 2.0

        remaining.sort(key=score_next)
        ordered.append(remaining.pop(0))
    return ordered


def _greedy_energy_camelot(tracks: list[dict], target_energies: list[float],
                            feedback: dict) -> list[dict]:
    """Greedy combinando energía objetivo y Camelot."""
    remaining = list(tracks)
    remaining.sort(key=lambda t: t["energy"])
    if not remaining:
        return []
    ordered = [remaining.pop(0)]
    pos = 1
    while remaining and pos < len(target_energies):
        target = target_energies[pos]
        current = ordered[-1]

        def combined_score(t: dict) -> float:
            cam = camelot_dist(current["key"], t["key"])
            energy_dev = abs(t["energy"] - target)
            bpm_diff = abs(current["bpm"] - t["bpm"]) / 2
            penalty = transition_penalty(current["id"], t["id"], feedback)
            return cam * 3.0 + energy_dev * 1.5 + bpm_diff + penalty * 2.0

        remaining.sort(key=combined_score)
        ordered.append(remaining.pop(0))
        pos += 1
    return ordered


def build_set(tracks: list[dict], config: SetConfig) -> list[dict]:
    """
    Construye un set completo según la configuración de movimientos y anclas.

    tracks: lista de dicts con keys: id, artist, title, bpm, key, energy
    config: SetConfig con movimientos y anclas globales
    """
    feedback = load_feedback()
    n_total = len(tracks)

    # Distribuir tracks entre movimientos según duration_pct
    result = []
    used_ids = set()

    for mov_idx, movement in enumerate(config.movements):
        # Número de tracks para este movimiento
        n_mov = max(2, round(n_total * movement.duration_pct))
        if mov_idx == len(config.movements) - 1:
            # Último movimiento: todos los que queden
            n_mov = n_total - len(result)

        # Pool disponible (no usados + anclas del movimiento)
        available = [t for t in tracks if t["id"] not in used_ids]

        ordered_mov = _assign_tracks_to_movement(available, movement, n_mov, feedback)

        for t in ordered_mov:
            used_ids.add(t["id"])
        result.extend(ordered_mov)

    # Añadir tracks no usados al final
    leftover = [t for t in tracks if t["id"] not in used_ids]
    result.extend(leftover)

    return result
