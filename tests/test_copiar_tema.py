"""Tests de las funciones de deteccion de `copiar_tema.py`, con audio sintetico.

Por que con audio sintetico y no con una referencia real: las referencias
(Tunnel, Panorama, Closing Doors, Interlocutor) son mp3 personales, no viven en
el repo (`*.mp3` esta en `.gitignore`) y una sesion sin acceso a esos archivos
—como una corrida en la nube, sin Ableton Live ni disco personal— no puede
transcribir nada real. Pero SI puede construir un click track o una progresion
de tonos con numpy, donde la respuesta correcta se conoce de antemano porque la
escribimos nosotros. Eso alcanza para blindar la parte de la cadena que ya
causo tres bugs silenciosos (grilla corrida, acorde aplastado a triada, bajo de
una sola semicorchea): la deteccion, no el timbre.

Lo que estos tests NO prueban: que la transcripcion de un tema real de progressive
house sea buena. Para eso segue haciendo falta `copiar_tema.py "<mp3>" --desde ...`
sobre una referencia, y verlo con `_verificar`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from copiar_tema import (  # noqa: E402
    ACORDES,
    _armonia,
    _afinar_bpm,
    _bajo,
    _banda,
    _cuantizar,
    _grilla,
    _puntaje,
    _sin_octavas,
)

SR = 22050


def _impulsos(tiempos: list[float], sr: int, dur_s: float) -> np.ndarray:
    n = int(sr * dur_s)
    a = np.zeros(n)
    for t in tiempos:
        i = int(round(t * sr))
        if 0 <= i < n:
            a[i] = 1.0
    return a


def _tono(midis: list[float], sr: int, dur_s: float, amp: float = 0.25,
         armonico: bool = False) -> np.ndarray:
    t = np.arange(int(sr * dur_s)) / sr
    y = np.zeros_like(t)
    for m in midis:
        f = 440.0 * 2 ** ((m - 69) / 12.0)
        y += amp * np.sin(2 * np.pi * f * t)
        if armonico:
            y += amp * 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return y


def _grilla_recta(bpm: float, n: int = 4000) -> np.ndarray:
    return np.arange(0, n) * (60.0 / bpm / 4)


def _notas_de(pista) -> list[tuple[float, float, int]]:
    """(inicio_en_pulsos, duracion_en_pulsos, altura) de una Pista, ordenado."""
    ev = sorted(pista._eventos, key=lambda e: e.tick)
    abiertas: dict[int, int] = {}
    out = []
    for e in ev:
        tipo = e.datos[0] & 0xF0
        if tipo == 0x90:
            abiertas[e.datos[1]] = e.tick
        elif tipo == 0x80 and e.datos[1] in abiertas:
            ini = abiertas.pop(e.datos[1])
            out.append((ini / 480, (e.tick - ini) / 480, e.datos[1]))
    return out


@pytest.mark.unit
class TestGrilla:
    def test_encuentra_el_uno_con_offset_arbitrario(self) -> None:
        """La grilla tiene que agarrar el downbeat aunque el fragmento no
        arranque en el compas 1 del tema (nunca arranca: `--desde` es un
        segundo cualquiera). El clap en 2 y 4 es lo que desambigua, y es
        exactamente el mecanismo que describe el docstring de `_grilla`."""
        bpm = 123.0
        negra = 60.0 / bpm
        offset = 0.83  # un segundo cualquiera, no calzado a compas
        kicks = [offset + c * 4 * negra + b * negra
                 for c in range(8) for b in range(4)]
        claps = [offset + c * 4 * negra + b * negra
                 for c in range(8) for b in (1, 3)]
        dur = 8 * 4 * negra + 1.0
        drums = (_banda(_impulsos(kicks, SR, dur), SR, 30, 100) * 3.0
                 + _banda(_impulsos(claps, SR, dur), SR, 300, 900) * 1.5)

        grilla = _grilla(drums, SR, bpm)

        assert abs(grilla[0] - offset % (4 * negra)) < negra / 4
        d = np.abs(np.array(kicks)[:, None] - grilla[None, :]).min(axis=1)
        assert (d < 0.020).mean() == 1.0

        idx = _cuantizar(np.array(claps), grilla)
        assert all(i % 16 in (4, 12) for i in idx), (
            "los claps tienen que caer en negra 2 y 4 (semicorchea 4 y 12), "
            "que es la definicion de que la grilla encontro el compas real")


@pytest.mark.unit
class TestAfinarBpm:
    def test_recupera_el_bpm_real_dentro_de_la_ventana_de_busqueda(self) -> None:
        """El buscador recorre bpm-4..bpm+4: solo puede corregir un tracker
        que se equivoco por eso, que es lo que dice el docstring que pasa en
        progressive ('en Afrika decia 123 con el tema a 121')."""
        bpm_real = 122.4
        negra = 60.0 / bpm_real
        dur = 16 * 4 * negra + 1.0
        kicks = [c * 4 * negra + b * negra for c in range(16) for b in range(4)]
        drums = _banda(_impulsos(kicks, SR, dur), SR, 30, 100)

        for crudo in (120.0, 124.0, 125.5):
            assert abs(_afinar_bpm(drums, SR, crudo) - bpm_real) < 0.1


@pytest.mark.unit
class TestCuantizar:
    def test_asigna_a_la_semicorchea_mas_cercana(self) -> None:
        grilla = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
        assert _cuantizar(np.array([0.04]), grilla) == {0}
        assert _cuantizar(np.array([0.06]), grilla) == {1}
        assert _cuantizar(np.array([0.19]), grilla) == {2}

    def test_vacio_no_rompe(self) -> None:
        assert _cuantizar(np.array([]), np.array([0.0, 0.1])) == set()


@pytest.mark.unit
class TestPuntajeAcorde:
    def test_prefiere_la_triada_exacta_sobre_un_superconjunto(self) -> None:
        """El bug que aplasto la armonia a doce compases de F: puntuar por
        SUMA hace ganar siempre al acorde con mas notas, porque cubre mas
        croma. La correlacion de Pearson no: un perfil que es EXACTAMENTE
        una triada menor (D F A, nada mas) tiene que elegir la triada menor,
        no una m7 o m9 que agregan notas que el perfil no tiene."""
        perfil = np.zeros(12)
        for pc in (2, 5, 9):  # D, F, A
            perfil[pc] = 1.0
        puntaje, raiz, sufijo = max(
            (_puntaje(perfil, r, g), r, n)
            for n, g in ACORDES.items() for r in range(12))
        assert (raiz, sufijo) == (2, "m")
        assert puntaje == pytest.approx(1.0)


@pytest.mark.unit
class TestArmonia:
    def test_detecta_una_progresion_no_un_solo_acorde(self) -> None:
        """Regresion directa del bug de doce compases de F: dos acordes
        distintos en cuatro compases tienen que salir como DOS acordes
        distintos, no aplastados al mismo."""
        bpm = 123.0
        grilla = _grilla_recta(bpm)
        dur_compas = 4 * (60.0 / bpm)
        dm7 = [38, 41, 45, 48]
        fmaj7 = [41, 45, 48, 52]
        other = np.concatenate([
            _tono(dm7, SR, dur_compas), _tono(dm7, SR, dur_compas),
            _tono(fmaj7, SR, dur_compas), _tono(fmaj7, SR, dur_compas),
        ])
        _, elegidos = _armonia(other, SR, grilla, 4 * 16, bpm)
        assert elegidos == ["Dm7", "Dm7", "Fmaj7", "Fmaj7"]


@pytest.mark.unit
class TestBajo:
    def test_agrupa_semicorcheas_de_la_misma_altura_en_una_nota(self) -> None:
        """El bug de 55 notas todas de una semicorchea: un bajo que sostiene
        dos compases tiene que salir como UNA nota de dos compases, no como
        treinta y dos golpes de la misma altura."""
        bpm = 123.0
        grilla = _grilla_recta(bpm)
        dur_compas = 4 * (60.0 / bpm)
        bass = np.concatenate([
            _tono([38], SR, dur_compas * 2, armonico=True),
            _tono([41], SR, dur_compas, armonico=True),
            np.zeros(int(SR * dur_compas)),
        ])
        notas = _notas_de(_bajo(bass, SR, grilla, 4 * 16, bpm))

        assert len(notas) == 2, f"se esperaban 2 notas sostenidas, salieron {notas}"
        (ini1, dur1, alt1), (ini2, dur2, alt2) = notas
        assert alt1 == 38 and alt2 == 41
        assert ini1 == pytest.approx(0.0, abs=0.05)
        assert dur1 == pytest.approx(8 * 0.92, abs=0.2)   # 2 compases
        assert ini2 == pytest.approx(8.0, abs=0.05)
        assert dur2 == pytest.approx(4 * 0.92, abs=0.2)   # 1 compas
        # el ultimo compas es silencio real: no puede haber una tercera nota
        # inventada ahi (la trampa que exactamente esta prueba busca detectar)

    def test_silencio_no_inventa_nota(self) -> None:
        bpm = 123.0
        grilla = _grilla_recta(bpm)
        bass = np.zeros(int(SR * 4 * (60.0 / bpm)))
        assert _notas_de(_bajo(bass, SR, grilla, 16, bpm)) == []


@pytest.mark.unit
class TestSinOctavas:
    def test_corrige_el_salto_de_octava_aislado(self) -> None:
        assert _sin_octavas([38, 50, 38]) == [38, 38, 38]

    def test_no_toca_un_salto_que_no_vuelve(self) -> None:
        assert _sin_octavas([38, 50, 41]) == [38, 50, 41]

    def test_listas_cortas_no_rompen(self) -> None:
        assert _sin_octavas([]) == []
        assert _sin_octavas([38]) == [38]
        assert _sin_octavas([38, 50]) == [38, 50]
