# -*- coding: utf-8 -*-
"""Manejar la app de Rekordbox desde un script: abrirla, importar, cerrarla.

POR QUE EXISTE
Rekordbox no tiene carpeta vigilada. Verificado el 2026-10-19 en el manual de la
7.2.3 y en las notas de version hasta la 7.2.19: lo unico que hay es Import Track
/ Import Folder, a mano. Y el import lo tiene que hacer Rekordbox mismo, porque
`add_content` de pyrekordbox deja un rb_file_id chico que el export al pen
rechaza con error [2]. Asi que lo automatico es apretar el boton por el DJ.

COMO
- Ctrl+O es "Import File" en Rekordbox 7 y abre el dialogo comun de Windows, que
  si expone UIAutomation: se escribe la ruta del Inbox para navegar y despues los
  nombres entre comillas.
- Rekordbox dibuja su interfaz con JUCE y no expone controles. Los carteles del
  arranque (actualizador, fin de la prueba gratis, novedades del agente) se
  cierran por ventana, y si no ceden, con un click en su boton.
- Analisis terminado = BPM > 0 y AnalysisDataPath escrito. La base se lee en solo
  lectura con Rekordbox abierto, que es seguro; escribirla no.
- Se cierra con WM_CLOSE y se espera a que el proceso salga. Nunca se mata: al
  salir Rekordbox consolida el WAL y hace su backup, y tarda ~40 segundos.
- Se lanza SIN las variables ELECTRON_*: desde la terminal de VS Code hereda
  ELECTRON_RUN_AS_NODE=1 y rekordboxAgent no arranca.
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from collections.abc import Iterable, Mapping
from pathlib import Path

RAICES_INSTALACION = (Path(r"C:\Program Files\rekordbox"), Path(r"C:\Program Files\Pioneer"))
PROCESO = "rekordbox.exe"
PROCESO_ACTUALIZADOR = "Upmgr rekordbox.exe"
PROCESO_AGENTE = "rekordboxAgent.exe"
TITULO_PRINCIPAL = "rekordbox"
TITULO_ACTUALIZADOR = "rekordbox update manager"
TITULO_AGENTE = "rekordboxAgent"
TITULO_DIALOGO = "Import Track"
CLASE_DIALOGO = "#32770"
ID_CAJA_NOMBRE = "1148"
# Ventanas que muestra mientras carga la coleccion: mientras haya una, no esta lista.
CARTELES_DE_CARGA = ("welcom", "Reading Tracks...", "Preparing...")
# La caja "File name" acepta mucho mas, pero una tanda corta que falla se repite
# barata; una de 300 nombres que falla no dice cual la rompio.
MAX_CHARS_NOMBRES = 4000
ESPERA_ESTABLE_S = 8          # sin carteles nuevos por este tiempo = arranco
ESPERA_ARRANQUE_S = 240
ESPERA_DIALOGO_S = 60         # en la prueba en vivo tardo mas de 10 s en aparecer
REPETIR_CIERRE_S = 30         # cerrar tarda ~40 s; si a los 30 sigue la ventana, se repite
ANLZ_RAIZ = Path(os.path.expandvars(r"%APPDATA%\Pioneer\rekordbox\share"))
WM_CLOSE = 0x0010
WM_COMMAND = 0x0111
IDCANCEL = 2
ESPERA_CIERRE_S = 240
ANALISIS_BASE_S = 60          # 2 temas tardaron 25 s; con margen
ANALISIS_POR_TEMA_S = 20


# ------------------------------------------------------------- funciones puras


def entorno_limpio(env: Mapping[str, str]) -> dict[str, str]:
    """El entorno sin variables de Electron, para que rekordboxAgent arranque."""
    return {k: v for k, v in env.items() if not k.upper().startswith("ELECTRON_")}


def tandas(nombres: list[str], max_chars: int) -> list[list[str]]:
    """Agrupa nombres para la caja del dialogo: '"a.mp3" "b.mp3"' <= max_chars."""
    grupos: list[list[str]] = []
    actual: list[str] = []
    largo = 0
    for nombre in nombres:
        costo = len(nombre) + 2 + (1 if actual else 0)   # comillas y espacio
        if actual and largo + costo > max_chars:
            grupos.append(actual)
            actual, largo, costo = [], 0, len(nombre) + 2
        actual = [*actual, nombre]
        largo += costo
    if actual:
        grupos.append(actual)
    return grupos


def clave_ruta(ruta: str | Path) -> str:
    """Ruta comparable: la base guarda '/', el disco '\\', y Windows ignora mayusculas."""
    return str(ruta).replace("\\", "/").casefold()


def faltan_analizar(filas: Mapping[str, tuple[int, str]], rutas: Iterable[Path]) -> list[Path]:
    """Las rutas que todavia no tienen fila analizada (BPM y ANLZ) en la base.

    `filas` es clave_ruta -> (BPM, AnalysisDataPath). Rekordbox crea la fila al
    importar y la completa al analizar: tener fila no alcanza.
    """
    faltan = []
    for ruta in rutas:
        bpm, anlz = filas.get(clave_ruta(ruta), (0, ""))
        if not (bpm and anlz):
            faltan.append(ruta)
    return faltan


def _version(carpeta: str) -> tuple[int, ...]:
    numeros = re.findall(r"\d+", carpeta)
    return tuple(int(n) for n in numeros)


def encontrar_exe(raices: Iterable[Path] = RAICES_INSTALACION) -> Path | None:
    """El rekordbox.exe de la version mas nueva instalada. REKORDBOX_EXE lo pisa."""
    candidatos = [exe for raiz in raices if raiz.is_dir()
                  for exe in raiz.glob("rekordbox */rekordbox.exe")]
    if not candidatos:
        return None
    return max(candidatos, key=lambda exe: _version(exe.parent.name))


# ------------------------------------------------------------ con la app abierta
# Lo de aca abajo necesita Windows, Rekordbox y pywinauto: se importa adentro de
# cada funcion para que los tests de arriba corran sin nada de eso.


def _procesos(nombre: str = PROCESO) -> list:
    import psutil
    return [p for p in psutil.process_iter(["name"]) if p.info["name"] == nombre]


def esta_abierto() -> bool:
    return bool(_procesos())


def _ventanas(*nombres_proceso: str) -> list:
    """Ventanas visibles de esos procesos, como (nombre_proceso, ventana).

    Se enumera con EnumWindows y se envuelve solo lo de Rekordbox. El
    Desktop().windows() de pywinauto envuelve TODAS las ventanas del escritorio
    de una, y si cualquiera de otra app se cierra en ese instante tira
    InvalidWindowHandle por la lista entera (paso en el QA del 2026-10-19).
    """
    import win32gui
    import win32process
    from pywinauto.controls.hwndwrapper import HwndWrapper
    pids = {p.pid: p.info["name"] for n in nombres_proceso for p in _procesos(n)}
    encontradas: list[tuple[str, int]] = []

    def juntar(hwnd: int, _) -> bool:
        try:
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in pids:
                    encontradas.append((pids[pid], hwnd))
        except Exception:  # noqa: BLE001 — una ventana que se cerro en el medio
            pass
        return True

    win32gui.EnumWindows(juntar, None)
    visibles = []
    for nombre, hwnd in encontradas:
        try:
            visibles.append((nombre, HwndWrapper(hwnd)))
        except Exception:  # noqa: BLE001 — idem, se cerro entre enumerar y envolver
            continue
    return visibles


def principal():
    """La ventana principal, o None si todavia no esta."""
    for _, ventana in _ventanas(PROCESO):
        if ventana.window_text() == TITULO_PRINCIPAL:
            return ventana
    return None


def abrir(exe: Path | None = None) -> None:
    exe = exe or (Path(os.environ["REKORDBOX_EXE"]) if os.getenv("REKORDBOX_EXE") else encontrar_exe())
    if exe is None or not exe.is_file():
        raise FileNotFoundError("No encuentro rekordbox.exe; definir REKORDBOX_EXE en el .env")
    subprocess.Popen([str(exe)], cwd=str(exe.parent), env=entorno_limpio(os.environ),
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)


def _pedir_cierre(handle: int) -> None:
    """WM_CLOSE sin esperar. El close() de pywinauto espera 2 s y tira
    TimeoutError si la ventana sigue visible, y Rekordbox tarda ~40 s en irse."""
    import win32gui
    win32gui.PostMessage(handle, WM_CLOSE, 0, 0)


def _click_si_es_suya(ventana, x: int, y: int) -> bool:
    """Click en (x, y) solo si en ese punto esta esa ventana y no otra encima."""
    import win32con
    import win32gui
    from pywinauto import mouse
    try:
        ventana.set_focus()
        time.sleep(0.3)
        debajo = win32gui.WindowFromPoint((x, y))
        if win32gui.GetAncestor(debajo, win32con.GA_ROOT) != ventana.handle:
            return False
        mouse.click(coords=(x, y))
        return True
    except Exception:  # noqa: BLE001 — la ventana se fue en el medio
        return False


def _cerrar_o_clickear(ventana, rel_x: float, rel_y: float) -> None:
    """WM_CLOSE primero; si la ventana JUCE lo ignora, click en su boton.

    Las coordenadas son proporciones del tamano de la ventana (asi aguantan otro
    escalado de pantalla); una x negativa son pixeles desde el borde derecho.
    """
    _pedir_cierre(ventana.handle)
    time.sleep(2)
    try:
        if not ventana.is_visible():
            return
        r = ventana.rectangle()
    except Exception:  # noqa: BLE001 — ya no existe: se cerro con el WM_CLOSE
        return
    x = r.left + int(r.width() * rel_x) if rel_x >= 0 else r.right + int(rel_x)
    y = r.top + int(r.height() * rel_y) if rel_y < 1 else r.top + int(rel_y)
    _click_si_es_suya(ventana, x, y)


def cerrar_carteles() -> list[str]:
    """Cierra los carteles del arranque. Devuelve cuales cerro."""
    cerrados = []
    principal_ = principal()
    for proceso, ventana in _ventanas(PROCESO, PROCESO_ACTUALIZADOR, PROCESO_AGENTE):
        titulo = ventana.window_text()
        r = ventana.rectangle()
        if proceso == PROCESO_ACTUALIZADOR and titulo == TITULO_ACTUALIZADOR:
            # "Close" cancela la actualizacion; actualizar es decision del DJ.
            # Boton al 83% del ancho y al 88% del alto, medido en la 7.2.14.
            _cerrar_o_clickear(ventana, 0.83, 0.88)
            cerrados.append("actualizador")
        elif proceso == PROCESO_AGENTE and titulo == TITULO_AGENTE:
            _pedir_cierre(ventana.handle)
            cerrados.append("novedades del agente")
        elif (proceso == PROCESO and titulo == "" and principal_ is not None
              and ventana.handle != principal_.handle
              and r.width() > 500 and r.height() > 500):
            # "Your free trial has ended". Solo con la principal ya armada: antes
            # de eso una ventana sin titulo puede ser la propia principal
            # cargando, y cerrarla es cerrar Rekordbox. La cruz esta a 30 px del
            # borde derecho y 18 del de arriba.
            _cerrar_o_clickear(ventana, -30, 18)
            cerrados.append("aviso de la prueba")
    return cerrados


def esperar_lista(timeout: float = ESPERA_ARRANQUE_S):
    """Espera a que cargue la coleccion, cerrando los carteles. Devuelve la principal."""
    inicio = time.time()
    estable_desde = None
    while time.time() - inicio < timeout:
        cerrados = cerrar_carteles()
        for c in cerrados:
            print(f"  cerrado: {c}")
        cargando = any(v.window_text() in CARTELES_DE_CARGA for _, v in _ventanas(PROCESO))
        ventana = principal()
        if ventana is None or cargando or cerrados:
            estable_desde = None
        elif estable_desde is None:
            estable_desde = time.time()
        elif time.time() - estable_desde >= ESPERA_ESTABLE_S:
            return ventana
        if not esta_abierto():
            raise RuntimeError("Rekordbox se cerro mientras arrancaba")
        time.sleep(1)
    raise TimeoutError(f"Rekordbox no termino de arrancar en {timeout:.0f} s")


def _dialogo():
    import win32gui
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto.uia_element_info import UIAElementInfo
    handle = win32gui.FindWindow(CLASE_DIALOGO, TITULO_DIALOGO)
    return UIAWrapper(UIAElementInfo(handle)) if handle else None


def _escribir(caja, texto: str) -> None:
    """Texto en la caja y Enter A ESA CAJA, no a lo que tenga el foco."""
    caja.iface_value.SetValue(texto)
    time.sleep(0.3)
    caja.type_keys("{ENTER}", set_foreground=True)


def cancelar_dialogos() -> int:
    """Cancela los dialogos comunes abiertos por Rekordbox (Import Track, avisos
    de archivo). Con uno abierto, Rekordbox no se deja cerrar."""
    import win32gui
    cancelados = 0
    for _, ventana in _ventanas(PROCESO):
        if ventana.class_name() == CLASE_DIALOGO:
            win32gui.PostMessage(ventana.handle, WM_COMMAND, IDCANCEL, 0)
            cancelados += 1
    return cancelados


def _esperar(condicion, timeout: float, que: str):
    inicio = time.time()
    while time.time() - inicio < timeout:
        valor = condicion()
        if valor:
            return valor
        time.sleep(0.5)
    raise TimeoutError(f"{que}: no paso en {timeout:.0f} s")


def _caja_nombre(dialogo):
    """La caja de texto de "File name", o None si el dialogo todavia no la armo."""
    try:
        for combo in dialogo.descendants(control_type="ComboBox"):
            if combo.automation_id() == ID_CAJA_NOMBRE:
                edits = combo.descendants(control_type="Edit")
                return edits[0] if edits else None
    except Exception:  # noqa: BLE001 — el arbol de UIA cambia mientras se arma
        return None
    return None


def _importar_tanda(carpeta: Path, tanda: list[str]) -> None:
    from pywinauto import keyboard
    ventana = principal()
    if ventana is None:
        raise RuntimeError("No esta la ventana principal de Rekordbox")
    ventana.set_focus()
    time.sleep(0.7)
    keyboard.send_keys("^o")
    dialogo = _esperar(_dialogo, ESPERA_DIALOGO_S, "el dialogo Import Track")
    # La ventana del dialogo aparece antes que sus controles: buscar la caja de
    # una vez fallo en el QA del 2026-10-19. Se espera a que exista.
    caja = _esperar(lambda: _caja_nombre(dialogo), ESPERA_DIALOGO_S, "la caja File name")
    _escribir(caja, str(carpeta))
    _esperar(lambda: any(str(carpeta) in t.window_text()
                         for t in dialogo.descendants(control_type="ToolBar")),
             10, f"navegar a {carpeta}")
    _escribir(caja, " ".join(f'"{n}"' for n in tanda))
    _esperar(lambda: _dialogo() is None, ESPERA_DIALOGO_S, "que acepte los archivos")


def importar(carpeta: Path, nombres: list[str]) -> None:
    """Importa esos archivos de `carpeta` con Ctrl+O, en tandas.

    Si algo falla, cancela los dialogos que hayan quedado abiertos antes de
    seguir: un Import Track colgado no deja cerrar Rekordbox.
    """
    for i, tanda in enumerate(tandas(nombres, MAX_CHARS_NOMBRES), 1):
        try:
            _importar_tanda(carpeta, tanda)
        except Exception:
            if cancelar_dialogos():
                print("  (cancele un dialogo que quedo abierto)")
            raise
        print(f"  tanda {i}: {len(tanda)} archivos pasados a Rekordbox")


def leer_analisis(db_path: Path, clave: str, prefijo: str) -> dict[str, tuple[int, str]]:
    """clave_ruta -> (BPM, AnalysisDataPath) de las filas activas bajo `prefijo`.

    El AnalysisDataPath cuenta solo si el .DAT ya esta escrito en share/: la
    columna puede llenarse antes que el archivo, y el BPM puede venir de los tags.
    """
    import sqlcipher3
    con = sqlcipher3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA key = " + repr(clave))
        filas = con.execute(
            "SELECT FolderPath, COALESCE(BPM, 0), COALESCE(AnalysisDataPath, '') "
            "FROM djmdContent WHERE rb_local_deleted = 0 AND FolderPath LIKE ?",
            (prefijo.replace("\\", "/") + "%",),
        ).fetchall()
    finally:
        con.close()
    return {clave_ruta(ruta): (bpm, anlz if anlz and (ANLZ_RAIZ / anlz.lstrip("/")).is_file() else "")
            for ruta, bpm, anlz in filas}


def esperar_analisis(rutas: list[Path], db_path: Path, clave: str, carpeta: Path) -> list[Path]:
    """Espera a que Rekordbox analice todo. Devuelve lo que no termino a tiempo."""
    timeout = ANALISIS_BASE_S + ANALISIS_POR_TEMA_S * len(rutas)
    inicio = time.time()
    faltan = list(rutas)
    while time.time() - inicio < timeout:
        try:
            faltan = faltan_analizar(leer_analisis(db_path, clave, str(carpeta)), rutas)
        except Exception as e:  # noqa: BLE001 — la base ocupada un instante no corta la espera
            print(f"  (lectura de la base fallo, reintento: {e})")
        if not faltan:
            return []
        print(f"  analizando: {len(rutas) - len(faltan)}/{len(rutas)}", flush=True)
        time.sleep(5)
    return faltan


def cerrar(timeout: float = ESPERA_CIERRE_S) -> bool:
    """Cierra Rekordbox ordenado y espera a que salga. Nunca lo mata."""
    # El pedido se repite: si llega mientras Rekordbox todavia arranca (sin
    # ventana principal) o con un cartel modal encima, se pierde. Paso en el QA
    # del 2026-10-19: un solo WM_CLOSE temprano y despues 240 s esperando.
    inicio = time.time()
    ultimo_pedido = 0.0
    while time.time() - inicio < timeout:
        if not esta_abierto():
            return True
        if time.time() - ultimo_pedido >= REPETIR_CIERRE_S:
            cancelar_dialogos()
            cerrar_carteles()
            ventana = principal()
            if ventana is not None:
                _pedir_cierre(ventana.handle)
                ultimo_pedido = time.time()
        time.sleep(1)
    return not esta_abierto()
