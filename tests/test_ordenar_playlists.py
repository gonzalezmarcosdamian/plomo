# -*- coding: utf-8 -*-
"""El orden del arbol de Rekordbox: lo que el DJ recorre en el CDJ para llegar a un set."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ordenar_playlists import camelot, numero_set, ordenar  # noqa: E402


def _ids(nombres):
    return [(str(i), n) for i, n in enumerate(nombres)]


def _nombres(hijos, orden):
    d = dict(hijos)
    return [d[i] for i in orden]


@pytest.mark.unit
class TestSets:
    def test_fechas_arriba_nuevos_primero_pool_al_final(self):
        h = _ids(["[POOL]", "0 Fechas", "148. A — 2h", "155. B — 2h", "153. C — 1h", "159. D — 2h"])
        assert _nombres(h, ordenar(h, "sets")) == ["0 Fechas", "159. D — 2h", "155. B — 2h",
                                                    "153. C — 1h", "148. A — 2h", "[POOL]"]

    def test_numero_set(self):
        assert numero_set("153. Session 03 · Cumple del 20") == 153
        assert numero_set("[POOL]") is None


@pytest.mark.unit
class TestCamelot:
    def test_orden_musical_no_alfabetico(self):
        # Alfabetico daba 10A, 10B, 11A, 12A, 1A...
        h = _ids(["10A", "1B", "12B", "1A", "2A", "10B"])
        assert _nombres(h, ordenar(h, "camelot")) == ["1A", "1B", "2A", "10A", "10B", "12B"]

    def test_lo_que_no_es_key_va_al_final(self):
        assert camelot("Sin key") > camelot("12B")


@pytest.mark.unit
class TestListaFija:
    def test_prefijos_en_orden_y_el_resto_atras_estable(self):
        regla = ["Session 01", "Session 02", "Sunset"]
        h = _ids(["Sunset · X (159)", "Otra", "Session 02 · B (150)", "Session 01 · A (148)", "Tercera"])
        assert _nombres(h, ordenar(h, regla)) == ["Session 01 · A (148)", "Session 02 · B (150)",
                                                  "Sunset · X (159)", "Otra", "Tercera"]

    def test_nombre_exacto(self):
        h = _ids(["MI SONIDO", "Pro DJ Library", "Sessions"])
        assert _nombres(h, ordenar(h, ["Sessions", "Pro DJ Library", "MI SONIDO"])) == \
            ["Sessions", "Pro DJ Library", "MI SONIDO"]

    def test_sin_tilde_no_matchea_con_tilde(self):
        # "Por Posicion de Set" (la que tiene listas) y "Por Posición de Set" (vacia)
        # son dos carpetas distintas: la regla nombra la que se queda.
        h = _ids(["Por Posición de Set", "Por Posicion de Set"])
        assert _nombres(h, ordenar(h, ["Por Posicion de Set"]))[0] == "Por Posicion de Set"
