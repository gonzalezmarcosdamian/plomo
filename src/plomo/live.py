"""Cliente de Ableton Live por OSC, sobre AbletonOSC.

Por que existe: la sintesis propia de `render_sketch.py` llego a su techo. Un pad
que es una suma de senoides suena a suma de senoides por bien balanceado que
este, y eso no se arregla con parametros. Lo que falta son instrumentos reales,
y para eso hay que hablar con un DAW.

Se eligio AbletonOSC y no un servidor MCP a proposito: esto es una libreria que
se importa, se testea y corre sola desde un script. Un protocolo de chat sirve
mientras hay alguien conversando; el proyecto necesita algo que funcione en un
cron a las tres de la manana.

AbletonOSC escucha en el puerto 11000 y contesta en el 11001.

Requisitos, una sola vez:
    1. Abrir Live
    2. Preferences > Link/Tempo/MIDI > Control Surface -> "AbletonOSC"
    3. Live muestra "AbletonOSC: Listening for OSC on port 11000"

Uso:
    from plomo.live import Live
    with Live() as live:
        print(live.version())
        live.tempo(123)
        i = live.crear_pista_midi("Bajo")
        live.cargar_midi(i, 0, notas, largo_compases=8)
"""
from __future__ import annotations

import queue
import re
import threading
import time
from math import ceil
from pathlib import Path

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

HOST = "127.0.0.1"
PUERTO_ENVIO = 11000
PUERTO_ESCUCHA = 11001
TIMEOUT = 3.0


_HZ = re.compile(r"([-\d.]+)\s*(k?)Hz", re.I)
_NUM = re.compile(r"(-?[\d.]+)")


def _a_hz(texto: str) -> float | None:
    """'1.35 kHz' -> 1350.0. Devuelve None si no es una frecuencia."""
    m = _HZ.search(texto)
    if not m:
        return None
    return float(m.group(1)) * (1000.0 if m.group(2) else 1.0)


def _a_numero(texto: str) -> float | None:
    """El primer numero del texto, con su multiplicador si es kHz.

    Sirve para dB, porcentajes, ms y cualquier cosa que Live muestre con
    unidad. La curva que va del valor normalizado al que se muestra no esta
    documentada y no es la misma en cada parametro —el Output del Saturator en
    0.5 muestra -18 dB—, asi que la unica forma confiable de pegarle a un valor
    es buscarlo contra lo que dice la pantalla.
    """
    hz = _a_hz(texto)
    if hz is not None:
        return hz
    m = _NUM.search(texto)
    return float(m.group(1)) if m else None


class LiveNoResponde(RuntimeError):
    """Live no contesto. Casi siempre es que falta activar el Control Surface."""


