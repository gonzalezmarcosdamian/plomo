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
