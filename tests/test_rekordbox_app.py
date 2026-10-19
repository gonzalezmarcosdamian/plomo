# -*- coding: utf-8 -*-
"""Las partes puras del manejo de Rekordbox: lo que decide QUE se le pide.

Lo que toca la ventana (Ctrl+O, el dialogo, cerrar) no se puede testear sin
Rekordbox abierto; lo que si se puede es que el pedido sea el correcto. Un error
aca no se ve: Rekordbox importa la mitad, o espera para siempre un analisis que
ya termino, o arranca roto porque heredo el entorno de VS Code.
"""
from pathlib import Path

import pytest

from plomo.rekordbox_app import (
    clave_ruta,
    encontrar_exe,
    entorno_limpio,
    faltan_analizar,
    tandas,
)


@pytest.mark.unit
class TestEntornoLimpio:
    def test_saca_electron_run_as_node(self):
        # Medido el 2026-10-19: lanzado desde la terminal de VS Code, Rekordbox
        # heredaba ELECTRON_RUN_AS_NODE=1, rekordboxAgent (Electron) arrancaba
        # como Node y Rekordbox salia con "Communication with rekordboxAgent failed".
        env = {"ELECTRON_RUN_AS_NODE": "1", "PATH": "C:\\x", "USERPROFILE": "C:\\u"}
        limpio = entorno_limpio(env)
        assert "ELECTRON_RUN_AS_NODE" not in limpio
        assert limpio["PATH"] == "C:\\x"
        assert limpio["USERPROFILE"] == "C:\\u"

    def test_saca_cualquier_variable_de_electron(self):
        env = {"ELECTRON_NO_ATTACH_CONSOLE": "1", "ELECTRON_ENABLE_LOGGING": "1"}
        assert entorno_limpio(env) == {}

    def test_no_modifica_el_original(self):
        env = {"ELECTRON_RUN_AS_NODE": "1"}
        entorno_limpio(env)
        assert env == {"ELECTRON_RUN_AS_NODE": "1"}


@pytest.mark.unit
class TestTandas:
    def test_entran_todos_en_una(self):
        assert tandas(["a.mp3", "b.mp3"], max_chars=100) == [["a.mp3", "b.mp3"]]

    def test_corta_antes_de_pasarse(self):
        # '"a.mp3" "b.mp3"' son 15 caracteres: con tope 10 va uno por tanda.
        assert tandas(["a.mp3", "b.mp3"], max_chars=10) == [["a.mp3"], ["b.mp3"]]

    def test_el_largo_cuenta_comillas_y_espacios(self):
        # '"a.mp3" "b.mp3"' = 7 + 1 + 7 = 15: con 15 entra justo, con 14 no.
        assert tandas(["a.mp3", "b.mp3"], max_chars=15) == [["a.mp3", "b.mp3"]]
        assert tandas(["a.mp3", "b.mp3"], max_chars=14) == [["a.mp3"], ["b.mp3"]]

    def test_un_nombre_mas_largo_que_el_tope_va_solo(self):
        # Mejor una tanda que se pasa que un archivo que nunca se importa.
        largo = "x" * 50 + ".mp3"
        assert tandas(["a.mp3", largo, "b.mp3"], max_chars=20) == [["a.mp3"], [largo], ["b.mp3"]]

    def test_sin_nombres_no_hay_tandas(self):
        assert tandas([], max_chars=100) == []


@pytest.mark.unit
class TestFaltanAnalizar:
    INBOX = "C:\\Users\\gonza\\Documents\\Music\\2026\\Nuevos\\Inbox"

    def _ruta(self, nombre: str) -> Path:
        return Path(self.INBOX) / nombre

    def test_sin_fila_todavia_falta(self):
        rutas = [self._ruta("a.mp3")]
        assert faltan_analizar({}, rutas) == rutas

    def test_con_bpm_y_anlz_esta_listo(self):
        rutas = [self._ruta("a.mp3")]
        filas = {clave_ruta(rutas[0]): (12300, "/PIONEER/USBANLZ/x/ANLZ0000.DAT")}
        assert faltan_analizar(filas, rutas) == []

    def test_bpm_cero_es_analisis_en_curso(self):
        # Rekordbox crea la fila al importar y la completa al analizar: la fila
        # sola no alcanza. Metro tuvo fila con BPM 0 durante 25 segundos.
        rutas = [self._ruta("a.mp3")]
        filas = {clave_ruta(rutas[0]): (0, "/PIONEER/USBANLZ/x/ANLZ0000.DAT")}
        assert faltan_analizar(filas, rutas) == rutas

    def test_sin_anlz_falta(self):
        rutas = [self._ruta("a.mp3")]
        filas = {clave_ruta(rutas[0]): (12300, "")}
        assert faltan_analizar(filas, rutas) == rutas

    def test_la_base_guarda_barras_normales(self):
        # FolderPath viene con '/', la ruta del disco con '\\'. Y Windows no
        # distingue mayusculas: "RÜFÜS" en el disco puede ser "rüfüs" en la base.
        ruta = self._ruta("RÜFÜS - Innerbloom.mp3")
        en_la_base = (self.INBOX.replace("\\", "/") + "/rüfüs - innerbloom.mp3")
        filas = {clave_ruta(en_la_base): (12000, "/PIONEER/x.DAT")}
        assert faltan_analizar(filas, [ruta]) == []


@pytest.mark.unit
class TestEncontrarExe:
    def _instalar(self, raiz: Path, carpeta: str) -> Path:
        exe = raiz / carpeta / "rekordbox.exe"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"")
        return exe

    def test_elige_la_version_mas_nueva(self, tmp_path):
        self._instalar(tmp_path, "rekordbox 6.8.7")
        nueva = self._instalar(tmp_path, "rekordbox 7.2.14")
        self._instalar(tmp_path, "rekordbox 7.2.9")
        # 7.2.14 > 7.2.9: se compara como numero, no como texto.
        assert encontrar_exe([tmp_path]) == nueva

    def test_ignora_carpetas_sin_exe(self, tmp_path):
        (tmp_path / "rekordbox 9.0.0").mkdir()
        vieja = self._instalar(tmp_path, "rekordbox 6.8.6")
        assert encontrar_exe([tmp_path]) == vieja

    def test_sin_instalacion_devuelve_none(self, tmp_path):
        assert encontrar_exe([tmp_path, tmp_path / "no_existe"]) is None
