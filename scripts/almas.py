# -*- coding: utf-8 -*-
"""Pieza de 1 minuto de la historia de las almas, sobre el set 159 (scripts/shaders/almas.frag).

"Una historia de amor abstracta de almas que se conocen, vuelan juntas, se separan, una se apaga y
se aleja, luego se acerca y la otra la cura, luego se acercan y vuelan y se alejan, hasta que al
final se separan pero brillando ambas" (el DJ, 2026-10-27).

2a version, tras "la idea esta pero esta mal lograda". Ocho momentos de 4 compases, contados desde
el drop de The Captain (CLAVES, en compases: 0 = el drop). La cura no cae en el drop del json sino
donde vuelve el bombo despues del hueco, que se mide en el audio (en el 159: un compas despues).
Las almas se mueven en coordenadas del cielo, con un resorte que les da inercia y frenada; la
camara las sigue aparte, y las estelas quedan en el cielo: juntas trenzan dos hilos.

Pulido tras "me encanto": vida adentro de cada alma (la apagada intenta encenderse y no puede:
intentos()), la cura como una onda que se abre y las deja en el centro, el cielo mas azul, el
nombre del tema cuando entra (textos(), como en las Sessions) y el render final en 4K.

Con las referencias (docs/ALMAS_REFERENCIAS.md, "las 5 cosas"): la respiracion acoplada cuenta la
relacion (respiracion()), la que sigue va con retardo y quien lleva cambia en la cura (retardo_a/b),
la cura en dos tiempos con un intento que no prende, y B se esconde detras de un banco de nubes
(detras_b, armar_eventos). Las nubes iluminadas desde cada alma viven en el shader.

Uso:
    python scripts/almas.py --salida C:/Users/gonza/Videos/plomo_prueba_almas.mp4 --res 3840x2160 --hoja hoja.jpg
    python scripts/almas.py --salida prueba.mp4 --res 960x540 --desde 26 --hasta 40   # un tramo
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import moderngl
import numpy as np
import soundfile as sf
from PIL import Image
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parents[1]
SHADER = RAIZ / "scripts" / "shaders" / "almas.frag"
MIX = RAIZ / "postproduction" / "mixes" / "159_mix"
VERTICES = "#version 330\nin vec2 pos;\nvoid main() { gl_Position = vec4(pos, 0.0, 1.0); }\n"
FPS, LARGO, DROP_EN = 30, 60.0, 36.0     # el drop de The Captain en el segundo 36 del minuto
TEMA_DROP, DROP_COMPAS = "The Captain", 144
NT, PASO_ESTELA = 40, 2                  # 40 puntos cada 2 cuadros: 2.7 s de camino en el cielo
SUB = 4                                  # pasos del resorte por cuadro
FUENTE, CREMA = Path("C:/Windows/Fonts/bahnschrift.ttf"), "0xF3EBDD"   # como en las Sessions
HOJA_EN = (2.5, 7.5, 11.6, 16.5, 23.0, 27.5, 31.5, 36.8, 38.4, 41.5, 49.0, 58.0)

# La hoja de recorrido hecha dato. Tiempo en compases desde el drop ("I+s" = s segundos desde que
# vuelve el bombo, la cura). Posiciones en el cielo, en unidades de alto de pantalla.
#  -18.3 a -16  aparecen: cada una por su lado, B lejos (chica)
#  -16 a -12    se conocen: se frenan, se miran (A retrocede un poco), se acercan, dudan, se tocan
#  -12 a -8     vuelan juntas: una vuelta por compas alrededor de la otra, el cielo pasa
#  -8 a -4      se separan; B se apaga, se hunde y se aleja (chica, gris); A frena y se queda
#  -4 a 0       B vuelve sola, despacio; A toma impulso y va; la rodea cada vez mas cerca
#  0 a I        el hueco del drop: todo se frena, A le pasa la luz (A baja, B sube, B se entibia)
#  I            vuelve el bombo: B se enciende, una onda de luz recorre las nubes, vuelve el color
#  I a 4        vuelan otra vez, mas alto y mas rapido
#  4 a 8        se alejan: vuelan a la par, cada vez mas lejos
#  8 al final   se separan: cada una para su lado, las dos brillando; el cielo se abre y amanece
CLAVES = {
    "a": [(-18.3, (-0.62, 0.00)), (-16, (-0.40, 0.02)), (-15, (-0.43, 0.01)), (-14, (-0.11, 0.06)),
          (-13.5, (-0.14, 0.055)), (-13, (-0.10, 0.06)), (-12.5, (-0.02, 0.065)), (-12, (0.0, 0.07)), (-10, (0.55, 0.20)),
          (-8, (1.50, 0.34)), (-7, (1.86, 0.42)), (-6, (2.06, 0.45)), (-5, (2.12, 0.44)),
          (-4, (2.14, 0.42)), (-3.25, (2.10, 0.47)), (-2.8, (2.30, 0.38)), (-2.5, (2.42, 0.20)),
          (-2, (2.47, 0.05)),
          ("I", (2.47, 0.06)), (2, (2.85, 0.30)), (4, (3.75, 0.62)), (6, (4.45, 0.86)),
          (8, (5.00, 1.02)), (9.5, (4.86, 1.15)), (10.5, (4.82, 1.19)), (12.2, (4.55, 1.35))],
    "b": [(-18.3, (0.66, 0.14)), (-16, (0.46, 0.11)), (-15, (0.47, 0.13)), (-14, (0.11, 0.07)),
          (-13.5, (0.14, 0.075)), (-13, (0.10, 0.07)), (-12.5, (0.02, 0.065)), (-12, (0.0, 0.07)), (-10, (0.55, 0.20)),
          (-8, (1.50, 0.34)), (-7, (2.02, 0.30)), (-6, (2.38, 0.10)), (-5, (2.56, -0.04)),
          (-4, (2.62, -0.10)), (-3.25, (2.58, -0.05)), (-2.5, (2.50, 0.03)), (-2, (2.47, 0.05)),
          ("I", (2.47, 0.06)), (2, (2.85, 0.30)), (4, (3.75, 0.62)), (6, (4.62, 0.62)),
          (8, (5.28, 0.66)), (9.5, (5.66, 0.78)), (10.5, (5.72, 0.80)), (12.2, (6.15, 0.95))],
    "cam": [(-18.3, (0.0, 0.06)), (-12, (0.0, 0.07)), (-10, (0.45, 0.18)), (-8, (1.40, 0.32)),
            (-6, (2.15, 0.30)), (-4, (2.32, 0.22)), (-2, (2.45, 0.10)), ("I", (2.47, 0.07)),
            (2, (2.80, 0.27)), (4, (3.65, 0.58)), (6, (4.40, 0.75)), (8, (5.05, 0.85)),
            (10, (5.25, 0.90)), (12.2, (5.30, 0.92))],
    "zoom": [(-18.3, 1.0), (-2.5, 1.0), (-1.5, 1.18), ("I", 1.18), ("I+1.6", 1.0), (8, 1.0), (12.2, 0.62)],
    "luz_a": [(-18.3, 0.7), (-16, 0.85), (-15, 1.0), (-7, 1.0), (-5, 0.8), (-3.25, 0.85), (-2.5, 1.0),
              (-0.6, 1.05), (-0.43, 0.9), (-0.05, 0.85), ("I-0.05", 0.72), ("I+0.25", 1.08), ("I+2.5", 1.0), (12.2, 1.05)],
    "luz_b": [(-18.3, 0.6), (-16, 0.8), (-15, 1.0), (-7.5, 1.0), (-6, 0.5), (-5, 0.22), (-4, 0.16),
              (-2, 0.18), (-0.55, 0.26), (-0.43, 0.68), (-0.3, 0.5), (-0.05, 0.17),
              ("I-0.05", 0.42), ("I+0.25", 1.2), ("I+2.5", 1.0), (12.2, 1.05)],
    "tam_a": [(-18.3, 1.0), (-0.65, 1.0), (-0.55, 0.9), (-0.43, 1.03), (-0.05, 0.95), ("I-0.1", 0.78), ("I+0.3", 1.06), ("I+2", 1.0), (12.2, 1.0)],
    "tam_b": [(-18.3, 0.6), (-16, 0.75), (-14, 0.95), (-12.5, 1.0), (-7, 1.0), (-6, 0.78), (-5, 0.62),
              (-4, 0.58), (-2.5, 0.62), (-2, 0.68), (-0.55, 0.72), (-0.43, 0.84), (-0.05, 0.68), ("I-0.1", 0.7), ("I+0.3", 1.06),
              ("I+2", 1.0), (12.2, 1.0)],
    "calor_b": [(-18.3, 0.0), (-2, 0.0), (-0.5, 0.15), ("I-0.05", 0.35), ("I+1.5", 0.15), (12.2, 0.15)],
    "puente": [(-18.3, 0.0), (-1, 0.0), (-0.55, 0.3), (-0.45, 1.0), (-0.3, 0.35), (-0.05, 0.45), ("I-0.05", 1.0), ("I+0.4", 0.0), (12.2, 0.0)],
    "frio": [(-18.3, 0.15), (-15, 0.0), (-7, 0.0), (-4, 1.0), (-0.55, 1.0), (-0.43, 0.85), (-0.05, 1.0), ("I", 1.0), ("I+1.2", 0.0), (12.2, 0.0)],
    "alba": [(-18.3, 0.0), (8, 0.0), (12.2, 1.0)],
    # el giro de las dos juntas (radio), el abrazo de A alrededor de B (radio) y la velocidad del
    # giro en vueltas por compas
    "giro": [(-18.3, 0.0), (-12.5, 0.0), (-11.5, 0.055), (-8.5, 0.06), (-7, 0.0), ("I", 0.0),
             ("I+1", 0.065), (4, 0.07), (5.5, 0.0), (12.2, 0.0)],
    "abrazo": [(-18.3, 0.0), (-2.5, 0.0), (-2, 0.09), (0, 0.08), ("I", 0.085), ("I+0.8", 0.0), (12.2, 0.0)],
    "vueltas": [(-18.3, 0.0), (-12.5, 0.0), (-11.5, 1.0), (-7, 1.0), (-6, 0.0), (-2.5, 0.0), (-2, 0.8),
                (-0.25, 0.45), (0, 0.15), ("I", 0.0), ("I+0.3", 1.2), (4, 1.0), (5.5, 0.3), (12.2, 0.0)],
    # alejandose todavia se buscan: un vaiven en espejo, una sube cuando la otra baja (radio)
    "vaiven": [(-18.3, 0.0), (4, 0.0), (5, 0.035), (8, 0.035), (10, 0.02), (12.2, 0.012)],
    # cuanto se mira cada una con la otra. "Es una historia de amor representada" (el DJ): se
    # miran al conocerse; en el vuelo, complices, apenas; A no le saca los ojos a B cuando se va, y B
    # perdida no mira a nadie hasta que vuelve; en la cura las dos; y al final se miran mientras se
    # alejan, con una pausa (9.5 a 10.5 en "a" y "b") para mirarse una ultima vez
    "mira_a": [(-18.3, 0.0), (-16, 0.0), (-15, 1.0), (-12.5, 1.0), (-11.5, 0.4), (-8, 0.4), (-7, 1.0),
               ("I", 1.0), ("I+2", 0.4), (4, 0.4), (5, 0.8), (9.5, 1.0), (10.5, 1.0), (12.2, 0.8)],
    "mira_b": [(-18.3, 0.0), (-16, 0.0), (-15, 1.0), (-12.5, 1.0), (-11.5, 0.4), (-8, 0.4), (-7, 0.5),
               (-6, 0.0), (-4, 0.0), (-3.25, 0.5), (-2, 1.0), ("I", 1.0), ("I+2", 0.4), (4, 0.4), (5, 0.8),
               (9.5, 1.0), (10.5, 1.0), (12.2, 0.8)],
    # cuanto respiran juntas (1 = al mismo tiempo)
    "sincro": [(-18.3, 0.0), (-14, 0.0), (-12.5, 1.0), (-7, 1.0), (-6, 0.0), (-2, 0.0), (0, 0.3), ("I", 0.3),
               ("I+0.5", 1.0), (12.2, 1.0)],
    # quien lleva (Heider y Simmel): la que sigue repite el camino de la otra con retardo, en
    # segundos. Antes de la cura lleva A (B contesta al conocerse y la sigue en el vuelo); separadas,
    # cada una por su lado; despues de la cura lleva B; al final, ninguna
    "retardo_b": [(-18.3, 0.0), (-16, 0.0), (-15, 0.5), (-12.5, 0.45), (-11, 0.25), (-8, 0.25), (-7, 0.0),
                  (12.2, 0.0)],
    "retardo_a": [(-18.3, 0.0), ("I", 0.0), ("I+1", 0.25), (4, 0.25), (6, 0.35), (8, 0.35), (9.5, 0.0), (12.2, 0.0)],
    # B esta detras de la capa de nubes cercana: la que se aleja se esconde, y despues asoma
    "detras_b": [(-18.3, 0.0), (-7, 0.0), (-6.5, 1.0), (-3.4, 1.0), (-2.8, 0.0), (12.2, 0.0)],
}


def segundo(clave: float | str, compas: float, impacto: float) -> float:
    if isinstance(clave, str):
        return impacto + float(clave[1:] or 0)
    return DROP_EN + clave * compas


def pista(nombre: str, t: np.ndarray, compas: float, impacto: float) -> np.ndarray:
    """Interpola una pista: suave entre claves (sale y llega frenando), las posiciones con
    Catmull-Rom para que el vuelo no se detenga en cada clave."""
    ts = np.array([segundo(c, compas, impacto) for c, _ in CLAVES[nombre]])
    if np.any(np.diff(ts) <= 0):
        raise ValueError(f"las claves de '{nombre}' no van en orden: {np.round(ts, 2).tolist()}")
    vs = np.array([np.atleast_1d(v) for _, v in CLAVES[nombre]], float)
    i = np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 2)
    u = np.clip((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1)[:, None]
    if vs.shape[1] == 1:
        u = u * u * (3 - 2 * u)
        return (vs[i] + (vs[i + 1] - vs[i]) * u)[:, 0]
    p0, p1, p2, p3 = vs[np.maximum(i - 1, 0)], vs[i], vs[i + 1], vs[np.minimum(i + 2, len(ts) - 1)]
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2
                  + (3 * p1 - p0 - 3 * p2 + p3) * u ** 3)


def resorte(objetivo: np.ndarray, dt: float, w0: np.ndarray, zeta: float) -> np.ndarray:
    """Sigue al objetivo con masa: arranca con atraso, frena pasandose un poco y se acomoda."""
    x, v = objetivo[0].copy(), np.zeros_like(objetivo[0])
    out = np.empty_like(objetivo)
    for k in range(len(objetivo)):
        acc = w0[k] ** 2 * (objetivo[k] - x) - 2 * zeta * w0[k] * v
        v = v + acc * dt
        x = x + v * dt
        out[k] = x
    return out


def bandas(audio: np.ndarray, sr: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Por cuadro: el golpe del bombo (0 a 1) y el grave lento (0 a 1)."""
    lo = sosfilt(butter(4, [40, 100], "bandpass", fs=sr, output="sos"), audio.mean(1))
    por = len(lo) // n
    e = np.sqrt(np.mean(lo[: por * n].reshape(n, por) ** 2, axis=1))
    lento = uniform_filter1d(e, int(2 * FPS))
    golpe = np.clip(e - uniform_filter1d(e, int(0.5 * FPS)), 0, None)
    golpe = np.clip(golpe / (np.percentile(golpe, 97) + 1e-9), 0, 1)
    for k in range(1, n):                                  # cae despacio, como una cuerda
        golpe[k] = max(golpe[k], golpe[k - 1] * 0.82)
    return golpe, lento / (np.percentile(lento, 95) + 1e-9)


