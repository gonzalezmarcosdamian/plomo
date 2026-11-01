"""Revisa clips de stock de Pixabay y marca lo sospechoso (BACKLOG 0.2).

POR QUE: elegir clips mirando cuadro por cuadro costaba ~380 mil tokens por
vuelta, y aun asi el editor se perdio la estela de avion de 116206. Este script
mira todo en CPU y deja una hoja con recortes SOLO de los cuadros marcados; el
agente mira esa hoja, no los clips.

Muestreo: 1 cuadro cada 2 s, achicado a 960 px de ancho (ffmpeg a pipe, CPU).

Chequeos (cada uno: marca, puntaje 0-1 y segundos donde marca):
  estelas    lineas rectas largas y finas en el tercio de arriba (Canny + Hough)
  sol        mancha mas brillante pegada a la linea del horizonte estimada
  hombre     bordes rectos largos y ~90 grados (marca de mas, a proposito)
  compresion bloques 8x8 (a 960 px: 8*960/ancho) en zonas lisas
  fase       letra estimada de la hora segun el cielo (ver fase_del_dia)
  largo      duracion, fps y si llega a 79 s tal cual o con RIFE x2 (40 s)

USO:
  python scripts/revisar_clips.py 116206 221999
  python scripts/revisar_clips.py --etapas data/video/session_05_candidatos.json
  python scripts/revisar_clips.py --etapas X.json --salida data/video/otra.json
  python scripts/revisar_clips.py --miniaturas     # despues: una hoja por etapa con todos los clips

Salida: data/video/session_05_revision.json y una hoja por etapa en
postproduction/stock/revision/hoja_etapa_<n>.jpg (max 1600 px de ancho).
"""
import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
REVISION = RAIZ / "postproduction" / "stock" / "revision"
SALIDA_DEF = RAIZ / "data" / "video" / "session_05_revision.json"

ANCHO = 960
PASO_S = 2.0
PLANO_S = 79.0
RIFE_S = 40.0
RECORTE = 400
HOJA_ANCHO = 1600

# --- umbrales (todos sobre el cuadro de 960 px de ancho) ---
ESTELA_LARGO = 0.12        # segmento >= 12% del ancho (960 px -> 115 px)
ESTELA_ZONA = 0.45         # se analiza el 45% de arriba (y las rectas deben estar en el tercio)
ESTELA_BAJO = 0.74         # = tercio / 0.45: el segmento queda sobre el primer tercio
ESTELA_MAX_SEGS = 1        # mas de una recta por cuadro = cielo texturado (con 5 marcaba casi todo)
ESTELA_CRESTA = 5.0        # DoG: cuanto mas clara que su entorno es la cresta (con 3, ruido de nubes)
ESTELA_CONTRASTE_MAX = 30.0  # mas que eso es un palo/rama oscura, no una estela
ESTELA_CONSIST = 0.85      # fraccion del largo con el mismo signo de contraste
ESTELA_DESB = 8.0          # diferencia max de brillo entre los dos lados
ESTELA_LISO = 14.0         # desvio tipico max del fondo alrededor (cielo liso)
# Una estela sigue ahi cuadro tras cuadro; el ruido de nubes salta. Medido el 2026-11-01 sobre 8 clips:
# 116206 (la estela real) marca 16 de 28 cuadros y los otros 7, de 1 a 9 de ~30. Ajustado sobre esos
# mismos clips: puede estar sobreajustado.
ESTELA_FRACCION = 0.4      # fraccion de cuadros marcados para marcar el clip
ESTELA_DUDA = 0.25         # desde aca va a la hoja como "estela?" para que la mire el editor (119784: 0.36)
RECORTES_POR_MOTIVO = 2    # por clip, para que la hoja no se llene de un solo clip
# Sin calibrar contra etiquetas reales: se informan, pero no deciden si el clip esta limpio.
SIN_CALIBRAR = ("sol", "hombre")
SOL_BRILLO = 235
SOL_DIST_HORIZ = 0.06      # fraccion del alto
HOMBRE_LARGO = 0.28
HOMBRE_MIN_RECTAS = 3
COMPRESION_EXCESO = 0.4    # y la grilla tiene que sobrar al menos 0.4 niveles de gris
COMPRESION_RATIO = 1.35    # gradiente en la grilla / fuera de la grilla


# ------------------------------------------------------------------ puras

