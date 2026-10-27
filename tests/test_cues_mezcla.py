# -*- coding: utf-8 -*-
"""Los cues salen de la estructura de la mezcla: caen en los compases de la grilla, no en el reloj."""
import sqlite3

import numpy as np
import pytest

from plomo.cues_mezcla import NOMBRES_DEL_ENGINE, cues_a_mano, cues_de_estructura
from plomo.mezcla import Estructura

COMPASES = 0.37 + np.arange(200) * 1.967     # la grilla arranca en 0.37 s, no en 0


def _e(breakdown=(64, 80), drop=80):
    return Estructura(bombo=np.ones(200), bajo=np.ones(200), bass_in=16, fin_bombo=128,
                      breakdown=breakdown, drop=drop)


@pytest.mark.unit
class TestCuesDeEstructura:
    def test_cada_cue_cae_en_su_compas_de_la_grilla(self):
        c = cues_de_estructura(COMPASES, _e())
        assert c.first_beat == pytest.approx(COMPASES[0])
        assert c.bass_in == pytest.approx(COMPASES[16])
        assert c.breakdown == pytest.approx(COMPASES[64])
        assert c.drop == pytest.approx(COMPASES[80])
        assert c.outro == pytest.approx(COMPASES[112])      # mix_out: 16 antes del fin del bombo

    def test_sin_breakdown_no_hay_breakdown_ni_drop_ni_medio(self):
        c = cues_de_estructura(COMPASES, _e(breakdown=None, drop=None), medios=np.ones(200))
        assert c.breakdown is None and c.drop is None and c.drop_mid is None

    def test_el_medio_cae_en_frase_entre_el_drop_y_el_mix_out(self):
        c = cues_de_estructura(COMPASES, _e(), medios=np.ones(200))
        assert c.drop_mid == pytest.approx(COMPASES[96])

    def test_sin_medios_no_hay_medio(self):
        assert cues_de_estructura(COMPASES, _e()).drop_mid is None


@pytest.mark.unit
class TestCuesAMano:
    def _con(self, filas):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE djmdCue (ContentID TEXT, Comment TEXT, InMsec INT, rb_local_deleted INT)")
        con.executemany("INSERT INTO djmdCue VALUES ('7', ?, ?, ?)", filas)
        return con

    def test_los_del_engine_no_cuentan(self):
        con = self._con([(n, 1000, 0) for n in NOMBRES_DEL_ENGINE])
        assert cues_a_mano(con, "7") == []

    def test_uno_puesto_a_mano_aparece_y_los_borrados_no(self):
        con = self._con([("Mix-OUT", 1000, 0), ("subida linda", 61500, 0), ("viejo", 2000, 1)])
        assert cues_a_mano(con, "7") == ["subida linda @ 61.5s"]