def medir_impacto(audio: np.ndarray, sr: int, compas: float) -> float:
    """Donde vuelve el bombo despues del hueco del drop. Ahi va la cura, no en el drop del json."""
    lo = sosfilt(butter(4, [40, 100], "bandpass", fs=sr, output="sos"), audio.mean(1))
    tiempo = compas / 4

    def energia(t: float) -> float:
        return float(np.sqrt(np.mean(lo[int((t - 0.03) * sr): int((t + 0.12) * sr)] ** 2)))

    ref = np.median([energia(DROP_EN + k * tiempo) for k in range(-24, -8)])
    golpes = [(k, energia(DROP_EN + k * tiempo) / ref) for k in range(-4, 9)]
    hondo = min(golpes, key=lambda g: g[1])[0]
    vuelta = next((k for k, e in golpes if k > hondo and e >= 0.6), None)
    # mas alla de un compas y cuarto se cruzaria con las claves de despues de la cura
    return DROP_EN + min(vuelta if vuelta is not None else 4, 5) * tiempo


def intentos(t: np.ndarray, semilla: int = 159) -> np.ndarray:
    """La apagada intenta encenderse y no puede: pulsos que suben rapido y se caen."""
    rng = np.random.default_rng(semilla)
    out, s = np.zeros_like(t), 0.0
    while s < t[-1]:
        s += rng.uniform(1.0, 2.2)
        x = t - s
        sube = np.sin(np.clip(x / 0.25, 0, 1) * np.pi / 2) ** 2
        out = np.maximum(out, rng.uniform(0.5, 1.0) * (x >= 0) * sube * np.exp(-np.clip(x - 0.25, 0, None) / 0.45))
    return out


