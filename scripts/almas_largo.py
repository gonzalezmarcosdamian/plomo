# -*- coding: utf-8 -*-
"""La historia de las almas a lo largo del set 159 entero: el video de la Session 05.

Sobre la maqueta de 1 minuto que el DJ aprobo ("me encanto", 2026-10-27; scripts/almas.py y
scripts/shaders/almas.frag): las mismas almas, el mismo cielo y las mismas reglas de movimiento
(resorte, quien lleva, respiracion acoplada, la cura en dos tiempos, la que se esconde), estiradas
a los 105 minutos. La historia pasa UNA vez y sigue la energia del set (aprobada el 2026-11-01):

  Aura y Bambook        aparecen y se conocen; se tocan en el drop de Bambook
  Karnaval a Summer     vuelan juntas: cada tema una figura (FIGURAS), cada drop un toque
  Dichotomy             se separan
  Winged, State         una se apaga, se hunde detras de las nubes y se aleja
  Conviction            la otra va a buscarla; un primer intento que no prende
  Dodonpachi            la cura, donde vuelve el bombo despues del drop (medido en el audio)
  Mutant                vuelan juntas otra vez, mas alto
  Omira                 se separan brillando las dos; amanece y fundido a negro

Todo se ancla a la mezcla (postproduction/mixes/159_mix.json): entradas (plan[].cambio_in),
breakdowns y drops medidos (estructura[].medido), en compases de 122. Tiempos en segundos del set.

Uso:
    python scripts/almas_largo.py --hoja C:/Users/gonza/Pictures/plomo_session_05_almas_recorrido.jpg
    python scripts/almas_largo.py --salida tramo.mp4 --desde 5500 --hasta 5560        # 2560x1440
    python scripts/almas_largo.py --salida p03.mp4 --desde 1200 --hasta 1800 --mudo   # para concatenar
El set entero se arma por tramos --mudo con cortes en segundos enteros (caen en cuadro justo), se
concatenan con ffmpeg -f concat -c copy y se les pone el wav una sola vez.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

import moderngl
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt

import almas
from almas import (FPS, FUENTE, MIX, SHADER, VERTICES, en_pantalla, golpe_y_fondo, intentos, interpolar,
                   medir_impacto, resorte, respiracion)

CAPITULOS = almas.RAIZ / "data" / "video" / "session_05_capitulos.json"
WAV = MIX.with_suffix(".wav")
GRAVE = MIX.with_name("159_mix_grave.npz")   # el grave por cuadro del set entero (cache)
SUB = 2                  # pasos del resorte por cuadro (la maqueta usa 4; aca son 105 minutos)
RETARDO = 2.0            # s que va atras la que sigue: al paso lento del vuelo largo se tiene que ver
FUNDIDO_FIN = 8.0
B0 = (0.0, 0.06)         # donde quedan juntas despues de tocarse; todo lo demas se mide desde ahi


def en(dx: float, dy: float, base: tuple = B0) -> tuple:
    return (base[0] + dx, base[1] + dy)


CURA = en(0.75, -0.30)   # adonde se hunde B, donde la encuentra A y donde se cura

# Karnaval a Summer O'clock: cada tema una figura del vuelo, que se arma en su drop.
# rumbo en grados (0 = derecha, 90 = sube), vel en cielo/s, giro = radio de la vuelta de una
# alrededor de la otra, vueltas por compas, sep = a la par (separadas de costado), vaiven en espejo,
# lleva = cual va adelante, tinte = el color de la noche (offset rgb)
FIGURAS = (
    dict(momento="vuelan juntas: suben", rumbo=18, vel=0.030, giro=0.060, vueltas=1.0, sep=0.0, vaiven=0.0,
         lleva="a", zoom=1.00, tinte=(0.0, 0.0, 0.0)),
    dict(momento="a la par, en espejo", rumbo=0, vel=0.034, giro=0.0, vueltas=0.0, sep=0.16, vaiven=0.035,
         lleva="b", zoom=0.92, tinte=(-0.06, 0.03, 0.10)),
    dict(momento="bajan, cerca, despacio", rumbo=-12, vel=0.022, giro=0.055, vueltas=0.5, sep=0.0, vaiven=0.0,
         lleva="a", zoom=1.15, tinte=(0.07, 0.02, -0.05)),
    dict(momento="vals lento, el cielo abierto", rumbo=8, vel=0.018, giro=0.090, vueltas=0.4, sep=0.0, vaiven=0.0,
         lleva="a", zoom=0.78, tinte=(0.0, 0.05, 0.12)),
    dict(momento="vuelven; ahora lleva B", rumbo=165, vel=0.028, giro=0.050, vueltas=1.2, sep=0.0, vaiven=0.0,
         lleva="b", zoom=1.00, tinte=(0.07, -0.02, 0.09)),
    dict(momento="el vuelo mas rapido, calido", rumbo=30, vel=0.042, giro=0.070, vueltas=1.5, sep=0.0, vaiven=0.0,
         lleva="a", zoom=1.05, tinte=(0.12, 0.03, -0.06), pulso=0.4),
    dict(momento="juegan: se cruzan", rumbo=-5, vel=0.032, giro=0.035, vueltas=1.0, sep=0.08, vaiven=0.05,
         lleva="b", zoom=0.95, tinte=(-0.03, 0.06, 0.02)),
    dict(momento="lo mas alto, antes de la caida", rumbo=45, vel=0.036, giro=0.065, vueltas=1.2, sep=0.0,
         vaiven=0.0, lleva="a", zoom=1.00, tinte=(0.09, 0.05, -0.02)),
)
MUTANT = dict(momento="vuelan otra vez, mas alto", rumbo=50, vel=0.040, giro=0.070, vueltas=1.4, sep=0.0,
              vaiven=0.0, lleva="b", zoom=1.00, tinte=(0.10, 0.05, 0.0), pulso=0.55)

INICIO = dict(ra=(-0.10, 0.0), rb=(0.62, 0.16), sep=0.0, vel=0.006, rumbo=0.0, giro=0.0, vueltas=0.0,
              abrazo=0.0, vaiven=0.0, zoom=1.08, luz_a=0.0, luz_b=0.0, tam_a=1.0, tam_b=0.5, calor_b=0.0,
              puente=0.0, frio=0.15, alba=0.0, mira_a=0.0, mira_b=0.0, sincro=0.0, retardo_a=0.0,
              retardo_b=0.0, detras_b=0.0, pulso=0.3, tr=0.0, tg=0.0, tb=0.0)


class Claves:
    """La hoja de recorrido hecha dato: pista -> {segundo del set: valor}."""

    def __init__(self) -> None:
        self.d: dict[str, dict[float, object]] = {}

    def pon(self, t: float, **valores) -> None:
        for k, v in valores.items():
            self.d.setdefault(k, {})[round(float(t), 3)] = v

    def pista(self, nombre: str, t: np.ndarray) -> np.ndarray:
        claves = sorted(self.d[nombre].items())
        ts = np.array([k for k, _ in claves])
        vs = np.array([np.atleast_1d(v) for _, v in claves], float)
        if len(ts) == 1:
            ts, vs = np.append(ts, ts[0] + 1.0), np.vstack([vs, vs])
        return interpolar(ts, vs, t)


# ---------------------------------------------------------------- la historia, por partes

def conocerse(cl: Claves, aura: dict, bam: dict, c: float) -> None:
    """A aparece sola; B aparece lejos en el breakdown de Aura; se ven en su drop; se acercan,
    dudan, bailan a distancia en el breakdown de Bambook y se tocan en su drop."""
    cl.pon(6.0, luz_a=0.0)
    cl.pon(30.0, luz_a=0.7)
    cl.pon(80.0, ra=(-0.02, 0.04))
    cl.pon(120.0, luz_a=0.85)
    cl.pon(aura["bk"], ra=(-0.12, -0.02), luz_b=0.0, mira_a=0.0, vel=0.006, zoom=1.0, frio=0.0)
    cl.pon(aura["bk"] + 8 * c, mira_a=1.0)                              # A la ve
    cl.pon(aura["bk"] + 16 * c, luz_b=0.6, vel=0.0, rb=(0.58, 0.15))
    cl.pon(aura["bk"] + 20 * c, ra=(-0.18, 0.0))                        # retrocede, apenas
    cl.pon(aura["d"], rb=(0.52, 0.14), luz_a=0.9, tam_b=0.55, mira_b=0.0)
    cl.pon(aura["d"] + 4 * c, mira_b=1.0)                               # B la mira
    cl.pon(aura["d"] + 8 * c, rb=(0.40, 0.10), tam_b=0.75, luz_b=0.85, ra=(-0.10, 0.03), luz_a=1.0)
    cl.pon(bam["e"] + 16 * c, ra=(-0.06, 0.05), rb=(0.12, 0.08), tam_b=0.95, luz_b=1.0, sincro=0.3)
    cl.pon(bam["e"] + 48 * c, ra=(-0.13, 0.04), rb=(0.21, 0.10))         # dudan
    cl.pon(bam["bk"], sincro=0.6, zoom=1.0, tam_b=1.0)
    cl.pon(bam["bk"] + 8 * c, ra=(-0.05, 0.06), rb=(0.06, 0.06), giro=0.03, vueltas=0.3, zoom=1.1)
    cl.pon(bam["d"] - 2 * c, ra=(-0.07, 0.06), rb=(0.08, 0.06), giro=0.0, vueltas=0.0, mira_a=1.0, mira_b=1.0)
    cl.pon(bam["d"] - 0.5 * c, ra=B0, rb=B0)                             # se tocan
    cl.pon(bam["d"] + 4 * c, giro=0.055, vueltas=1.0, sincro=1.0, zoom=1.0, mira_a=0.4, mira_b=0.4)
    cl.pon(bam["d"] + 8 * c, retardo_b=RETARDO)                         # B la sigue
    cl.pon(bam["d"] + 16 * c, vel=0.02, rumbo=10.0)


def vuelo(cl: Claves, tema: dict, c: float, fig: dict) -> None:
    """Un tema del vuelo: entra la figura a medias, el breakdown es un respiro (lento, de lejos, se
    miran), antes del drop se abren apenas, en el drop se tocan y despues se arma la figura entera.
    El rumbo, el color y quien lleva cambian entre el final de un tema y la entrada del otro."""
    e, bk, d = tema["e"], tema["bk"], tema["d"]
    z, pulso = fig["zoom"], fig.get("pulso", 0.3)
    rasgo = {"rumbo": fig["rumbo"], "tr": fig["tinte"][0], "tg": fig["tinte"][1], "tb": fig["tinte"][2],
             "retardo_a": RETARDO if fig["lleva"] == "b" else 0.0,
             "retardo_b": RETARDO if fig["lleva"] == "a" else 0.0}

    def cuerpo(s: float) -> dict:
        return {k: s * fig[k] for k in ("vel", "giro", "vueltas", "sep", "vaiven")}

    cl.pon(e, zoom=z, sincro=1.0, mira_a=0.4, mira_b=0.4, pulso=pulso, **rasgo, **cuerpo(0.7))
    cl.pon(bk, vel=0.4 * fig["vel"], giro=0.025, vueltas=0.3, sep=0.03, vaiven=0.0, zoom=0.88 * z, pulso=0.2)
    cl.pon(bk + 8 * c, mira_a=1.0, mira_b=1.0)
    cl.pon(d - 2 * c, sep=0.08, giro=0.0, vueltas=0.15, zoom=0.9 * z)
    cl.pon(d - 0.5 * c, sep=0.0)
    cl.pon(d, zoom=1.06 * z, pulso=pulso + 0.2, vel=0.6 * fig["vel"])
    cl.pon(d + 4 * c, zoom=z, mira_a=0.4, mira_b=0.4, **cuerpo(1.0))
    cl.pon(d + 16 * c, **rasgo)
    cl.pon(d + 24 * c, pulso=pulso)


def separarse(cl: Claves, dic: dict, winged: dict, c: float) -> None:
    """Dichotomy: dejan de respirar juntas, el giro se apaga, se abren de costado mirandose, se
    inclinan una vez mas y en el drop se van cada una a un lado."""
    e, bk, d = dic["e"], dic["bk"], dic["d"]
    cl.pon(e, rumbo=10.0, vel=0.025, giro=0.04, vueltas=0.8, sep=0.0, vaiven=0.0, zoom=1.0, sincro=1.0,
           retardo_a=0.0, retardo_b=0.0, tr=0.0, tg=0.0, tb=0.03, pulso=0.3, ra=B0, rb=B0)
    cl.pon(e + 16 * c, sincro=0.6, giro=0.02, vueltas=0.5, sep=0.06)
    cl.pon(bk, vel=0.008, giro=0.0, vueltas=0.0, sep=0.20, sincro=0.2, mira_a=1.0, mira_b=1.0, zoom=0.95, pulso=0.2)
    cl.pon(d - c, sep=0.15)
    cl.pon(d, sep=0.2, vel=0.0, ra=B0, rb=B0, sincro=0.0)
    cl.pon(d + 4 * c, sep=0.0, ra=en(-0.38, 0.08), rb=en(0.40, -0.04), zoom=0.85)
    cl.pon(winged["e"], ra=en(-0.44, 0.10), rb=en(0.46, -0.06))


def apagarse(cl: Claves, w: dict, s: dict, c: float) -> None:
    """Winged: B pierde la luz y deja de mirar. State of Progression: se hunde, se achica, se
    esconde detras del banco de nubes y el cielo pierde el color. A se queda, mirandola."""
    cl.pon(w["e"], luz_b=1.0, frio=0.0, tam_b=1.0, luz_a=1.0, mira_b=1.0)
    cl.pon(w["bk"], luz_b=0.75, frio=0.3, mira_b=0.6, rb=en(0.52, -0.10), tam_b=0.9, tr=-0.02, tg=0.0, tb=0.05)
    cl.pon(w["d"], pulso=0.25)
    cl.pon(w["d"] + 8 * c, luz_b=0.55, frio=0.5, mira_b=0.3, rb=en(0.58, -0.15), tam_b=0.82)
    cl.pon(w["d"] + 16 * c, luz_a=0.9)
    cl.pon(s["e"], rb=en(0.62, -0.18))
    cl.pon(s["e"] + 8 * c, detras_b=0.0)
    cl.pon(s["e"] + 16 * c, detras_b=1.0)
    cl.pon(s["bk"], rb=en(0.72, -0.28), tam_b=0.62, luz_b=0.22, frio=1.0, mira_b=0.0, pulso=0.15)
    cl.pon(s["d"], luz_b=0.16, tam_b=0.58, rb=CURA, luz_a=0.8)
    cl.pon(s["d"] + 8 * c, ra=en(-0.50, 0.13))                          # A junta impulso


def buscarla(cl: Claves, v: dict, c: float) -> None:
    """Conviction: A cruza el cielo hasta ella, B asoma de la nube y la mira, A la rodea y en el
    drop le pasa la luz: B se enciende un instante y se vuelve a caer."""
    ini, e, bk, d = v["desde"], v["e"], v["bk"], v["d"]
    cl.pon(ini, ra=en(-0.50, 0.13), zoom=0.85, luz_a=0.85, sincro=0.0)
    cl.pon(ini + 20.0, ra=en(0.05, -0.05))
    cl.pon(e, ra=en(-0.22, 0.06, CURA), zoom=0.95)
    cl.pon(e + 16 * c, detras_b=1.0)
    cl.pon(e + 32 * c, ra=en(-0.10, 0.03, CURA), zoom=1.0)
    cl.pon(e + 40 * c, detras_b=0.0, mira_b=0.5)
    cl.pon(bk, ra=CURA, abrazo=0.0, vueltas=0.0, mira_b=1.0, puente=0.0, luz_b=0.18)
    cl.pon(bk + 4 * c, abrazo=0.09, vueltas=0.8)
    cl.pon(d - 2 * c, puente=0.25)
    cl.pon(d - 0.55 * c, luz_b=0.26, puente=0.3, tam_b=0.72, tam_a=1.0, frio=1.0)
    cl.pon(d, puente=1.0, luz_b=0.68, tam_b=0.84, tam_a=0.9, frio=0.85, pulso=0.3)
    cl.pon(d + 0.3 * c, luz_b=0.5, puente=0.35)
    cl.pon(d + c, luz_b=0.17, tam_b=0.68, puente=0.1, frio=1.0, tam_a=1.0)
    cl.pon(d + 4 * c, puente=0.0, vueltas=0.5, abrazo=0.08, pulso=0.15)


def curarla(cl: Claves, o: dict, c: float, hueco: float, cura: float) -> None:
    """Dodonpachi: la cura de la maqueta, en dos tiempos: en el hueco (el bombo cortado, medido) A
    baja, le pasa la luz y B se entibia; donde vuelve el bombo B se enciende, la onda abre el cielo
    y vuelve el color. Desde ahi lleva B."""
    h, I = hueco, cura
    cl.pon(o["e"], abrazo=0.07, vueltas=0.3, luz_a=0.95)
    cl.pon(o["bk"], vueltas=0.35, calor_b=0.0, zoom=1.0)
    cl.pon(h - 2.5 * c, zoom=1.0)
    cl.pon(h - 2 * c, luz_b=0.18, tam_b=0.68)
    cl.pon(h - 1.5 * c, zoom=1.18)
    cl.pon(h - c, puente=0.0)
    cl.pon(h - 0.5 * c, calor_b=0.15)
    cl.pon(h - 0.25 * c, vueltas=0.45)
    cl.pon(h, luz_a=0.85, luz_b=0.17, puente=0.45, vueltas=0.15, sincro=0.3)
    cl.pon(I - 0.1, tam_a=0.78, tam_b=0.7)
    cl.pon(I - 0.05, luz_a=0.72, luz_b=0.42, calor_b=0.35, puente=1.0)
    cl.pon(I, vueltas=0.0, giro=0.0, abrazo=0.085, frio=1.0, zoom=1.18, sincro=0.3, retardo_a=0.0,
           retardo_b=0.0, mira_a=1.0, mira_b=1.0, vel=0.0, rumbo=40.0)
    cl.pon(I + 0.25, luz_a=1.08, luz_b=1.2)
    cl.pon(I + 0.3, tam_a=1.06, tam_b=1.06, vueltas=1.2)
    cl.pon(I + 0.4, puente=0.0)
    cl.pon(I + 0.5, sincro=1.0)
    cl.pon(I + 0.8, abrazo=0.0)
    cl.pon(I + 1.0, giro=0.065)
    cl.pon(I + 1.2, frio=0.0)
    cl.pon(I + 1.5, calor_b=0.15)
    cl.pon(I + 1.6, zoom=1.0)
    cl.pon(I + 2.0, tam_a=1.0, tam_b=1.0, mira_a=0.4, mira_b=0.4)
    cl.pon(I + 2.5, luz_a=1.0, luz_b=1.0, pulso=1.0)
    cl.pon(I + 8 * c, retardo_a=RETARDO, pulso=0.6, tr=0.04, tg=0.02, tb=0.0)
    cl.pon(I + 16 * c, vel=0.03)


def final(cl: Claves, o: dict, c: float, fin: float) -> None:
    """Omira: vuelan a la par buscandose (vaiven), se tocan una ultima vez en el drop y se separan
    brillando; se frenan a mirarse, siguen, el cielo se abre y amanece."""
    d = o["d"]
    cl.pon(o["e"], rumbo=20.0, vel=0.03, giro=0.05, vueltas=1.0, sep=0.0, vaiven=0.0, zoom=1.0,
           retardo_a=RETARDO, retardo_b=0.0, mira_a=0.4, mira_b=0.4, pulso=0.45, tr=0.06, tg=0.03, tb=0.0)
    cl.pon(o["bk"], giro=0.0, vueltas=0.0, sep=0.08, vaiven=0.035, vel=0.02, retardo_a=3.0, mira_a=0.8,
           mira_b=0.8, zoom=0.95)
    cl.pon(d - 2 * c, sep=0.04)
    cl.pon(d - 0.5 * c, sep=0.0, ra=CURA, rb=CURA)
    cl.pon(d, vel=0.012, pulso=0.5, alba=0.0, luz_a=1.0, luz_b=1.0, zoom=1.0)
    cl.pon(d + 4 * c, luz_a=1.05, luz_b=1.05)
    cl.pon(d + 16 * c, ra=en(-0.45, 0.10, CURA), rb=en(0.50, 0.22, CURA), mira_a=1.0, mira_b=1.0, vaiven=0.02)
    cl.pon(d + 22 * c, ra=en(-0.50, 0.11, CURA), rb=en(0.55, 0.24, CURA))   # se frenan a mirarse
    cl.pon(d + 48 * c, alba=1.0)
    cl.pon(fin - 10.0, ra=en(-0.80, 0.18, CURA), rb=en(0.95, 0.40, CURA), mira_a=0.8, mira_b=0.8, zoom=0.62,
           vaiven=0.012)


def recorrido(T: list[dict], c: float, hueco: float, cura: float, fin: float) -> Claves:
    cl = Claves()
    cl.pon(0.0, **INICIO)
    conocerse(cl, T[0], T[1], c)
    for k, fig in enumerate(FIGURAS, start=2):
        vuelo(cl, T[k], c, fig)
    separarse(cl, T[10], T[11], c)
    apagarse(cl, T[11], T[12], c)
    buscarla(cl, T[13], c)
    curarla(cl, T[14], c, hueco, cura)
    vuelo(cl, T[15], c, MUTANT)
    final(cl, T[16], c, fin)
    return cl


# ---------------------------------------------------------------- de las claves al movimiento

def atras(t: np.ndarray, xy: np.ndarray, retardo: np.ndarray) -> np.ndarray:
    """La que sigue repite el camino de la otra con retardo (Heider y Simmel)."""
    return np.stack([np.interp(t - retardo, t, xy[:, j]) for j in (0, 1)], 1)


def intentos_en(t: np.ndarray, activo: np.ndarray) -> np.ndarray:
    out = np.zeros_like(t)
    idx = np.flatnonzero(activo)
    if len(idx):
        i0, i1 = idx[0], idx[-1] + 1
        out[i0:i1] = intentos(t[i0:i1] - t[i0])
    return out


def coreografia(t: np.ndarray, cl: Claves, compas: float, cura: float, caida: float,
                busca: tuple[float, float]) -> dict:
    """Como almas.coreografia, con un camino que viaja: el centro avanza con rumbo y velocidad,
    cada alma se para respecto del centro (ra, rb, sep de costado) y la camara las sigue con
    aire adelante. B solo se puede apagar desde Winged (caida)."""
    dt = t[1] - t[0]
    p = {k: cl.pista(k, t) for k in cl.d}
    rum = np.radians(p["rumbo"])
    rumbo = np.stack([np.cos(rum), np.sin(rum)], 1)
    costado = np.stack([-rumbo[:, 1], rumbo[:, 0]], 1) * (p["sep"] / 2)[:, None]
    centro = np.cumsum(rumbo * p["vel"][:, None], axis=0) * dt
    obj_a = atras(t, centro + p["ra"] + costado, p["retardo_a"])
    obj_b = atras(t, centro + p["rb"] - costado, p["retardo_b"])
    apagada = np.clip(1 - p["luz_b"] / 0.4, 0, 1) * (t >= caida)
    a = resorte(obj_a, dt, np.full(len(t), 7.0), 0.55)
    b = resorte(obj_b, dt, 6.0 - 3.2 * apagada, 0.6)
    cam = resorte(0.5 * (obj_a + obj_b) + rumbo * (2.5 * p["vel"])[:, None], dt, np.full(len(t), 1.6), 1.0)
    th = np.cumsum(2 * np.pi * p["vueltas"] / compas) * dt
    elipse = np.stack([np.cos(th), 0.5 * np.sin(th)], 1)
    a = a + elipse * (p["giro"] + p["abrazo"])[:, None]
    b = b - elipse * p["giro"][:, None]
    espejo = np.stack([np.zeros_like(t), p["vaiven"] * np.sin(np.pi * t / compas)], 1)
    a, b = a + espejo, b - espejo
    prof = 0.15 * np.sin(th)
    tam_a = p["tam_a"] * (1 - prof * (p["giro"] + p["abrazo"]) / 0.07)
    tam_b = p["tam_b"] * (1 + prof * p["giro"] / 0.07)
    ayuda = np.clip((t - busca[0]) / (busca[1] - busca[0]), 0, 1)
    intento = apagada * intentos_en(t, apagada > 0) * (0.6 + 0.4 * ayuda)
    a = a + 0.006 * np.stack([np.sin(0.7 * t), np.sin(0.9 * t + 1.0)], 1)
    b = b + (0.006 + 0.012 * apagada)[:, None] * np.stack([np.sin(0.8 * t + 2.0), np.sin(0.6 * t + 0.5)], 1)
    b = b + 0.004 * intento[:, None] * np.stack([np.sin(37.0 * t), np.cos(41.0 * t)], 1)
    fa, fb = respiracion(t, dt, compas, cura, p["sincro"], apagada)
    resp_a, resp_b = np.sin(fa), (1 - 0.5 * apagada) * np.sin(fb)
    return {"a": a, "b": b, "cam": cam, "zoom": p["zoom"], "luz_a": p["luz_a"] * (1 + 0.04 * resp_a),
            "luz_b": (p["luz_b"] + 0.10 * intento) * (1 + 0.04 * resp_b), "detras_b": p["detras_b"],
            "tam_a": tam_a, "tam_b": tam_b, "resp_a": resp_a, "resp_b": resp_b, "vida_a": p["luz_a"],
            "vida_b": p["luz_b"] * (1 - apagada) + 1.2 * intento, "mira_a": p["mira_a"], "mira_b": p["mira_b"],
            "calor_b": p["calor_b"], "frio": p["frio"], "alba": p["alba"], "puente": p["puente"],
            "pulso": p["pulso"], "tr": p["tr"], "tg": p["tg"], "tb": p["tb"]}


# ---------------------------------------------------------------- la mezcla medida

def anclas(mix: dict) -> tuple[float, list[dict]]:
    """Por tema: entrada, breakdown y drop en segundos del set, y el nombre limpio del capitulo."""
    compas = 240 / mix["tempo"]
    caps = json.loads(CAPITULOS.read_text(encoding="utf-8"))["capitulos"]
    if not len(mix["plan"]) == len(mix["estructura"]) == len(caps) == 17:
        raise SystemExit("el plan, la estructura y los capitulos no tienen los 17 temas del 159 v8c")
    temas = []
    for p, e, cap in zip(mix["plan"], mix["estructura"], caps):
        m = e["medido"]
        temas.append({"titulo": cap["titulo"], "artista": cap["artista"], "desde": p["desde"],
                      "e": p.get("cambio_in") or p["desde"], "bk": p["desde"] + m["breakdown"][0] * compas,
                      "d": p["desde"] + m["drop"] * compas})
    return compas, temas


def cura_de(drop: float, compas: float) -> tuple[float, float]:
    """El hueco y la cura, medidos en el audio: donde vuelve el bombo (almas.medir_impacto) y desde
    donde estaba cortado. En Dodonpachi el bombo se corta tres tiempos ANTES del drop y vuelve justo
    en el drop (en The Captain era al reves: el hueco caia despues). Sin hueco, medio compas."""
    sr = sf.info(str(WAV)).samplerate
    ini = drop - almas.DROP_EN
    audio, _ = sf.read(str(WAV), start=int(ini * sr), stop=int((ini + 60) * sr), dtype="float32", always_2d=True)
    cura = ini + medir_impacto(audio, sr, compas)
    lo = sosfilt(butter(4, [40, 100], "bandpass", fs=sr, output="sos"), audio.mean(1))
    tiempo = compas / 4

    def relativa(k: int) -> float:
        t = almas.DROP_EN + k * tiempo
        return float(np.sqrt(np.mean(lo[int((t - 0.03) * sr): int((t + 0.12) * sr)] ** 2)))

    ref = np.median([relativa(k) for k in range(-24, -8)])
    vuelta = round((cura - drop) / tiempo)
    h = vuelta
    while h > vuelta - 12 and relativa(h - 1) / ref < 0.3:
        h -= 1
    return (drop + h * tiempo if h < vuelta else cura - compas / 2), cura


def energia_grave(n: int) -> np.ndarray:
    """El grave (40-100 Hz) por cuadro, del set entero, leido de a bloques; queda en cache."""
    if GRAVE.exists():
        e = np.load(GRAVE)["e"]
        if len(e) >= n:
            return e[:n]
    sr = sf.info(str(WAV)).samplerate
    por = sr // FPS
    sos = butter(4, [40, 100], "bandpass", fs=sr, output="sos")
    zi, resto, partes = np.zeros((sos.shape[0], 2)), np.zeros(0), []
    for bloque in sf.blocks(str(WAV), blocksize=por * FPS * 60, dtype="float32", always_2d=True):
        y, zi = sosfilt(sos, bloque.mean(1), zi=zi)
        y = np.concatenate([resto, y])
        k = len(y) // por * por
        partes.append(np.sqrt(np.mean(y[:k].reshape(-1, por) ** 2, axis=1)))
        resto = y[k:]
    e = np.concatenate(partes)
    e = np.pad(e, (0, max(0, n - len(e))), mode="edge")
    np.savez_compressed(GRAVE, e=e)
    return e[:n]


def armar_eventos(c: dict, T: list[dict], compas: float, cura: float) -> dict:
    """Los toques (Bambook, cada drop del vuelo, el intento de Conviction, Mutant, Omira), la cura
    y el banco de nubes donde se esconde B (fijo en la capa cercana, como en la maqueta)."""
    ultimo = len(c["zoom"]) - 1

    def cuadro(s: float) -> int:
        return min(int(s * FPS), ultimo)

    def mitad(f: int) -> np.ndarray:
        return (c["a"][f] + c["b"][f]) / 2

    f0, f1 = cuadro(T[1]["d"] - 2 * compas), cuadro(T[1]["d"] + 2 * compas)
    toque = f0 + int(np.argmin(np.linalg.norm(c["a"][f0:f1] - c["b"][f0:f1], axis=1)))
    toques = [(toque / FPS, mitad(toque)), (T[13]["d"], c["b"][cuadro(T[13]["d"])])]
    toques += [(T[k]["d"], mitad(cuadro(T[k]["d"]))) for k in (*range(2, 10), 15, 16)]
    fb = cuadro(T[12]["e"] + 12 * compas)
    zc = 1 + (c["zoom"][fb] - 1) * 1.4
    banco = en_pantalla(c["b"][fb], c["cam"][fb], c["zoom"][fb]) / zc + c["cam"][fb] * 1.7
    return {"toques": sorted(toques, key=lambda x: x[0]), "cura": (cura, c["b"][cuadro(cura)]), "banco": banco}


def momentos(T: list[dict], c: float, hueco: float, cura: float, eventos: dict, fin: float) -> tuple[list, list]:
    """La historia con sus minutos, y el cuadro que cuenta cada tema en la hoja."""
    historia = [("A aparece", 6.0), ("B aparece lejos (breakdown de Aura)", T[0]["bk"]),
                ("se ven (drop de Aura)", T[0]["d"]), ("se tocan (drop de Bambook)", eventos["toques"][0][0]),
                ("vuelan juntas (entra Karnaval)", T[2]["e"]), ("dejan de respirar juntas (entra Dichotomy)", T[10]["e"]),
                ("se separan (drop de Dichotomy)", T[10]["d"]), ("B empieza a apagarse (breakdown de Winged)", T[11]["bk"]),
                ("B se esconde en la nube (State)", T[12]["e"] + 12 * c), ("B en lo mas hondo (drop de State)", T[12]["d"]),
                ("A va a buscarla (empieza Conviction)", T[13]["desde"]), ("intento que no prende (drop de Conviction)", T[13]["d"]),
                ("hueco: se corta el bombo, A le pasa la luz", hueco), ("la cura: vuelve el bombo (drop de Dodonpachi)", cura),
                ("vuelan otra vez (entra Mutant)", T[15]["e"]), ("drop de Mutant", T[15]["d"]),
                ("se separan brillando (drop de Omira)", T[16]["d"]), ("fundido a negro", fin - FUNDIDO_FIN)]
    hoja = [(T[0]["d"] + 4 * c, 0, "B aparece; se ven"), (eventos["toques"][0][0] + 1.0, 1, "se tocan")]
    hoja += [(T[k]["d"] + 8 * c, k, FIGURAS[k - 2]["momento"]) for k in range(2, 10)]
    hoja += [(T[10]["d"] + 6 * c, 10, "se separan"), (T[11]["d"] + 12 * c, 11, "B se apaga"),
             (T[12]["d"], 12, "B se hunde detras de las nubes"), (T[13]["d"] + 0.15, 13, "A la busca: no prende"),
             (cura + 0.8, 14, "la cura"), (T[15]["d"] + 8 * c, 15, MUTANT["momento"]),
             (T[16]["d"] + 40 * c, 16, "se separan brillando")]
    return historia, hoja


# ---------------------------------------------------------------- dibujar

def mmss(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


def limpio(titulo: str) -> str:
    return re.sub(r"\s*\((Extended|Original)( Mix)?\)\s*$", "", titulo, flags=re.I)


def abrir_gl(ancho: int, alto: int) -> tuple:
    ctx = moderngl.create_standalone_context()
    prog = ctx.program(vertex_shader=VERTICES, fragment_shader=SHADER.read_text(encoding="utf-8"))
    vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "2f", "pos")])
    fbo = ctx.simple_framebuffer((ancho, alto))
    fbo.use()
    prog["uRes"].value = (ancho, alto)
    return prog, vao, fbo


def dibujar(gl: tuple, f: int, esc: dict) -> bytes:
    prog, vao, fbo = gl
    c = esc["c"]
    u = almas.uniformes(f, c, esc["golpe"], esc["fondo"], esc["eventos"])
    u["uGolpe"] = float(esc["golpe"][f] * c["pulso"][f])
    u["uTinte"] = (float(c["tr"][f]), float(c["tg"][f]), float(c["tb"][f]))
    for nombre, valor in u.items():
        if nombre in prog:
            prog[nombre].value = valor
    vao.render(moderngl.TRIANGLE_STRIP)
    return fbo.read(components=3)


def hoja(ruta: str, gl: tuple, esc: dict, cuadros: list, res: tuple[int, int]) -> None:
    """Un cuadro por tema, rotulado con minuto, tema y momento: 4 columnas de 400 px."""
    w, h, pie = 400, 225, 44
    fuente, chica = ImageFont.truetype(str(FUENTE), 15), ImageFont.truetype(str(FUENTE), 13)
    lienzo = Image.new("RGB", (4 * w, ((len(cuadros) + 3) // 4) * (h + pie)), (10, 10, 12))
    dib = ImageDraw.Draw(lienzo)
    for i, (t, k, momento) in enumerate(cuadros):
        im = Image.frombytes("RGB", res, dibujar(gl, int(t * FPS), esc)).transpose(Image.FLIP_TOP_BOTTOM)
        x, y = (i % 4) * w, (i // 4) * (h + pie)
        lienzo.paste(im.resize((w, h), Image.LANCZOS), (x, y))
        dib.text((x + 8, y + h + 4), f"{mmss(t)}  {limpio(esc['T'][k]['titulo'])}", font=fuente, fill=(243, 235, 221))
        dib.text((x + 8, y + h + 24), momento, font=chica, fill=(190, 180, 165))
    lienzo.save(ruta, quality=88)
    print(f"hoja: {ruta} ({lienzo.width}x{lienzo.height})")


def tramo(a: argparse.Namespace, gl: tuple, esc: dict, res: tuple[int, int], dur: float) -> None:
    """Renderiza [desde, hasta) del set. Fundido de entrada solo si arranca en 0 y de salida solo si
    llega al final, para que los tramos se peguen sin costura."""
    n = len(esc["c"]["zoom"])
    f0, f1 = int(round(a.desde * FPS)), min(n, int(round((a.hasta if a.hasta else dur) * FPS)))
    largo = (f1 - f0) / FPS
    vf = ["vflip"] + (["fade=in:0:45"] if f0 == 0 else [])
    vf += [f"fade=out:{f1 - f0 - int(FUNDIDO_FIN * FPS)}:{int(FUNDIDO_FIN * FPS)}"] if f1 == n else []
    tmp = tempfile.TemporaryDirectory()
    plan = [{"tema": f"{x['artista']} - {x['titulo']}", "desde": x["e"], "cambio_in": x["e"]}
            for x in esc["T"] if x["e"] + 9.5 > a.desde and x["e"] + 1.5 < a.desde + largo]
    letras = almas.textos({"plan": plan}, 0.0, a.desde, res[1], Path(tmp.name), largo=dur)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{res[0]}x{res[1]}",
           "-r", str(FPS), "-i", "-"]
    if not a.mudo:
        af = (["afade=in:d=1.5"] if f0 == 0 else []) + ([f"afade=out:st={largo - FUNDIDO_FIN:.3f}:d={FUNDIDO_FIN}"]
                                                        if f1 == n else [])
        cmd += ["-ss", f"{a.desde:.3f}", "-t", f"{largo:.3f}", "-i", str(WAV), "-af", ",".join(af) or "anull",
                "-c:a", "aac", "-b:a", "320k", "-shortest"]
    cmd += ["-vf", ",".join(vf) + letras, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(Path(a.salida).resolve())]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE, cwd=tmp.name)
    t0 = time.perf_counter()
    for f in range(f0, f1):
        ff.stdin.write(dibujar(gl, f, esc))
    ff.stdin.close()
    ff.wait()
    seg = time.perf_counter() - t0
    tmp.cleanup()
    if ff.returncode:
        raise SystemExit(f"ffmpeg termino con error {ff.returncode}")
    fps = (f1 - f0) / seg
    print(f"{a.salida}: {mmss(a.desde)} a {mmss(a.desde + largo)}, {f1 - f0} cuadros en {seg:.1f} s = {fps:.1f} cuadros/s;"
          f" el set entero ({n} cuadros) a este paso: {n / fps / 3600:.2f} h")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", help="mp4 del tramo")
    ap.add_argument("--res", default="2560x1440")
    ap.add_argument("--desde", type=float, default=0.0, help="segundo del set")
    ap.add_argument("--hasta", type=float, help="segundo del set (por defecto, el final)")
    ap.add_argument("--mudo", action="store_true", help="sin audio, para concatenar tramos")
    ap.add_argument("--hoja", help="jpg con un cuadro por tema, rotulado")
    a = ap.parse_args()
    if not a.salida and not a.hoja:
        ap.error("falta --salida o --hoja")
    res = tuple(map(int, a.res.split("x")))
    mix = json.loads(MIX.with_suffix(".json").read_text(encoding="utf-8"))
    compas, T = anclas(mix)
    dur = float(mix["duracion_s"])
    n = int(dur * FPS)
    hueco, cura = cura_de(T[14]["d"], compas)
    t0 = time.perf_counter()
    dt = 1 / (FPS * SUB)
    c = coreografia(np.arange(n * SUB) * dt, recorrido(T, compas, hueco, cura, dur), compas, cura, T[11]["e"],
                    (T[13]["desde"], T[13]["d"]))
    c = {k: v[::SUB] for k, v in c.items()}
    golpe, fondo = golpe_y_fondo(energia_grave(n))
    esc = {"c": c, "golpe": golpe, "fondo": fondo, "eventos": armar_eventos(c, T, compas, cura), "T": T}
    print(f"coreografia de {mmss(dur)} en {time.perf_counter() - t0:.1f} s")
    historia, cuadros = momentos(T, compas, hueco, cura, esc["eventos"], dur)
    for que, s in historia:
        print(f"  {mmss(s):>8}  {que}")
    gl = abrir_gl(*res)
    if a.hoja:
        hoja(a.hoja, gl, esc, cuadros, res)
    if a.salida:
        tramo(a, gl, esc, res, dur)


if __name__ == "__main__":
    main()
