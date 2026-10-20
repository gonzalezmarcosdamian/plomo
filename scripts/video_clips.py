# -*- coding: utf-8 -*-
"""El video de una Session con clips reales, editados al ritmo de la mezcla.

POR QUE
-------
"Me encanto saca el session 4 que esta, y cambialo por este tipo de video, de ahora en mas los
hacemos asi" (el DJ, 2026-10-20, despues de la prueba de 1 minuto con clips de Pixabay sobre el
drop de Fog Machine). Reemplaza a `video_animar.py --shader` para las Sessions: en vez de
dibujar, monta clips de data/video/clips_sessions.json con la misma gramatica que la prueba.

COMO EDITA
----------
Los compases salen de la grilla de la mezcla, contados desde cada cambio de tema (los cambios
caen en el uno de una frase). El drop es el salto de bajo+cuerpo de `video_animar.camara`, y el
break es esa misma senal baja durante cuatro compases o mas.

    groove        planos de 4 compases que se funden en un beat, gente y paisaje alternados
    break         planos de 8 compases de paisaje que se funden en un compas
    antes del drop  los ultimos 4 compases, planos de 2 con corte seco
    drop          corte seco en el uno, ocho compases en planos de 2 (gente con los brazos arriba)
    cambio de tema  plano nuevo, fundido de dos beats y el nombre del tema abajo a la izquierda

La luz sigue el set: atardecer hasta el 40%, anochecer hasta el 52% y noche despues. Los fuegos
artificiales se guardan para los drops del ultimo 20%. Todo lleva un mismo grade (calido, vineta,
grano) para que clips de autores distintos parezcan la misma tarde.

COMO RENDERIZA
--------------
En piezas: cada plano solo y cada fundido entre dos planos es un ffmpeg chico de una o dos
entradas, en una grilla global de cuadros. Las piezas se unen sin recodificar y el audio de la
mezcla entra tal cual (PCM), asi el video se verifica muestra por muestra igual que los otros.
Una pieza terminada no se rehace: si se corta, se retoma.

USO
---
    python scripts/video_clips.py --nombre session_04 --master postproduction/mixes/157_mix.wav
        --mix postproduction/mixes/157_mix.json [--desde 900 --hasta 1110] [--salida X.mov]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import video_animar as va  # noqa: E402

STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
BIBLIOTECA = RAIZ / "data" / "video" / "clips_sessions.json"
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
FPS = 30
W, H = 2560, 1440
FASES = ((0.40, "atardecer"), (0.52, "anochecer"), (1.01, "noche"))
FUEGOS = {134018, 134015, 134017, 134014, 292813, 133783, 13522, 5269}
FUEGOS_DESDE = 0.80            # los fuegos artificiales, solo en los drops del final
UMBRAL_DROP = 0.33             # pico de impacto (video_animar.camara) que cuenta como drop
BREAK_PREVIO = 0.25            # ...si antes hubo un break: bajo+cuerpo por debajo de esto
UMBRAL_BREAK = 0.45            # seccion por debajo de esto, cuatro compases seguidos, es break
SIN_REPETIR = 10               # un clip no vuelve antes de este numero de planos
CAMARA_LENTA_MAX = 1.8         # un clip corto se estira hasta esto antes de buscar otro
TRABAJOS = 3
# el grade de la prueba que aprobo el DJ; la noche se calienta menos para no ensuciar las luces
GRADO = {
    "atardecer": "eq=saturation=1.08:contrast=1.04,colorbalance=rs=0.06:gs=0.01:bs=-0.06:rm=0.04:bm=-0.04",
    "anochecer": "eq=saturation=1.05:contrast=1.04,colorbalance=rs=0.03:bs=-0.01:rm=0.02",
    "noche": "eq=saturation=1.05:contrast=1.05,colorbalance=rh=0.03:bh=-0.02",
}
TERMINACION = "vignette=PI/5,noise=alls=4:allf=t"
CREMA = "0xF3EBDD"
CODIF = ["-c:v", "libx264", "-preset", "faster", "-crf", "19", "-maxrate", "16M", "-bufsize", "32M",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-video_track_timescale", "30000", "-threads", "4", "-an"]


def fase_de(p: float) -> str:
    return next(nombre for tope, nombre in FASES if p < tope)


# ---------------------------------------------------------------- compases y secciones

def seccion_de(r: dict) -> np.ndarray:
    """Bajo + cuerpo suavizados: lo que cae en el break y vuelve de golpe en el drop."""
    fps = int(r["fps"])
    return np.clip(va.suavizar(np.clip((r["bajo"] + r["cuerpo"]) / 2, 0, 1), 1.0, fps) / 0.55, 0, 1)


def compases(r: dict, plan: list[dict]) -> tuple[np.ndarray, list[int]]:
    """Inicio de cada compas en el mix, y en que compas empieza cada tema.

    El uno de cada tema no se toma del cambio: el cambio cae a veces un beat antes (con el 18:02 de
    Fog Machine la grilla quedo medio segundo corrida). De los cuatro beats posibles se elige el
    que mas coincide con los cambios de seccion, que en house caen siempre en el uno de la frase."""
    fps = int(r["fps"])
    beats = r["beats"][0].astype(float)
    cambio = np.abs(np.diff(seccion_de(r), prepend=0.0))
    cambio = np.convolve(cambio, np.ones(int(0.3 * fps)), mode="same")
    cambios = [0.0] + [c["cambio_in"] for c in plan[1:]]
    barras, inicio_tema = [], []
    for k, t0 in enumerate(cambios):
        t1 = cambios[k + 1] if k + 1 < len(cambios) else beats[-1] + 1
        j0 = int(np.argmin(abs(beats - t0)))
        fin = int(np.searchsorted(beats, t1 - 0.05))

        def puntaje(f: int) -> float:
            js = np.arange(j0 + f, fin, 4)
            return float(cambio[np.clip((beats[js] * fps).astype(int), 0, len(cambio) - 1)].sum())

        fase = max(range(4), key=puntaje)
        if barras and beats[j0 + fase] - barras[-1] < 0.3:
            fase += 4
        inicio_tema.append(len(barras))
        barras += [float(beats[j]) for j in range(j0 + fase, fin, 4)]
    return np.array(barras), inicio_tema


def marcar(r: dict, barras: np.ndarray) -> tuple[set[int], set[int]]:
    """Que compases son drop y cuales son break.

    El drop es un pico del impacto despues de un break de verdad (bajo + cuerpo casi en cero en los
    ocho compases previos), enganchado al compas mas cercano al pico. El cruce del umbral no sirve:
    la senal esta suavizada y sube dos segundos antes del golpe, y caia un compas antes. Sin pedir
    el break salian 32 drops; con esto, 16 en los 16 temas del 157, Fog Machine en 18:01.8 y
    Stamina en 69:13.1."""
    fps = int(r["fps"])
    seccion = seccion_de(r)
    imp = va.camara(r, fps)["impacto"]
    idx = np.clip((barras * fps).astype(int), 0, len(imp) - 1)
    bar = float(np.median(np.diff(barras)))
    drops = set()
    for f in range(fps, len(imp) - fps):
        if imp[f] < UMBRAL_DROP or imp[f] != imp[f - fps:f + fps].max():
            continue
        antes = seccion[max(0, f - int(8 * bar * fps)):f - int(1.5 * fps)]
        if not len(antes) or antes.min() >= BREAK_PREVIO:
            continue
        b = int(np.argmin(abs(barras - f / fps)))
        if all(abs(b - d) >= 16 for d in drops):
            drops.add(b)
    fin = np.append(idx[1:], len(seccion) - 1)
    nivel = np.array([seccion[a:max(a + 1, z)].mean() for a, z in zip(idx, fin)])
    bajo = nivel < UMBRAL_BREAK
    breaks = set()
    b = 0
    while b < len(bajo):
        if bajo[b]:
            z = b
            while z < len(bajo) and bajo[z]:
                z += 1
            if z - b >= 4:
                breaks.update(range(b, z))
            b = z
        else:
            b += 1
    return drops, breaks - drops


# ---------------------------------------------------------------- el plan de planos

class Elector:
    """Elige el clip de cada plano: el menos usado del grupo, sin repetir uno reciente, y cada
    vez desde otro punto del clip."""

    def __init__(self, clips: list[dict], semilla: int = 4):
        self.clips = {c["id"]: c for c in clips if (STOCK / f"{c['id']}.mp4").exists()}
        self.usos = {i: 0 for i in self.clips}
        self.cursor = {i: random.Random(semilla + i).uniform(0, max(0.0, c["duracion"] - 8))
                       for i, c in self.clips.items()}
        self.recientes: list[int] = []

    def grupo(self, fase: str, rol: str, p: float) -> list[int]:
        quiero = {"anochecer": {"calma": [("anochecer", "calma")],
                                "gente": [("atardecer", "gente"), ("noche", "gente")],
                                "drop": [("atardecer", "drop"), ("noche", "drop")]}}.get(fase)
        claves = quiero[rol] if quiero else [(fase, rol)]
        ids = [i for i, c in self.clips.items() if (c["fase"], c["rol"]) in claves]
        if rol == "drop" and fase == "noche" and p < FUEGOS_DESDE:
            ids = [i for i in ids if i not in FUEGOS] or ids
        # un grupo vacio (un clip que no bajo) no frena el plan: la misma fase, o cualquiera
        return ids or [i for i, c in self.clips.items() if c["fase"] == fase] or list(self.clips)

    def elegir(self, fase: str, rol: str, p: float, necesito: float) -> tuple[int, float, float]:
        ids = self.grupo(fase, rol, p)
        aptos = [i for i in ids if self.clips[i]["duracion"] * CAMARA_LENTA_MAX >= necesito + 0.5] or ids
        libres = [i for i in aptos if i not in self.recientes[-SIN_REPETIR:]] or aptos
        i = min(libres, key=lambda x: (self.usos[x], x))
        dur = self.clips[i]["duracion"]
        lento = min(max(1.0, (necesito + 0.4) / max(dur - 0.3, 0.5)), CAMARA_LENTA_MAX)
        largo = necesito / lento
        desde = self.cursor[i]
        if desde + largo > dur - 0.2:
            desde = 0.2
        self.cursor[i] = desde + largo + 1.0
        self.usos[i] += 1
        self.recientes.append(i)
        return i, round(desde, 3), round(lento, 4)


def planificar(barras: np.ndarray, inicio_tema: list[int], drops: set[int], breaks: set[int],
               total_s: float, clips: list[dict]) -> list[dict]:
    bar = float(np.median(np.diff(barras)))
    elector = Elector(clips)
    temas = set(inicio_tema)
    planos, b, alterna = [], 0, 0
    previos = {d - 4 for d in drops}

    def tope(desde: int, largo: int) -> int:
        """Un plano no cruza un drop, un cambio de tema ni el arranque de los cortes previos."""
        for z in range(desde + 1, desde + largo):
            if z in drops or z in temas or z in previos or z >= len(barras):
                return z
        return desde + largo

    corrida_drop = 0
    while b < len(barras):
        p = barras[b] / total_s
        fase = fase_de(p)
        if b in drops:
            corrida_drop = 4
        if corrida_drop:
            rol, largo, entra = ("drop" if corrida_drop % 2 == 0 else "gente"), 2, "corte"
            corrida_drop -= 1
        elif any(d - 4 <= b < d for d in drops):
            rol, largo, entra = "gente", 2, "corte"
        elif b in breaks:
            rol, largo, entra = "calma", 8, "funde_compas"
        else:
            rol = ("gente", "calma", "gente", "calma", "gente", "gente")[alterna % 6]
            alterna += 1
            largo, entra = 4, "funde"
        if b in temas and b > 0 and entra != "corte":
            entra = "funde_tema"
        z = tope(b, largo)
        t0 = float(barras[b])
        t1 = float(barras[z]) if z < len(barras) else total_s
        fundido = {"corte": 0.0, "funde": bar / 4, "funde_tema": bar / 2, "funde_compas": bar}[entra]
        if b == 0:
            entra, fundido = "negro", 0.0
        clip, desde, lento = elector.elegir(fase, rol, p, t1 - t0 + fundido)
        planos.append({"t0": round(t0, 3), "t1": round(t1, 3), "fase": fase, "rol": rol, "clip": clip,
                       "desde": desde, "lento": lento, "entra": entra, "fundido": round(fundido, 3)})
        b = z
    planos[-1]["t1"] = round(total_s, 3)
    return planos


# ---------------------------------------------------------------- piezas y render

def piezas(planos: list[dict]) -> list[dict]:
    """Cada plano solo y cada fundido, en cuadros de la grilla global."""
    out = []
    for i, pl in enumerate(planos):
        f0, f1 = round(pl["t0"] * FPS), round(pl["t1"] * FPS)
        sig = planos[i + 1] if i + 1 < len(planos) else None
        d_sig = round(sig["fundido"] * FPS) if sig else 0
        aparece = f0 - round(pl["fundido"] * FPS)       # el cuadro donde el plano empieza a verse
        if f1 - d_sig > f0:
            out.append({"tipo": "solo", "f0": f0, "f1": f1 - d_sig, "a": i, "aparece_a": aparece})
        if d_sig:
            out.append({"tipo": "funde", "f0": f1 - d_sig, "f1": f1, "a": i, "b": i + 1,
                        "aparece_a": aparece, "aparece_b": f1 - d_sig})
    return out


def entrada(pl: dict, desde_cuadro: int, cuadros: int) -> list[str]:
    seg = pl["desde"] + desde_cuadro / FPS / pl["lento"]
    return ["-ss", f"{seg:.3f}", "-t", f"{cuadros / FPS / pl['lento'] + 0.5:.3f}",
            "-i", str(STOCK / f"{pl['clip']}.mp4")]


def cadena(k: int, pl: dict) -> str:
    # el tpad repite el ultimo cuadro si el clip se acaba antes: una pieza corta correria el audio
    return (f"[{k}:v]setpts=(PTS-STARTPTS)*{pl['lento']},fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
            f"{GRADO[pl['fase']]},format=yuv420p,tpad=stop_mode=clone:stop_duration=10")


LINEAS = (("artista", 50, 190), ("titulo", 38, 128))   # campo, tamano, alto desde abajo


def escribir_textos(capitulos: list[dict], carpeta: Path) -> None:
    """Un archivo por renglon, una sola vez antes de los trabajos en paralelo."""
    for k, c in enumerate(capitulos):
        for linea, (campo, _, _) in enumerate(LINEAS):
            (carpeta / f"cap_{k:02d}_{linea}.txt").write_text(" ".join(c[campo].split()), encoding="utf-8")


def textos(capitulos: list[dict], t0: float, t1: float) -> str:
    """drawtext de los nombres de tema que se ven en [t0, t1), con la hora global."""
    filtros = []
    for k, c in enumerate(capitulos):
        a = c["t"] + (2.0 if k == 0 else 1.5)
        z = a + 9.0
        if z < t0 or a > t1:
            continue
        for linea, (_, tam, y) in enumerate(LINEAS):
            T = f"(t+{t0:.3f})"
            alfa = f"if(lt({T},{a:.2f}),0,if(lt({T},{a + 1:.2f}),{T}-{a:.2f},if(lt({T},{z - 1.5:.2f}),1,max(0,({z:.2f}-{T})/1.5))))"
            filtros.append(f"drawtext=fontfile=fuente.ttf:textfile=cap_{k:02d}_{linea}.txt:fontsize={tam}"
                           f":fontcolor={CREMA}:x=96:y=h-{y}:shadowcolor=black@0.55:shadowx=2:shadowy=2"
                           f":alpha='{alfa}'")
    return ("," + ",".join(filtros)) if filtros else ""


def comando(pz: dict, planos: list[dict], capitulos: list[dict], total_f: int, salida: Path) -> list[str]:
    n = pz["f1"] - pz["f0"]
    t0, t1 = pz["f0"] / FPS, pz["f1"] / FPS
    a = planos[pz["a"]]
    args = entrada(a, pz["f0"] - pz["aparece_a"], n)
    if pz["tipo"] == "solo":
        grafo = cadena(0, a) + "[v0];[v0]"
    else:
        b = planos[pz["b"]]
        args += entrada(b, pz["f0"] - pz["aparece_b"], n)
        grafo = (cadena(0, a) + "[v0];" + cadena(1, b) + "[v1];"
                 f"[v0][v1]xfade=transition=fade:duration={n / FPS:.4f}:offset=0,")
    grafo += TERMINACION + textos(capitulos, t0, t1)
    if pz["f0"] == 0:
        grafo += ",fade=t=in:st=0:d=2"
    if pz["f1"] >= total_f:
        grafo += f",fade=t=out:st={max(0.0, n / FPS - 3):.3f}:d=3"
    return ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, "-filter_complex", grafo + "[out]",
            "-map", "[out]", "-frames:v", str(n), *CODIF, str(salida)]


def huella(pz: dict, planos: list[dict]) -> str:
    claves = [pz["tipo"], pz["f0"], pz["f1"]] + [planos[pz[k]] for k in ("a", "b") if k in pz]
    return hashlib.sha1(json.dumps(claves, sort_keys=True).encode()).hexdigest()[:10]


def renderizar(lista: list[tuple[int, dict]], planos: list[dict], capitulos: list[dict], total_f: int,
               carpeta: Path) -> list[Path]:
    """`lista` lleva el numero de cada pieza en el video entero: asi una prueba sobre un tramo deja
    piezas que el render completo reusa."""
    carpeta.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FUENTE, carpeta / "fuente.ttf")
    escribir_textos(capitulos, carpeta)
    archivos = [carpeta / f"{n:05d}_{huella(pz, planos)}.mp4" for n, pz in lista]
    pendientes = [k for k, f in enumerate(archivos) if not f.exists()]
    print(f"{len(lista)} piezas, {len(lista) - len(pendientes)} ya estaban", flush=True)
    inicio, hechas = time.time(), 0

    def una(k: int) -> None:
        tmp = archivos[k].with_suffix(".tmp.mp4")
        r = subprocess.run(comando(lista[k][1], planos, capitulos, total_f, tmp),
                           cwd=carpeta, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"pieza {k}: {r.stderr[-1500:]}")
        tmp.replace(archivos[k])

    with ThreadPoolExecutor(TRABAJOS) as ex:
        for fut in as_completed([ex.submit(una, k) for k in pendientes]):
            fut.result()
            hechas += 1
            if hechas % 25 == 0 or hechas == len(pendientes):
                ritmo = (time.time() - inicio) / hechas
                print(f"  {hechas}/{len(pendientes)} piezas, faltan {ritmo * (len(pendientes) - hechas) / 60:.1f} min",
                      flush=True)
    return archivos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--mix", required=True)
    ap.add_argument("--desde", type=float, default=0.0)
    ap.add_argument("--hasta", type=float)
    ap.add_argument("--salida")
    ap.add_argument("--solo-plan", action="store_true", help="arma la edicion y la guarda, sin renderizar")
    a = ap.parse_args()

    r = dict(np.load(RAIZ / "data" / "video" / f"{a.nombre}_rasgos.npz"))
    capitulos = json.loads((RAIZ / "data" / "video" / f"{a.nombre}_capitulos.json").read_text(encoding="utf-8"))
    mix = json.loads((RAIZ / a.mix).read_text(encoding="utf-8"))
    clips = json.loads(BIBLIOTECA.read_text(encoding="utf-8"))["clips"]
    total_s = len(r["cuerpo"]) / int(r["fps"])

    barras, inicio_tema = compases(r, mix["plan"])
    drops, breaks = marcar(r, barras)
    planos = planificar(barras, inicio_tema, drops, breaks, total_s, clips)
    edicion = RAIZ / "data" / "video" / f"{a.nombre}_edicion.json"
    edicion.write_text(json.dumps({"drops_s": sorted(round(float(barras[d]), 2) for d in drops),
                                   "planos": planos}, ensure_ascii=False, indent=1), encoding="utf-8")
    usados = {p["clip"] for p in planos}
    print(f"{len(barras)} compases, {len(drops)} drops, {len(breaks)} compases de break, {len(planos)} planos "
          f"con {len(usados)} clips -> {edicion.relative_to(RAIZ)}", flush=True)
    if a.solo_plan:
        return

    total_f = round(total_s * FPS)
    f_desde = round(a.desde * FPS)
    f_hasta = round(a.hasta * FPS) if a.hasta else total_f
    lista = [(n, pz) for n, pz in enumerate(piezas(planos)) if pz["f1"] > f_desde and pz["f0"] < f_hasta]
    archivos = renderizar(lista, planos, capitulos["capitulos"], total_f,
                          RAIZ / "postproduction" / "video" / f"{a.nombre}_piezas")

    salida = Path(a.salida) if a.salida else RAIZ / "postproduction" / "video" / f"{a.nombre}.mov"
    indice = salida.with_suffix(".piezas.txt")
    indice.write_text("".join(f"file '{f.as_posix()}'\n" for f in archivos), encoding="utf-8")
    t_ini = lista[0][1]["f0"] / FPS
    dur = (lista[-1][1]["f1"] - lista[0][1]["f0"]) / FPS
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(indice),
           "-ss", f"{t_ini:.3f}", "-t", f"{dur:.3f}", "-i", str(RAIZ / a.master),
           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "pcm_s24le", str(salida)]
    if salida.suffix == ".mp4":
        cmd[-2:-1] = ["aac", "-b:a", "320k"]
    rr = subprocess.run(cmd, capture_output=True, text=True)
    if rr.returncode:
        sys.exit(rr.stderr[-2000:])
    print(f"-> {salida}  ({dur / 60:.1f} min, {salida.stat().st_size / 1e9:.2f} GB)", flush=True)


if __name__ == "__main__":
    main()
