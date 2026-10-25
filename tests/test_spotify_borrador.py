# -*- coding: utf-8 -*-
"""Lo que decide si un candidato de Spotify entra a la lista mientras se itera.

Spotify ya no da BPM, key ni energia: el filtro de mezcla corre con lo que dice
Muzpa. Un error aca mete un tema que no mezcla con sus vecinos, y el DJ lo
escucha como un salto.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from spotify_borrador import genero_ok, mezcla_ok, puntaje  # noqa: E402


@pytest.mark.unit
class TestMezclaOk:
    VECINOS = [{"key": "6A", "bpm": 120}, {"key": "7A", "bpm": 123}]

    def test_mezcla_con_los_dos(self):
        assert mezcla_ok("6A", 121, self.VECINOS)

    def test_rueda_de_dos_no_entra(self):
        assert not mezcla_ok("8A", 121, self.VECINOS)

    def test_bpm_de_mas_de_dos_contra_un_vecino_no_entra(self):
        # 124 esta a 1 de 123 pero a 4 de 120.
        assert not mezcla_ok("6A", 124, self.VECINOS)

    def test_sin_dato_de_muzpa_no_entra(self):
        # Sin key o sin BPM no se puede saber si mezcla: mejor no proponerlo.
        assert not mezcla_ok(None, 121, self.VECINOS)
        assert not mezcla_ok("6A", None, self.VECINOS)

    def test_vecino_sin_dato_no_bloquea(self):
        assert mezcla_ok("6A", 121, [{"key": None, "bpm": None}])

    def test_primer_lugar_tiene_un_solo_vecino(self):
        assert mezcla_ok("4A", 122, [{"key": "4A", "bpm": 123}])


@pytest.mark.unit
class TestPuntaje:
    def test_la_coaparicion_pesa_mas_que_el_nombre(self):
        en_playlists = {"coaparicion": 1}
        del_mismo_sello_y_artista = {"por_sello": 1, "por_artista": 1}
        assert puntaje(en_playlists) > puntaje(del_mismo_sello_y_artista)

    def test_la_voz_probable_resta(self):
        # Es una lista para trabajar: "feat." o "Vocal Mix" en el titulo baja al candidato.
        assert puntaje({"coaparicion": 1, "voz_probable": True}) < puntaje({"coaparicion": 1})


@pytest.mark.unit
class TestGeneroOk:
    @pytest.mark.parametrize("cat", ["Organic House / Downtempo", "Progressive House", "Melodic House/Techno"])
    def test_generos_del_mundo_del_set(self, cat):
        assert genero_ok(cat)

    @pytest.mark.parametrize("cat", ["Techno (Peak Time/Driving/Hard)", "Trance", "Tech House", "", None])
    def test_fuera_del_set(self, cat):
        assert not genero_ok(cat)


@pytest.mark.unit
class TestSelloDeCopyright:
    # Spotify saco `label` del album en 2026: el sello sale del copyright.
    @pytest.mark.parametrize("texto,sello", [
        ("(C) 2026 Closure", "Closure"),
        ("℗ 2025 All Day I Dream", "All Day I Dream"),
        ("2024 Univack", "Univack"),
        ("(P) 2023 Enormous Tunes, A Division Of GNKP", "Enormous Tunes"),
    ])
    def test_saca_simbolo_anio_y_division(self, texto, sello):
        from spotify_borrador import sello_de_copyright
        assert sello_de_copyright([{"text": texto}]) == sello

    def test_sin_copyright(self):
        from spotify_borrador import sello_de_copyright
        assert sello_de_copyright([]) is None
