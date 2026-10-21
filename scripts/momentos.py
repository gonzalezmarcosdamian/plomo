# -*- coding: utf-8 -*-
"""Los mejores momentos de una toma del DJ tocando: donde se mueve, levanta la cara o las manos.

POR QUE
-------
Para elegir tramos de sus tomas con criterio y no a ojo (el clip IMG_2209 del 2026-10-20: 6:40,
el primer 1:10 acomodandose sin musica). MediaPipe Pose lee 33 puntos del cuerpo por cuadro, y con
eso se mide, en cada segundo:

    movimiento    cuanto se mueven hombros, codos, munecas y cabeza (en anchos de hombro por seg)
    cara          la cara a la vista y la cabeza levantada, no mirando la consola
    manos         una muneca por encima de los hombros: el gesto grande
    musica        que suene algo: el audio por encima de -30 dBFS

y se puntua cada tramo de `--largo` segundos. El resultado queda en data/video/<nombre>_momentos.json
para el editor y para `reencuadre_vertical.py`.

USO
---
    python scripts/momentos.py grabaciones/video/IMG_2209.MOV [--largo 15] [--top 6]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import mediapipe as mp
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MODELO = RAIZ / "postproduction" / "modelos" / "pose_landmarker_full.task"
MUESTRAS_POR_S = 6
ANCHO = 640
NARIZ, OJO_I, OJO_D, HOMBRO_I, HOMBRO_D, CODO_I, CODO_D, MUNECA_I, MUNECA_D = 0, 2, 5, 11, 12, 13, 14, 15, 16
CUERPO = [NARIZ, HOMBRO_I, HOMBRO_D, CODO_I, CODO_D, MUNECA_I, MUNECA_D]
PESOS = {"movimiento": 0.45, "cara": 0.25, "manos": 0.30}


def poses(video: Path) -> tuple[np.ndarray, np.ndarray, float]:
    """Puntos (x, y, visibilidad) por muestra; NaN donde no hay persona."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout)
    alto = round(ANCHO * 9 / 16)
    lee = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={MUESTRAS_POR_S},scale={ANCHO}:{alto}",
                            "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    opciones = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODELO)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=1)
    puntos, tiempos = [], []
    with mp.tasks.vision.PoseLandmarker.create_from_options(opciones) as detector:
        k = 0
        while True:
            b = lee.stdout.read(ANCHO * alto * 3)
            if len(b) < ANCHO * alto * 3:
                break
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(b, np.uint8).reshape(alto, ANCHO, 3))
            t_ms = int(k * 1000 / MUESTRAS_POR_S)
            r = detector.detect_for_video(img, t_ms)
            if r.pose_landmarks:
                puntos.append([(p.x, p.y, p.visibility) for p in r.pose_landmarks[0]])
            else:
                puntos.append([(np.nan, np.nan, 0.0)] * 33)
            tiempos.append(t_ms / 1000)
            k += 1
    return np.array(puntos, np.float32), np.array(tiempos), dur