def _planas(lineas):
    """HoughLinesP devuelve Nx1x4 (cv2 4) o Nx4 (cv2 5)."""
    return np.asarray(lineas).reshape(-1, 4)


def rectas_distintas(segs):
    """Cuenta rectas distintas: fragmentos de la misma recta (angulo a menos de 6
    grados y distancia al origen a menos de 12 px) cuentan una vez.

    Antes eran cubos fijos de 6 grados y 12 px: una sola estela de 3 px de ancho
    caia en 4 cubos vecinos y contaba como 4 rectas."""
    rectas = []
    for s in segs:
        a = angulo(s)
        t = math.radians(a)
        d = -s[0] * math.sin(t) + s[1] * math.cos(t)
        if not any(abs(a - a0) < 6 and abs(d - d0) < 12 for a0, d0 in rectas):
            rectas.append((a, d))
    return len(rectas)


def segmentos_largos(lineas, ancho, frac):
    """Filtra segmentos (x1,y1,x2,y2) de longitud >= frac*ancho."""
    out = []
    for x1, y1, x2, y2 in lineas:
        if math.hypot(x2 - x1, y2 - y1) >= frac * ancho:
            out.append((int(x1), int(y1), int(x2), int(y2)))
    return out


def angulo(seg):
    x1, y1, x2, y2 = seg
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0


def hay_angulo_recto(segs, tol=8.0):
    """True si hay dos segmentos a ~90 grados entre si."""
    angs = [angulo(s) for s in segs]
    for i in range(len(angs)):
        for j in range(i + 1, len(angs)):
            d = abs(angs[i] - angs[j])
            if abs(d - 90.0) <= tol:
                return True
    return False


def _banda_fina(gris, seg):
    """Perfil de la linea contra el fondo a ambos lados.

    Devuelve (contraste, consistencia, std_fondo, desbalance):
    contraste = brillo del centro menos el de los lados (mediana, con signo);
    consistencia = fraccion de puntos de la linea con el mismo signo que la
    mediana y |dif| >= 1.5 (una estela real es constante en todo su largo);
    std_fondo = desvio de los lados; desbalance = diferencia entre lado y lado.
    """
    x1, y1, x2, y2 = (float(v) for v in seg)
    n = max(int(math.hypot(x2 - x1, y2 - y1) / 3), 2)
    xs = np.linspace(x1, x2, n)
    ys = np.linspace(y1, y2, n)
    norm = math.hypot(x2 - x1, y2 - y1) or 1.0
    nx, ny = -(y2 - y1) / norm, (x2 - x1) / norm
    h, w = gris.shape

    def banda(offs):
        filas = []
        for off in offs:
            px = np.clip((xs + nx * off).round().astype(int), 0, w - 1)
            py = np.clip((ys + ny * off).round().astype(int), 0, h - 1)
            filas.append(gris[py, px].astype(np.float32))
        return np.mean(filas, axis=0)

    c = banda((-1, 0, 1))
    a = banda((-9, -8, -7))
    b = banda((7, 8, 9))
    dif = c - (a + b) / 2
    med = float(np.median(dif))
    signo = 1.0 if med >= 0 else -1.0
    consist = float(np.mean((dif * signo) >= 1.5))
    lados = np.concatenate([a, b])
    return med, consist, float(lados.std()), abs(float(np.median(a) - np.median(b)))


