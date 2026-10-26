# -*- coding: utf-8 -*-
"""La receta de cada Session de paisajes: que la 05 no pise a la 04 y que ningun tema quede sin etapa."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import naturaleza  # noqa: E402
from naturaleza import ETAPAS, FRASE, MIN_PLANO, etapa_de, receta  # noqa: E402


@pytest.mark.unit
class TestReceta:
    def test_sin_archivo_es_la_receta_de_la_04(self, tmp_path, monkeypatch):
        monkeypatch.setattr(naturaleza, "RAIZ", tmp_path)
        assert receta("session_04") == {"frase": FRASE, "min_plano": MIN_PLANO, "etapas": ETAPAS}

    def test_el_archivo_pisa_frase_plano_y_etapas(self, tmp_path, monkeypatch):
        (tmp_path / "data" / "video").mkdir(parents=True)
        (tmp_path / "data" / "video" / "session_09_recorrido.json").write_text(json.dumps(
            {"frase": 32, "min_plano": 24, "etapas": [{"nombre": "Tarde", "temas": [0, 1], "luz": "[A]"}]}),
            encoding="utf-8")
        monkeypatch.setattr(naturaleza, "RAIZ", tmp_path)
        assert receta("session_09") == {"frase": 32, "min_plano": 24, "etapas": [("Tarde", (0, 1), "[A]")]}

    def test_la_05_cubre_los_17_temas_una_vez_cada_uno(self):
        temas = [k for _, ts, _ in receta("session_05")["etapas"] for k in ts]
        assert sorted(temas) == list(range(17))


@pytest.mark.unit
class TestEtapaDe:
    def test_numera_desde_uno(self):
        assert etapa_de(0, ETAPAS) == 1
        assert etapa_de(15, ETAPAS) == 6

    def test_tema_sin_etapa_corta_con_el_motivo(self):
        with pytest.raises(SystemExit, match="tema 16"):
            etapa_de(16, ETAPAS)
