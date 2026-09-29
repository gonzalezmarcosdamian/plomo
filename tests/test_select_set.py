"""Tests de las funciones puras de select_set — la regla de artista y Camelot.

Son las que deciden si dos temas del mismo productor pueden convivir en un set.
Un bug aca no rompe nada visible: produce un set malo en silencio.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from plomo.rules import R  # noqa: E402
from select_set import arc_target, cam_dist, camelot, names  # noqa: E402


@pytest.mark.unit
class TestNames:
    def test_artista_simple(self) -> None:
        assert names("Dilby", "Sensei (Original Mix)") == {"dilby"}

    def test_separa_colaboraciones(self) -> None:
        assert names("Kamilo Sanclemente & Jossem", "Inner Motion") == {
            "kamilo sanclemente",
            "jossem",
        }

    def test_remixer_cuenta_como_artista(self) -> None:
        # Kyotto aparece como artista en un tema y como remixer en otro:
        # el set no puede llevar los dos.
        a = names("KYOTTO", "Trigger")
        b = names("Cary Crank", "Inner Atlas (Kyotto Remix)")
        assert a & b == {"kyotto"}

    def test_sufijo_extended_no_rompe_el_match(self) -> None:
        # Regresion: "Marsh Extended" y "Marsh's Extended" no matcheaban con
        # "marsh", asi que el solver podia meter los dos temas de mas energia
        # de la biblioteca (E8.6 y E8.3) en el mismo set.
        whiteroom = names("Andy Moor & Adam White", "The Whiteroom (Marsh Extended Mix)")
        attraction = names("Ferry Corsten, Marsh", "Attraction (Marsh's Extended Mix)")
        assert "marsh" in whiteroom
        assert "marsh" in attraction
        assert whiteroom & attraction == {"marsh"}

    def test_remixer_entre_corchetes(self) -> None:
        assert "sultan + shepard" in names(
            "Lane 8", "Survive (feat. Channy Leaneagh) [Sultan + Shepard Remix]"
        )

    def test_ignora_palabras_de_version(self) -> None:
        assert names("Dilby", "Sensei (Extended Mix)") == {"dilby"}


@pytest.mark.unit
class TestCamelot:
    def test_parsea_key_valida(self) -> None:
        assert camelot("8A") == (8, "A")
        assert camelot("12B") == (12, "B")

    def test_key_invalida(self) -> None:
        assert camelot("?") is None
        assert camelot("") is None

    def test_misma_key_distancia_cero(self) -> None:
        assert cam_dist("8A", "8A") == 0

    def test_vecino_distancia_uno(self) -> None:
        assert cam_dist("8A", "9A") == 1
        assert cam_dist("8A", "7A") == 1

    def test_cruza_el_cero(self) -> None:
        assert cam_dist("12A", "1A") == 1
        assert cam_dist("1A", "12A") == 1

    def test_relativa_mayor_cuesta_un_paso_y_entra(self) -> None:
        # Cambiar de modo sin cambiar de numero cuesta UN paso, no cero: 8A y 8B
        # comparten las notas pero no el color, y el solver lo cobra como
        # cualquier otro movimiento. Lo que importa es que entre, y entra porque
        # el tope de la regla es 2.
        assert cam_dist("8A", "8B") == 1
        assert cam_dist("8A", "8B") <= R.get("armonia.max_camelot_dist")

    def test_salto_lejano(self) -> None:
        assert cam_dist("4A", "9A") == 5

    def test_key_desconocida_es_incompatible(self) -> None:
        assert cam_dist("8A", "?") == 99


@pytest.mark.unit
class TestArcoDeEnergia:
    def test_arranca_abajo_y_sube_al_pico(self) -> None:
        # Donde cae el pico se LEE de la regla. Estaba escrito 0.82 aca adentro,
        # la regla paso a 0.6 cuando se midio que 0.85 se acoplaba a la zona de
        # retroceso, y el test quedo fallando por copiar un numero que no le
        # pertenece. Un test que duplica una regla la convierte en dos reglas.
        n = 12
        pico = R.get("energia.pico_en_pct")
        arco = [arc_target(i, n, 4.0, 7.0) for i in range(n)]
        assert arco[0] == pytest.approx(4.0)
        assert arco.index(max(arco)) == round(pico * (n - 1))
        assert max(arco) == pytest.approx(7.0, abs=0.2)

    def test_el_cierre_baja_del_pico(self) -> None:
        n = 12
        assert arc_target(n - 1, n, 4.0, 7.0) < 7.0


@pytest.mark.unit
class TestAcentos:
    def test_el_mismo_productor_con_y_sin_acento_es_uno_solo(self) -> None:
        # Rekordbox guarda el mismo nombre de las dos formas segun de donde vino
        # el archivo. Sin normalizar, el tope por artista los deja convivir: el
        # 2026-09-29 el mejor candidato para acompanar a Go era otro Leger, con
        # Leger ya en el set.
        a = names("Sébastien Léger, Lost Miracle", "Dodonpachi (Original Mix)")
        b = names("Sebastien Leger, Roy Rosenfeld", "Panko Day (Extended Mix)")
        assert a & b == {"sebastien leger"}

    def test_tambien_en_el_remixer(self) -> None:
        a = names("Simon Vuarambón", "Afrika")
        b = names("Tantum, Hyunji-A", "Keep My Letters (Simon Vuarambon Remix)")
        assert a & b == {"simon vuarambon"}
