"""Renderiza un DJ mix: cada tema estirado al tempo del set, y cada transicion con la tecnica del DJ.

LA TECNICA, MEDIDA Y NO SUPUESTA
--------------------------------
Los numeros de `Plantilla` salen de separar los dos decks en las tres transiciones
de la grabacion de consola del 2026-09-23 (agente `bajo`, regresion por banda):
- el entrante suena 40-75 s antes del cambio de bajos, con medios y agudos de 3 a
  12 dB abajo y el grave cortado (o a medias, -12 a -30 dB, al final);
- el cambio de bajos dura 2-4 s: el grave del saliente se va y el del entrante
  entra, con un pozo corto en el medio;
- despues, el saliente sigue 20-30 s sin sub, sus medios bajan a -6/-8 dB y se
  apaga.
A 122 BPM eso es entrar 32 compases antes y sacar el saliente en 12.

EL PUNTO DE CAMBIO
------------------
El grave del entrante entra donde entra el suyo (`bass_in`, medido y en frase) y
eso cae sobre el compas del saliente donde empiezan sus ultimos 16 de bombo
(`mix_out`, medido y en frase). No sobre los cues: "los cues no son 100%
precisos" y la medicion los corrige (ver `plomo.mezcla`).

TEMPO
-----
Constante para todo el set: dos bombos superpuestos necesitan coincidir en
menos de 5 ms, y el estirado variable de Rubber Band aplica sus cambios cada
23 ms. Cada tema se estira por un factor fijo, con la tonalidad intacta.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

import numpy as np
import pyloudnorm as pyln
from pedalboard import time_stretch
from scipy.signal import butter, sosfilt

from plomo.mezcla import Estructura, Tema

SR = 44100
CORTE_GRAVE_HZ = 180.0          # como el aislador de un mixer de tres bandas
CORTE_AGUDO_HZ = 2200.0
SILENCIO_DB = -60.0
LUFS_TRIM = -10.0               # todos los temas al mismo cuerpo antes de sumar


@dataclass(frozen=True)
class Plantilla:
    compases_antes: int = 32        # el entrante arranca 32 compases antes del cambio
    medios_inicio_db: float = -12.0
    medios_casi_db: float = -3.0    # ... a 8 compases del cambio
    grave_cortado_db: float = -40.0
    grave_parcial_db: float = -18.0  # los ultimos 8 compases antes del cambio
    salida_grave_tiempos: float = 2.0    # el grave del saliente se va en 2 tiempos
    entrada_grave_tiempos: float = 2.0   # el del entrante entra en 2 tiempos
    salida_compases: int = 12       # el saliente se apaga en 12 compases despues del cambio
    salida_medios_db: float = -6.0  # ... bajando primero a -6 dB en 8


@dataclass(frozen=True)
class Colocado:
    """Un tema ya ubicado en el mix: todo en segundos del MIX."""
    tema: Tema
    factor: float               # estiramiento: >1 acelera
    offset: float               # donde cae el segundo 0 del tema (estirado) en el mix
    desde: float                # desde donde suena (mix)
    hasta: float                # hasta donde suena (mix)
    cambio_in: float | None     # el cambio de bajos con el anterior
    cambio_out: float | None    # el cambio de bajos con el siguiente


def _compas_mix(t: Tema, factor: float, offset: float, compas: int) -> float:
    c = t.compases
    compas = min(max(compas, 0), len(c) - 1)
    return offset + c[compas] / factor


def planificar(temas: list[Tema], estructuras: list[Estructura], tempo: float,
               p: Plantilla = Plantilla()) -> list[Colocado]:
    """Donde arranca, donde termina y donde cambia de bajos cada tema."""
    seg_compas = 240.0 / tempo
    colocados: list[Colocado] = []
    offset, desde, cambio_in = 0.0, 0.0, None
    for i, (t, e) in enumerate(zip(temas, estructuras)):
        f = tempo / t.bpm
        if i > 0:
            ant, e_ant = colocados[-1], estructuras[i - 1]
            t_cambio = _compas_mix(ant.tema, ant.factor, ant.offset, e_ant.mix_out())
            # 32 compases antes del cambio, aunque el bajo propio arranque antes: suena con el grave cortado
            compas_in = max(e.bass_in, p.compases_antes)
            offset = t_cambio - t.compases[compas_in] / f
            desde = offset + t.compases[max(0, compas_in - p.compases_antes)] / f
            cambio_in = t_cambio
            colocados[-1] = Colocado(ant.tema, ant.factor, ant.offset, ant.desde,
                                     t_cambio + p.salida_compases * seg_compas, ant.cambio_in, t_cambio)
        hasta = offset + t.duracion / f       # el ultimo suena hasta el final
        colocados.append(Colocado(t, f, offset, desde, hasta, cambio_in, None))
    return colocados


def _envolventes(c: Colocado, tempo: float, p: Plantilla) -> dict[str, list[tuple[float, float]]]:
    """Puntos (segundo del mix, dB) por banda. Entre puntos, lineal en dB."""
    compas, tiempo = 240.0 / tempo, 60.0 / tempo
    grave, medio = [], []
    if c.cambio_in is None:
        grave += [(c.desde, 0.0)]
        medio += [(c.desde, 0.0)]
    else:
        x = c.cambio_in
        # el fader sube desde silencio en 2 compases, no aparece de golpe en -12
        medio += [(c.desde, SILENCIO_DB), (c.desde + 2 * compas, p.medios_inicio_db),
                  (x - 8 * compas, p.medios_casi_db), (x, 0.0)]
        grave += [(c.desde, p.grave_cortado_db), (x - 8 * compas, p.grave_cortado_db),
                  (x - 8 * compas + 0.01, p.grave_parcial_db), (x, p.grave_parcial_db),
                  (x + p.entrada_grave_tiempos * tiempo, 0.0)]
    if c.cambio_out is not None:
        y = c.cambio_out
        grave += [(y - p.salida_grave_tiempos * tiempo, 0.0), (y, p.grave_cortado_db)]
        medio += [(y, 0.0), (y + 8 * compas, p.salida_medios_db),
                  (y + p.salida_compases * compas, SILENCIO_DB)]
    else:
        grave += [(c.hasta, 0.0)]
        medio += [(c.hasta, 0.0)]
    return {"grave": grave, "medio": medio, "agudo": medio}


def _decodificar(ruta, desde_s: float, hasta_s: float) -> np.ndarray:
    """ffmpeg directo a float32 estereo: mucho mas rapido que audioread con mp3."""
    crudo = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, desde_s):.3f}",
                            "-to", f"{hasta_s:.3f}", "-i", str(ruta), "-f", "f32le", "-ac", "2",
                            "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(crudo, dtype=np.float32).reshape(-1, 2).copy()


BANDA_CLICK = (1000.0, 8000.0)   # el golpe que marca la grilla; el cuerpo del bombo llega 7-20 ms despues


def ataques_cerca(audio: np.ndarray, t0: float, tiempos: np.ndarray,
                  banda: tuple[float, float] = BANDA_CLICK, ventana_s: float = 0.040) -> tuple[np.ndarray, np.ndarray]:
    """Para cada tiempo de grilla, el ataque mas fuerte a +-40 ms y su fuerza.

    Se mide el CLICK (1-8 kHz) y no el cuerpo grave: entre uno y otro hay de 7 a 20 ms segun
    el diseno de cada bombo (medido por el agente `bajo`), asi que alinear cuerpos de dos
    bombos distintos los desfasa. La grilla de Rekordbox marca el golpe.
    """
    x = sosfilt(butter(4, banda, "bandpass", fs=SR, output="sos"), audio.mean(1))
    env = np.convolve(np.abs(x), np.ones(44) / 44, "same")              # 1 ms
    subida = np.diff(env, prepend=env[0])
    v = int(ventana_s * SR)
    cuando, fuerza = [], []
    for t in tiempos:
        i = int((t - t0) * SR)
        tramo = subida[max(0, i - v): i + v]
        if len(tramo) == 2 * v and tramo.max() > 0:
            k = int(np.argmax(tramo))
            cuando.append(t0 + (i - v + k) / SR)
            fuerza.append(tramo[k])
        else:
            cuando.append(np.nan)
            fuerza.append(0.0)
    return np.array(cuando), np.array(fuerza)


def _desfase_grilla(crudo: np.ndarray, ini: float, tema: Tema) -> float:
    """Cuanto despues de la grilla de Rekordbox cae el golpe en ESTE audio decodificado.

    La grilla se calculo con el decodificador de Rekordbox; aca decodifica ffmpeg. En mp3 el
    retardo del codificador puede correr todo unos milisegundos, y dos bombos superpuestos
    se escuchan dobles a partir de ~5. Se mide sobre los golpes francos.
    """
    beats = tema.beats[(tema.beats > ini + 0.1) & (tema.beats < ini + len(crudo) / SR - 0.1)]
    cuando, fuerza = ataques_cerca(crudo, ini, beats)
    ok = np.isfinite(cuando)
    if ok.sum() < 16:
        return 0.0
    lags, fuerza = (cuando - beats)[ok], fuerza[ok]
    return float(np.median(lags[fuerza >= np.percentile(fuerza, 60)]))


def _bandas(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Linkwitz-Riley de 4to orden: las tres bandas suman plano (con la fase de un pasatodo)."""
    lr = lambda tipo, fc: butter(2, fc, tipo, fs=SR, output="sos")
    dos = lambda sos, s: sosfilt(sos, sosfilt(sos, s, axis=0), axis=0)
    grave = dos(lr("lowpass", CORTE_GRAVE_HZ), x)
    resto = dos(lr("highpass", CORTE_GRAVE_HZ), x)
    medio = dos(lr("lowpass", CORTE_AGUDO_HZ), resto)
    agudo = dos(lr("highpass", CORTE_AGUDO_HZ), resto)
    # el grave pasa por el mismo pasatodo de 2200 Hz que el resto, para que sumen en fase
    grave = dos(lr("lowpass", CORTE_AGUDO_HZ), grave) + dos(lr("highpass", CORTE_AGUDO_HZ), grave)
    return grave, medio, agudo


