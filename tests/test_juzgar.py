"""Test de `variacion()`, la metrica que cerro la dimension "variacion por
compas" en la vuelta 3 (0.64 -> 0.84 -> 1.06, adentro de 0.85-2.50).

Con ruido sintetico, no con un render: no hay Live en esta sesion para
producir un render propio, y las referencias son mp3 personales fuera del
repo. Lo que se puede verificar sin ninguno de los dos es que el INSTRUMENTO
mide lo que dice medir: compases identicos dan variacion 0, compases
distintos dan variacion mayor que cero. Si esto se rompiera, "1.06 adentro de
rango" dejaria de significar nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from juzgar import BPM, variacion  # noqa: E402

SR = 22050


@pytest.mark.unit
class TestVariacion:
    def test_compases_identicos_dan_variacion_cero(self) -> None:
        x = int(round(SR * 4 * 60.0 / BPM))
        rng = np.random.default_rng(0)
        compas = rng.standard_normal(x) * 0.1
        y = np.tile(compas, 16)
        assert variacion(y, BPM) == 0.0

    def test_compases_distintos_dan_variacion_mayor_que_cero(self) -> None:
        x = int(round(SR * 4 * 60.0 / BPM))
        rng = np.random.default_rng(0)
        y = np.concatenate([rng.standard_normal(x) * 0.1 for _ in range(16)])
        assert variacion(y, BPM) > 0.3

    def test_menos_de_cuatro_compases_devuelve_cero_sin_romper(self) -> None:
        x = int(round(SR * 4 * 60.0 / BPM))
        y = np.zeros(x * 2)
        assert variacion(y, BPM) == 0.0
