# -*- coding: utf-8 -*-
"""Que entra al Inbox y que no: lo que decide si Rekordbox recibe un duplicado.

Desde que el import es automatico, todo lo que llega al Inbox se importa sin que
nadie lo mire. Un tema que ya esta en la biblioteca y vuelve a bajarse tiene que
quedarse afuera; si entra, Rekordbox lo carga como tema nuevo y queda duplicado.
"""
import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from import_all import clave_nombre, ya_en_biblioteca  # noqa: E402


def _indice(**rutas: list[str]) -> dict[str, list[str]]:
    return {clave_nombre(nombre): lista for nombre, lista in rutas.items()}


@pytest.mark.unit
class TestYaEnBiblioteca:
    def test_nombre_nuevo_entra(self):
        assert ya_en_biblioteca("Nuevo.mp3", {}, existe=lambda p: True) is None

    def test_mismo_nombre_con_archivo_en_disco_queda_afuera(self):
        # El caso del 2026-10-19: Maze 28 - Constant Daydream (TEELCO Remix)
        # estaba en Descargas Y en la biblioteca, con otro hash (Rekordbox le
        # reescribe los tags), asi que comparar bytes no sirve: va el nombre.
        indice = {clave_nombre("Maze 28 - Constant Daydream.mp3"):
                  ["C:/Music/2026-10/Maze 28 - Constant Daydream.mp3"]}
        assert ya_en_biblioteca("Maze 28 - Constant Daydream.mp3", indice, existe=lambda p: True) \
            == "C:/Music/2026-10/Maze 28 - Constant Daydream.mp3"

    def test_mismo_nombre_pero_archivo_perdido_entra(self):
        # Si el archivo de la biblioteca se perdio, la descarga nueva es el
        # reemplazo: entra, y fix_existing_tracks re-apunta la fila existente.
        indice = {clave_nombre("Perdido.mp3"): ["C:/Music/2024/Perdido.mp3"]}
        assert ya_en_biblioteca("Perdido.mp3", indice, existe=lambda p: False) is None

    def test_varias_filas_alcanza_con_una_viva(self):
        # Dos filas con el mismo nombre (una vieja rota, una sana): el archivo
        # esta en la biblioteca. Antes el indice se quedaba con la ultima fila
        # y, si era la rota, la descarga entraba como duplicado de la sana.
        indice = {clave_nombre("Tema.mp3"): ["C:/viejo/Tema.mp3", "C:/sano/Tema.mp3"]}
        assert ya_en_biblioteca("Tema.mp3", indice,
                                existe=lambda p: p.startswith("C:/sano")) == "C:/sano/Tema.mp3"

    def test_acentos_compuestos_y_descompuestos_son_el_mismo_nombre(self):
        # macOS y algunos zips guardan "é" como e + tilde suelta (NFD); Windows
        # y Rekordbox como un solo caracter (NFC). Para el ojo son iguales.
        nfc = unicodedata.normalize("NFC", "Sébastien Léger - Lanterne.mp3")
        nfd = unicodedata.normalize("NFD", nfc)
        assert nfc != nfd
        indice = {clave_nombre(nfc): ["C:/Music/x.mp3"]}
        assert ya_en_biblioteca(nfd, indice, existe=lambda p: True) == "C:/Music/x.mp3"