def _curva(puntos: list[tuple[float, float]], t: np.ndarray) -> np.ndarray:
    xs, ys = zip(*sorted(puntos))
    return (10 ** (np.interp(t, xs, ys) / 20)).astype(np.float32)[:, None]


def renderizar_tema(c: Colocado, tempo: float, p: Plantilla,
                    margen: float = 2.0) -> tuple[int, np.ndarray, float, np.ndarray]:
    """El tramo que suena de un tema, estirado, ecualizado y con su trim.

    Devuelve (muestra de inicio en el mix, audio, desfase grilla-bombo en s, audio SIN ecualizar)
    — el ultimo es para verificar los bombos: en el ecualizado el grave del entrante esta cortado."""
    a_tema = lambda t_mix: (t_mix - c.offset) * c.factor        # segundo del mix -> segundo del tema original
    ini, fin = max(0.0, a_tema(c.desde) - margen), min(c.tema.duracion, a_tema(c.hasta) + margen)
    crudo = _decodificar(c.tema.archivo, ini, fin)
    lag = _desfase_grilla(crudo, ini, c.tema)
    # pedalboard espera (canales, muestras)
    estirado = time_stretch(np.ascontiguousarray(crudo.T), SR, stretch_factor=c.factor, high_quality=True,
                            transient_mode="crisp").T.astype(np.float32)
    # el audio del segundo `ini` del tema cae en el mix donde cae la grilla, corrida por lo medido
    t0_mix = c.offset + (ini - lag) / c.factor
    t = t0_mix + np.arange(len(estirado)) / SR
    cuerpo = estirado[(t > c.desde) & (t < c.hasta)]
    lufs = pyln.Meter(SR).integrated_loudness(cuerpo) if len(cuerpo) > SR * 10 else LUFS_TRIM
    trim = 10 ** ((LUFS_TRIM - lufs) / 20)
    env = _envolventes(c, tempo, p)
    grave, medio, agudo = _bandas(estirado * trim)
    sale = grave * _curva(env["grave"], t) + medio * _curva(env["medio"], t) + agudo * _curva(env["agudo"], t)
    fuera = (t < c.desde) | (t > c.hasta)
    sale[fuera] = 0.0
    return int(round(t0_mix * SR)), sale.astype(np.float32), lag, (estirado * trim).astype(np.float32)