class Live:
    """Conversacion con Live. Cada consulta espera su respuesta o falla."""

    def __init__(self, host: str = HOST, timeout: float = TIMEOUT) -> None:
        self.timeout = timeout
        self._respuestas: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        disp = Dispatcher()
        disp.set_default_handler(self._recibir)
        self._server = ThreadingOSCUDPServer((host, PUERTO_ESCUCHA), disp)
        self._hilo = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._hilo.start()
        self._cliente = SimpleUDPClient(host, PUERTO_ENVIO)

    def _recibir(self, direccion: str, *args) -> None:
        with self._lock:
            cola = self._respuestas.get(direccion)
        if cola is not None:
            cola.put(args)

    # -- primitivas ------------------------------------------------------
    def enviar(self, direccion: str, *args) -> None:
        """Dispara y no espera. Para lo que no devuelve nada."""
        self._cliente.send_message(direccion, list(args))

    def preguntar(self, direccion: str, *args):
        """Envia y espera la respuesta en la misma direccion."""
        cola: queue.Queue = queue.Queue()
        with self._lock:
            self._respuestas[direccion] = cola
        try:
            self._cliente.send_message(direccion, list(args))
            try:
                return cola.get(timeout=self.timeout)
            except queue.Empty:
                raise LiveNoResponde(
                    f"Live no contesto a {direccion} en {self.timeout}s.\n"
                    "  Revisar: Live abierto, y en Preferences > Link/Tempo/MIDI\n"
                    "  el Control Surface 'AbletonOSC' seleccionado.") from None
        finally:
            with self._lock:
                self._respuestas.pop(direccion, None)

    # -- lo que se usa de verdad -----------------------------------------
    def version(self) -> str:
        mayor, menor = self.preguntar("/live/application/get/version")
        return f"{mayor}.{menor}"

    def test(self) -> bool:
        """Muestra un cartel en Live. Es la forma de confirmar que hay linea."""
        return bool(self.preguntar("/live/test"))

    def tempo(self, bpm: float | None = None) -> float:
        if bpm is not None:
            self.enviar("/live/song/set/tempo", float(bpm))
        return float(self.preguntar("/live/song/get/tempo")[0])

    def n_pistas(self) -> int:
        return int(self.preguntar("/live/song/get/num_tracks")[0])

    def crear_pista_midi(self, nombre: str | None = None) -> int:
        """Crea una pista MIDI al final y devuelve su indice."""
        antes = self.n_pistas()
        self.enviar("/live/song/create_midi_track", -1)
        for _ in range(20):          # la creacion no es instantanea
            time.sleep(0.05)
            if self.n_pistas() > antes:
                break
        else:
            raise LiveNoResponde("Live no creo la pista")
        indice = self.n_pistas() - 1
        if nombre:
            self.enviar("/live/track/set/name", indice, nombre)
        return indice

    def cargar_midi(self, pista: int, slot: int,
                    notas: list[tuple[float, float, int, int]],
                    largo_compases: float = 8.0) -> None:
        """Crea un clip y le mete las notas.

        `notas` viene en el formato de `plomo.midi.leer`:
        (inicio_en_pulsos, duracion_en_pulsos, altura, velocidad).
        """
        # Se borra primero. `create_clip` sobre un slot ocupado tira "This clip
        # slot already has a clip" y sigue, y despues las notas se mandan al
        # clip viejo — el resultado depende de que hubiera antes en vez de ser
        # el archivo que se pidio cargar.
        self.enviar("/live/clip_slot/delete_clip", pista, slot)
        time.sleep(0.1)
        self.enviar("/live/clip_slot/create_clip", pista, slot,
                    float(largo_compases * 4))
        time.sleep(0.15)
        for inicio, dur, altura, vel in notas:
            self.enviar("/live/clip/add/notes", pista, slot,
                        int(altura), float(inicio), float(dur), int(vel), 0)

    def parametros(self, pista: int, dispositivo: int) -> list[str]:
        r = self.preguntar("/live/device/get/parameters/name", pista, dispositivo)
        return [str(x) for x in r[2:]]

    def rango_parametro(self, pista: int, disp: int, idx: int) -> tuple[float, float]:
        lo = self.preguntar("/live/device/get/parameters/min", pista, disp)[2:]
        hi = self.preguntar("/live/device/get/parameters/max", pista, disp)[2:]
        return float(lo[idx]), float(hi[idx])

    def set_parametro(self, pista: int, disp: int, idx: int, valor: float) -> None:
        self.enviar("/live/device/set/parameter/value", pista, disp, idx, float(valor))

    def valor_mostrado(self, pista: int, disp: int, idx: int) -> str:
        return str(self.preguntar("/live/device/get/parameter/value_string",
                                  pista, disp, idx)[3])

    def ajustar_a(self, pista: int, disp: int, idx: int, objetivo: float) -> float:
        """Deja un parametro en el valor que muestra la pantalla, sea cual sea
        su unidad. Es `ajustar_a_hz` generalizado a dB, %, ms y demas."""
        lo, hi = self.rango_parametro(pista, disp, idx)
        creciente = None
        for _ in range(26):
            medio = (lo + hi) / 2
            self.set_parametro(pista, disp, idx, medio)
            time.sleep(0.02)
            actual = _a_numero(self.valor_mostrado(pista, disp, idx))
            if actual is None:
                break
            if creciente is None:
                # se descubre de que lado crece en vez de suponerlo
                self.set_parametro(pista, disp, idx, hi)
                time.sleep(0.02)
                arriba = _a_numero(self.valor_mostrado(pista, disp, idx)) or 0.0
                self.set_parametro(pista, disp, idx, lo)
                time.sleep(0.02)
                abajo = _a_numero(self.valor_mostrado(pista, disp, idx)) or 0.0
                creciente = arriba >= abajo
                self.set_parametro(pista, disp, idx, medio)
                time.sleep(0.02)
                continue
            if (actual < objetivo) == creciente:
                lo = medio
            else:
                hi = medio
        return _a_numero(self.valor_mostrado(pista, disp, idx)) or 0.0

    def ajustar_a_hz(self, pista: int, disp: int, idx: int, hz: float) -> float:
        """Deja un parametro de frecuencia en los Hz pedidos.

        Muchos parametros de Live no se escriben en su unidad sino normalizados
        sobre una curva que no esta documentada. El Frequency del Auto Filter,
        por ejemplo, va de 0 a 1 y en 0.6878 muestra 2.32 kHz (verificado en
        runtime). Escribir 1350 creyendo que son Hz lo clampea al maximo, que es
        el filtro abierto del todo — lo contrario de lo que se pidio.

        Pero tampoco es cierto que todo sea 0-1: el Filter Type del mismo device
        va de 0 a 9. Por eso el rango se PREGUNTA en vez de asumirse, y despues
        se busca por biseccion contra `value_string`, que devuelve el valor real
        que muestra la pantalla. Asi no hace falta saber como mapea cada device.
        """
        lo, hi = self.rango_parametro(pista, disp, idx)
        for _ in range(24):
            medio = (lo + hi) / 2
            self.set_parametro(pista, disp, idx, medio)
            time.sleep(0.02)
            texto = self.valor_mostrado(pista, disp, idx)
            actual = _a_hz(texto)
            if actual is None:
                break
            if actual < hz:
                lo = medio
            else:
                hi = medio
        return _a_hz(self.valor_mostrado(pista, disp, idx)) or 0.0

    def nombre_pista(self, indice: int) -> str:
        # Los getters de pista de AbletonOSC contestan (indice, valor), no solo
        # el valor: `create_track_callback` antepone el track_index a todo lo que
        # devuelve. Leer [0] daba el numero de pista disfrazado de nombre — se
        # veia como pistas llamadas "0", "1", "2". Los getters de song (tempo,
        # num_tracks) no llevan ese prefijo y si empiezan en [0].
        return str(self.preguntar("/live/track/get/name", indice)[1])

    # -- browser (extension propia de AbletonOSC, ver browser.py) ----------
    def listar_browser(self, categoria: str = "instruments",
                       filtro: str = "") -> list[str]:
        """Que hay para cargar. Sirve para elegir con lo que existe de verdad
        en esta instalacion y no adivinar nombres de presets."""
        resp = self.preguntar("/live/browser/list", categoria, filtro)
        return [str(x) for x in resp[2:]]

    def n_dispositivos(self, pista: int) -> int:
        return int(self.preguntar("/live/track/get/num_devices", pista)[1])

    def cambiar_instrumento(self, pista: int, candidatos: list[str],
                            categoria: str = "instruments") -> str | None:
        """Saca lo que haya en la pista y carga otra cosa.

        Hay que borrar antes: `load_item` inserta, no reemplaza, asi que cargar
        encima deja los dos instrumentos apilados sonando juntos. Se borra de
        atras para adelante porque los indices se corren con cada borrado.
        """
        for i in reversed(range(self.n_dispositivos(pista))):
            self.enviar("/live/track/delete_device", pista, i)
        time.sleep(0.2)
        return self.cargar_instrumento(pista, candidatos, categoria)

    def cargar_instrumento(self, pista: int, candidatos: list[str],
                           categoria: str = "instruments") -> str | None:
        """Prueba los nombres en orden y carga el primero que exista.

        Se prueba en orden a proposito: el primero es el preset que se quiere,
        los siguientes son el device crudo. Asi el boceto suena bien si el
        preset esta, y suena igual igual si la instalacion no lo trae.
        """
        for nombre in candidatos:
            _, estado, cargado = self.preguntar("/live/browser/load",
                                                pista, categoria, nombre)
            if str(estado) == "ok":
                return str(cargado)
        return None

    # -- mezcla ----------------------------------------------------------
    # Todo esto ya existia en AbletonOSC y el proyecto no lo usaba: se cargaban
    # instrumentos y clips pero no habia forma de mezclar, asi que todo sonaba
    # al volumen que quedara.
    def volumen(self, pista: int, valor: float | None = None) -> float:
        """0-1, no dB. El 0 dB del fader cae cerca de 0.85, no de 1.0."""
        if valor is not None:
            self.enviar("/live/track/set/volume", pista, float(valor))
        return float(self.preguntar("/live/track/get/volume", pista)[1])

    def paneo(self, pista: int, valor: float | None = None) -> float:
        if valor is not None:
            self.enviar("/live/track/set/panning", pista, float(valor))
        return float(self.preguntar("/live/track/get/panning", pista)[1])

    def send(self, pista: int, indice: int, valor: float) -> None:
        self.enviar("/live/track/set/send", pista, indice, float(valor))

    def mute(self, pista: int, si: bool = True) -> None:
        self.enviar("/live/track/set/mute", pista, 1 if si else 0)

    def solo(self, pista: int, si: bool = True) -> None:
        self.enviar("/live/track/set/solo", pista, 1 if si else 0)

    def nivel(self, pista: int) -> float:
        """Nivel de salida real de la pista. Es la unica forma de medir algo de
        lo que suena sin exportar, que la Trial no deja hacer."""
        return float(self.preguntar("/live/track/get/output_meter_level", pista)[1])

    def dispositivos(self, pista: int) -> list[str]:
        return [str(x) for x in self.preguntar("/live/track/get/devices/name", pista)[1:]]

    # -- estructura y transporte -----------------------------------------
    def estructura(self) -> dict:
        """Vuelca el Set entero —pistas, devices y todos sus parametros con sus
        rangos— a un JSON y lo devuelve. Una sola llamada en vez de preguntar
        parametro por parametro."""
        import json
        import os
        import tempfile
        self.enviar("/live/song/export/structure")
        time.sleep(1.0)
        ruta = Path(tempfile.gettempdir()) / "abletonosc-song-structure.json"
        if not ruta.exists():
            raise LiveNoResponde(f"Live no dejo el volcado en {ruta}")
        return json.loads(ruta.read_text(encoding="utf-8"))

    def reproducir(self) -> None:
        self.enviar("/live/song/start_playing")

    def detener(self) -> None:
        self.enviar("/live/song/stop_playing")

    def marcador(self, compas: float, nombre: str) -> None:
        """Deja un marcador con nombre en el Arrangement. Es la forma mas barata
        de que el arreglo se vea adentro de Live y no solo en ARREGLO.md."""
        self.enviar("/live/song/set/current_song_time", float(compas * 4))
        time.sleep(0.15)
        self.enviar("/live/song/cue_point/add_or_delete")
        time.sleep(0.15)

    # -- ciclo de vida ---------------------------------------------------
    def cerrar(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def __enter__(self) -> "Live":
        return self

    def __exit__(self, *_) -> None:
        self.cerrar()


# Que instrumento va en cada clip. Se prueba en orden y gana el primero que
# exista: primero el preset que se quiere, despues el device crudo. El device
# crudo esta en toda instalacion de Live, incluida la Trial, asi que la ultima
# opcion de cada lista nunca falla.
#
# La eleccion sigue el sonido de los artistas de referencia (Eze Arias, Emi
# Galvan, Vuarambon): pads anchos y sostenidos, bajo redondo sin ataque, arpegio
# corto con delay, bateria seca.
INSTRUMENTOS: dict[str, tuple[str, list[str]]] = {
    # pad ancho y sostenido, sin ataque marcado
    "acordes":  ("instruments", ["Sandman Pad", "Thick Chord Pad", "Wavetable"]),
    # bajo redondo con peso abajo: en progressive el bajo no se escucha, se siente
    "bajo":     ("instruments", ["Deep Bass", "Analog Bass", "Operator"]),
    # Collision es modelado fisico, no sintesis aditiva: de ahi sale lo organico
    "arpegio":  ("instruments", ["Ocean Pluck", "Snappy Pluck", "Wavetable"]),
    # 909 es la bateria de este genero desde hace treinta anios
    "bateria":  ("drums",       ["909 Core Kit", "808 Core Kit", "Drum Rack"]),
    # pluck y no pad sostenido: la melodia sostenida sonaba a organo de iglesia
    "melodia":  ("instruments", ["Tube Lead Pluck", "Sweet Lead", "Operator"]),
    # el gancho corto que reemplazo al arpegio de semicorcheas. Wavetable y no
    # modelado fisico: los presets acusticos tienen formante y suenan a bocina.
    # Despues se le cierra el filtro al rolloff medido del tema de referencia.
    "detalle":  ("instruments", ["Deep Pluck", "Snappy Pluck", "Wavetable"]),
    # los adornos que rompen el patron: van a otro kit para no pisar la base
    # "Drums Warm & Wide" NO va aca aunque el nombre lo sugiera: es un Audio
    # Effect Rack de bus, no un kit. Como fallback cargaria una cadena de
    # efectos en una pista MIDI y no sonaria nada.
    "repiques": ("drums",       ["909 Core Kit", "707 Core Kit", "Drum Rack"]),
    # el redoble que acelera al cerrar cada seccion
    "subida":   ("drums",       ["909 Core Kit", "Drum Rack"]),
    # Estas dos son samples propios, no presets. Cargar un wav en una pista MIDI
    # hace que Live arme un Simpler solo, y entonces el sample se dispara con
    # notas: el momento exacto en que entra queda escrito en el arreglo en vez
    # de depender de un arrastre a mano.
    "voz":      ("user_library", ["voz_ava_cantada", "voz_ava"]),
    # el gancho del concepto corto: mismo criterio que "detalle"
    "gancho":   ("instruments", ["Deep Pluck", "Snappy Pluck", "Wavetable"]),
    # El solo: modelado fisico de cuerda, no un sintetizador. Tension es lo mas
    # cerca de una guitarra que trae Live sin packs.
    # Tension y no el rack de guitarra: es modelado fisico de cuerda, y sobre
    # todo EXPONE `PB Range`, que viene en 2 semitonos — el mismo rango para el
    # que estan escritos los bends. El rack `Guitar Electric Clean` no lo expone
    # y AbletonOSC no entra a las cadenas de un Rack, asi que ahi los bends
    # salen con la amplitud que el preset tenga y el solo entero desafina.
    "solo":     ("instruments", ["Tension", "Guitar Electric Clean"]),
    # El cierre NO va con guitarra. Se probo y el veredicto fue que suena mal,
    # y ademas su material —notas de 4 a 12 pulsos— es de pad: una cuerda
    # sostenida doce pulsos sin bend es una nota quieta, un pad sostenido doce
    # pulsos es lo que el genero hace para cerrar.
    "cierre":   ("instruments", ["Sandman Pad", "Warm Analog Pad", "Wavetable"]),
    "riser":    ("user_library", ["riser_aire", "riser_sutil", "riser"]),
    # pedal grave sostenido: pad ancho y oscuro, sin ataque
    "atmosfera": ("instruments", ["Warm Analog Pad", "Sandman Pad", "Wavetable"]),
    # Kit aparte del de la base para que la percusion tenga voz propia, pero
    # ELECTRONICO. Un kit acustico de sesion mete timbales y toms de parche, y
    # eso choca contra todo lo demas: el tema es sintetico y la percusion suena
    # a otra grabacion pegada encima.
    "percusion": ("drums",       ["707 Core Kit", "606 Core Kit", "Drum Rack"]),
}


def _instrumento_de(archivo: Path) -> tuple[str, list[str]] | None:
    """Los clips se llaman 01_acordes, 02_bajo, etc. Se busca por la parte
    despues del numero para no atarse al orden."""
    parte = archivo.stem.split("_", 1)[-1].lower()
    return INSTRUMENTOS.get(parte)


def cargar_boceto(carpeta: Path, bpm: float | None = None,
                  con_instrumentos: bool = True) -> None:
    """Mete los cinco clips de un boceto en Live, una pista por clip.

    Es el puente que le faltaba al proyecto: `make_sketch.py` genera el MIDI y
    esto lo pone adentro del DAW, donde hay instrumentos de verdad.

    Con `con_instrumentos` cada pista arranca con algo que suena, para poder
    darle play y escuchar sin tocar nada. No es la eleccion final: es el punto
    de partida para que la decision sea sobre un sonido y no sobre silencio.
    """
    from plomo.midi import leer

    archivos = sorted(carpeta.glob("*.mid"))
    if not archivos:
        raise FileNotFoundError(f"no hay clips MIDI en {carpeta}")

    leidos = [leer(f) for f in archivos]

    # Un solo largo para todos los clips, y en compases enteros.
    #
    # Antes cada clip se media por donde terminaba su ultima nota, que da un
    # numero roto y distinto por pista (8.15, 7.99, 7.93, 7.98, 7.78). Cinco
    # loops de largo distinto arrancan juntos y se separan en cada vuelta: a los
    # cuatro loops la melodia estaba un compas adelante de los acordes. Sonaba a
    # error de cuantizacion y era aritmetica.
    #
    # Se mide por donde EMPIEZA la ultima nota, no por donde termina: la cola de
    # un pad que cruza el final del loop se corta, que es lo que tiene que pasar.
    ultimo_ataque = max(n[0] for _, _, notas in leidos for n in notas)
    compases = ceil(ultimo_ataque / 4 + 1e-9)
    compases = max(4, ceil(compases / 4) * 4)      # frases de 4 compases

    with Live() as live:
        print(f"  Live {live.version()}")
        live.tempo(bpm or leidos[0][1])
        print(f"  tempo: {live.tempo():.0f} BPM, loop de {compases} compases")
        for f, (nombre, _, notas) in zip(archivos, leidos):
            largo = compases
            pista = live.crear_pista_midi(nombre)
            live.cargar_midi(pista, 0, notas, largo_compases=largo)
            cargado = None
            if con_instrumentos:
                eleccion = _instrumento_de(f)
                if eleccion is not None:
                    categoria, candidatos = eleccion
                    cargado = live.cargar_instrumento(pista, candidatos, categoria)
            print(f"  pista {pista}: {nombre:10} {len(notas):3d} notas, "
                  f"{largo:.0f} compases  {cargado or '(sin instrumento)'}")
