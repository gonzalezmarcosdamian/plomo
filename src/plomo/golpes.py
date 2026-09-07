"""Extraccion de golpes percusivos desde tracks de la biblioteca propia.

POR QUE EXISTE
--------------
`render_sketch.py` sintetiza toda la bateria con sumas de armonicos y ruido
filtrado. Mide bien contra las plantillas y suena a sintetizador: el timbre es
el mismo sin importar el registro. Este modulo aporta el material que falta —
kicks, hats y claps reales, sacados de los tracks que Gonzalo mas toca.

MATERIAL CON DERECHOS — LEER
----------------------------
Lo que sale de aca son fragmentos de grabaciones comerciales ajenas. Un golpe
aislado de ~300 ms sirve como REFERENCIA DE TIMBRE para produccion propia y
para escuchar una maqueta antes de elegir sonidos. No es un sample para
publicar, ni para distribuir, ni para que termine adentro de un track que se
sube a un sello. La carpeta `data/samples/` esta en .gitignore por eso.

Si el uso deja de ser "escuchar un boceto en esta maquina" y pasa a ser
"esto sale a la calle", el golpe hay que reemplazarlo por uno propio o por uno
de una libreria con licencia. Esa linea la cruza una persona, no un script.

QUE TAN LIMPIO SALE
-------------------
Aislar un kick de una mezcla terminada es imposible en el sentido estricto:
siempre viene con cola de bajo, de reverb y con lo que suene encima. Lo que se
hace aca es buscar el golpe MENOS CONTAMINADO del track — que casi siempre cae
en la intro o el outro, donde el kick esta solo — y medir cuanta basura quedo.
La metrica es `bleed_db`: energia arriba de 300 Hz despues de los primeros
80 ms, relativa al pico del golpe. Se guarda en el indice de procedencia y se
reporta siempre, tambien cuando sale mal.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, find_peaks, sosfiltfilt

SR = 44100

# Umbrales de calidad. Salen de medir los 8 tracks mas tocados: los mejores
# candidatos dan -17 a -24 dB de bleed en kick y -20 a -34 en hat. Por encima
# de estos valores el golpe trae demasiado encima y se marca como sucio.
BLEED_ACEPTABLE_DB = -15.0
# Fraccion minima de energia en 20-120 Hz para que un kick sea un kick.
SUB_MINIMO_PCT = 80.0


@dataclass
class Golpe:
    """Un golpe extraido, con su procedencia y sus metricas de separacion."""
    clase: str
    archivo: str
    origen: str
    segundo: float
    dur_ms: float
    bleed_db: float
    bleed_db_crudo: float
    sub_pct: float
    centroide_hz: float
    limpio: bool

    def como_dict(self) -> dict:
        return asdict(self)


# -- filtros ----------------------------------------------------------------
def _sos(lo: float, hi: float | None, tipo: str):
    ny = SR / 2
    if tipo == "band":
        return butter(4, [lo / ny, min(hi, ny * 0.99) / ny], btype="band", output="sos")
    return butter(4, lo / ny, btype=tipo, output="sos")


def banda(x: np.ndarray, lo: float, hi: float | None = None,
          tipo: str = "band") -> np.ndarray:
    """Filtro de fase cero. `tipo`: band, highpass o lowpass."""
    return sosfiltfilt(_sos(lo, hi, tipo), x)


def _envolvente(x: np.ndarray, hop: int) -> np.ndarray:
    """RMS por bloque. Es el detector de onsets: barato y suficiente."""
    n = (len(x) - hop) // hop
    return np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))


# -- metricas de separacion -------------------------------------------------
def bleed_db(w: np.ndarray, desde_ms: float = 80.0, corte_hz: float = 300.0) -> float:
    """Cuanta energia ajena queda en la cola, relativa al pico del golpe.

    Un kick propio ya no tiene casi nada arriba de 300 Hz pasados los 80 ms: lo
    que quede ahi es el hat del contratiempo, el pad o la reverb del track.
    Es la medida honesta de "que tan aislado quedo esto".
    """
    alto = banda(w, corte_hz, tipo="highpass")
    cola = float(np.sqrt(np.mean(alto[int(desde_ms / 1000 * SR):] ** 2)))
    pico = float(np.sqrt(np.mean(w[:int(0.03 * SR)] ** 2)))
    return 20 * np.log10((cola + 1e-12) / (pico + 1e-12))


def sub_pct(w: np.ndarray) -> float:
    """Porcentaje de energia en 20-120 Hz. Un kick de progressive da 90+."""
    esp = np.abs(np.fft.rfft(w)) ** 2
    f = np.fft.rfftfreq(len(w), 1 / SR)
    return float(esp[(f >= 20) & (f < 120)].sum() / (esp.sum() + 1e-12) * 100)


def caida_db(w: np.ndarray, desde_ms: float, pico_ms: float = 8.0) -> float:
    """Cuanto bajo el golpe respecto de su ataque. Mide si es transitorio o bed."""
    pico = float(np.sqrt(np.mean(w[:int(pico_ms / 1000 * SR)] ** 2)))
    resto = w[int(desde_ms / 1000 * SR):]
    if len(resto) < 64:
        return -99.0
    return 20 * np.log10((float(np.sqrt(np.mean(resto ** 2))) + 1e-12) / (pico + 1e-12))


# -- deteccion de candidatos ------------------------------------------------
# Cada clase se detecta en la banda donde vive y se descarta con la banda donde
# NO deberia vivir. El hat y el clap se descartan cuando coinciden con un kick
# fuerte: ahi abajo hay tanta energia que el recorte sale montado.
@dataclass(frozen=True)
class Clase:
    nombre: str
    detectar: tuple[float, float]   # banda donde se busca el onset
    ventana_ms: float
    pre_ms: float
    guardar_hp: float               # pasaaltos al guardar (0 = full band)
    separacion_ms: float            # distancia minima entre onsets
    percentil: float                # altura minima del pico, percentil de la envolvente
    evitar_kick: bool
    caida_desde_ms: float           # para el ranking: donde se mide la cola
    centroide: tuple[float, float] | None  # centroide que tiene que dar; None = no aplica


# El `guardar_hp` del hat es alto a proposito. Con el pasaaltos en 400 Hz el
# onset se detectaba arriba de 6 kHz pero la ventana guardaba todo el medio: el
# resultado tenia el centroide en 2.1 kHz y era indistinguible del clap — las
# dos clases caian sobre los mismos eventos. Un hat de verdad no tiene nada
# abajo de 3 kHz, y recortarlo ahi es lo que lo separa del bed.
#
# El `centroide` es el control de que la clase sea lo que dice. Sin el, el
# detector de clap agarraba hats (centroide 6.7 kHz) y los guardaba como clap.
# En el kick va en None: el centroide de una senal full band es un promedio
# lineal de frecuencia, asi que un 2% de energia en 8 kHz lo corre 160 Hz y
# rechaza kicks perfectos. Ahi el control que sirve es `sub_pct`.
CLASES = {
    "kick":        Clase("kick",        (30, 120),    350, 6.0,     0, 250, 90, False,  80, None),
    "hat":         Clase("hat",         (6000, 16000), 110, 3.0, 3500,  60, 92, True,   60, (5000, 14000)),
    "hat_abierto": Clase("hat_abierto", (5000, 16000), 300, 3.0, 3000, 150, 95, True,  150, (4500, 13000)),
    "clap":        Clase("clap",        (900, 5000),   250, 4.0,  300, 150, 95, True,  150, (900, 4500)),
}


def centroide_hz(w: np.ndarray) -> float:
    """Centroide espectral: donde esta el centro de gravedad del timbre."""
    esp = np.abs(np.fft.rfft(w)) ** 2
    f = np.fft.rfftfreq(len(w), 1 / SR)
    return float((f * esp).sum() / (esp.sum() + 1e-12))


def _candidatos(y: np.ndarray, c: Clase) -> list[tuple[float, int]]:
    """Devuelve (puntaje, muestra_inicio) ordenado de mejor a peor.

    El puntaje es el bleed para el kick y la caida para el resto: en los dos
    casos, mas negativo = mas aislado.
    """
    hop = 128 if c.nombre == "kick" else 64
    det = banda(y, *c.detectar)
    env = _envolvente(det, hop)
    if env.size == 0:
        return []
    picos, _ = find_peaks(env, height=float(np.percentile(env, c.percentil)) or 1e-9,
                          distance=max(int(c.separacion_ms / 1000 * SR / hop), 1))
    env_grave = _envolvente(banda(y, 30, 120), hop) if c.evitar_kick else None
    tope_grave = float(np.percentile(env_grave, 90)) * 0.5 if c.evitar_kick else 0.0

    ancho, pre = int(c.ventana_ms / 1000 * SR), int(c.pre_ms / 1000 * SR)
    fuera = []
    for i in picos:
        s = int(i) * hop - pre
        if s < 0 or s + ancho > len(y):
            continue
        if env_grave is not None and i < len(env_grave) and env_grave[i] > tope_grave:
            continue
        w = y[s:s + ancho]
        if np.max(np.abs(w)) < 0.05:
            continue
        util = banda(w, c.guardar_hp, tipo="highpass") if c.guardar_hp else w
        if c.centroide and not c.centroide[0] <= centroide_hz(util) <= c.centroide[1]:
            continue
        if c.nombre == "kick":
            if sub_pct(w) < SUB_MINIMO_PCT:
                continue
            fuera.append((bleed_db(w), s))
        else:
            fuera.append((caida_db(util, c.caida_desde_ms), s))
    fuera.sort()
    return fuera


def _recortar(y: np.ndarray, s: int, c: Clase, limpiar: bool) -> np.ndarray:
    """Aisla la ventana, la limpia y le pone los fades.

    `limpiar` apaga la cola de la banda alta con una exponencial de 12 ms. Eso
    saca el hat del contratiempo que se cuela en la cola del kick sin tocarle el
    click del ataque, que es lo que le da la definicion. Cambia el timbre: por
    eso se guardan las dos mediciones de bleed, cruda y limpia.
    """
    w = y[s:s + int(c.ventana_ms / 1000 * SR)].astype(np.float64).copy()
    if c.guardar_hp:
        w = banda(w, c.guardar_hp, tipo="highpass")
    else:
        w = banda(w, 20, tipo="highpass")   # saca el DC, que en un kick pesa
        if limpiar:
            alto = banda(w, 4000, tipo="highpass")
            t = np.arange(len(w)) / SR
            w = (w - alto) + alto * np.exp(-t / 0.012)
    entrada = max(int(0.0008 * SR), 1)
    w[:entrada] *= np.linspace(0, 1, entrada)
    salida = int(len(w) * 0.25)
    w[-salida:] *= np.linspace(1, 0, salida) ** 1.5
    pico = float(np.max(np.abs(w)))
    return w / pico if pico > 1e-9 else w


# -- extraccion -------------------------------------------------------------
def _separados(candidatos: list[tuple[float, int]], cuantos: int,
               minimo_seg: float = 8.0) -> list[tuple[float, int]]:
    """Se queda con los mejores, pero espaciados en el tiempo.

    Sin esto los N mejores caen en el mismo compas de la intro y son el mismo
    golpe N veces. Espaciarlos da variantes reales del mismo sonido.
    """
    elegidos: list[tuple[float, int]] = []
    for puntaje, s in candidatos:
        if all(abs(s - otro) > minimo_seg * SR for _, otro in elegidos):
            elegidos.append((puntaje, s))
        if len(elegidos) >= cuantos:
            break
    return elegidos


def extraer_de_track(audio: np.ndarray, origen: str, destino: Path,
                     clases: list[str], por_clase: int = 3,
                     limpiar: bool = True) -> list[Golpe]:
    """Extrae y guarda los golpes de un track ya cargado en memoria.

    `audio` es mono a 44100. `origen` es el nombre del archivo fuente, que se
    escribe en el indice: de que track salio cada golpe no es un detalle, es la
    unica forma de rastrear el material despues.
    """
    destino.mkdir(parents=True, exist_ok=True)
    golpes: list[Golpe] = []
    for nombre in clases:
        c = CLASES[nombre]
        for k, (_, s) in enumerate(_separados(_candidatos(audio, c), por_clase), 1):
            crudo = audio[s:s + int(c.ventana_ms / 1000 * SR)]
            w = _recortar(audio, s, c, limpiar)
            archivo = destino / f"{nombre}_{k:02d}.wav"
            sf.write(str(archivo), w, SR, subtype="PCM_24")
            bleed = float(bleed_db(w))
            golpes.append(Golpe(
                clase=nombre, archivo=archivo.name, origen=origen,
                segundo=round(s / SR, 2), dur_ms=round(len(w) / SR * 1000, 1),
                bleed_db=round(bleed, 1),
                bleed_db_crudo=round(float(bleed_db(crudo)), 1),
                sub_pct=round(float(sub_pct(w)), 1),
                centroide_hz=round(centroide_hz(w), 0),
                limpio=bool(bleed <= BLEED_ACEPTABLE_DB),
            ))
    return golpes


# -- consumo: lo que usa render_sketch --------------------------------------
# El .mid de bateria habla en alturas MIDI; la carpeta de samples habla en
# nombres de clase. Este es el unico lugar donde se traducen.
ALTURA_A_CLASE = {36: "kick", 39: "clap", 42: "hat", 46: "hat_abierto",
                  51: "hat_abierto", 70: "hat"}


def cargar_muestras(carpeta: Path) -> dict[str, list[np.ndarray]]:
    """Carga todas las variantes de cada clase que haya en la carpeta.

    Devuelve solo lo que encontro. Lo que falte lo resuelve quien llama con su
    sintesis: una carpeta con kick y sin hat tiene que seguir funcionando.

    Las variantes se devuelven en lista porque alternarlas golpe a golpe es
    medio metro de lo que separa una bateria de una caja de ritmos: el mismo
    archivo repetido 900 veces vuelve a sonar a maquina aunque el sample sea
    real.
    """
    muestras: dict[str, list[np.ndarray]] = {}
    for nombre in CLASES:
        variantes = []
        # El patron pide dos digitos a proposito: con `{nombre}_*.wav`, la clase
        # `hat` se comia tambien los `hat_abierto_01.wav` y el hat cerrado
        # terminaba tocando hats abiertos la mitad de las veces.
        for archivo in sorted(carpeta.glob(f"{nombre}_[0-9][0-9].wav")):
            y, sr = sf.read(str(archivo))
            if sr != SR:
                raise ValueError(f"{archivo.name} esta a {sr} Hz, se esperaba {SR}")
            y = np.asarray(y, dtype=np.float64)
            variantes.append(y.mean(axis=1) if y.ndim > 1 else y)
        if variantes:
            muestras[nombre] = variantes
    return muestras


def igualar_energia(muestra: np.ndarray, referencia: np.ndarray) -> np.ndarray:
    """Escala la muestra a la energia total de la voz sintetica que reemplaza.

    Sin esto la comparacion sintesis vs samples mide dos mezclas distintas y la
    diferencia no se puede atribuir al timbre. Igualada la energia, lo unico que
    cambia entre las dos maquetas es de que esta hecho el golpe.

    Se iguala energia total (suma de cuadrados) y no RMS a proposito: los dos
    golpes duran distinto — 350 ms el sample contra 420 ms el sintetico — y el
    RMS promedia sobre la duracion, asi que igualarlo dejaria al mas corto
    aportando menos a la mezcla. Lo que pesa en una mezcla es la energia que
    entrega el golpe, no su promedio temporal.
    """
    e_muestra = float(np.sum(muestra ** 2))
    e_ref = float(np.sum(referencia ** 2))
    if e_muestra < 1e-12:
        return muestra
    return muestra * np.sqrt(e_ref / e_muestra)
