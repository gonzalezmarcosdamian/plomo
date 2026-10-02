# -*- coding: utf-8 -*-
"""El cruce del historial es por nombre, asi que normalizar es lo que decide."""
from plomo.tocados import normalizar


def test_ignora_mayusculas_y_puntuacion():
    assert normalizar("Sinking Sky") == normalizar("sinking  sky")
    assert normalizar("Midnight Current (Original Mix)") == "midnightcurrentoriginalmix"


def test_ignora_acentos():
    # Fejka, Sebastien Leger y companhia vienen con tilde desde Rekordbox y sin
    # tilde desde el nombre de archivo. Si no se igualan, el historial no cruza.
    assert normalizar("Fejká") == normalizar("Fejka")
    assert normalizar("Sébastien Léger") == normalizar("Sebastien Leger")


def test_el_remixer_sigue_contando():
    # Dos versiones del mismo tema NO son el mismo tema: el DJ puede haber
    # tocado una y no la otra, y meterle la que toco es el error que esto evita.
    assert normalizar("Low Era (Original Mix)") != normalizar("Low Era (Kebin Van Reeken Remix)")


def test_vacio_no_rompe():
    assert normalizar("") == ""
    assert normalizar(None) == ""
