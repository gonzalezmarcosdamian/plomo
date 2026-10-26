# -*- coding: utf-8 -*-
"""El lector del pen: lo que se usa para verificar que el pen quedo igual que la PC."""
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from read_pen_playlists import arbol, cadena  # noqa: E402


@pytest.mark.unit
class TestCadena:
    def test_corta_ascii(self):
        assert cadena(b"\x09abc", 0) == "abc"

    def test_larga_utf16_con_tildes(self):
        txt = "Sesión · Melódico".encode("utf-16-le")
        b = b"\x90" + struct.pack("<H", len(txt) + 4) + b"\x00" + txt
        assert cadena(b, 0) == "Sesión · Melódico"

    def test_larga_ascii(self):
        txt = b"Pro DJ Library"
        assert cadena(b"\x40" + struct.pack("<H", len(txt) + 4) + b"\x00" + txt, 0) == "Pro DJ Library"


@pytest.mark.unit
class TestArbol:
    # pid: (nombre, padre, es_carpeta, orden)
    LISTAS = {
        1: ("Pro DJ Library", 0, True, 1),
        2: ("Sessions", 0, True, 0),
        3: ("Sets Armados", 1, True, 0),
        4: ("159. Work", 3, False, 0),
        5: ("Session 01", 2, False, 0),
        6: ("Sunset", 2, False, 1),
    }

    def test_orden_del_pen_e_indentado(self):
        entradas = {5: [(1, 10), (2, 11)], 6: [(1, 12)], 4: [(1, 12)]}
        assert arbol(self.LISTAS, entradas) == [
            "Sessions",
            "  Session 01  (2)",
            "  Sunset  (1)",
            "Pro DJ Library",
            "  Sets Armados",
            "    159. Work  (1)",
        ]

    def test_lista_vacia_muestra_cero(self):
        assert "  Sunset  (0)" in arbol(self.LISTAS, {})

    def test_una_carpeta_que_se_contiene_no_cuelga(self):
        assert arbol({1: ("Loop", 1, True, 0)}, {}, padre=1) == []
