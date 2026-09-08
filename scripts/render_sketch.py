"""Sintetiza un boceto MIDI a audio, para escucharlo sin abrir un DAW.

No hay ningun instrumento instalado en esta maquina, asi que las voces se
sintetizan a mano: aditivas para los tonales, ruido filtrado y barrido de
frecuencia para la bateria. Los efectos y la cadena de master son `pedalboard`.

El objetivo no es que suene terminado — es escuchar si la armonia, el groove y
la forma funcionan antes de invertir una tarde en elegir sonidos. Un boceto que
se escucha se descarta en treinta segundos si esta mal.

Arma una maqueta de 64 compases con ocho tramos: aire, pulso, groove, build,
breakdown, drop, meseta y salida. Arranca casi vacia a proposito y suma capas
tramo a tramo. Lo que la separa de un loop repetido es el filtro que se abre a
lo largo del build, el riser antes del drop, el golpe que lo marca, el sidechain
que cambia de profundidad por tramo y el ensanchado mid/side por bus.

Con `--samples` la bateria deja de sintetizarse y usa golpes reales extraidos
de la biblioteca con `scripts/extraer_golpes.py`. Ese es el unico camino que
rompe el techo del enfoque: la sintesis mide bien contra las plantillas pero da
el mismo timbre en cualquier registro, y el timbre es lo que hace que una
maqueta suene a maquina. Los golpes reales entran igualados en energia a la voz
sintetica que reemplazan, para que lo unico que cambie sea de que esta hecho el
sonido. Sin el flag funciona como siempre: los samples son opcionales.

Ojo: los golpes salen de grabaciones ajenas. Son referencia de timbre para
escuchar un boceto, no material para publicar. Ver `data/samples/README.md`.

Uso:
    python scripts/render_sketch.py postproduction/bocetos/eze_arias_4A
    python scripts/render_sketch.py <carpeta> --plantilla data/plantillas/vuarambon.json --abrir
    python scripts/render_sketch.py <carpeta> --samples data/samples/<origen>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import librosa  # noqa: E402
import numpy as np  # noqa: E402
import pyloudnorm  # noqa: E402
import soundfile as sf  # noqa: E402
from pedalboard import (  # noqa: E402
    Chorus, Compressor, Delay, HighShelfFilter, HighpassFilter, Limiter,
    LowpassFilter, Pedalboard, Reverb,
)
from scipy.signal import butter, lfilter, lfilter_zi, sosfiltfilt  # noqa: E402

from plomo.golpes import (  # noqa: E402
    ALTURA_A_CLASE, cargar_muestras, igualar_energia,
)
from plomo.midi import leer  # noqa: E402

SR = 44100
PULSOS_POR_COMPAS = 4
LUFS_OBJETIVO = -9.2   # entre la plantilla de Eze Arias y la de Vuarambon
COMPASES_POR_TRAMO = 8
KICK, CLAP, CHH, OHH, RIDE, SHAKER = 36, 39, 42, 46, 51, 70
# Realce de aire del master, en dB sobre 8.5 kHz. Dos valores porque son
# dos fuentes de sonido distintas: la sintesis no llega arriba de 10 kHz y
# hay que ayudarla; un hat real ya trae ese aire puesto.
AIRE_SINTESIS_DB = 4.5
AIRE_SAMPLES_DB = 0.0

# Seis tramos de 8 compases. Cada uno declara que suena, cuanto abre el filtro
# del pad (Hz, del principio al final del tramo) y cuanto duckea el sidechain.
# El corte del pad es la automatizacion que mas cambia la sensacion: un pad
# cerrado que se abre a lo largo del build es la mitad del genero.
# Las ganancias suben tramo a tramo a proposito: si la entrada ya viene al
# maximo, el drop no puede ser mas grande que nada y el track queda plano. El
# drop pasa de 1.0 porque tiene que ganarle al build, no empatarle.
# Los cortes del pad arrancan mas arriba de lo que la intuicion pide: con el
# filtro en 300-780 Hz durante el primer 30% del track, casi la mitad de la
# maqueta no tenia nada en la banda media y el balance quedaba -3 puntos contra
# la referencia. Un pad cerrado abre el arco, pero cerrado de mas es un hueco.
#
# Tramos por FRACCION del track, no por bloques iguales de 8 compases. Las
# proporciones salen de `data/plantillas/lo_tocado.json`, que midio los 39
# tracks mas reproducidos: groove hasta el 52%, breakdown 11%, drop 37% —
# y el drop llega hasta el final, no hay seccion de salida. Los bloques fijos
# obligaban a inventar una meseta y una salida que el corpus no tiene.
ARREGLO = [
    {"nombre": "aire",      "hasta": 0.14, "corte": (420, 700),   "duck": 0.32,
     "g": {"bateria": 0.45, "bajo": 0.0, "acordes": 0.25, "arpegio": 0.0, "melodia": 0.0}},
    {"nombre": "pulso",     "hasta": 0.30, "corte": (700, 1150),   "duck": 0.46,
     "g": {"bateria": 0.70, "bajo": 0.65, "acordes": 0.40, "arpegio": 0.0, "melodia": 0.0}},
    {"nombre": "groove",    "hasta": 0.44, "corte": (1150, 1900),  "duck": 0.55,
     "g": {"bateria": 0.88, "bajo": 0.90, "acordes": 0.68, "arpegio": 0.34, "melodia": 0.0}},
    {"nombre": "build",     "hasta": 0.52, "corte": (1900, 3400), "duck": 0.60,
     "g": {"bateria": 0.95, "bajo": 0.98, "acordes": 0.92, "arpegio": 0.95, "melodia": 0.39}},
    {"nombre": "breakdown", "hasta": 0.63, "corte": (3000, 1900), "duck": 0.0,
     "g": {"bateria": 0.0, "bajo": 0.0, "acordes": 1.0, "arpegio": 0.27, "melodia": 1.34}},
    {"nombre": "drop",      "hasta": 0.82, "corte": (2400, 3200), "duck": 0.64,
     "g": {"bateria": 1.20, "bajo": 1.18, "acordes": 1.05, "arpegio": 1.22, "melodia": 1.48}},
    {"nombre": "drop pleno", "hasta": 1.00, "corte": (3200, 2600), "duck": 0.62,
     "g": {"bateria": 1.15, "bajo": 1.12, "acordes": 1.0, "arpegio": 1.16, "melodia": 1.2}},
]




def _frec(altura: int) -> float:
    return 440.0 * 2 ** ((altura - 69) / 12)


def _env(n: int, ataque: float, decaimiento: float, sostenido: float,
         suelta: float) -> np.ndarray:
    """Envolvente ADSR simple, en muestras."""
    a = max(int(ataque * SR), 1)
    d = max(int(decaimiento * SR), 1)
    r = max(int(suelta * SR), 1)
    s = max(n - a - d, 0)
    e = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sostenido, d),
        np.full(s, sostenido),
    ])[:n]
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)), constant_values=sostenido)
    cola = min(r, n)
    e[n - cola:] *= np.linspace(1, 0, cola)
    return e


def _aditivo(f: float, n: int, armonicos: int, caida: float) -> np.ndarray:
    """Suma de armonicos con caida 1/h**caida. Sin alias: corta en Nyquist."""
    t = np.arange(n) / SR
    y = np.zeros(n)
    for h in range(1, armonicos + 1):
        if f * h >= SR / 2:
            break
        y += np.sin(2 * np.pi * f * h * t) / h ** caida
    return y


# -- voces ------------------------------------------------------------------
def voz_pad(f: float, dur: float, vel: int) -> np.ndarray:
    n = int(dur * SR)
    y = sum(_aditivo(f * c, n, 10, 1.1) for c in (0.9965, 1.0, 1.0035)) / 3
    return y * _env(n, 0.30, 0.7, 0.80, 1.6) * (vel / 127) * 0.17


def voz_bajo(f: float, dur: float, vel: int) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    # Sub adelante y poco armonico. Un bajo hipnotico se sostiene con el
    # fundamental; los armonicos altos lo suben al medio y lo vuelven melodico,
    # que es lo contrario de anclar.
    y = (np.sin(2 * np.pi * f * t)
         + 0.62 * np.sin(2 * np.pi * f * 2 * t)
         + 0.18 * np.sin(2 * np.pi * f * 3 * t))
    return y * np.exp(-t / 0.165) * _env(n, 0.004, 0.02, 1.0, 0.05) * (vel / 127) * 0.80


def voz_pluck(f: float, dur: float, vel: int) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    # 14 armonicos con caida mas suave: el arpegio es el unico tonal que puede
    # aportar arriba de 2 kHz sin ensuciar el medio donde vive el pad.
    return (_aditivo(f, n, 14, 1.05) * np.exp(-t / 0.10)
            * _env(n, 0.003, 0.01, 1.0, 0.02) * (vel / 127) * 0.11)


def voz_lead(f: float, dur: float, vel: int) -> np.ndarray:
    """Lead heroico: mas armonicos y tres osciladores desafinados.

    Una linea que se canta necesita cuerpo en los medios altos. El pad vive
    filtrado abajo; esta tiene que atravesar por arriba sin gritar.
    """
    n = int(dur * SR)
    y = (_aditivo(f, n, 9, 1.25)
         + 0.55 * _aditivo(f * 1.004, n, 7, 1.35)
         + 0.30 * _aditivo(f * 0.996, n, 5, 1.4))
    return y * _env(n, 0.06, 0.30, 0.85, 0.30) * (vel / 127) * 0.13


def _ruido(n: int, semilla: int = 7) -> np.ndarray:
    return np.random.default_rng(semilla).standard_normal(n)


def golpe_kick() -> np.ndarray:
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    # barrido de 150 a 48 Hz: el "punch" es la caida de altura, no el volumen
    f = 48 + 102 * np.exp(-t / 0.028)
    cuerpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.19)
    click = _ruido(n) * np.exp(-t / 0.0025) * 0.35
    return (cuerpo + click) * 1.05


def golpe_clap() -> np.ndarray:
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k, retardo in enumerate((0.0, 0.009, 0.019)):
        i = int(retardo * SR)
        y[i:] += (_ruido_banda(n - i, 900, 5200) *
                  np.exp(-np.arange(n - i) / SR / 0.011) * (0.9 ** k))
    cola = _ruido_banda(n, 700, 3800, 13) * np.exp(-t / 0.09) * 0.28
    return (y + cola) * 0.26


def _ruido_banda(n: int, lo: float, hi: float, semilla: int = 7) -> np.ndarray:
    """Ruido acotado a una banda. El ruido blanco pelado raspa: tiene energia
    hasta 22 kHz y ninguna percusion real la tiene."""
    ny = SR / 2
    sos = butter(4, [lo / ny, min(hi, ny * 0.98) / ny], btype="band", output="sos")
    return sosfiltfilt(sos, _ruido(n, semilla))


def golpe_hat(abierto: bool) -> np.ndarray:
    """Hat filtrado, no un estallido de ruido blanco.

    El hat de un 909 crudo tiene energia plana hasta arriba de todo y en un
    progressive suena a arena. Aca: banda acotada, algo de contenido metalico
    inarmonico, y una entrada de 1.5 ms que le saca el click del ataque.
    """
    tau = 0.065 if abierto else 0.014
    n = int((0.28 if abierto else 0.07) * SR)
    t = np.arange(n) / SR
    banda = _ruido_banda(n, 5000 if abierto else 6800, 12500)
    metal = sum(np.sin(2 * np.pi * f * t) for f in (6100, 8400, 10900)) / 3
    y = (banda * 0.82 + metal * 0.18) * np.exp(-t / tau)
    entrada = int(0.0015 * SR)
    y[:entrada] *= np.linspace(0, 1, entrada)
    return y * (0.070 if abierto else 0.042)


def golpe_shaker() -> np.ndarray:
    """Shaker: lo que sostiene el movimiento en el palo Cattaneo/Vuarambon.

    Va donde iria el hat de semicorcheas, pero mas corto, mas agudo y mucho mas
    abajo en la mezcla. Se siente antes de escucharse.
    """
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    y = _ruido_banda(n, 6000, 12500, 17) * np.exp(-t / 0.010)
    entrada = int(0.002 * SR)
    y[:entrada] *= np.linspace(0, 1, entrada)
    return y * 0.030


def golpe_ride() -> np.ndarray:
    """Ride: parciales metalicos inarmonicos + ruido. Sube la sensacion de
    movimiento sin sumar volumen, que es para lo que sirve en la segunda mitad."""
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    metal = sum(np.sin(2 * np.pi * f * t) for f in (3100, 4300, 5700, 7300)) / 4
    return (metal * 0.4 + _ruido(n, 11) * 0.6) * np.exp(-t / 0.13) * 0.075


# -- automatizacion ---------------------------------------------------------
def _lowpass_variable(x: np.ndarray, cortes: np.ndarray, bloque: int = 2048) -> np.ndarray:
    """Pasabajos con frecuencia de corte que cambia en el tiempo.

    Se filtra por bloques arrastrando el estado del filtro, que es lo que evita
    el chasquido en cada cambio de coeficiente.
    """
    salida = np.zeros_like(x)
    for canal in range(x.shape[0]):
        estado = None
        for i in range(0, x.shape[1], bloque):
            tramo = x[canal, i:i + bloque]
            if not len(tramo):
                break
            fc = float(np.clip(cortes[i:i + bloque].mean(), 60, SR / 2 * 0.95))
            b, a = butter(2, fc / (SR / 2), btype="low")
            if estado is None:
                estado = lfilter_zi(b, a) * tramo[0]
            salida[canal, i:i + bloque], estado = lfilter(b, a, tramo, zi=estado)
    return salida


def _ensanchar(x: np.ndarray, cantidad: float) -> np.ndarray:
    """Ensancha el estereo por mid/side. cantidad 1.0 = sin cambio.

    El pad y el arpegio de la maqueta salian casi mono (0.81 de correlacion en
    el medio contra 0.54 de la referencia). Sumar reverb para ganar ancho trae
    de vuelta la cola larga; el mid/side ensancha sin agregar cola.

    El grave NO se toca: el sub tiene que quedar mono o se cancela en un sistema
    grande.
    """
    mid = (x[0] + x[1]) * 0.5
    side = (x[0] - x[1]) * 0.5 * cantidad
    return np.vstack([mid + side, mid - side])


def _bordes(largo: int, util: int) -> list[tuple[int, int]]:
    """Muestra de inicio y fin de cada tramo, segun su fraccion del track."""
    out, desde = [], 0
    for t in ARREGLO:
        hasta = min(int(t["hasta"] * util), largo)
        out.append((desde, max(hasta, desde + 1)))
        desde = hasta
    return out


def _curva(largo: int, valores: list[float], bordes: list[tuple[int, int]],
           rampa_seg: float = 0.5) -> np.ndarray:
    """Valor por tramo, con rampa en los bordes para que no chasquee."""
    g = np.zeros(largo)
    for v, (i, fin) in zip(valores, bordes):
        g[i:fin] = v
    if valores:
        g[bordes[-1][1]:] = valores[-1]
    r = int(rampa_seg * SR)
    for k in range(1, len(valores)):
        i = bordes[k][0]
        if i + r < largo and i - r > 0:
            g[i - r:i + r] = np.linspace(valores[k - 1], valores[k], 2 * r)
    return g


def _curva_lineal(largo: int, pares: list[tuple[float, float]],
                  bordes: list[tuple[int, int]]) -> np.ndarray:
    """Interpola de principio a fin DENTRO de cada tramo, no solo en el borde.

    Es la diferencia entre un filtro que salta de un valor a otro y uno que se
    abre a lo largo de todo el tramo.
    """
    g = np.zeros(largo)
    for (ini, fin_v), (i, fin) in zip(pares, bordes):
        g[i:fin] = np.linspace(ini, fin_v, fin - i)
    if pares:
        g[bordes[-1][1]:] = pares[-1][1]
    return g


# Cuanto puede moverse cada parte de una vuelta a la otra. La bateria casi
# nada — un kick que se corre se escucha como error, no como humano.
VARIACION = {
    #             timing_ms  vel_%   prob. de hueco
    "bateria":   (      6.0,  0.08,           0.03),
    "bajo":      (     11.0,  0.10,           0.06),
    "acordes":   (     16.0,  0.12,           0.05),
    "arpegio":   (     14.0,  0.16,           0.14),
    "melodia":   (     18.0,  0.10,           0.04),
}
# Alturas de la bateria que nunca se saltean: sacar un kick o un clap rompe el
# pulso, y el hueco deja de leerse como respiracion.
INTOCABLES_PERC = {36, 39}

# Cada cuantas vueltas del loop suena realmente cada parte. Un gancho que suena
# 29 veces seguidas deja de ser un gancho: la melodia aparece cada dos vueltas y
# el arpegio se toma una de cada tres. El silencio de una parte es lo que hace
# que se note cuando vuelve.
# Ojo: bajar la frecuencia baja tambien el aporte promedio de esa parte al
# balance. Sacar un tercio del arpegio y media melodia hundio el medio de 7.5%
# a 5.1%. Las ganancias en ARREGLO estan compensadas por eso — si se cambian
# estos numeros, hay que volver a compensarlas.
CADA = {"melodia": 2, "arpegio": 3}
# Que vuelta de cada ciclo se saltea (para que no coincidan todas en la misma).
DESFASE = {"melodia": 1, "arpegio": 2}


def _semilla(*partes) -> int:
    """Semilla estable entre corridas.

    Antes esto era `hash((nombre, vuelta, inicio, altura))`. El `hash()` de
    Python sobre strings esta aleatorizado por proceso (PYTHONHASHSEED), asi que
    cada corrida daba OTRO microtiming y OTROS huecos sobre el mismo MIDI —
    justo lo contrario de lo que promete el docstring de `variar`. Con eso, dos
    maquetas nunca eran comparables: la diferencia medida entre una version y
    otra incluia una interpretacion distinta, no solo el cambio que se queria
    probar. blake2b no depende del proceso.
    """
    crudo = "|".join(str(p) for p in partes).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(crudo, digest_size=4).digest(), "big")


def variar(notas, loop_pulsos: float, nombre: str, seg_por_pulso: float):
    """Hace que cada vuelta del loop sea distinta de la anterior.

    Es la correccion de "suena a robot". El swing y el jitter de `make_sketch`
    viven ADENTRO de los 8 compases; despues esos 8 compases se copiaban 28
    veces con exactamente la misma variacion. Una maquina no es la que cuantiza:
    es la que repite la misma imperfeccion.

    Cada vuelta recibe su propia semilla, asi que el resultado sigue siendo
    identico entre corridas y dos versiones se pueden comparar.
    """
    jit_ms, jit_vel, p_hueco = VARIACION.get(nombre, (10.0, 0.1, 0.05))
    salida = []
    for inicio, dur, altura, vel in notas:
        vuelta = int(inicio // loop_pulsos)
        rng = np.random.default_rng(_semilla(nombre, vuelta, round(inicio, 3),
                                             altura))
        # la vuelta entera sube o baja de intensidad, como una mano que se cansa
        # o se entusiasma; encima de eso, cada nota tiene su propio desvio
        rng_v = np.random.default_rng(_semilla(nombre, vuelta))
        nivel = 1.0 + rng_v.uniform(-jit_vel, jit_vel)
        if rng.random() < p_hueco and not (
                nombre == "bateria" and altura in INTOCABLES_PERC):
            continue
        corrida = rng.normal(0, jit_ms / 1000) / seg_por_pulso
        v = int(np.clip(vel * nivel * (1 + rng.normal(0, jit_vel / 2)), 1, 127))
        salida.append((max(0.0, inicio + corrida), dur, altura, v))
    return salida


def capa_aire(largo: int, seg_por_pulso: float) -> np.ndarray:
    """Cama de textura: ruido filtrado arriba, con respiracion lenta.

    Existe porque el aire de un progressive no sale de los instrumentos
    tonales. Las voces de aca son sumas de armonicos con caida 1/h: el armonico
    20 de un pad de 100 Hz queda en 2 kHz con amplitud 0.036, o sea nada. En un
    track real esa banda la llenan la percusion, las colas de reverb y una capa
    de textura — vinilo, campo, shimmer. Sin ella la maqueta mide 2.5% de aire
    contra 4.4% de la referencia, y no es un problema de ecualizacion: es una
    capa que falta.

    Se mueve despacio a proposito: si pulsa al ritmo se vuelve un instrumento,
    y esto tiene que sentirse como el aire del cuarto.
    """
    t = np.arange(largo) / SR
    base = _ruido_banda(largo, 3000, 17000, 41)
    # dos LFO lentos e inconmensurables para que no se escuche el ciclo
    resp = (0.55 + 0.45 * np.sin(2 * np.pi * t / (seg_por_pulso * 32))
            * np.sin(2 * np.pi * t / (seg_por_pulso * 13.7)))
    # Haas parcial: con el canal derecho retrasado entero la correlacion se iba
    # a 0.16 contra 0.44 de la referencia — mas ancho que un track real, que es
    # tan defecto como ser mono. Se mezcla mitad directo, mitad retrasado.
    retrasado = np.roll(base, int(0.006 * SR))
    izq = base * resp
    der = (0.55 * base + 0.45 * retrasado) * resp
    # 0.012 y no 0.055. La habia subido para que la banda de aire llegara al
    # 4.4% de la referencia; el resultado medía bien y sonaba a ruido. La
    # referencia tiene aire de colas de reverb y de platillos, no de una cama de
    # ruido constante: llenar la banda correcta con el material equivocado da el
    # numero y no da el sonido.
    return np.vstack([izq, der]) * 0.012


def _riser(largo: int, fin_muestra: int, dur_seg: float) -> np.ndarray:
    """Ruido que sube en filtro y en volumen hasta el golpe. Anuncia el drop."""
    n = int(dur_seg * SR)
    i = max(fin_muestra - n, 0)
    n = fin_muestra - i
    if n <= 0:
        return np.zeros((2, largo))
    t = np.linspace(0, 1, n)
    crudo = _ruido(n, 23)
    filtrado = _lowpass_variable(np.vstack([crudo, crudo]), 400 + 6000 * t ** 2)
    filtrado *= (t ** 2.2) * 0.085
    buf = np.zeros((2, largo))
    buf[:, i:i + n] = filtrado
    return buf


def _impacto(largo: int, inicio: int) -> np.ndarray:
    """Golpe grave + aire en el compas 1 del drop. Marca el momento."""
    n = min(int(2.2 * SR), largo - inicio)
    if n <= 0:
        return np.zeros((2, largo))
    t = np.arange(n) / SR
    f = 28 + 65 * np.exp(-t / 0.13)
    grave = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55) * 0.5
    aire = _ruido(n, 31) * np.exp(-t / 0.30) * 0.10
    buf = np.zeros((2, largo))
    buf[0, inicio:inicio + n] = grave + aire
    buf[1, inicio:inicio + n] = grave + np.roll(aire, 40)
    return buf


# -- render -----------------------------------------------------------------
def _render_tonal(notas, voz, largo: int, seg_por_pulso: float,
                  ancho: float = 0.0) -> np.ndarray:
    """Mezcla las notas en un buffer estereo. `ancho` reparte por altura."""
    buf = np.zeros((2, largo))
    for inicio, dur, altura, vel in notas:
        i = int(inicio * seg_por_pulso * SR)
        y = voz(_frec(altura), dur * seg_por_pulso + 0.35, vel)
        fin = min(i + len(y), largo)
        if fin <= i:
            continue
        y = y[:fin - i]
        pan = np.clip((altura % 12 - 5.5) / 5.5, -1, 1) * ancho
        buf[0, i:fin] += y * (1 - pan) * 0.5
        buf[1, i:fin] += y * (1 + pan) * 0.5
    return buf


def _sinteticos() -> dict[int, np.ndarray]:
    """La bateria sintetizada. Es el fallback y la referencia de nivel."""
    return {KICK: golpe_kick(), CLAP: golpe_clap(), CHH: golpe_hat(False),
            OHH: golpe_hat(True), RIDE: golpe_ride(), SHAKER: golpe_shaker()}


def _banco(carpeta: Path | None) -> tuple[dict[int, list[np.ndarray]], dict[int, str]]:
    """Arma el banco de golpes: samples reales donde haya, sintesis donde no.

    Sin `--samples` devuelve la sintesis de siempre, que es el unico modo que
    funciona sin depender de nada externo. Con samples, cada clase que exista en
    la carpeta reemplaza a su voz sintetica IGUALADA EN ENERGIA, para que la
    unica variable que cambie entre las dos maquetas sea el timbre.

    El sub del kick se deja sin tocar: es el sonido que se vino a buscar.
    """
    sint = _sinteticos()
    banco = {altura: [y] for altura, y in sint.items()}
    fuente = {altura: "sintesis" for altura in sint}
    if carpeta is None:
        return banco, fuente
    if not carpeta.exists():
        sys.exit(f"no existe la carpeta de samples {carpeta}")
    muestras = cargar_muestras(carpeta)
    if not muestras:
        print(f"  (en {carpeta} no hay golpes; se sintetiza todo)")
        return banco, fuente
    for altura, clase in ALTURA_A_CLASE.items():
        if clase not in muestras or altura not in sint:
            continue
        banco[altura] = [igualar_energia(v, sint[altura]) for v in muestras[clase]]
        fuente[altura] = f"{clase} x{len(banco[altura])}"
    return banco, fuente


def _avisar_fuente(carpeta: Path | None, fuente: dict[int, str]) -> None:
    """Deja dicho de que esta hecho cada golpe. Si no se dice, no se sabe."""
    nombres = {KICK: "kick", CLAP: "clap", CHH: "hat", OHH: "hat abierto",
               RIDE: "ride", SHAKER: "shaker"}
    if carpeta is None:
        print("  golpes:   sintesis (sin --samples)")
        return
    detalle = ", ".join(f"{nombres[a]}={fuente[a]}" for a in nombres if a in fuente)
    print(f"  golpes:   {carpeta.name}")
    print(f"            {detalle}")
    print("            material con derechos: referencia de timbre, no para publicar")


def _render_bateria(notas, largo: int, seg_por_pulso: float,
                    banco: dict[int, list[np.ndarray]]) -> tuple[np.ndarray, list[int]]:
    buf = np.zeros((2, largo))
    kicks: list[int] = []
    # Vuelta por vuelta se rota entre las variantes de cada clase. Con un solo
    # archivo por clase esto no hace nada; con tres, saca el efecto ametralladora
    # de escuchar exactamente la misma forma de onda 900 veces seguidas.
    turno: dict[int, int] = {}
    for inicio, _, altura, vel in notas:
        variantes = banco.get(altura)
        if not variantes:
            continue
        turno[altura] = turno.get(altura, -1) + 1
        y = variantes[turno[altura] % len(variantes)]
        i = int(inicio * seg_por_pulso * SR)
        if altura == KICK:
            kicks.append(i)
        fin = min(i + len(y), largo)
        if fin <= i:
            continue
        golpe = y[:fin - i] * (vel / 127)
        pan = {CHH: 0.25, OHH: -0.25, RIDE: 0.4, SHAKER: -0.35}.get(altura, 0.0)
        buf[0, i:fin] += golpe * (1 - pan) * 0.5
        buf[1, i:fin] += golpe * (1 + pan) * 0.5
    return buf, kicks


def _sidechain(largo: int, kicks: list[int], tau: float = 0.21) -> np.ndarray:
    """Ducking contra el kick a profundidad 1. Se escala despues por tramo.

    Es lo que hace respirar a un progressive: sin esto el pad tapa el bombo y
    suena a maqueta de teclado.
    """
    g = np.ones(largo)
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    curva = 1 - np.exp(-t / tau)
    ataque = int(0.003 * SR)
    curva[:ataque] = np.linspace(1, curva[ataque], ataque)
    for i in kicks:
        fin = min(i + n, largo)
        g[i:fin] = np.minimum(g[i:fin], curva[:fin - i])
    return g


def _comparar(mezcla: np.ndarray, kicks: list[int], largo: int,
              plantilla: Path | None = None) -> None:
    """Mide la maqueta contra la plantilla que la genero.

    Se compara track entero contra track entero, que es como `derive_template`
    calcula el balance de la referencia. Se reporta ademas el reparto medido
    solo en los tramos con kick, que aisla la mezcla del arreglo — pero como
    dato al lado, no como resta: restar una medida contra la otra mete un sesgo
    de +3.5 puntos de sub que se lee como error de mezcla y no lo es.
    """
    # Antes agarraba la primera plantilla alfabetica del glob: el dia que
    # existio vuarambon.json la maqueta se seguia comparando contra Eze Arias,
    # en silencio. La plantilla se elige explicita.
    if plantilla is None:
        candidatas = sorted((Path(__file__).resolve().parent.parent / "data" /
                             "plantillas").glob("*.json"))
        if not candidatas:
            return
        plantilla = candidatas[0]
        print(f"\n  (sin --plantilla: se usa {plantilla.name})")
    if not plantilla.exists():
        sys.exit(f"no existe la plantilla {plantilla}")
    ref = json.loads(plantilla.read_text(encoding="utf-8"))

    bandas = {"sub": (20, 60), "bajo": (60, 250), "medio": (250, 2000),
              "aire": (2000, 16000)}

    def reparto(x: np.ndarray) -> dict[str, float]:
        """Reparto por bandas con el MISMO metodo que construyo la plantilla.

        `derive_template.py` llama a `reverse_engineer.analizar`, que mide con
        una STFT de n_fft=4096. Aca antes se media con una rfft de todo el
        archivo de una. No son la misma medida: con 4096 muestras el sub tiene
        cuatro bins y la ventana de Hann desparrama energia entre ellos, asi que
        la rfft entera leia hasta 2.5 puntos mas de sub sobre el mismo WAV.
        Toda esa diferencia era del metodo, y se estaba reportando como delta de
        mezcla contra la referencia.
        """
        S = np.abs(librosa.stft(x.astype(np.float32), n_fft=4096)) ** 2
        f = librosa.fft_frequencies(sr=SR, n_fft=4096)
        total = float(S.sum()) or 1e-9
        return {n: float(S[(f >= lo) & (f < hi)].sum()) / total * 100
                for n, (lo, hi) in bandas.items()}

    con_kick = np.zeros(largo, dtype=bool)
    for i in kicks:
        con_kick[i:min(i + int(0.5 * SR), largo)] = True
    mono = mezcla.mean(axis=0)
    if con_kick.sum() < SR:
        return
    entera, solo_kick = reparto(mono), reparto(mono[con_kick])

    # La columna que se RESTA es la del track entero, porque asi calcula el
    # balance `derive_template.py`. Antes se restaba kick-only contra una
    # referencia de track entero: no son la misma medida y el sesgo llegaba a
    # +3.5 puntos de sub, o sea que parte del error reportado era del metodo.
    # La kick-only queda al lado porque sirve —aisla la mezcla del arreglo—
    # pero no se compara contra nada.
    print(f"\n  contra '{ref.get('nombre', '?')}' ({ref['n_tracks']} tracks)")
    print(f"  {'':10} {'maqueta':>9} {'referencia':>11} {'delta':>8}"
          f" {'(solo kick)':>12}")
    for nombre in bandas:
        m, r = entera[nombre], ref["balance"][nombre]
        print(f"  {nombre:<10} {m:>8.1f}% {r:>10.1f}% {m - r:>+8.1f}"
              f" {solo_kick[nombre]:>11.1f}%")
    L, R = mezcla[0], mezcla[1]
    if L.std() > 1e-9 and R.std() > 1e-9:
        print(f"  {'ancho':<10} {float(np.corrcoef(L, R)[0, 1]):>9.2f} {'':>11}"
              "   (1.00 = mono)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("--compases", type=int, default=224,
                    help="224 a 123 BPM da 7.3 min, el largo mediano del corpus")
    ap.add_argument("--lufs", type=float, default=LUFS_OBJETIVO)
    ap.add_argument("--plantilla", type=Path,
                    help="contra que plantilla medir, ej data/plantillas/vuarambon.json")
    ap.add_argument("--samples", type=Path,
                    help="carpeta de golpes reales, ej data/samples/<origen>. "
                         "Sin esto se sintetiza todo, como antes")
    ap.add_argument("--abrir", action="store_true")
    args = ap.parse_args()

    archivos = {p.stem.split("_", 1)[1]: p for p in sorted(args.carpeta.glob("*.mid"))}
    faltan = {"acordes", "bajo", "arpegio", "bateria", "melodia"} - set(archivos)
    if faltan:
        sys.exit(f"faltan clips en {args.carpeta}: {', '.join(sorted(faltan))}")

    _, bpm, _ = leer(archivos["bateria"])
    seg_por_pulso = 60.0 / bpm
    largo = int(args.compases * PULSOS_POR_COMPAS * seg_por_pulso * SR) + SR
    util = int(args.compases * PULSOS_POR_COMPAS * seg_por_pulso * SR)
    bordes = _bordes(largo, util)

    print(f"boceto: {args.carpeta.name}   {bpm:.0f} BPM   {args.compases} compases "
          f"({args.compases * PULSOS_POR_COMPAS * 60 / bpm:.0f}s)")

    def repetir(notas, loop_pulsos: float, nombre: str):
        total = args.compases * PULSOS_POR_COMPAS
        cada, desf = CADA.get(nombre, 1), DESFASE.get(nombre, 0)
        repetidas = [(ini + v * loop_pulsos, dur, alt, vel)
                     for v in range(int(np.ceil(total / loop_pulsos)))
                     if v % cada != desf % cada or cada == 1
                     for ini, dur, alt, vel in notas
                     if ini + v * loop_pulsos < total]
        return variar(repetidas, loop_pulsos, nombre, seg_por_pulso)

    partes: dict[str, np.ndarray] = {}
    for nombre, voz, ancho in [("acordes", voz_pad, 0.35), ("bajo", voz_bajo, 0.0),
                               ("arpegio", voz_pluck, 0.8), ("melodia", voz_lead, 0.3)]:
        _, _, notas = leer(archivos[nombre])
        loop = np.ceil(max(n[0] + n[1] for n in notas)
                       / PULSOS_POR_COMPAS) * PULSOS_POR_COMPAS
        partes[nombre] = _render_tonal(repetir(notas, loop, nombre), voz, largo,
                                       seg_por_pulso, ancho)
        print(f"  {nombre:9} {len(notas):3d} notas, loop de {loop / 4:.0f} compases")

    _, _, notas_bat = leer(archivos["bateria"])
    loop_bat = np.ceil(max(n[0] + n[1] for n in notas_bat)
                       / PULSOS_POR_COMPAS) * PULSOS_POR_COMPAS
    banco, fuente = _banco(args.samples)
    partes["bateria"], kicks = _render_bateria(
        repetir(notas_bat, loop_bat, "bateria"), largo, seg_por_pulso, banco)
    print(f"  {'bateria':9} {len(notas_bat):3d} notas, {len(kicks)} kicks")
    _avisar_fuente(args.samples, fuente)

    tramos = ARREGLO

    # el pad se filtra con automatizacion; el resto va con cadena fija
    partes["acordes"] = _lowpass_variable(
        partes["acordes"], _curva_lineal(largo, [t["corte"] for t in tramos], bordes))

    cadenas = {
        "acordes": Pedalboard([Chorus(rate_hz=0.35, depth=0.6, mix=0.6),
                               Reverb(room_size=0.86, damping=0.42, wet_level=0.34,
                                      dry_level=0.80, width=1.0)]),
        "bajo": Pedalboard([LowpassFilter(420)]),
        "arpegio": Pedalboard([HighpassFilter(320),
                               Delay(delay_seconds=seg_por_pulso * 0.75,
                                     feedback=0.32, mix=0.26),
                               Reverb(room_size=0.6, wet_level=0.24,
                                      dry_level=0.85, width=1.0)]),
        # el ancho de la melodia lo pone el delay, no la reverb: la cola larga
        # es lo que la volvia coral
        "melodia": Pedalboard([Delay(delay_seconds=seg_por_pulso * 0.75,
                                     feedback=0.38, mix=0.34),
                               Reverb(room_size=0.75, wet_level=0.24,
                                      dry_level=0.86, width=1.0)]),
        "bateria": Pedalboard([Compressor(threshold_db=-14, ratio=2.5,
                                          attack_ms=4, release_ms=90)]),
    }

    duck_base = _sidechain(largo, kicks)
    prof = _curva(largo, [t["duck"] for t in tramos], bordes, rampa_seg=0.4)
    duck = 1 - (1 - duck_base) * prof   # profundidad de ducking por tramo

    # Cuanto se ensancha cada bus. El bajo y la bateria quedan como estan: el
    # sub mono es innegociable.
    ANCHO_BUS = {"acordes": 2.0, "arpegio": 2.2, "melodia": 1.7,
                 "bajo": 1.0, "bateria": 1.15}

    mezcla = np.zeros((2, largo))
    for nombre, audio in partes.items():
        audio = cadenas[nombre](audio.astype(np.float32), SR).astype(np.float64)
        audio = _ensanchar(audio, ANCHO_BUS[nombre])
        if nombre != "bateria":
            audio *= duck
        mezcla += audio * _curva(largo, [t["g"][nombre] for t in tramos], bordes,
                                 rampa_seg=1.6)

    # la cama de aire sigue el arreglo: entra con el groove y abre en el drop
    aire = capa_aire(largo, seg_por_pulso) * duck
    mezcla += aire * _curva(
        largo, [0.35, 0.6, 0.85, 1.0, 0.7, 1.0, 0.9], bordes, rampa_seg=1.0)

    # riser al final del breakdown y golpe en el compas 1 del drop
    for k, t in enumerate(tramos):
        if t["nombre"] == "drop" and k:
            inicio = bordes[k][0]
            mezcla += _riser(largo, inicio, dur_seg=6.0)
            mezcla += _impacto(largo, inicio)

    # El aire era la unica banda que fallaba contra la referencia en las dos
    # formas de medir (-2.0). Las voces sinteticas no lo tienen de fabrica: son
    # sumas de armonicos que se apagan mucho antes de los 10 kHz.
    #
    # Con `--samples` el realce baja: la correccion existia para tapar un agujero
    # de la sintesis, y un hat real ya trae su propio aire. Dejando los 4.5 dB
    # puestos, la maqueta con samples se iba a +6.0 contra la referencia — o sea
    # que parte del error medido lo generaba una compensacion que ya no hacia
    # falta. Cuando cambia la fuente del sonido hay que revisar los parches que
    # se le habian hecho a la fuente vieja.
    realce_aire = AIRE_SINTESIS_DB if args.samples is None else AIRE_SAMPLES_DB
    # El shelf de aire tambien salio: existia para tapar el mismo agujero y lo
    # unico que hacia era levantar el ruido que ya sobraba.
    mezcla = Pedalboard([HighShelfFilter(cutoff_frequency_hz=8500,
                                         gain_db=realce_aire),
                         Compressor(threshold_db=-3, ratio=1.15,
                                    attack_ms=35, release_ms=280)])(
        mezcla.astype(np.float32), SR).astype(np.float64)

    # Primero se sube al LUFS objetivo y despues limita. Al reves — bajarle la
    # ganancia a todo para que el pico entre — el track termina varios dB por
    # debajo del objetivo, que es exactamente lo que no se queria.
    medidor = pyloudnorm.Meter(SR)
    antes = medidor.integrated_loudness(mezcla.T)
    mezcla *= 10 ** ((args.lufs - antes) / 20)
    mezcla = Pedalboard([Limiter(threshold_db=-0.6, release_ms=90)])(
        mezcla.astype(np.float32), SR).astype(np.float64)
    despues = medidor.integrated_loudness(mezcla.T)

    wav = args.carpeta / "maqueta.wav"
    sf.write(str(wav), mezcla.T, SR, subtype="PCM_16")
    salida = wav
    try:
        mp3 = args.carpeta / "maqueta.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-b:a", "256k", str(mp3)], check=True)
        salida = mp3
    except (OSError, subprocess.CalledProcessError):
        print("  (sin ffmpeg: queda solo el WAV)")

    print("\n  forma: " + " | ".join(t["nombre"] for t in tramos))
    print(f"  {despues:.1f} LUFS   pico {20 * np.log10(np.max(np.abs(mezcla))):.1f} dBFS")
    _comparar(mezcla, kicks, largo, args.plantilla)
    print(f"\n-> {salida}")

    if args.abrir:
        subprocess.Popen(["cmd", "/c", "start", "", str(salida)], shell=False)


if __name__ == "__main__":
    main()
