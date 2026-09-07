"""Camelot wheel utilities."""
from typing import Tuple, Optional


def parse(camelot: str) -> Optional[Tuple[int, int]]:
    """Parse '8A' → (8, 0), '12B' → (12, 1). Returns None if invalid."""
    if not camelot or camelot == '?':
        return None
    try:
        num = int(''.join(c for c in camelot if c.isdigit()))
        if not 1 <= num <= 12:
            return None
        letter = 0 if 'A' in camelot.upper() else 1
        return (num, letter)
    except (ValueError, IndexError):
        return None


def distance(k1: str, k2: str) -> int:
    """Camelot wheel distance: minimal hops including modal switch."""
    n1 = parse(k1)
    n2 = parse(k2)
    if not n1 or not n2:
        return 99
    wheel = min(abs(n1[0] - n2[0]), 12 - abs(n1[0] - n2[0]))
    modal = 0 if n1[1] == n2[1] else 1
    return wheel + modal


def is_compatible(k1: str, k2: str, max_jump: int = 1) -> bool:
    """True if Camelot move is within max_jump (default ±1 wheel hop)."""
    return distance(k1, k2) <= max_jump


def greedy_order(start_key: str, candidates: list[dict], key_field: str = 'key') -> list[dict]:
    """Order candidates greedy by Camelot proximity from start_key.

    Each candidate must have key_field. Returns ordered list.
    """
    remaining = list(candidates)
    ordered = []
    current = start_key
    while remaining:
        remaining.sort(key=lambda c: distance(current, c.get(key_field, '?')))
        pick = remaining.pop(0)
        ordered.append(pick)
        current = pick.get(key_field, current)
    return ordered


# -- Conversion desde notacion musical -------------------------------------
# Los setlists de referencia (1001tracklists, Muzpa, Beatport) vienen en
# notacion musical, no en Camelot. Sin esta tabla el backtest no puede medir
# las transiciones de Digweed contra la regla de Camelot.
_MINOR = {"G#": "1A", "Ab": "1A", "D#": "2A", "Eb": "2A", "A#": "3A", "Bb": "3A",
          "F": "4A", "C": "5A", "G": "6A", "D": "7A", "A": "8A", "E": "9A",
          "B": "10A", "F#": "11A", "Gb": "11A", "C#": "12A", "Db": "12A"}
_MAJOR = {"B": "1B", "F#": "2B", "Gb": "2B", "C#": "3B", "Db": "3B",
          "G#": "4B", "Ab": "4B", "D#": "5B", "Eb": "5B", "A#": "6B", "Bb": "6B",
          "F": "7B", "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B"}


def from_musical(key: str) -> Optional[str]:
    """'Bm' -> '10A', 'Ab' -> '4B', 'F# min' -> '11A'. None si no parsea.

    Acepta: 'Am', 'A min', 'A minor', 'A', 'Amaj', 'A major', con # o b.
    Si ya viene en Camelot ('8A') lo devuelve tal cual.
    """
    if not key:
        return None
    k = key.strip()
    if parse(k) and any(c.isdigit() for c in k):
        return k.upper()
    k = k.replace("-", " ").strip()
    low = k.lower()
    es_menor = (
        low.endswith("m") and not low.endswith("maj")
        or "min" in low
    )
    raiz = k[0].upper()
    if len(k) > 1 and k[1] in "#b":
        raiz += k[1] if k[1] == "#" else "b"
    tabla = _MINOR if es_menor else _MAJOR
    return tabla.get(raiz)
