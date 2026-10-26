# -*- coding: utf-8 -*-
"""El nombre de cada copia en la carpeta Sessions: lo que el DJ ve en el CDJ."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from armar_sessions import concepto, nombre_lista  # noqa: E402


@pytest.mark.unit
class TestConcepto:
    def test_saca_numero_duracion_y_fecha(self):
        assert concepto("148. Housero Progresivo · 1 a 3 AM — 2h — 2026-09-28") == "Housero Progresivo · 1 a 3 AM"

    def test_no_repite_session_si_el_set_ya_la_dice(self):
        # El 153 y el 157 se llaman "Session 03 · ..." y "Session 04 · ...": la
        # etiqueta la pone la copia, no hay que verla dos veces.
        assert concepto("153. Session 03 · Cumple del 20 — 1h40 — 2026-10-19") == "Cumple del 20"

    def test_nombre_sin_duracion(self):
        assert concepto("150. Sostenido") == "Sostenido"


@pytest.mark.unit
def test_nombre_lista_lleva_etiqueta_y_numero():
    # El numero entre parentesis es como el script reencuentra la copia la proxima vez.
    assert nombre_lista("Sunset", 159, "159. Work · Organic con brillo — 2h — 2026-10-25") \
        == "Sunset · Work · Organic con brillo (159)"