def respiracion(t: np.ndarray, dt: float, compas: float, impacto: float, sincro: np.ndarray,
                apagada: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """La respiracion cuenta la relacion (luciernagas sincronicas). Cada una tiene su frecuencia
    (A cada 2 compases, B cada 3.1 s) y un acople que las pone en fase cuando estan juntas. La
    apagada respira irregular y se sale de fase; la cura la vuelve a meter, y al final siguen en
    fase aunque esten lejos. La que lleva arrastra mas: antes de la cura A, despues B."""
    rng = np.random.default_rng(7)
    nudos = np.arange(0, t[-1] + 1.0, 0.7)
    irregular = np.interp(t, nudos, rng.uniform(-1, 1, len(nudos)))
    w_a = 2 * np.pi / (2 * compas)
    w_b = 2 * np.pi / 3.1 * (1 + 0.6 * apagada * irregular)
    acople = 3.0 * sincro
    fa, fb = np.empty_like(t), np.empty_like(t)
    x, y = 0.0, 2.2                                       # se conocen fuera de fase
    for i in range(len(t)):
        ka, kb = (0.15, 1.0) if t[i] < impacto else (1.0, 0.15)
        x, y = x + (w_a + acople[i] * ka * np.sin(y - x)) * dt, y + (w_b[i] + acople[i] * kb * np.sin(x - y)) * dt
        fa[i], fb[i] = x, y
    return fa, fb


def coreografia(t: np.ndarray, compas: float, impacto: float, dt: float) -> dict:
    """Todo lo que se mueve, por paso de tiempo, en coordenadas del cielo."""
    p = {k: pista(k, t, compas, impacto) for k in CLAVES}
    p["a"] = pista("a", t - p["retardo_a"], compas, impacto)    # la que sigue va atras en el tiempo
    p["b"] = pista("b", t - p["retardo_b"], compas, impacto)
    # el resorte: A decidida, B mas liviana; apagada, B pesa y tarda
    a = resorte(p["a"], dt, np.full(len(t), 7.0), 0.55)
    b = resorte(p["b"], dt, 6.0 - 3.2 * np.clip(1 - p["luz_b"] / 0.4, 0, 1), 0.6)
    cam = resorte(p["cam"], dt, np.full(len(t), 3.0), 1.0)
    th = np.cumsum(2 * np.pi * p["vueltas"] / compas) * dt
    elipse = np.stack([np.cos(th), 0.5 * np.sin(th)], 1)
    a = a + elipse * (p["giro"] + p["abrazo"])[:, None]
    b = b - elipse * p["giro"][:, None]
    espejo = np.stack([np.zeros_like(t), p["vaiven"] * np.sin(np.pi * t / compas)], 1)
    a, b = a + espejo, b - espejo
    prof = 0.15 * np.sin(th)                               # arriba de la elipse = mas lejos
    tam_a = p["tam_a"] * (1 - prof * (p["giro"] + p["abrazo"]) / 0.07)
    tam_b = p["tam_b"] * (1 + prof * p["giro"] / 0.07)
    # que respiren: un vaiven chico. B apagada intenta encenderse: en cada intento le sube la luz de
    # adentro, el halo y un temblor, y se cae; los intentos crecen cuando A llega a ayudarla
    apagada = np.clip(1 - p["luz_b"] / 0.4, 0, 1)
    ayuda = np.clip((t - segundo(-4, compas, impacto)) / (4 * compas), 0, 1)
    intento = apagada * intentos(t) * (0.6 + 0.4 * ayuda)
    temblor = np.stack([np.sin(37.0 * t), np.cos(41.0 * t)], 1)
    a = a + 0.006 * np.stack([np.sin(0.7 * t), np.sin(0.9 * t + 1.0)], 1)
    b = b + (0.006 + 0.012 * apagada)[:, None] * np.stack([np.sin(0.8 * t + 2.0), np.sin(0.6 * t + 0.5)], 1)
    b = b + 0.004 * intento[:, None] * temblor
    luz_b = p["luz_b"] + 0.10 * intento
    vida_b = p["luz_b"] * (1 - apagada) + 1.2 * intento
    fa, fb = respiracion(t, dt, compas, impacto, p["sincro"], apagada)
    resp_a, resp_b = np.sin(fa), (1 - 0.5 * apagada) * np.sin(fb)
    luz_a = p["luz_a"] * (1 + 0.04 * resp_a)
    luz_b = luz_b * (1 + 0.04 * resp_b)
    return {"a": a, "b": b, "cam": cam, "zoom": p["zoom"], "luz_a": luz_a, "luz_b": luz_b, "detras_b": p["detras_b"],
            "tam_a": tam_a, "tam_b": tam_b, "resp_a": resp_a, "resp_b": resp_b, "vida_a": p["luz_a"], "vida_b": vida_b,
            "mira_a": p["mira_a"], "mira_b": p["mira_b"],
            "calor_b": p["calor_b"], "frio": p["frio"], "alba": p["alba"], "puente": p["puente"]}


def armar_eventos(c: dict, compas: float, impacto: float) -> dict:
    """Donde y cuando: el primer toque (cuando de verdad se tocan, con el retardo de B), el
    intento que no prende, la cura, y el banco de nubes donde B se esconde (fijo en la capa
    cercana, centrado donde B esta a mitad de camino)."""
    cuadro = lambda s: int(segundo(s, compas, impacto) * FPS)
    f0, f1 = cuadro(-13), cuadro(-11.5)
    toque = f0 + int(np.argmin(np.linalg.norm(c["a"][f0:f1] - c["b"][f0:f1], axis=1)))
    intento = cuadro(-0.43)
    fb = cuadro(-4.5)
    zc = 1 + (c["zoom"][fb] - 1) * 1.4
    banco = en_pantalla(c["b"][fb], c["cam"][fb], c["zoom"][fb]) / zc + c["cam"][fb] * 1.7
    return {"toques": [(toque / FPS, (c["a"][toque] + c["b"][toque]) / 2), (intento / FPS, c["b"][intento])],
            "cura": (impacto, c["b"][int(impacto * FPS)]), "banco": banco}


def en_pantalla(xy: np.ndarray, cam: np.ndarray, zoom: float) -> np.ndarray:
    return (xy - cam) * zoom


def uniformes(f: int, c: dict, golpe: np.ndarray, fondo: np.ndarray, eventos: dict) -> dict:
    """Los valores del shader para el cuadro f (c ya muestreado por cuadro)."""
    cam, zoom, t = c["cam"][f], float(c["zoom"][f]), f / FPS
    idx = np.maximum(f - np.arange(NT) * PASO_ESTELA, 0)
    u = {"uTime": t, "uCam": tuple(cam), "uZoom": zoom, "uCalorB": float(c["calor_b"][f]),
         "uFrio": float(c["frio"][f]), "uPuente": float(c["puente"][f]), "uAlba": float(c["alba"][f]), "uFondo": 0.8 + 0.2 * float(fondo[f]),
         "uGolpe": float(golpe[f]) * (0.35 if t < eventos["cura"][0] else 1.0)}
    for k, s in (("A", "a"), ("B", "b")):
        u[f"uPos{k}"] = tuple(en_pantalla(c[s][f], cam, zoom))
        u[f"uLuz{k}"] = float(c[f"luz_{s}"][f])
        u[f"uTam{k}"] = float(c[f"tam_{s}"][f] * zoom ** 0.5)
        u[f"uResp{k}"] = float(c[f"resp_{s}"][f])
        u[f"uVida{k}"] = float(c[f"vida_{s}"][f])
        u[f"uMira{k}"] = float(c[f"mira_{s}"][f])
        pts = en_pantalla(c[s][idx], cam, zoom)
        u[f"uEstela{k}"] = [(float(x), float(y), float(lz)) for (x, y), lz in zip(pts, c[f"luz_{s}"][idx])]
    u["uDetrasB"] = float(c["detras_b"][f])
    zc = 1 + (zoom - 1) * 1.4
    u["uBanco"] = tuple(float(v) for v in (*((eventos["banco"] - cam * 1.7) * zc), 0.35 * zc))
    toques = [e for e in eventos["toques"] if e[0] <= t] or eventos["toques"][:1]
    for nombre, (cuando, donde) in (("uOnda", eventos["cura"]), ("uToque", toques[-1])):
        xy = en_pantalla(donde, cam, zoom)
        u[nombre] = (float(xy[0]), float(xy[1]), t - cuando)
    return u


def textos(mix: dict, inicio: float, desde: float, alto: int, carpeta: Path) -> str:
    """El nombre del tema cuando entra, como en las Sessions (naturaleza.textos): titulo arriba,
    artista abajo, a la izquierda, chico, en crema; entra 1.5 s despues del cambio y dura 8 s.
    Las medidas de las Sessions son para 1440 de alto y aca se escalan."""
    shutil.copyfile(FUENTE, carpeta / "fuente.ttf")
    limpio = lambda s: re.sub(r"\s*\((Extended|Original)( Mix)?\)\s*$", "", " ".join(s.split()), flags=re.I)
    e = alto / 1440
    filtros = []
    for k, tema in enumerate(mix["plan"]):
        a = (tema.get("cambio_in") or tema["desde"]) - inicio + 1.5
        z = a + 8.0
        if a < 0 or a > LARGO:
            continue
        artista, _, titulo = tema["tema"].partition(" - ")
        (carpeta / f"titulo_{k:02d}.txt").write_text(limpio(titulo or artista), encoding="utf-8")
        (carpeta / f"artista_{k:02d}.txt").write_text(artista if titulo else "", encoding="utf-8")
        T = f"(t+{desde:.3f})"
        alfa = f"if(lt({T},{a:.3f}),0,if(lt({T},{a + 1:.3f}),{T}-{a:.3f},if(lt({T},{z - 1.5:.3f}),1,max(0,({z:.3f}-{T})/1.5))))"
        comun = (f"fontfile=fuente.ttf:fontcolor={CREMA}:x={round(104 * e)}:shadowcolor=black@0.45:"
                 f"shadowx={round(2 * e)}:shadowy={round(2 * e)}")
        filtros.append(f"drawtext={comun}:textfile=titulo_{k:02d}.txt:fontsize={round(42 * e)}:y=h-{round(164 * e)}:alpha='0.94*{alfa}'")
        filtros.append(f"drawtext={comun}:textfile=artista_{k:02d}.txt:fontsize={round(30 * e)}:y=h-{round(112 * e)}:alpha='0.78*{alfa}'")
    return ("," + ",".join(filtros)) if filtros else ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", required=True)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--desde", type=float, default=0.0, help="segundo del minuto (para probar un tramo)")
    ap.add_argument("--hasta", type=float, default=LARGO)
    ap.add_argument("--hoja", help="ademas, una hoja de 12 cuadros chicos (960 px)")
    a = ap.parse_args()
    ancho, alto = map(int, a.res.split("x"))
    mix = json.loads(MIX.with_suffix(".json").read_text(encoding="utf-8"))
    k = next(i for i, t in enumerate(mix["plan"]) if TEMA_DROP in t["tema"])
    compas = 4 * 60 / mix["tempo"]
    drop = mix["plan"][k]["desde"] + mix["estructura"][k]["medido"]["drop"] * compas
    inicio = drop - DROP_EN
    sr = sf.info(str(MIX.with_suffix(".wav"))).samplerate
    audio, _ = sf.read(str(MIX.with_suffix(".wav")), start=int(inicio * sr), stop=int((inicio + LARGO) * sr),
                       dtype="float32")
    n = int(LARGO * FPS)
    golpe, fondo = bandas(audio, sr, n)
    impacto = medir_impacto(audio, sr, compas)

    dt = 1 / (FPS * SUB)
    c = coreografia(np.arange(n * SUB) * dt, compas, impacto, dt)
    c = {kk: v[::SUB] for kk, v in c.items()}
    eventos = armar_eventos(c, compas, impacto)

    ctx = moderngl.create_standalone_context()
    prog = ctx.program(vertex_shader=VERTICES, fragment_shader=SHADER.read_text(encoding="utf-8"))
    vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "2f", "pos")])
    fbo = ctx.simple_framebuffer((ancho, alto))
    fbo.use()
    prog["uRes"].value = (ancho, alto)
    f0, f1 = int(a.desde * FPS), int(min(a.hasta, LARGO) * FPS)
    largo = (f1 - f0) / FPS
    fundidos = f"fade=in:0:45,fade=out:{n - 60}:60" if f0 == 0 and f1 == n else "null"
    tmp = tempfile.TemporaryDirectory()
    letras = textos(mix, inicio, a.desde, alto, Path(tmp.name))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ancho}x{alto}", "-r", str(FPS),
         "-i", "-", "-ss", f"{inicio + a.desde:.3f}", "-t", f"{largo:.3f}", "-i", str(MIX.with_suffix(".wav")),
         "-vf", f"vflip,{fundidos}{letras}", "-af", f"afade=in:d=1.5,afade=out:st={max(largo - 2, 0):.3f}:d=2",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", str(Path(a.salida).resolve())],
        stdin=subprocess.PIPE, cwd=tmp.name)
    muestras = {int(s * FPS) for s in HOJA_EN}
    hoja = []
    for f in range(f0, f1):
        for nombre, valor in uniformes(f, c, golpe, fondo, eventos).items():
            if nombre in prog:
                prog[nombre].value = valor
        vao.render(moderngl.TRIANGLE_STRIP)
        crudo = fbo.read(components=3)
        ff.stdin.write(crudo)
        if f in muestras:
            hoja.append(Image.frombytes("RGB", (ancho, alto), crudo).transpose(Image.FLIP_TOP_BOTTOM).resize((240, 135)))
    ff.stdin.close()
    ff.wait()
    tmp.cleanup()
    if ff.returncode:
        raise SystemExit(f"ffmpeg termino con error {ff.returncode}")
    if a.hoja and hoja:
        lienzo = Image.new("RGB", (960, 135 * ((len(hoja) + 3) // 4)))
        for i, im in enumerate(hoja):
            lienzo.paste(im, ((i % 4) * 240, (i // 4) * 135))
        lienzo.save(a.hoja, quality=85)
    print(f"{a.salida}  (s {a.desde:.0f} a {a.desde + largo:.0f}; desde {int(inicio // 60)}:{inicio % 60:04.1f} del mix;"
          f" drop de {TEMA_DROP} en el s {DROP_EN:.0f}, vuelve el bombo y se cura en el s {impacto:.2f})")


if __name__ == "__main__":
    main()
