# -*- coding: utf-8 -*-
"""La energia del comentario de Rekordbox tiene que salir con o sin etiqueta.

El comentario real es "E:7.9 [peak] | v1:7.0". El parseo viejo hacia
split("|")[0] menos "E:", quedaba "7.9 [peak]", float() fallaba y el tema caia
a un proxy por BPM. Los etiquetados [mid] y [peak] son justamente los que el DJ
mas trabajo, asi que el error pegaba donde mas dolia.
"""
import re

import pytest

# el mismo patron que usa scripts/build_set.py
PATRON = r"E:\s*([0-9]+(?:\.[0-9]+)?)"


def energia(comentario: str) -> float | None:
    m = re.search(PATRON, comentario)
    return float(m.group(1)) if m else None


@pytest.mark.parametrize("comentario, esperado", [
    ("E:7.9 [peak] | v1:7.0", 7.9),          # el caso que fallaba
    ("E:6.6 [mid] | v1:6.1", 6.6),           # idem
    ("E:5.6", 5.6),                          # el que si andaba
    ("E: 8.0", 8.0),                         # con espacio
    ("E:10 [peak]", 10.0),                   # entero, sin decimales
])
def test_saca_la_energia_del_comentario(comentario, esperado):
    assert energia(comentario) == esperado


def test_sin_energia_devuelve_none():
    assert energia("") is None
    assert energia("solo una nota del DJ") is None


def test_el_parseo_viejo_fallaba_con_etiqueta():
    # se deja documentado el bug para que no vuelva por otro camino
    viejo = "E:7.9 [peak] | v1:7.0".split("|")[0].replace("E:", "").strip()
    with pytest.raises(ValueError):
        float(viejo)
