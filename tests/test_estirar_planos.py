"""Tests de scripts/estirar_planos.py: las cuentas, sin ffmpeg ni RIFE."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import estirar_planos as ep  # noqa: E402


def test_cuadros_necesarios_suma_el_margen_de_naturaleza():
    assert ep.cuadros_necesarios(62.97) == 1920  # (62.97 + 1) * 30 = 1919.1 -> 1920


def test_un_clip_de_60_fps_alcanza_sin_inventar():
    assert ep.modo(n_in=3600, n_out=2000) == "reales"


def test_un_clip_corto_va_con_rife():
    assert ep.modo(n_in=1200, n_out=2400) == "rife"


def test_mas_de_x3_no_se_estira():
    with pytest.raises(ValueError, match="mas largo"):
        ep.modo(n_in=600, n_out=2400)


def test_nombre_del_estirado():
    assert ep.nombre_estirado("session_05", 7, 168620) == "s05_007_168620.mp4"
