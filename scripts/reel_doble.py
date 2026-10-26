# -*- coding: utf-8 -*-
"""Reel 9:16 en doble exposicion: el DJ tocando y los paisajes de la Session fundidos en el.

POR QUE
-------
Para el Reel de la Session 04 el DJ eligio (2026-10-26): doble exposicion ("su silueta se llena
de montanas o estrellas en los drops"), pulso con el bombo, cortes al beat, destellos que entran en
el drop y el color de la marca. Lo que ya habia dicho sigue valiendo: no es un recorte pegado sobre
un fondo (eso fue "MALISIMAS" el 2026-10-21), su cara y su piel naturales, y sobre la imagen solo
el nombre del tema.

COMO
----
- La toma: un recorte 9:16 quieto del 4K (1216x2160), centrado en sus hombros, sin movimiento falso.
- El matte: RVM (Robust Video Matting, recurrente, a 0.4: a 0.25 se tragaba la cortina debajo del
  brazo levantado), acotado por la mascara de MediaPipe Pose: lejos de su cuerpo no hay persona y
  adentro no hay agujeros. El color del borde sale del primer plano descontaminado de RVM, asi no
  queda el gris de la cortina pegado a la silueta.
- La consola es una mascara fija: su borde de arriba es una recta, medida en cada plano.
- La fusion: el paisaje entra en "screen" adentro de la silueta, o sea en lo oscuro de la campera y
  la gorra no, la cara y las manos no. En el borde, la luz del paisaje envuelve la figura.
- Haces, destellos y polvo de luz generados aca, que entran con el drop; el pulso sale del bombo
  medido en la mezcla, no de la grilla.

USO
---
    python scripts/reel_doble.py cuadros --t 1.0 8.15 13.5 27 --salida <dir>   # cuadros a 1080x1920
    python scripts/hoja_reel.py ...                                            # la hoja de recorrido
    python scripts/reel_doble.py render [--planos 0 1 ...] [--salida X.mp4]    # el Reel entero

El render (reel_render.py) lee cada plano de corrido, deja una pieza sin perdida por plano (se retoma
si se corta), une con la mezcla y verifica el audio contra el tramo recortado con ffmpeg. Con --planos
solo hace esas piezas, sin unir: asi se reparten entre dos procesos.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PLAN = RAIZ / "data" / "video" / "reel_session04.json"
RVM = RAIZ / "postproduction" / "modelos" / "rvm_mobilenetv3_fp32.onnx"
POSE = RAIZ / "postproduction" / "modelos" / "pose_landmarker_full.task"
STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
FPS = 30
W, H = 1080, 1920
CW, CH = 1216, 2160            # recorte 9:16 del 4K (par: con 1215 ffmpeg recorta 1214)
RVM_RATIO = 0.4
CALENTAR_S = 1.2               # RVM es recurrente: arranca antes del plano para llegar asentado
CREMA = (243, 235, 221)
BLANCO_CALIDO = np.array([1.0, 0.90, 0.74], np.float32)

# cuanto pesa cada cosa en cada modo (ver "modos" en el plan). La composicion es una doble exposicion de
# pelicula: el paisaje entero y el DJ sobre negro, sumados en "screen". "opaco" oscurece el paisaje debajo
# de su cuerpo (0, un fantasma; 1, solido): con 0 lo negro de la campera desaparece en el paisaje y el
# paisaje se lo come. "piel" deja la cara, las manos y la gorra naturales y opacas. "aire" aclara un poco
# el paisaje de afuera de la silueta, para que adentro se lea mas hondo.
MODOS = {
    "fusion":  {"dj": 0.85, "opaco": 0.20, "consola": 0.85, "piel": 0.70, "aire": 0.0,  "envoltura": 0.0,
                "haces": 0.0,  "polvo": 0.15, "brazos": 0.6},
    "paisaje": {"dj": 0.55, "opaco": 0.0,  "consola": 1.00, "piel": 0.30, "aire": 0.0,  "envoltura": 0.0,
                "haces": 0.0,  "polvo": 0.15, "brazos": 0.0},
    "drop":    {"dj": 1.0,  "opaco": 0.38, "consola": 0.95, "piel": 1.0,  "aire": 0.0,  "envoltura": 0.18,
                "haces": 0.30, "polvo": 1.0, "brazos": 1.0},
}


# ---------------------------------------------------------------- el audio: drop y bombos

def golpes(mezcla: Path, drop_aprox: float, beat: float, antes: int, despues: int) -> tuple[float, np.ndarray]:
    """El golpe del drop y cada bombo del tramo, medidos en la mezcla (no la grilla: aca difiere 0.4 s)."""
    sr = sf.info(str(mezcla)).samplerate
    t0, t1 = drop_aprox - antes * beat - 1.0, drop_aprox + despues * 4 * beat + 1.0
    x, _ = sf.read(str(mezcla), start=int(t0 * sr), stop=int(t1 * sr), dtype="float32")
    lo = sosfiltfilt(butter(4, [40, 110], btype="band", fs=sr, output="sos"), x.mean(1))
    e = np.sqrt(np.convolve(lo ** 2, np.ones(int(0.004 * sr)) / int(0.004 * sr), mode="same"))
    i0, i1 = int((drop_aprox - 0.5 - t0) * sr), int((drop_aprox + 0.5 - t0) * sr)
    pico = e[i0:i1].max()
    drop = t0 + (i0 + int(np.argmax(e[i0:i1] > 0.5 * pico))) / sr

    def ataque(tb: float) -> float:
        a, z = int((tb - 0.06 - t0) * sr), int((tb + 0.06 - t0) * sr)
        seg = e[a:z]
        return t0 + (a + int(np.argmax(seg > 0.5 * seg.max()))) / sr

    bombos = [drop] + [ataque(drop + k * beat) for k in range(1, int(despues * 4))]
    return drop, np.array(bombos)


def pulso(t: float, bombos: np.ndarray, tau: float = 0.11) -> float:
    pasados = bombos[bombos <= t + 1e-6]
    if not len(pasados):
        return 0.0
    return float(np.exp(-(t - pasados[-1]) / tau))


# ---------------------------------------------------------------- la toma: cuadros, matte y pose

def leer_toma(toma: Path, desde: float, seg: float, x0: int, cada60: int) -> np.ndarray:
    """Cuadros RGB del recorte 9:16. cada60=2 toma uno de cada dos (30 por segundo), 1 todos."""
    vf = f"crop={CW}:{CH}:{x0}:0" + (",select='not(mod(n\\,2))'" if cada60 == 2 else "")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, desde):.3f}", "-i", str(toma),
           "-t", f"{seg:.3f}", "-map", "0:v:0", "-vf", vf, "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, CH, CW, 3)


@lru_cache(maxsize=1)
def sesion_rvm():
    import onnxruntime as ort
    return ort.InferenceSession(str(RVM), providers=["DmlExecutionProvider", "CPUExecutionProvider"])


class Matte:
    """RVM cuadro a cuadro: es recurrente, asi que el estado pasa de un cuadro al siguiente."""

    def __init__(self) -> None:
        self.sesion = sesion_rvm()
        self.rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4

    def __call__(self, f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        src = (f.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        fgr, pha, *self.rec = self.sesion.run(None, {
            "src": src, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2], "r4i": self.rec[3],
            "downsample_ratio": np.array([RVM_RATIO], np.float32)})
        return pha[0, 0], fgr[0].transpose(1, 2, 0)


def matte_rvm(cuadros: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
    m = Matte()
    salida = [m(f) for f in cuadros]
    return [x[0] for x in salida], [x[1] for x in salida]


class Pose:
    """MediaPipe Pose en modo video: (puntos 33x3 en pixeles del recorte, mascara del cuerpo) por cuadro."""

    def __init__(self, fps: float) -> None:
        import mediapipe as mp
        self.mp = mp
        op = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(POSE)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=1, output_segmentation_masks=True)
        self.det = mp.tasks.vision.PoseLandmarker.create_from_options(op)
        self.fps, self.k = fps, 0

    def __call__(self, f: np.ndarray) -> tuple[np.ndarray | None, np.ndarray | None]:
        chico = np.ascontiguousarray(cv2.resize(f, (CW // 2, CH // 2), interpolation=cv2.INTER_AREA))
        r = self.det.detect_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=chico),
                                      int(self.k * 1000 / self.fps))
        self.k += 1
        if not r.pose_landmarks:
            return None, None
        pts = np.array([(q.x * CW, q.y * CH, q.visibility) for q in r.pose_landmarks[0]], np.float32)
        return pts, cv2.resize(r.segmentation_masks[0].numpy_view(), (CW, CH), interpolation=cv2.INTER_LINEAR)

    def close(self) -> None:
        self.det.close()


def poses(cuadros: np.ndarray, fps: float) -> list[tuple[np.ndarray | None, np.ndarray | None]]:
    pose = Pose(fps)
    try:
        return [pose(f) for f in cuadros]
    finally:
        pose.close()


def centrar(toma: Path, desde: float, seg: float) -> int:
    """x0 del recorte: la mediana del centro de su cuerpo en el tramo (momentos.py, 6 por segundo).
    Con el de un solo cuadro, en el 193 s quedaba cortado: despues se corre a la derecha."""
    mom = json.loads((RAIZ / "data" / "video" / f"{toma.stem}_momentos.json").read_text(encoding="utf-8"))
    n = mom["muestras_por_s"]
    cx = [c for c in mom["centro_x"][int(desde * n):int((desde + seg) * n) + 1] if c is not None]
    centro = float(np.median(cx)) * 3840
    return int(np.clip(round((centro - CW / 2) / 2) * 2, 0, 3840 - CW))


def borde_consola(cuadros: np.ndarray) -> np.ndarray:
    """La recta del borde de arriba de la consola: y por columna, ajustada sin las manos encima.

    Es el PRIMER paso de claro a oscuro bajando, no el mas fuerte: el mas fuerte caia en los pads
    encendidos, 26 px mas abajo, y entre la campera y la consola quedaba una franja de paisaje."""
    med = np.median(cuadros[:: max(1, len(cuadros) // 7)].astype(np.float32).mean(3), axis=0)
    y0 = 1600
    zona = cv2.GaussianBlur(med, (0, 0), 1.5)[y0:1820]
    grad = zona[:-6] - zona[6:]                     # claro arriba, oscuro abajo
    fuerte = grad > 22
    hay = fuerte.any(axis=0)
    primero = np.argmax(fuerte, axis=0)
    ys = np.array([primero[x] + int(np.argmax(grad[primero[x]:primero[x] + 9, x])) for x in range(CW)], np.float64)
    ys += y0 + 3
    xs = np.arange(CW, dtype=np.float64)
    # arranca de la altura mas repetida (las manos y la campera dan bordes sueltos), y ajusta la recta
    # con los que caen cerca; un ajuste directo se iba al medio y en el 360 s se quedaba sin columnas
    moda = float(np.argmax(np.bincount(np.round(ys[hay]).astype(int))))
    ok = hay & (np.abs(ys - moda) < 6)
    if ok.sum() < 80:
        return np.full(CW, moda)
    a, b = np.polyfit(xs[ok], ys[ok], 1)
    cerca = hay & (np.abs(ys - (a * xs + b)) < 3)
    if cerca.sum() >= 80:
        a, b = np.polyfit(xs[cerca], ys[cerca], 1)
    return a * xs + b


# ---------------------------------------------------------------- el paisaje

@lru_cache(maxsize=1)
def elegidos() -> dict[int, dict]:
    el = {}
    for f in sorted((RAIZ / "data" / "video").glob("session_04_etapa_*.json")):
        for p in json.loads(f.read_text(encoding="utf-8"))["planos"]:
            el[p["n"]] = p
    return el


def leer_paisaje(n: int, desde: float, seg: float, x_rel: float, y_rel: float = 0.0, alto: int = H) -> np.ndarray:
    """Cuadros 1080x1920 del plano aprobado, con su encuadre y su grado de la Session. `alto` agranda el
    paisaje (1920 = el alto justo) y `x_rel`/`y_rel` eligen que parte cae en el cuadro vertical."""
    p = elegidos()[n]
    ruta = RAIZ / p["archivo"] if "archivo" in p else STOCK / f"{p['id']}.mp4"
    ancho = round(alto * 16 / 9 / 2) * 2
    x, y = int(round((ancho - W) * x_rel)), int(round((alto - H) * y_rel))
    vf = (f"fps={FPS},{p['encuadre']},setsar=1,format=gbrp16le,{p['grado']},"
          f"scale={ancho}:{alto}:flags=lanczos,crop={W}:{H}:{x}:{y},format=rgb48le")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{p['desde'] + desde:.3f}", "-i", str(ruta),
           "-t", f"{seg + 0.2:.3f}", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint16).reshape(-1, H, W, 3)


# ---------------------------------------------------------------- color

def grado_dj(x: np.ndarray) -> np.ndarray:
    """Primaria invisible: la mitad del tinte calido de la luz de la pieza, negros firmes, contraste suave.
    La cortina medida (0.63, 0.58, 0.56) y el blanco de la campera tiraban a amarillo."""
    x = x * np.array([0.975, 1.0, 1.03], np.float32)
    x = np.clip((x - 0.018) / 0.982, 0, 1)
    s = x * x * (3 - 2 * x)
    return np.clip(x + (s - x) * 0.22, 0, 1)


def grado_marca(x: np.ndarray) -> np.ndarray:
    """El paisaje con el color de la marca: calido y naranja, con contraste. El amarillo del sol (125) salia
    limon: el verde baja en las luces, que es donde el amarillo se vuelve naranja."""
    x = np.clip(x * np.array([1.04, 0.95, 0.84], np.float32), 0, 1)
    # el amarillo (verde cerca del rojo) se corre a naranja: el verde baja hasta 0.68 del rojo
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    sobra = np.clip(g - 0.68 * r, 0, None) * suave(0.10, 0.35, r - b)
    x = np.stack([r, g - 0.85 * sobra, b], axis=2)
    s = np.clip(x, 0, 1)
    s = s * s * (3 - 2 * s)
    return np.clip(x + (s - x) * 0.35, 0, 1)


def screen(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 1 - (1 - a) * (1 - b)


def suave(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- mascaras de la figura

def disco(r: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def rellenar(m: np.ndarray) -> np.ndarray:
    """La mascara binaria con sus agujeros cerrados (lo que el fondo no alcanza desde el borde del cuadro)."""
    h, w = m.shape
    pad = np.zeros((h + 2, w + 2), np.uint8)
    pad[1:-1, 1:-1] = m
    cv2.floodFill(pad, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 2)
    return (pad[1:-1, 1:-1] != 2).astype(np.uint8)


def manga_crema(a: np.ndarray, cuadro: np.ndarray) -> np.ndarray:
    """La manga crema, por su color, adentro de la silueta. En el ultimo plano RVM dejaba muescas
    semitransparentes de 15 a 25 px en la manga que da contra la pared (96 de 177 cuadros), algunas
    abiertas hacia afuera, y un cierre de la mascara no las tapaba. Medido en ese plano: la manga da luma
    150-185 con R-B 23-48; la pared, luma 115-143 con R-B 4-18, y el reflejo de la lampara, R-B negativo."""
    x = cuadro.astype(np.float32)
    luma = x.mean(2)
    crema = suave(145, 165, luma) * suave(16, 26, x[..., 0] - x[..., 2])
    casco = rellenar(cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, disco(14)))
    casco = cv2.erode(casco, disco(2)).astype(np.float32)
    return np.maximum(a, cv2.GaussianBlur(crema * casco, (0, 0), 1.2))


def alfa_fina(pha: np.ndarray, seg: np.ndarray | None, cierre: int = 4) -> np.ndarray:
    """El matte de RVM, limpio. Cuatro arreglos, cada uno por algo que se vio en el Reel (2026-10-26):
    - MediaPipe rellena agujeros, pero solo adentro de la silueta de RVM: su mascara es gruesa y bajo el
      codo y bajo la mano metia una franja de cortina (cuadros 118 y 175);
    - un cierre chico tapa el moteado de RVM en la manga blanca contra la pared clara (cuadro 705);
    - lo semitransparente lejos del cuerpo solido se apaga: eran pedazos de cortina sueltos (cuadro 881);
    - el borde se cierra un pixel: afuera quedaba una linea de la sombra de la manga sobre la cortina.
    `cierre` es el radio de ese cierre. El plano lo sube cuando la manga blanca da contra la pared clara:
    en el ultimo plano RVM dejaba muescas semitransparentes de 15 a 25 px adentro de la manga, en 96 de
    sus 177 cuadros, y con 4 no se tapaban. Un cierre no agranda el borde de afuera, solo llena lo que
    queda entre dos partes solidas."""
    if seg is None:
        return pha
    a = np.maximum(pha, cv2.morphologyEx(pha, cv2.MORPH_CLOSE, disco(cierre)))
    silueta = cv2.GaussianBlur(rellenar((a > 0.5).astype(np.uint8)).astype(np.float32), (0, 0), 2)
    cuerpo = (seg > 0.5).astype(np.uint8)
    cerca = cv2.GaussianBlur(cv2.dilate(cuerpo, disco(70)).astype(np.float32), (0, 0), 12)
    adentro = cv2.GaussianBlur(cv2.erode(cuerpo, disco(35)).astype(np.float32), (0, 0), 6) * silueta
    a = np.maximum(a * np.clip(cerca * 1.6 - 0.3, 0, 1), adentro)
    lejos = cv2.distanceTransform((a < 0.85).astype(np.uint8), cv2.DIST_L2, 5)
    a = a * (1 - suave(10, 28, lejos))
    a = cv2.erode(a, disco(1))
    return np.clip((a - 0.06) / 0.94, 0, 1)


def cabeza(pts: np.ndarray | None) -> np.ndarray:
    """1 arriba del menton (la gorra y la cara), 0 desde el cuello de la campera, en el recorte.
    La transicion cae sobre el cuello blanco, donde el screen no cambia nada y no se ve."""
    if pts is None:
        return np.zeros((CH, CW), np.float32)
    ojo_y = (pts[2, 1] + pts[5, 1]) / 2
    boca_y = (pts[9, 1] + pts[10, 1]) / 2
    menton = boca_y + 0.9 * max(boca_y - ojo_y, 30)
    yy = np.arange(CH, dtype=np.float32)[:, None]
    return np.broadcast_to(1 - suave(menton - 10, menton + 70, yy), (CH, CW)).astype(np.float32)


def torso(pts: np.ndarray | None) -> np.ndarray:
    """El torso (hombros y caderas de MediaPipe), con un borde ancho y suave, en el recorte."""
    m = np.zeros((CH, CW), np.float32)
    if pts is None:
        return m
    poli = pts[[11, 12, 24, 23], :2].astype(np.int32)
    cv2.fillPoly(m, [poli], 1.0)
    # sin agrandarlo: dilatado se metia en los brazos, que cuelgan pegados al cuerpo
    return desenfoque(cv2.erode(m, disco(15)), 35)


def piel(rgb: np.ndarray) -> np.ndarray:
    """La piel por su color, no por zonas: cara, cuello y manos donde esten. Medido en la toma: la piel da
    Cr 155-167 y Cb 96-110; la campera crema Cr 140-143 y Cb 114-126; la remera beige Cr 142."""
    ycc = cv2.cvtColor((np.clip(rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2YCrCb).astype(np.float32)
    m = suave(146, 153, ycc[..., 1]) * (1 - suave(114, 120, ycc[..., 2])) * suave(45, 75, ycc[..., 0])
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disco(4))
    return desenfoque(cv2.dilate(m, disco(4)), 3)


def fuente_de_luz(pts: np.ndarray | None) -> tuple[float, float]:
    """Detras de la cabeza: de ahi salen los haces, y la cabeza los tapa."""
    if pts is None:
        return CW / 2, CH * 0.2
    ojo_y = (pts[2, 1] + pts[5, 1]) / 2
    boca_y = (pts[9, 1] + pts[10, 1]) / 2
    return float(pts[0, 0]), float(ojo_y - 1.2 * max(boca_y - ojo_y, 30))


def mascara_consola(borde: np.ndarray) -> np.ndarray:
    yy = np.arange(CH, dtype=np.float32)[:, None]
    return np.clip(yy - borde[None, :].astype(np.float32) - 1.0, 0, 1)


@dataclass(frozen=True)
class Figura:
    """Todo lo de la toma que necesita la composicion, ya a 1080x1920."""
    dj: np.ndarray
    fgr: np.ndarray
    alfa: np.ndarray
    consola: np.ndarray
    relleno: np.ndarray       # 0 en la cabeza y la piel
    llenar: np.ndarray        # 1 en el torso, 0.25 en los brazos
    luz: tuple[float, float]


def a_salida(x: np.ndarray) -> np.ndarray:
    return cv2.resize(x, (W, H), interpolation=cv2.INTER_AREA)


def figura(cuadro: np.ndarray, pha: np.ndarray, fgr: np.ndarray, pts, seg, borde: np.ndarray,
           cierre: int = 4) -> Figura:
    dj = a_salida(cuadro.astype(np.float32) / 255)
    # nitidez sin halos: radio chico y umbral, despues de bajar a 1080
    blando = cv2.GaussianBlur(dj, (0, 0), 1.1)
    detalle = dj - blando
    dj = np.clip(dj + 0.35 * detalle * (np.abs(detalle) > 0.004), 0, 1)
    lx, ly = fuente_de_luz(pts)
    alfa = alfa_fina(pha, seg, cierre)
    if cierre > 4:
        alfa = manga_crema(alfa, cuadro)
    # RVM corta el cuerpo unos px antes del borde de la consola: se baja hasta tocarla, sin costura
    yy = np.arange(CH, dtype=np.float32)[:, None]
    # (poco: con 16 px la manga arrastraba un parche de cortina hasta la consola)
    banda = ((yy > borde[None, :] - 9) & (yy < borde[None, :] + 3)).astype(np.float32)
    abajo = cv2.dilate(alfa, np.ones((9, 1), np.uint8), anchor=(0, 8))
    alfa = np.maximum(alfa, abajo * banda)
    proteger = np.maximum(a_salida(cabeza(pts)), piel(dj))
    # el paisaje llena sobre todo el torso; en los brazos entra poco, si no las franjas oscuras de las
    # mangas quedaban huecas y el brazo se partia
    llenar = 0.25 + 0.75 * a_salida(torso(pts))
    return Figura(dj=grado_dj(dj), fgr=grado_dj(a_salida(np.clip(fgr, 0, 1))),
                  alfa=a_salida(alfa), consola=a_salida(mascara_consola(borde)),
                  relleno=1 - proteger, llenar=llenar, luz=(lx * W / CW, ly * H / CH))


# ---------------------------------------------------------------- composicion

def desenfoque(x: np.ndarray, sigma: float) -> np.ndarray:
    return cv2.GaussianBlur(x, (0, 0), sigma)


def haces(fuente: np.ndarray, centro: tuple[float, float], pasos: int = 28) -> np.ndarray:
    """Rayos que salen de `centro`: la luz del fondo arrastrada hacia afuera (desenfoque radial)."""
    acc = np.zeros_like(fuente)
    peso = 0.0
    for i in range(pasos):
        s = 1.0 + i * 0.03
        m = np.float32([[1 / s, 0, centro[0] * (1 - 1 / s)], [0, 1 / s, centro[1] * (1 - 1 / s)]])
        d = 0.93 ** i
        acc += cv2.warpAffine(fuente, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * d
        peso += d
    return acc / peso


def color_de_adentro(f: Figura) -> np.ndarray:
    """El color del borde sale de los pixeles de adentro (convolucion normalizada), no de la toma: en el
    borde de media transparencia la toma tiene gris de cortina mezclado, y eso era un aro claro."""
    adentro = (f.alfa > 0.97).astype(np.float32)
    num = desenfoque(f.dj * adentro[..., None], 3)
    den = desenfoque(adentro, 3)[..., None]
    lejos = den < 0.02
    return np.where(lejos, f.fgr, num / np.maximum(den, 1e-3))


def exposicion(P: np.ndarray, dj: float) -> np.ndarray:
    """Cuanto de el entra en la doble exposicion. Escalarlo parejo (P * dj) dejaba la campera blanca gris en
    la apertura (0.85 -> 0.53); con una curva lo blanco queda en 0.75 y lo oscuro sigue transparente."""
    if dj >= 1:
        return P
    return min(1.0, dj + 0.3) * np.power(np.clip(P, 0, 1), 1 + 0.6 * (1 - dj))


def componer(f: Figura, paisaje: np.ndarray, modo: str, ajustes: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    """La doble exposicion, sin efectos. Devuelve la imagen y el fondo (para los haces).

    El cuerpo entra como una segunda exposicion sobre negro: donde es claro (la campera blanca) se ve el,
    donde es oscuro (lo negro y lo verde de la campera) se ve el paisaje. La cabeza y la piel van con una
    composicion comun (el sobre el paisaje), porque el screen suma luz en el borde de media transparencia
    y alrededor de la cara dejaba un halo claro."""
    m = {**MODOS[modo], **(ajustes or {})}
    a, k = f.alfa[..., None], f.consola[..., None]
    solido = suave(0.85, 1.0, f.alfa)[..., None]
    P = color_de_adentro(f) * (1 - solido) + f.dj * solido
    figura_ = np.maximum(f.alfa, f.consola)
    afuera = screen(paisaje, BLANCO_CALIDO * m["aire"]) if m["aire"] else paisaje
    pluma = desenfoque(f.alfa, 4)[..., None]
    # adentro el paisaje se oscurece con una curva y no multiplicando: el amarillo oscurecido parejo da
    # oliva; con la curva el verde y el azul bajan mas que el rojo y queda naranja hondo
    adentro = np.power(np.clip(paisaje, 0, 1), 1 + 1.5 * m["opaco"])
    base = afuera * (1 - pluma) + adentro * pluma
    doble = screen(base, exposicion(P, m["dj"]) * a)
    if m["envoltura"]:
        fuera = 1 - figura_
        luz = desenfoque(afuera * fuera[..., None], 6) / (desenfoque(fuera, 6)[..., None] + 1e-3)
        borde = (f.alfa * desenfoque(fuera, 6))[..., None]
        doble = doble + (screen(doble, luz) - doble) * borde * m["envoltura"]
    comun = P * a + afuera * (1 - a)
    proteger = 1 - f.relleno
    w = (proteger * m["piel"] + f.relleno * (1 - f.llenar) * m["brazos"])[..., None]
    O = doble * (1 - w) + comun * w
    # la consola: la toma tal cual, con apenas paisaje. En el armado iba en transparencia como el y quedaba
    # banada de niebla (lo marco el DJ en la hoja). En el modo paisaje va sin nada encima (1.0): con 0.70 el
    # negro de la toma, (30,27,23), quedaba en (75,46,26), con los arboles del 118 encima, y la consola
    # cambiaba de tono en cada corte (lo marco el revisor, 2026-10-26)
    consola = screen(afuera * (1 - m["consola"]), f.dj)
    return O * (1 - k) + consola * k, afuera


@dataclass(frozen=True)
class Particula:
    x: float
    y: float
    r: float
    v: float
    vaiven: float
    fase: float
    brillo: float
    delante: bool


def particulas(n: int = 150, semilla: int = 4) -> list[Particula]:
    rng = np.random.default_rng(semilla)
    out = []
    for _ in range(n):
        grande = rng.random() < 0.18
        out.append(Particula(x=float(rng.uniform(0, W)), y=float(rng.uniform(0, H)),
                             r=float(rng.uniform(8, 18) if grande else rng.uniform(1.6, 4.2)),
                             v=float(rng.uniform(18, 55)), vaiven=float(rng.uniform(8, 30)),
                             fase=float(rng.uniform(0, 2 * np.pi)),
                             brillo=float(rng.uniform(0.16, 0.34) if grande else rng.uniform(0.55, 1.0)),
                             delante=bool(grande and rng.random() < 0.6)))
    return out


def polvo(t: float, ps: list[Particula], delante: bool) -> np.ndarray:
    capa = np.zeros((H, W), np.float32)
    for p in ps:
        if p.delante != delante:
            continue
        y = (p.y - p.v * t) % (H + 80) - 40
        x = p.x + p.vaiven * np.sin(0.7 * t + p.fase)
        b = p.brillo * (0.65 + 0.35 * np.sin(2.1 * t + 3 * p.fase))
        rr = int(p.r * 3) + 2
        x0, y0 = int(x) - rr, int(y) - rr
        if x0 < -2 * rr or y0 < -2 * rr or x0 > W or y0 > H:
            continue
        yy, xx = np.mgrid[y0:y0 + 2 * rr + 1, x0:x0 + 2 * rr + 1].astype(np.float32)
        g = b * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * p.r ** 2))
        ya, yb, xa, xb = max(0, y0), min(H, y0 + 2 * rr + 1), max(0, x0), min(W, x0 + 2 * rr + 1)
        if ya < yb and xa < xb:
            capa[ya:yb, xa:xb] += g[ya - y0:yb - y0, xa - x0:xb - x0]
    return capa


CALIDO = np.array([1.0, 0.80, 0.56], np.float32)


def destello(t_drop: float, centro: tuple[float, float], frase_s: float) -> np.ndarray:
    """El destello: un trazo horizontal de luz por el sol, con su halo, que entra en el golpe del drop y se
    apaga en un beat; vuelve mas suave en el uno de cada frase de cuatro compases."""
    golpes_ = [(0.0, 0.85)] + [(k * frase_s, 0.30) for k in (1, 2)]
    i = sum(peso * np.exp(-(t_drop - t0) / 0.32) for t0, peso in golpes_ if t_drop >= t0 - 1e-6)
    if t_drop < -1.5 / FPS or i < 0.01:
        return np.zeros((H, W, 3), np.float32)
    if t_drop < 0:
        i = 0.3
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dy, dx = yy - centro[1], xx - centro[0]
    nucleo = np.exp(-(dy / 3.5) ** 2) * np.exp(-dx ** 2 / (2 * 650 ** 2))
    halo = np.exp(-(dy / 26) ** 2) * np.exp(-dx ** 2 / (2 * 480 ** 2)) * 0.35
    gloria = np.exp(-(dx ** 2 + dy ** 2) / (2 * 150 ** 2)) * 0.45
    return (nucleo[..., None] * BLANCO_CALIDO + (halo + gloria)[..., None] * CALIDO) * float(i)


def donde_el_sol(fondo: np.ndarray) -> tuple[float, float] | None:
    """El punto mas claro del paisaje, si es un sol (o su corona) y no un cielo parejo."""
    chico = cv2.resize(fondo.mean(2), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    chico = desenfoque(chico, 4)
    y, x = np.unravel_index(int(np.argmax(chico)), chico.shape)
    if chico[y, x] < 0.86 or chico[y, x] - float(np.median(chico)) < 0.25:
        return None
    return float(x * 8 + 4), float(y * 8 + 4)


def efectos(O: np.ndarray, fondo: np.ndarray, f: Figura, modo: str, t: float, td: float, pul: float,
            ps: list[Particula], sol_en_cuadro: bool = False) -> np.ndarray:
    """Haces, polvo de luz, brillo y el destello del drop. `td` es el tiempo desde el golpe del drop.

    El destello sale solo si el paisaje tiene sol: donde lo encuentra `donde_el_sol`, o, si el plano dice
    `sol_en_cuadro`, detras de su cabeza. Sin sol no va: en el arrebol (136) el destello caia detras de la
    cabeza y se leia como una estela que cruzaba el cielo (lo marco el revisor, 2026-10-26)."""
    m = MODOS[modo]
    entra = float(suave(-0.05, 0.6, np.float32(td))) if td >= -0.05 else 0.0
    tapa = 1 - np.maximum(f.alfa, f.consola)
    sol = donde_el_sol(fondo)
    if m["haces"] and entra and sol is not None:
        # solo lo muy claro (el sol y su corona), tapado por el: asi salen rayos y no un velo parejo
        luz = suave(0.78, 0.98, fondo.mean(2)) * tapa
        O = screen(O, haces(luz, sol, 32)[..., None] * CALIDO * m["haces"] * 1.6 * (0.75 + 0.5 * pul) * entra)
    nivel = m["polvo"] * (0.3 + 0.7 * entra) * (0.8 + 0.4 * pul)
    if nivel > 0.02:
        capa = polvo(t, ps, False) * tapa + desenfoque(polvo(t, ps, True), 2.5)
        O = screen(O, capa[..., None] * CALIDO * nivel)
    hl = np.clip(O - 0.70, 0, 1)
    O = screen(O, (desenfoque(hl, 14) * 0.9 + desenfoque(hl, 45) * 0.7) * (0.20 + (0.15 + 0.2 * pul) * entra))
    if sol is not None or sol_en_cuadro:
        O = screen(O, destello(td, sol if sol is not None else f.luz, 16 * 60 / 122.5) * tapa[..., None])
    flash = 0.5 * np.exp(-td / 0.14) if td >= 0 else (0.18 if td > -1.5 / FPS else 0.0)
    return screen(O, BLANCO_CALIDO * flash)


def zoom(O: np.ndarray, s: float) -> np.ndarray:
    if s <= 1.0005:
        return O
    # con BORDER_REFLECT y cubica el borde salia con G y B en cero: una linea roja alrededor del cuadro
    m = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
    return cv2.warpAffine(O, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def texto(img: np.ndarray, tema: dict, tau: float) -> np.ndarray:
    """El nombre del tema, chico, arriba a la izquierda (abajo lo tapa el texto de Instagram)."""
    alfa = float(np.interp(tau, [0.4, 1.2, 6.3, 7.3], [0, 1, 1, 0]))
    if alfa <= 0:
        return img
    from PIL import Image, ImageDraw, ImageFont
    base = Image.fromarray(img).convert("RGBA")
    capa = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for txt, tam, y, op in ((tema["titulo"], 40, 232, 0.94), (tema["artista"], 28, 284, 0.80)):
        fuente = ImageFont.truetype(str(FUENTE), tam)
        d.text((66, y + 2), txt, font=fuente, fill=(0, 0, 0, int(110 * alfa)))
        d.text((64, y), txt, font=fuente, fill=(*CREMA, int(255 * op * alfa)))
    return np.array(Image.alpha_composite(base, capa).convert("RGB"))


# ---------------------------------------------------------------- el plan y un cuadro

@dataclass(frozen=True)
class Reel:
    plan: dict
    drop: float
    bombos: np.ndarray
    beat: float

    @property
    def inicio(self) -> float:
        return self.drop - self.plan["compases_antes"] * 4 * self.beat

    @property
    def duracion(self) -> float:
        return (self.plan["compases_antes"] + self.plan["compases_despues"]) * 4 * self.beat

    def plano(self, tau: float) -> dict:
        b = (self.inicio + tau - self.drop) / self.beat
        return next(p for p in self.plan["planos"] if p["desde"] <= b + 1e-6 < p["hasta"])


def cargar() -> Reel:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    beat = 60 / plan["tempo"]
    drop, bombos = golpes(RAIZ / plan["mezcla"], plan["drop_aprox"], beat, plan["compases_antes"] * 4,
                          plan["compases_despues"])
    return Reel(plan, drop, bombos, beat)


def preparar(r: Reel, tau: float) -> tuple[dict, Figura, np.ndarray]:
    """El plano que suena en `tau`, la figura del DJ en ese cuadro y el paisaje con el color de la marca."""
    p = r.plano(tau)
    toma = RAIZ / r.plan["toma"]
    en_plano = r.inicio + tau - (r.drop + p["desde"] * r.beat)
    s = p["toma"] + en_plano / p["lento"]
    x0 = centrar(toma, p["toma"], (p["hasta"] - p["desde"]) * r.beat / p["lento"])
    cada60 = 1 if p["lento"] == 2 else 2
    calentar = CALENTAR_S / p["lento"]
    cuadros = leer_toma(toma, s - calentar, calentar + 0.5 / 60, x0, cada60)
    k = min(len(cuadros) - 1, int(round(calentar * 60 / cada60)))
    cuadros = cuadros[:k + 1]
    phas, fgrs = matte_rvm(cuadros)
    pts, seg = poses(cuadros, 60 / cada60)[-1]
    fig = figura(cuadros[-1], phas[-1], fgrs[-1], pts, seg, borde_consola(cuadros), p.get("cierre", 4))
    pais = grado_marca(leer_paisaje(p["paisaje"], p["paisaje_desde"] + en_plano, 0.05, p["paisaje_x"],
                                    p.get("paisaje_y", 0.0), p.get("paisaje_alto", H))[0].astype(np.float32) / 65535)
    return p, fig, pais


def terminar(r: Reel, tau: float, p: dict, fig: Figura, pais: np.ndarray, ps: list[Particula]) -> np.ndarray:
    """La composicion, los efectos, el pulso y el texto de un cuadro."""
    t_mix = r.inicio + tau
    O, fondo = componer(fig, pais, p["modo"], {k: p[k] for k in ("dj", "opaco", "piel") if k in p})
    td = t_mix - r.drop
    pul = pulso(t_mix, r.bombos) if td >= 0 else 0.0
    O = efectos(O, fondo, fig, p["modo"], tau, td, pul, ps, p.get("sol_en_cuadro", False))
    O = zoom(np.clip(O, 0, 1), 1 + 0.014 * pul)
    img = (np.clip(O, 0, 1) * 255 + np.random.default_rng(int(tau * 1000)).uniform(-0.5, 0.5, O.shape)).clip(0, 255)
    return texto(img.astype(np.uint8), r.plan["tema"], tau)


def cuadro(r: Reel, tau: float, ps: list[Particula]) -> np.ndarray:
    p, fig, pais = preparar(r, tau)
    return terminar(r, tau, p, fig, pais, ps)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cuadros")
    c.add_argument("--t", type=float, nargs="+", required=True, help="segundos del Reel")
    c.add_argument("--salida", required=True)
    rd_ = sub.add_parser("render", help="el Reel entero (ver reel_render.py)")
    rd_.add_argument("--salida", default=None)
    rd_.add_argument("--planos", type=int, nargs="*", help="solo estos planos (las piezas); sin unir")
    a = ap.parse_args()
    if a.cmd == "render":
        import reel_render
        reel_render.main(a.salida, a.planos)
        return
    r = cargar()
    print(f"drop {r.drop:.3f} s ({int(r.drop // 60)}:{r.drop % 60:04.1f}), Reel {r.inicio:.3f} a "
          f"{r.inicio + r.duracion:.3f} ({r.duracion:.2f} s), drop en el {r.drop - r.inicio:.2f} del Reel", flush=True)
    if a.cmd == "cuadros":
        out = Path(a.salida)
        out.mkdir(parents=True, exist_ok=True)
        ps = particulas()
        for tau in a.t:
            img = cuadro(r, tau, ps)
            ruta = out / f"cuadro_{tau:05.2f}.png"
            cv2.imwrite(str(ruta), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print(f"  {tau:5.2f} s  {r.plano(tau)['modo']:8s} -> {ruta.name}", flush=True)


if __name__ == "__main__":
    main()
