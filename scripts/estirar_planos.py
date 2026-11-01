# -*- coding: utf-8 -*-
"""Estira cada plano elegido de una Session de paisajes hasta su largo, con RIFE si hace falta.

POR QUE
-------
La Session 05 va con planos de 32 compases: de 63 a 134 s con los fundidos. Los clips de Pixabay
que sirven cubren de 20 a 78 s (medido con revisar_clips.py el 2026-11-01), asi que casi todo plano
necesita entre x1.3 y x2.5. En la 04 se estiro a mano, clip por clip, y quedaron 188 archivos sin
receta. Esto lo hace en tanda desde lo que eligio el editor, y anota en el mismo JSON de la etapa
de donde salio cada estirado: si se borra un estirado, se rehace.

COMO
----
Por cada plano de data/video/<nombre>_etapa_*.json que no tenga `archivo`:
- saca el tramo [desde, hasta] del clip con el `encuadre` del editor (ya a 2560x1440) a JPG;
- si hay cuadros reales de sobra (un clip de 60 fps), los reparte sin inventar nada;
- si no, RIFE (rife-ncnn-vulkan, en la placa de video) inventa los que faltan;
- codifica a 30 fps y deja en el plano `archivo`, `desde` 0, `encuadre` "null" y el origen en
  `fuente`. El `grado` queda para el render.
Los cuadros temporales van en JPG: en PNG un plano de 134 s a 1440p ocupaba unos 28 GB.

USO
---
    python scripts/estirar_planos.py --nombre session_05 [--planos 3 7] [--dry]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
DEST = RAIZ / "postproduction" / "stock" / "estirados"
TMP = RAIZ / "postproduction" / "stock" / "estirados_tmp"
RIFE = RAIZ / "postproduction" / "herramientas" / "rife-ncnn-vulkan-20221029-windows"
FPS = 30
MARGEN_S = 1.0          # naturaleza.py pide 1 s de mas al leer cada plano
FACTOR_MAX = 3.0        # mas que esto se ve inventado (el revisor marco texturas en la 04)


def cuadros_necesarios(segundos_de_clip: float) -> int:
    """Los cuadros que el plano muestra a 30 fps, mas el margen que lee naturaleza.py."""
    return math.ceil((segundos_de_clip + MARGEN_S) * FPS)


def modo(n_in: int, n_out: int) -> str:
    """'reales' si alcanzan los cuadros que hay; 'rife' si hay que inventar."""
    if n_in <= 0:
        raise ValueError("el tramo no tiene cuadros")
    if n_out / n_in > FACTOR_MAX:
        raise ValueError(f"hace falta x{n_out / n_in:.1f}, mas de x{FACTOR_MAX:g}: elegir un clip mas largo")
    return "reales" if n_in >= n_out else "rife"


def nombre_estirado(nombre: str, n: int, id_: int) -> str:
    return f"{nombre.replace('session_', 's')}_{n:03d}_{id_}.mp4"


def _probe(ruta: Path) -> tuple[float, float]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=r_frame_rate:format=duration", "-of", "json", str(ruta)],
                       capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    num, den = d["streams"][0]["r_frame_rate"].split("/")
    return float(num) / float(den), float(d["format"]["duration"])


def _contar(ruta: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", str(ruta)], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def estirar(sel: dict, segundos: float, salida: Path) -> str:
    """Hace el estirado de un plano. Devuelve el modo usado."""
    ruta = STOCK / f"{sel['id']}.mp4"
    fps, dur = _probe(ruta)
    desde = float(sel.get("desde", 0.0))
    hasta = min(float(sel.get("hasta", dur)), dur)
    n_out = cuadros_necesarios(segundos)
    tmp = TMP / salida.stem
    shutil.rmtree(tmp, ignore_errors=True)
    ent, sal = tmp / "entrada", tmp / "salida"
    ent.mkdir(parents=True), sal.mkdir()
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{desde:.3f}", "-t", f"{hasta - desde:.3f}", "-i", str(ruta),
                        "-vf", f"{sel['encuadre']},setsar=1", "-fps_mode", "passthrough", "-q:v", "2",
                        str(ent / "%08d.jpg")], check=True)
        n_in = len(list(ent.glob("*.jpg")))
        m = modo(n_in, n_out)
        if m == "reales":
            # se leen los n_in cuadros a la velocidad que los lleva a n_out y se toman a 30 fps
            fuente, tasa = ent, n_in * FPS / n_out
        else:
            subprocess.run([str(RIFE / "rife-ncnn-vulkan.exe"), "-i", str(ent), "-o", str(sal), "-n", str(n_out),
                            "-m", str(RIFE / "rife-v4.6"), "-f", "%08d.jpg"], check=True, capture_output=True)
            fuente, tasa = sal, FPS
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", f"{tasa:.6f}", "-i", str(fuente / "%08d.jpg"),
                        "-r", str(FPS), "-frames:v", str(n_out), "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-pix_fmt", "yuv420p", str(salida)], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    hechos = _contar(salida)
    if hechos < n_out - 1:
        raise RuntimeError(f"{salida.name}: {hechos} cuadros, se esperaban {n_out}")
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--planos", type=int, nargs="*", help="solo estos planos")
    ap.add_argument("--dry", action="store_true", help="muestra el factor de cada plano sin hacer nada")
    a = ap.parse_args()
    largos = {p["n"]: p["segundos_de_clip"] for p in json.loads(
        (RAIZ / "data" / "video" / f"{a.nombre}_planos.json").read_text(encoding="utf-8"))["planos"]}
    DEST.mkdir(parents=True, exist_ok=True)
    archivos = sorted((RAIZ / "data" / "video").glob(f"{a.nombre}_etapa_*.json"))
    pendientes = [(f, p) for f in archivos for p in json.loads(f.read_text(encoding="utf-8"))["planos"]
                  if "archivo" not in p and (not a.planos or p["n"] in a.planos)]
    print(f"{len(pendientes)} planos para estirar", flush=True)
    inicio, fallados = time.time(), []
    for k, (f, p) in enumerate(pendientes, 1):
        salida = DEST / nombre_estirado(a.nombre, p["n"], p["id"])
        if a.dry:
            fps, dur = _probe(STOCK / f"{p['id']}.mp4")
            seg = min(float(p.get("hasta", dur)), dur) - float(p.get("desde", 0))
            print(f"  plano {p['n']:3d}: {p['id']} {seg:.0f} s a {fps:.0f} fps -> {largos[p['n']]:.0f} s, "
                  f"x{cuadros_necesarios(largos[p['n']]) / (seg * fps):.2f}")
            continue
        t0 = time.time()
        try:
            m = estirar(p, largos[p["n"]], salida)
        except (subprocess.CalledProcessError, ValueError, RuntimeError) as e:
            fallados.append(p["n"])
            print(f"  plano {p['n']} FALLO: {str(e)[-300:]}", flush=True)
            continue
        # se relee y se escribe al toque: si se corta, lo hecho queda anotado
        datos = json.loads(f.read_text(encoding="utf-8"))
        for q in datos["planos"]:
            if q["n"] == p["n"]:
                q["fuente"] = {k2: q[k2] for k2 in ("id", "desde", "hasta", "encuadre") if k2 in q}
                q.update({"archivo": str(salida.relative_to(RAIZ)).replace("\\", "/"), "desde": 0.0, "paso": 1,
                          "encuadre": "null"})
                q.pop("id", None)
                q.pop("hasta", None)
        f.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        resto = (time.time() - inicio) / k * (len(pendientes) - k) / 60
        print(f"  plano {p['n']} listo ({m}, {time.time() - t0:.0f} s); {k}/{len(pendientes)}, faltan {resto:.0f} min",
              flush=True)
    if fallados:
        sys.exit(f"fallaron los planos {fallados}")


if __name__ == "__main__":
    main()
