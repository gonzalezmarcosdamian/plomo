"""Tests for Camelot wheel utilities."""
import pytest
from plomo.camelot import parse, distance, is_compatible, greedy_order


def test_parse_valid():
    assert parse('8A') == (8, 0)
    assert parse('12B') == (12, 1)
    assert parse('1a') == (1, 0)


def test_parse_invalid():
    assert parse('?') is None
    assert parse('') is None
    assert parse('13A') is None


def test_distance_same_key():
    assert distance('8A', '8A') == 0


def test_distance_modal_switch():
    assert distance('8A', '8B') == 1


def test_distance_wheel_hop():
    assert distance('8A', '9A') == 1
    assert distance('12A', '1A') == 1  # wrap-around


def test_distance_long_jump():
    assert distance('1A', '6A') == 5


def test_is_compatible():
    assert is_compatible('8A', '9A')  # +1
    assert is_compatible('8A', '8B')  # modal
    assert not is_compatible('1A', '5A')  # +4


def test_greedy_order():
    candidates = [
        {'key': '5A'},
        {'key': '9A'},
        {'key': '8A'},
        {'key': '7A'},
    ]
    ordered = greedy_order('8A', candidates)
    keys = [c['key'] for c in ordered]
    # From 8A, closest is 8A (dist 0) but no, no candidate is 8A starting...
    # 8A → 7A or 9A (dist 1) → next closest
    assert keys[0] in ('7A', '9A', '8A')