def nivel_audio(video: Path, dur: float) -> np.ndarray:
    """dBFS por segundo del audio estereo (el espacial de 4 canales del iPhone ffmpeg no lo lee)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:a:0", "-ac", "1", "-ar", "8000",
                        "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.float32)
    n = int(dur)
    return np.array([20 * np.log10(np.sqrt(np.mean(a[s * 8000:(s + 1) * 8000] ** 2)) + 1e-9) for s in range(n)])


def rasgos(p: np.ndarray, t: np.ndarray, dur: float, db: np.ndarray) -> dict[str, np.ndarray]:
    xy = p[:, :, :2]
    hombros = np.linalg.norm(xy[:, HOMBRO_I] - xy[:, HOMBRO_D], axis=1)
    escala = np.nanmedian(hombros)
    vel = np.linalg.norm(np.diff(xy[:, CUERPO], axis=0), axis=2).mean(1) * MUESTRAS_POR_S / escala
    vel = np.concatenate([[0], np.nan_to_num(vel)])
    medio_hombro_y = xy[:, [HOMBRO_I, HOMBRO_D], 1].mean(1)
    levanta = (medio_hombro_y - xy[:, NARIZ, 1]) / escala              # mas alto = cabeza mas arriba
    cara = np.clip((np.nan_to_num(levanta) - np.nanpercentile(levanta, 30)) / 0.25, 0, 1) * (p[:, NARIZ, 2] > 0.6)
    # una mano arriba cuenta si esta lejos de la cabeza: cerca es acomodarse la gorra o los
    # auriculares (en IMG_2209, el 1:20 y el 6:22 salian primeros por eso)
    lejos = [np.linalg.norm(xy[:, m] - xy[:, NARIZ], axis=1) / escala > 0.9 for m in (MUNECA_I, MUNECA_D)]
    arriba = [(medio_hombro_y - xy[:, m, 1]) / escala for m in (MUNECA_I, MUNECA_D)]
    manos = np.clip(np.nan_to_num(np.maximum(np.where(lejos[0], arriba[0], -1), np.where(lejos[1], arriba[1], -1)),
                                  nan=-1) / 0.3, 0, 1)
    cerca = [np.linalg.norm(xy[:, m] - xy[:, NARIZ], axis=1) / escala < 0.6 for m in (MUNECA_I, MUNECA_D)]
    acomoda = (cerca[0] | cerca[1]).astype(np.float32)
    # tocando: una mano abajo, a la altura de la consola (con los auriculares en la mano, al pecho, no)
    tocando = ((xy[:, MUNECA_I, 1] > medio_hombro_y + 1.0 * escala) |
               (xy[:, MUNECA_D, 1] > medio_hombro_y + 1.0 * escala)).astype(np.float32)
    n = int(dur)
    por_s = {}
    for nombre, serie in (("movimiento", vel), ("cara", cara), ("manos", manos), ("acomoda", acomoda),
                          ("tocando", tocando)):
        v = np.array([serie[(t >= s) & (t < s + 1)].mean() if np.any((t >= s) & (t < s + 1)) else 0 for s in range(n)])
        por_s[nombre] = v
    por_s["movimiento"] = np.clip(por_s["movimiento"] / max(np.percentile(por_s["movimiento"], 95), 1e-6), 0, 1)
    por_s["musica"] = (db[:n] > -30).astype(np.float32)
    por_s["en_cuadro"] = np.array([np.mean(~np.isnan(xy[(t >= s) & (t < s + 1), NARIZ, 0])) for s in range(n)])
    return por_s


def mejores(r: dict[str, np.ndarray], largo: int, top: int) -> list[dict]:
    puntos = ((sum(PESOS[k] * r[k] for k in PESOS) - 0.6 * r["acomoda"]) * (0.3 + 0.7 * r["tocando"])
              * r["musica"] * r["en_cuadro"])
    ventanas = [(float(puntos[s:s + largo].mean()), s) for s in range(0, len(puntos) - largo + 1)]
    elegidas: list[dict] = []
    for valor, s in sorted(ventanas, reverse=True):
        if all(abs(s - e["desde"]) >= largo for e in elegidas):
            tramo = {k: round(float(r[k][s:s + largo].mean()), 2) for k in PESOS}
            elegidas.append({"desde": s, "hasta": s + largo, "puntaje": round(valor, 3), **tramo})
        if len(elegidas) == top:
            break
    return elegidas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--largo", type=int, default=15)
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()
    video = RAIZ / a.video
    p, t, dur = poses(video)
    db = nivel_audio(video, dur)
    r = rasgos(p, t, dur, db)
    top = mejores(r, a.largo, a.top)
    salida = RAIZ / "data" / "video" / f"{video.stem}_momentos.json"
    # la pose por muestra queda para el reencuadre: el centro del cuerpo en x, suavizable
    with np.errstate(all="ignore"):
        centro = np.nanmean(p[:, CUERPO, 0], axis=1)
    salida.write_text(json.dumps({"video": a.video, "duracion_s": round(dur, 2), "muestras_por_s": MUESTRAS_POR_S,
                                  "mejores": top, "por_segundo": {k: [round(float(x), 3) for x in v] for k, v in r.items()},
                                  "centro_x": [None if np.isnan(c) else round(float(c), 4) for c in centro]},
                                 ensure_ascii=False), encoding="utf-8")
    print(f"{video.name}: {dur / 60:.1f} min, musica en {int(r['musica'].sum())} s")
    for e in top:
        print(f"  {e['desde'] // 60}:{e['desde'] % 60:02d}-{e['hasta'] // 60}:{e['hasta'] % 60:02d}  puntaje {e['puntaje']:.2f}  "
              f"(movimiento {e['movimiento']}, cara {e['cara']}, manos {e['manos']})")
    print("->", salida.relative_to(RAIZ))


if __name__ == "__main__":
    main()