def limpiar_cielo(gris):
    """Quita lo oscuro y fino (pastos, ramas, cables) del tercio de arriba.

    Black-hat con kernel 13 marca las lineas oscuras finas; se rellenan con
    inpaint. Lo que queda son nubes, estelas y arboles grandes. Sin esto el
    pasto de 116206 tapa la estela con cientos de falsas rectas.
    """
    h = gris.shape[0]
    tercio = gris[: int(h * ESTELA_ZONA)]
    bh = cv2.morphologyEx(tercio, cv2.MORPH_BLACKHAT,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    oscuro = cv2.dilate((bh > 10).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
    return cv2.inpaint(tercio, oscuro, 4, cv2.INPAINT_TELEA)


def detectar_estelas(gris):
    """Estelas: rectas largas y finas CLARAS sobre el cielo, tercio de arriba.

    Cresta clara fina = DoG(1, 5) > ESTELA_CRESTA sobre el cielo limpio, y
    Hough probabilistica. Devuelve (puntaje 0-1, segmentos).
    """
    h, w = gris.shape
    limpio = limpiar_cielo(gris).astype(np.float32)
    cresta = cv2.GaussianBlur(limpio, (0, 0), 1.0) - cv2.GaussianBlur(limpio, (0, 0), 5)
    binaria = (cresta > ESTELA_CRESTA).astype(np.uint8) * 255
    lineas = cv2.HoughLinesP(binaria, 1, np.pi / 180, threshold=50,
                             minLineLength=int(ESTELA_LARGO * w), maxLineGap=6)
    if lineas is None:
        return 0.0, []
    tope = h * ESTELA_ZONA * ESTELA_BAJO
    segs = [s for s in segmentos_largos(_planas(lineas), w, ESTELA_LARGO)
            if max(s[1], s[3]) < tope]
    if not segs or rectas_distintas(segs) > ESTELA_MAX_SEGS:  # muchas rectas = textura de nubes, no una estela
        return 0.0, []
    largo = max(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segs) / w
    return min(largo / 0.3, 1.0), segs


def estimar_horizonte(gris):
    """Fila del horizonte: mayor salto vertical del perfil de brillo por fila."""
    h = gris.shape[0]
    perfil = cv2.GaussianBlur(gris, (0, 0), 3).mean(axis=1)
    d = np.abs(np.diff(perfil))
    d = np.convolve(d, np.ones(9) / 9, mode="same")
    lo, hi = int(h * 0.25), int(h * 0.90)
    return lo + int(np.argmax(d[lo:hi]))


def detectar_sol(gris):
    """Sol tocando el horizonte. Devuelve (puntaje, (x, y) o None)."""
    h, w = gris.shape
    suave = cv2.GaussianBlur(gris, (0, 0), 4)
    _, vmax, _, pos = cv2.minMaxLoc(suave)
    if vmax < SOL_BRILLO:
        return 0.0, None
    horiz = estimar_horizonte(gris)
    dist = abs(pos[1] - horiz) / h
    if dist > SOL_DIST_HORIZ:
        return 0.0, None
    return float(1.0 - dist / SOL_DIST_HORIZ), (pos[0], pos[1])


def detectar_hombre(gris):
    """Rectas largas y ~90 grados. Devuelve (puntaje, segmentos)."""
    h, w = gris.shape
    bordes = cv2.Canny(cv2.GaussianBlur(gris, (0, 0), 1.0), 40, 110)
    lineas = cv2.HoughLinesP(bordes, 1, np.pi / 180, threshold=int(0.10 * w),
                             minLineLength=int(HOMBRE_LARGO * w), maxLineGap=6)
    if lineas is None:
        return 0.0, []
    segs = segmentos_largos(_planas(lineas), w, HOMBRE_LARGO)
    if len(segs) < HOMBRE_MIN_RECTAS and not hay_angulo_recto(segs):
        return 0.0, []
    puntaje = min(len(segs) / 8.0, 1.0)
    if hay_angulo_recto(segs):
        puntaje = max(puntaje, 0.7)
    return puntaje, segs


def blockiness(gris, bloque):
    """Razon de gradiente horizontal en la grilla del bloque vs fuera, en zonas lisas."""
    if bloque < 4:  # a 4K el bloque queda en 2 px a 960 px de ancho: no se mide
        return 1.0
    g = gris.astype(np.float32)
    dx = np.abs(np.diff(g, axis=1))
    lisa = cv2.blur(np.abs(cv2.Laplacian(gris, cv2.CV_32F)), (9, 9))[:, :-1] < 2.0
    cols = np.arange(dx.shape[1])
    en_grilla = (cols % bloque) == (bloque - 1)
    a = dx[:, en_grilla][lisa[:, en_grilla]]
    b = dx[:, ~en_grilla][lisa[:, ~en_grilla]]
    if a.size < 500 or b.size < 500:
        return 1.0
    if a.mean() - b.mean() < COMPRESION_EXCESO:
        return 1.0
    return float((a.mean() + 1e-3) / (b.mean() + 1e-3))


def fase_del_dia(luma, calidez, rosa):
    """Letra estimada de la fase del dia segun el cielo (grosera).

    luma: brillo medio 0-255 del cielo; calidez: R-B medio; rosa: R-G medio
    con B>G (magenta/arrebol). Umbrales:
      G noche      luma < 45
      F hora azul  luma < 100 y calidez <= 12
      E arrebol    luma < 150 y rosa > 12
      D puesta     luma < 150 y calidez > 12
      C naranja    luma < 200 y calidez > 35
      B dorada     calidez > 12
      A tarde alta resto (cielo claro y neutro/azul)
    """
    if luma < 45:
        return "G"
    if luma < 100 and calidez <= 12:
        return "F"
    if luma < 150 and rosa > 12:
        return "E"
    if luma < 150 and calidez > 12:
        return "D"
    if luma < 200 and calidez > 35:
        return "C"
    if calidez > 12:
        return "B"
    return "A"


def evaluar_largo(duracion, fps):
    """Si el clip llega a 79 s tal cual, con RIFE x2 (40 s) o es corto."""
    if duracion >= PLANO_S:
        alcance = "tal_cual"
    elif duracion >= RIFE_S:
        alcance = "rife_x2"
    else:
        alcance = "corto"
    return {"duracion_s": round(duracion, 1), "fps": round(fps, 2), "alcance": alcance}


def extraer_ids(datos):
    """Ids por etapa de session_05_candidatos.json: candidatos y, si hay, nuevos."""
    out = []
    for e in datos.get("etapas", []):
        ids = [c["id"] for c in e.get("candidatos", [])]
        ids += [c["id"] for c in e.get("nuevos", []) or []]
        vistos = []
        for i in ids:
            if i not in vistos:
                vistos.append(i)
        out.append((e.get("n"), vistos))
    return out


# -------------------------------------------------------------------- E/S

def metadatos(ruta):
    cap = cv2.VideoCapture(str(ruta))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return (n / fps if fps else 0.0), fps, w, h


def leer_cuadros(ruta, w, h):
    """Un cuadro cada 2 s a 960 px de ancho (ffmpeg a pipe, CPU). Lista de BGR."""
    alto = int(round(h * ANCHO / w / 2) * 2)
    cmd = ["ffmpeg", "-v", "error", "-threads", "2", "-i", str(ruta),
           "-vf", f"fps=1/{PASO_S},scale={ANCHO}:{alto}:flags=area",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    crudo = subprocess.run(cmd, capture_output=True, check=True).stdout
    tam = ANCHO * alto * 3
    return [np.frombuffer(crudo[i:i + tam], np.uint8).reshape(alto, ANCHO, 3)
            for i in range(0, len(crudo) - tam + 1, tam)]


def recorte(cuadro, centro):
    h, w = cuadro.shape[:2]
    cx, cy = centro
    x0 = int(np.clip(cx - RECORTE // 2, 0, max(w - RECORTE, 0)))
    y0 = int(np.clip(cy - RECORTE // 2, 0, max(h - RECORTE, 0)))
    return cuadro[y0:y0 + RECORTE, x0:x0 + RECORTE].copy()


def analizar_clip(id_, ruta):
    """Analiza un clip. Devuelve (registro, lista de (segundo, motivo, recorte))."""
    dur, fps, w, h = metadatos(ruta)
    cuadros = leer_cuadros(ruta, w, h)
    res = {"estelas": [], "sol": [], "hombre": [], "compresion": []}
    punt = {k: 0.0 for k in res}
    recortes, fases = [], []
    bloque = 8 * ANCHO / w
    bloque = int(round(bloque)) if abs(bloque - round(bloque)) < 0.05 else 0
    for k, cu in enumerate(cuadros):
        t = k * PASO_S
        gris = cv2.cvtColor(cu, cv2.COLOR_BGR2GRAY)
        p, segs = detectar_estelas(gris)
        if segs:
            res["estelas"].append(t)
            punt["estelas"] = max(punt["estelas"], p)
            s = max(segs, key=lambda q: math.hypot(q[2] - q[0], q[3] - q[1]))
            recortes.append((t, "estela", recorte(cu, ((s[0] + s[2]) // 2, (s[1] + s[3]) // 2))))
        p, pos = detectar_sol(gris)
        if pos:
            res["sol"].append(t)
            punt["sol"] = max(punt["sol"], p)
            recortes.append((t, "sol", recorte(cu, pos)))
        p, segs = detectar_hombre(gris)
        if segs:
            res["hombre"].append(t)
            punt["hombre"] = max(punt["hombre"], p)
            if len(res["hombre"]) <= 2:
                s = segs[0]
                recortes.append((t, "hombre", recorte(cu, ((s[0] + s[2]) // 2, (s[1] + s[3]) // 2))))
        r = blockiness(gris, bloque)
        if r >= COMPRESION_RATIO:
            res["compresion"].append(t)
            punt["compresion"] = max(punt["compresion"], min((r - 1) / 1.0, 1.0))
            if len(res["compresion"]) <= 1:
                recortes.append((t, "compresion", recorte(cu, (ANCHO // 2, cu.shape[0] // 2))))
        cielo = cu[: max(cu.shape[0] // 4, 1)].reshape(-1, 3).astype(np.float32)
        b, g, rr = cielo.mean(axis=0)
        luma = 0.114 * b + 0.587 * g + 0.299 * rr
        rosa = (rr - g) if b > g else 0.0
        fases.append(fase_del_dia(luma, rr - b, rosa))
    marcas = {}
    for k, v in res.items():
        marca = len(v) >= max(1, ESTELA_FRACCION * len(cuadros)) if k == "estelas" else len(v) >= 1
        marcas[k] = {"marca": marca, "puntaje": round(punt[k], 2),
                     "segundos": [round(x, 1) for x in v]}
        if k == "estelas":
            marcas[k]["duda"] = not marca and len(v) >= max(1, ESTELA_DUDA * len(cuadros))
    fase = max(set(fases), key=fases.count) if fases else "?"
    reg = {"id": id_, "cuadros": len(cuadros), "ancho_origen": w, "alto_origen": h,
           "marcas": marcas, "fase": {"letra": fase, "por_cuadro": "".join(fases)},
           "largo": evaluar_largo(dur, fps), "sin_calibrar": list(SIN_CALIBRAR) + ["fase"]}
    reg["limpio"] = not any(m["marca"] for k, m in marcas.items() if k not in SIN_CALIBRAR)
    return reg, recortes_marcados(recortes, marcas)


def recortes_marcados(recortes: list, marcas: dict) -> list:
    """Solo los recortes de lo que marco el clip entero, y pocos por motivo."""
    clave = {"estela": "estelas", "sol": "sol", "hombre": "hombre", "compresion": "compresion"}
    cuenta, salida = {}, []
    for t, motivo, img in recortes:
        m = marcas[clave[motivo]]
        if not (m["marca"] or m.get("duda")) or cuenta.get(motivo, 0) >= RECORTES_POR_MOTIVO:
            continue
        cuenta[motivo] = cuenta.get(motivo, 0) + 1
        salida.append((t, motivo if m["marca"] else motivo + "?", img))
    return salida


def hacer_hoja(n, items):
    """items: lista de (id, segundo, motivo, recorte). Hoja JPG <= 1600 px."""
    if not items:
        return None
    cols = HOJA_ANCHO // RECORTE
    filas = math.ceil(len(items) / cols)
    hoja = np.zeros((filas * RECORTE, cols * RECORTE, 3), np.uint8)
    for k, (id_, t, motivo, rec) in enumerate(items):
        y, x = (k // cols) * RECORTE, (k % cols) * RECORTE
        hoja[y:y + rec.shape[0], x:x + rec.shape[1]] = rec
        txt = f"{id_} {t:.0f}s {motivo}"
        cv2.rectangle(hoja, (x, y), (x + 8 * len(txt) + 120, y + 22), (0, 0, 0), -1)
        cv2.putText(hoja, txt, (x + 4, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    REVISION.mkdir(parents=True, exist_ok=True)
    destino = REVISION / f"hoja_etapa_{n}.jpg"
    cv2.imwrite(str(destino), hoja, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return destino


MINI_W, MINI_H = 196, 110   # dos cuadros por clip, cuatro clips por fila: 1600 px de ancho
MINI_CELDA = 2 * MINI_W + 8


def rotulo(reg: dict) -> str:
    """'119784 77s B E?': id, largo, fase y las marcas (E estela, S sol, H hombre, C compresion)."""
    if "error" in reg:
        return f"{reg['id']} {reg['error'][:20]}"
    m = reg["marcas"]
    letras = "".join(c for c, k in (("E", "estelas"), ("S", "sol"), ("H", "hombre"), ("C", "compresion"))
                     if m[k]["marca"])
    if m["estelas"].get("duda"):
        letras += "E?"
    corto = " corto" if reg["largo"]["alcance"] == "corto" else ""
    return f"{reg['id']} {reg['largo']['duracion_s']:.0f}s {reg['fase']['letra']} {letras}{corto}".strip()


def cuadro_chico(ruta: Path, seg: float) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{seg:.2f}", "-i", str(ruta), "-frames:v", "1",
                        "-vf", f"scale={MINI_W}:{MINI_H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True)
    if len(r.stdout) != MINI_W * MINI_H * 3:
        return np.zeros((MINI_H, MINI_W, 3), np.uint8)
    return np.frombuffer(r.stdout, np.uint8).reshape(MINI_H, MINI_W, 3)


def hoja_miniaturas(n: int, registros: list[dict]) -> Path | None:
    """Todos los clips de la etapa, dos cuadros cada uno (al 25% y al 75%), con su rotulo.

    Lo que el script no sabe medir todavia (la luz, el sol, lo hecho por el hombre) lo
    mira el editor aca, de una sola lectura por etapa, sin abrir los clips."""
    regs = [r for r in registros if r.get("etapa") == n]
    if not regs:
        return None
    cols = HOJA_ANCHO // MINI_CELDA
    alto = MINI_H + 22
    hoja = np.zeros((math.ceil(len(regs) / cols) * alto, HOJA_ANCHO, 3), np.uint8)
    for k, reg in enumerate(regs):
        y, x = (k // cols) * alto, (k % cols) * MINI_CELDA
        dur = reg.get("largo", {}).get("duracion_s", 0)
        for j, frac in enumerate((0.25, 0.75)):
            if dur:
                hoja[y + 22:y + alto, x + j * MINI_W:x + (j + 1) * MINI_W] = cuadro_chico(
                    STOCK / f"{reg['id']}.mp4", dur * frac)
        cv2.putText(hoja, rotulo(reg), (x + 4, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    REVISION.mkdir(parents=True, exist_ok=True)
    destino = REVISION / f"miniaturas_etapa_{n}.jpg"
    cv2.imwrite(str(destino), hoja, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ids", nargs="*", help="ids de Pixabay")
    ap.add_argument("--etapas", help="JSON de candidatos por etapa")
    ap.add_argument("--salida", default=str(SALIDA_DEF))
    ap.add_argument("--miniaturas", action="store_true",
                    help="solo arma las hojas de miniaturas por etapa desde el JSON de --salida, sin analizar")
    args = ap.parse_args()

    if args.miniaturas:
        registros = json.loads(Path(args.salida).read_text(encoding="utf-8"))
        for n in sorted({r.get("etapa") for r in registros if r.get("etapa") is not None}):
            print(f"  miniaturas: {hoja_miniaturas(n, registros)}")
        return

    if args.etapas:
        etapas = extraer_ids(json.loads(Path(args.etapas).read_text(encoding="utf-8")))
    else:
        etapas = [(0, [int(i) for i in args.ids])]
    if not any(ids for _, ids in etapas):
        ap.error("pasa ids o --etapas")

    registros = []
    for n, ids in etapas:
        items = []
        for id_ in ids:
            ruta = STOCK / f"{id_}.mp4"
            if not ruta.exists():
                registros.append({"id": id_, "etapa": n, "error": "no esta bajado"})
                print(f"[{n}] {id_}: no esta bajado")
                continue
            t0 = time.time()
            try:
                reg, recs = analizar_clip(id_, ruta)
            except Exception as e:  # un clip roto no frena al resto
                registros.append({"id": id_, "etapa": n, "error": str(e)[:200]})
                print(f"[{n}] {id_}: error {e}")
                continue
            reg["etapa"] = n
            reg["segundos_de_analisis"] = round(time.time() - t0, 1)
            registros.append(reg)
            items += [(id_, t, m, r) for t, m, r in recs]
            m = reg["marcas"]
            print(f"[{n}] {id_}: " + " ".join(f"{k}={len(v['segundos'])}" for k, v in m.items())
                  + f" fase={reg['fase']['letra']} largo={reg['largo']['alcance']} ({reg['segundos_de_analisis']}s)")
        hoja = hacer_hoja(n, items)
        if hoja:
            print(f"  hoja: {hoja}")
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(registros, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {salida}")


if __name__ == "__main__":
    main()
