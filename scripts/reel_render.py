# -*- coding: utf-8 -*-
"""El render entero del Reel en doble exposicion (lo llama `reel_doble.py render`).

POR QUE
-------
El DJ dijo "ok" a la hoja de recorrido (2026-10-26). Los cuadros de la hoja se hacian de a uno, con
un calentamiento de RVM por cuadro; el video entero lee cada plano de corrido: RVM y la pose van en
secuencia, que es como se los entreno, y el borde no tiembla de un cuadro al siguiente.

COMO
----
- Un plano es una pieza sin perdida (FFV1, RGB) en postproduction/video/reel_session04_piezas. Una pieza
  terminada con sus cuadros justos no se rehace: si el render se corta, se retoma.
- La union pasa a H.264 high 4:2:0 BT.709 a 14 Mbps (Instagram recomprime bien entre 12 y 16) y pone la
  mezcla tal cual: el tramo exacto en muestras, a 48 kHz, AAC 320k, con un fundido de un beat al
  entrar y otro al salir, sin tocar el nivel.
- `verificar` compara el audio del Reel contra el mismo tramo recortado con ffmpeg (desfase en muestras,
  ganancia y diferencia) y cuenta cuadros, tamano, fps, perfil y bitrate.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Iterator

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel_doble as rd  # noqa: E402

PIEZAS = rd.RAIZ / "postproduction" / "video" / "reel_session04_piezas"
SALIDA = Path(r"C:\Users\gonza\Videos\plomo_reel_session04.mp4")
VERSION = 3            # subirla cuando cambie la composicion: las piezas de antes no se reusan
SR_SALIDA = 48000
COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]


def rango(r: rd.Reel, i: int) -> tuple[int, int]:
    """Los cuadros [k0, k1) del plano i en la grilla del Reel; el corte cae en el cuadro mas cercano al golpe."""
    planos = r.plan["planos"]
    total = round(r.duracion * rd.FPS)
    k = lambda b: round((r.drop + b * r.beat - r.inicio) * rd.FPS)
    return (0 if i == 0 else k(planos[i]["desde"])), (total if i == len(planos) - 1 else k(planos[i]["hasta"]))


def cuadros_de_toma(toma: Path, indices: list[int], x0: int) -> Iterator[np.ndarray]:
    """Los cuadros pedidos (indices a 60 por segundo, crecientes), del recorte 9:16, de corrido."""
    i0, i1 = indices[0], indices[-1]
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{i0 / 60 - 0.004:.4f}", "-i", str(toma),
           "-frames:v", str(i1 - i0 + 1), "-map", "0:v:0", "-vf", f"crop={rd.CW}:{rd.CH}:{x0}:0", "-vsync", "0",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    pedidos = Counter(indices)
    tam = rd.CW * rd.CH * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    try:
        for idx in range(i0, i1 + 1):
            buf = proc.stdout.read(tam)
            if len(buf) < tam:
                raise RuntimeError(f"la toma se corto en el cuadro {idx} (pedidos hasta {i1})")
            f = np.frombuffer(buf, np.uint8).reshape(rd.CH, rd.CW, 3)
            for _ in range(pedidos[idx]):
                yield f
    finally:
        proc.stdout.close()
        proc.wait()


def cuadros_de_paisaje(p: dict, desde: float, n: int) -> Iterator[np.ndarray]:
    """n cuadros del paisaje del plano, con su grado de la Session y el color de la marca."""
    sel = rd.elegidos()[p["paisaje"]]
    ruta = rd.RAIZ / sel["archivo"] if "archivo" in sel else rd.STOCK / f"{sel['id']}.mp4"
    alto = p.get("paisaje_alto", rd.H)
    ancho = round(alto * 16 / 9 / 2) * 2
    x, y = int(round((ancho - rd.W) * p["paisaje_x"])), int(round((alto - rd.H) * p.get("paisaje_y", 0.0)))
    vf = (f"fps={rd.FPS},{sel['encuadre']},setsar=1,format=gbrp16le,{sel['grado']},"
          f"scale={ancho}:{alto}:flags=lanczos,crop={rd.W}:{rd.H}:{x}:{y},format=rgb48le")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{sel['desde'] + desde:.3f}", "-i", str(ruta),
           "-frames:v", str(n), "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"]
    tam = rd.W * rd.H * 3 * 2
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    ultimo = None
    try:
        for _ in range(n):
            buf = proc.stdout.read(tam)
            if len(buf) == tam:
                ultimo = rd.grado_marca(np.frombuffer(buf, np.uint16).reshape(rd.H, rd.W, 3).astype(np.float32) / 65535)
            elif ultimo is None:
                raise RuntimeError(f"el paisaje {p['paisaje']} no dio cuadros desde {desde:.2f} s")
            yield ultimo
    finally:
        proc.stdout.close()
        proc.wait()


def huella(r: rd.Reel, i: int) -> str:
    # solo el modo del plano: un cambio en otro modo no tiene por que rehacer este plano
    p = r.plan["planos"][i]
    claves = [VERSION, p, rango(r, i), rd.MODOS[p["modo"]], round(r.drop, 4), r.plan["tema"]]
    return hashlib.sha1(json.dumps(claves, sort_keys=True, default=str).encode()).hexdigest()[:10]


def contar(ruta: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_frames", "-of", "csv=p=0", str(ruta)], capture_output=True, text=True)
    return int(out.stdout.strip() or 0)


def render_plano(r: rd.Reel, i: int, ps: list[rd.Particula], salida: Path) -> None:
    p = r.plan["planos"][i]
    k0, k1 = rango(r, i)
    toma = rd.RAIZ / r.plan["toma"]
    t_p0 = r.drop + p["desde"] * r.beat - r.inicio            # segundo del Reel donde arranca el plano
    paso = 2 // p["lento"]                                       # cuadros de 60 por cuadro de salida
    salen = [round((p["toma"] + (k / rd.FPS - t_p0) / p["lento"]) * 60) for k in range(k0, k1)]
    calentar = [salen[0] - paso * j for j in range(int(rd.CALENTAR_S * rd.FPS), 0, -1)]
    x0 = rd.centrar(toma, p["toma"], (p["hasta"] - p["desde"]) * r.beat / p["lento"])
    borde = rd.borde_consola(np.stack([rd.leer_toma(toma, s / 60, 0.02, x0, 1)[0]
                                       for s in np.linspace(calentar[0], salen[-1], 7).astype(int)]))
    matte, pose = rd.Matte(), rd.Pose(60 / paso)
    pais = cuadros_de_paisaje(p, p["paisaje_desde"] + (k0 / rd.FPS - t_p0), k1 - k0)
    tmp = salida.with_suffix(".tmp.mkv")
    enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{rd.W}x{rd.H}", "-r", str(rd.FPS), "-i", "-", "-c:v", "ffv1", "-level", "3",
                            "-pix_fmt", "gbrp", str(tmp)], stdin=subprocess.PIPE)
    try:
        for n, f in enumerate(cuadros_de_toma(toma, calentar + salen, x0)):
            pha, fgr = matte(f)
            pts, seg = pose(f)
            if n < len(calentar):
                continue
            k = k0 + n - len(calentar)
            fig = rd.figura(f, pha, fgr, pts, seg, borde, p.get("cierre", 4))
            img = rd.terminar(r, k / rd.FPS, p, fig, next(pais), ps)
            enc.stdin.write(np.ascontiguousarray(img).tobytes())
    finally:
        pose.close()
        enc.stdin.close()
        enc.wait()
    if contar(tmp) != k1 - k0:
        raise RuntimeError(f"plano {i}: {contar(tmp)} cuadros, se esperaban {k1 - k0}")
    tmp.replace(salida)


def piezas(r: rd.Reel, solo: list[int] | None) -> list[Path]:
    PIEZAS.mkdir(parents=True, exist_ok=True)
    ps = rd.particulas()
    rutas = []
    for i in range(len(r.plan["planos"])):
        ruta = PIEZAS / f"plano_{i:02d}_{huella(r, i)}.mkv"
        rutas.append(ruta)
        k0, k1 = rango(r, i)
        if (solo is not None and i not in solo) or (ruta.exists() and contar(ruta) == k1 - k0):
            continue
        t = time.time()
        render_plano(r, i, ps, ruta)
        print(f"  plano {i:2d} ({r.plan['planos'][i]['modo']}): {k1 - k0} cuadros en {time.time() - t:.0f} s",
              flush=True)
    return rutas


def unir(r: rd.Reel, rutas: list[Path], salida: Path) -> None:
    lista = PIEZAS / "lista.txt"
    lista.write_text("".join(f"file '{x.as_posix()}'\n" for x in rutas), encoding="utf-8")
    sr = rd.sf.info(str(rd.RAIZ / r.plan["mezcla"])).samplerate
    total = round(r.duracion * rd.FPS)
    s0 = round(r.inicio * sr)
    s1 = s0 + round(total / rd.FPS * sr)
    dur = total / rd.FPS
    audio = (f"[1:a]atrim=start_sample={s0}:end_sample={s1},asetpts=N/SR/TB,"
             f"aresample={SR_SALIDA}:resampler=soxr:precision=28,"
             f"afade=t=in:st=0:d={r.beat:.4f},afade=t=out:st={dur - r.beat:.4f}:d={r.beat:.4f}[a]")
    # setparams: sin el, -color_primaries y -color_trc no llegaban al archivo (quedaban "unknown")
    video = ("[0:v]scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p,"
             "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[v]")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
           "-i", str(rd.RAIZ / r.plan["mezcla"]), "-filter_complex", f"{video};{audio}", "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-b:v", "14M", "-maxrate", "16M",
           "-bufsize", "28M", "-g", "30", "-r", str(rd.FPS), *COLOR,
           "-c:a", "aac", "-b:a", "320k", "-ar", str(SR_SALIDA), "-movflags", "+faststart", str(salida)]
    rr = subprocess.run(cmd, capture_output=True, text=True)
    if rr.returncode:
        raise RuntimeError(rr.stderr[-2000:])
    print(f"-> {salida} ({salida.stat().st_size / 1e6:.1f} MB)", flush=True)


def referencia(r: rd.Reel) -> np.ndarray:
    """El mismo tramo de la mezcla recortado por ffmpeg con la misma cadena, en PCM (sin AAC)."""
    sr = rd.sf.info(str(rd.RAIZ / r.plan["mezcla"])).samplerate
    total = round(r.duracion * rd.FPS)
    s0 = round(r.inicio * sr)
    s1 = s0 + round(total / rd.FPS * sr)
    dur = total / rd.FPS
    af = (f"atrim=start_sample={s0}:end_sample={s1},asetpts=N/SR/TB,aresample={SR_SALIDA}:resampler=soxr:precision=28,"
          f"afade=t=in:st=0:d={r.beat:.4f},afade=t=out:st={dur - r.beat:.4f}:d={r.beat:.4f}")
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(rd.RAIZ / r.plan["mezcla"]),
                          "-af", af, "-f", "f32le", "-ac", "2", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def verificar(r: rd.Reel, salida: Path) -> dict:
    prob = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                                      str(salida)], capture_output=True, text=True).stdout)
    v = next(s for s in prob["streams"] if s["codec_type"] == "video")
    a = next(s for s in prob["streams"] if s["codec_type"] == "audio")
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(salida), "-map", "0:a",
                          "-f", "f32le", "-ac", "2", "-"], capture_output=True, check=True).stdout
    dec = np.frombuffer(raw, np.float32).reshape(-1, 2)
    ref = referencia(r)
    n = min(len(dec), len(ref))
    m_ref, m_dec = ref[:n].mean(1), dec[:n].mean(1)
    # desfase: correlacion en una ventana de 4 s alrededor del drop, +-50 ms
    c = int((r.drop - r.inicio) * SR_SALIDA)
    w = m_ref[c - 2 * SR_SALIDA:c + 2 * SR_SALIDA]
    lags = range(-2400, 2401)
    corr = [float(np.dot(w, m_dec[c - 2 * SR_SALIDA + L:c + 2 * SR_SALIDA + L])) for L in lags]
    lag = list(lags)[int(np.argmax(corr))]
    medio = slice(SR_SALIDA, n - SR_SALIDA)                      # sin los fundidos
    ganancia = float(np.sqrt((dec[medio] ** 2).mean() / (ref[medio] ** 2).mean()))
    error = dec[:n] - ref[:n]
    snr = 10 * np.log10((ref[:n] ** 2).mean() / max((error ** 2).mean(), 1e-12))
    return {"cuadros": contar(salida), "esperados": round(r.duracion * rd.FPS), "ancho": v["width"],
            "alto": v["height"], "fps": v["r_frame_rate"], "perfil": v.get("profile"), "pix_fmt": v["pix_fmt"],
            "video_kbps": round(int(v.get("bit_rate", 0)) / 1000), "audio": f"{a['codec_name']} {a['sample_rate']} Hz "
            f"{round(int(a.get('bit_rate', 0)) / 1000)} kbps", "duracion_s": float(prob["format"]["duration"]),
            "muestras_audio": len(dec), "muestras_ref": len(ref), "desfase_muestras": lag,
            "ganancia_db": round(20 * np.log10(ganancia), 3), "snr_aac_db": round(float(snr), 1)}


def main(salida: str | None, solo: list[int] | None) -> None:
    r = rd.cargar()
    print(f"Reel: la mezcla desde {r.inicio:.3f} s, {r.duracion:.3f} s, drop en el {r.drop - r.inicio:.3f} "
          f"({round(r.duracion * rd.FPS)} cuadros)", flush=True)
    rutas = piezas(r, solo)
    if solo is not None:
        return
    destino = Path(salida) if salida else SALIDA
    unir(r, rutas, destino)
    print(json.dumps(verificar(r, destino), ensure_ascii=False, indent=1), flush=True)
