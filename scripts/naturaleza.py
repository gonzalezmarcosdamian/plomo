# -*- coding: utf-8 -*-
"""El video de una Session con paisajes: planos largos, fundidos largos, un recorrido con sentido.

POR QUE
-------
"Yo haria un mix mas largo de paisajes seleccionados... transiciones mas largas no 8 segundo,
quedo una locura de cambios el otro, quiero que sea todo naturaleza, con un sentido" (el DJ,
2026-10-21). La prueba de 3 minutos de la Session 04 (del mar a la costa) fue "si asi hace la
session 4 y publicala". Esto escala esa prueba al set entero.

LA GRILLA
---------
La mezcla va a tempo fijo; cada tema trae su compas 0 en la mezcla (`desde` del plan de
mezclar.py) y su estructura en compases (`estructura.medido`: breakdown y drop). Los planos
cambian en el uno de una frase del tema que manda en ese momento:
- cada 16 compases;
- un solo plano largo en el breakdown;
- un plano nuevo en el drop y otro cuando entra cada tema.
Cada plano llega con un fundido de 4 compases que termina en esa frontera. El uno se corre con el
bombo real de cada tema, medido en la mezcla: la grilla nominal y el golpe difieren decenas de ms.

USO
---
    python scripts/naturaleza.py plan --mix postproduction/mixes/157_mix.json --nombre session_04
        -> data/video/session_04_planos.json (los huecos: cuando entra, cuando llena, cuando sale)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FRASE = 16          # compases entre cambios de plano
FUNDIDO = 4         # compases de cada fundido
MIN_PLANO = 12      # un plano no dura menos que esto
FPS = 30
SUBIDA_A_ARRANQUE = 0.055
ETAPAS = [  # (nombre, temas por indice del plan, la luz)
    ("Mar al amanecer", (0, 1, 2), "primera luz y amanecer sobre el agua"),
    ("Costa y dunas", (3, 4), "luz dorada de manana"),
    ("Bosque y rio", (5, 6, 7), "luz de dia entre los arboles"),
    ("Cascadas y montanas", (8, 9, 10), "tarde"),
    ("Cumbres sobre las nubes, al atardecer", (11, 12, 13), "atardecer"),
    ("La noche", (14, 15), "del anochecer a la via lactea"),
]


def ataque_del_bombo(master: Path, desde: float, hasta: float, base: float, beat: float) -> float:
    """Cuanto despues de la grilla nominal cae el bombo real, en segundos (mediana de los golpes fuertes)."""
    info = sf.info(str(master))
    sr = info.samplerate
    x, _ = sf.read(str(master), start=int(desde * sr), stop=int(hasta * sr), dtype="float32")
    m = resample_poly(x.mean(1), 8000, sr)
    lo = sosfiltfilt(butter(4, [40, 100], btype="band", fs=8000, output="sos"), m)
    e = np.sqrt(np.convolve(lo ** 2, np.ones(40) / 40, mode="same"))[::8]          # 1 kHz
    desfases, picos = [], []
    k0 = int(np.ceil((desde + 0.25 - base) / beat))
    k1 = int((hasta - 0.25 - base) / beat)
    # el golpe es la subida mas brusca de la envolvente cerca del beat. Con el cruce del 50% en
    # +-200 ms, en Stamina (bajo grave sostenido) agarraba la cola del golpe anterior: -185 ms,
    # cuando el bombo del drop cae a +42.
    sube = np.diff(e, prepend=e[0])
    for k in range(k0, k1):
        tb = base + k * beat
        i0, i1 = int(round((tb - 0.12 - desde) * 1000)), int(round((tb + 0.12 - desde) * 1000))
        seg = sube[i0:i1]
        if len(seg) < 200:
            continue
        picos.append(seg.max())
        desfases.append((i0 + int(np.argmax(seg)) - (tb - desde) * 1000) / 1000)
    picos, desfases = np.array(picos), np.array(desfases)
    fuertes = picos > np.percentile(picos, 50)
    # la subida mas brusca cae ~55 ms despues del arranque del golpe: en los golpes limpios de
    # despues de un break el arranque da +42 ms (Stamina) y +50 (Fog Machine) contra +107 y +98
    return float(np.median(desfases[fuertes])) - SUBIDA_A_ARRANQUE if fuertes.any() else 0.0


def plan(mix: dict, master: Path) -> list[dict]:
    compas = 4 * 60 / mix["tempo"]
    temas = mix["plan"]
    entra = [0.0] + [t["cambio_in"] for t in temas[1:]]
    fronteras = []          # (segundo, que pasa, tema)
    for k, t in enumerate(temas):
        r0 = entra[k]
        r1 = entra[k + 1] if k + 1 < len(temas) else mix["duracion_s"]
        off = ataque_del_bombo(master, max(r0, t["desde"]), min(r1, t["desde"] + 400 * compas), t["desde"], compas / 4)
        est = mix["estructura"][k]["medido"]
        b0, b1 = est.get("breakdown", [None, None])
        drop = est.get("drop")
        uno = lambda c: t["desde"] + c * compas + off
        propias = []
        c = 0
        while uno(c) < r1 - 0.5:
            if uno(c) > r0 - 0.5:
                propias.append((c, "frase"))
            c += FRASE
        if k > 0:
            propias = [(round((r0 - t["desde"]) / compas), "tema")] + [p for p in propias if abs(uno(p[0]) - r0) > 1]
        if b0 is not None and b1 is not None:
            propias = [p for p in propias if not (b0 < p[0] < b1)]          # el breakdown es un solo plano
            for cb, que in ((b0, "breakdown"), (drop or b1, "drop")):
                if r0 + 1 < uno(cb) < r1 - 1:
                    propias = [p for p in propias if abs(p[0] - cb) >= MIN_PLANO] + [(cb, que)]
        for c, que in sorted(propias):
            fronteras.append((round(uno(c), 3), que, k))
        print(f"{k:2d} {t['tema'][:44]:44} bombo {off * 1000:+5.0f} ms, {len(propias)} fronteras", flush=True)
    fronteras.sort()
    # un plano no dura menos de MIN_PLANO compases: se borra la frontera de "frase" que lo achica
    limpias = [fronteras[0]]
    for f in fronteras[1:]:
        if f[0] - limpias[-1][0] < MIN_PLANO * compas:
            if f[1] == "frase":
                continue
            if limpias[-1][1] == "frase":
                limpias.pop()
        limpias.append(f)
    # el ultimo plano tampoco: si queda corto contra el final, el anterior llega hasta el cierre
    if mix["duracion_s"] - limpias[-1][0] < MIN_PLANO * compas and len(limpias) > 1:
        limpias.pop()
    planos = []
    for i, (t0, que, k) in enumerate(limpias):
        t1 = limpias[i + 1][0] if i + 1 < len(limpias) else mix["duracion_s"]
        entra_desde = 0.0 if i == 0 else round(t0 - FUNDIDO * compas, 3)
        etapa = next(e for e, (_, ts, _) in enumerate(ETAPAS) if k in ts) + 1
        planos.append({"n": i + 1, "etapa": etapa, "entra": entra_desde, "lleno": t0 if i else 0.0,
                       "sale": round(t1, 3), "que": "inicio" if i == 0 else que, "tema": temas[k]["tema"],
                       "segundos_de_clip": round(t1 - entra_desde, 2)})
    return planos


# ---------------------------------------------------------------- render

W, H = 2560, 1440
STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
CREMA = "0xF3EBDD"
PLANOS_POR_TRAMO = 6
CODIF = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-maxrate", "24M", "-bufsize", "48M", "-video_track_timescale", "30000", "-an"]


def fps_de(ruta: Path, cache: dict) -> float:
    if ruta not in cache:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                            "-of", "csv=p=0", str(ruta)], capture_output=True, text=True).stdout.strip()
        n, d = r.split("/")
        cache[ruta] = float(n) / float(d)
    return cache[ruta]


def duracion_de(ruta: Path, cache: dict) -> float:
    clave = ("dur", ruta)
    if clave not in cache:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                           capture_output=True, text=True).stdout.strip()
        cache[clave] = float(r or 0)
    return cache[clave]


def eleccion(nombre: str) -> dict[int, dict]:
    """Lo que eligieron los editores, por numero de plano."""
    elegidos = {}
    for f in sorted((RAIZ / "data" / "video").glob(f"{nombre}_etapa_*.json")):
        for p in json.loads(f.read_text(encoding="utf-8"))["planos"]:
            elegidos[p["n"]] = p
    return elegidos


def entrada(p: dict, sel: dict, desde_cuadro: int, cuadros: int, cache: dict) -> tuple[list[str], str]:
    """Los args de entrada y la cadena de filtros de un plano, desde su cuadro `desde_cuadro`."""
    ruta = RAIZ / sel["archivo"] if "archivo" in sel else STOCK / f"{sel['id']}.mp4"
    paso = int(sel.get("paso", 1))
    fps = fps_de(ruta, cache)
    seg = sel["desde"] + desde_cuadro * paso / fps
    largo = cuadros * paso / fps + 1.0
    hay = duracion_de(ruta, cache) - seg
    if hay < 0.5:
        raise ValueError(f"plano {sel['n']}: arranca en {seg:.1f} s y el clip {ruta.name} dura "
                         f"{duracion_de(ruta, cache):.1f} s: no hay cuadros que mostrar")
    if hay < cuadros * paso / fps - 0.05:
        print(f"AVISO plano {sel['n']}: el clip {ruta.name} no alcanza por {cuadros * paso / fps - hay:.1f} s "
              "(se repite el ultimo cuadro)", flush=True)
    # la misma base de tiempo para todos (1/30): xfade no funde clips de 1/30000 con clips de 1/60000
    filtro = ((f"select='not(mod(n\\,{paso}))'," if paso > 1 else "") + "settb=1/30,setpts=N,fps=30,"
              f"{sel['encuadre']},setsar=1,format=gbrp16le,{sel['grado']},format=yuv420p10le,"
              f"tpad=stop_mode=clone:stop_duration={cuadros / FPS + 1:.2f}")
    return ["-ss", f"{seg:.3f}", "-t", f"{largo:.3f}", "-i", str(ruta)], filtro


def textos(temas: list[dict], t0: float, t1: float) -> str:
    """El nombre del tema, como en la prueba aprobada: titulo arriba, artista abajo, a la izquierda."""
    filtros = []
    for k, tm in enumerate(temas):
        a = tm["t"] + (2.0 if k == 0 else 1.5)
        z = a + 8.0
        if z < t0 or a > t1:
            continue
        T = f"(t+{t0:.3f})"
        alfa = f"if(lt({T},{a:.3f}),0,if(lt({T},{a + 1:.3f}),{T}-{a:.3f},if(lt({T},{z - 1.5:.3f}),1,max(0,({z:.3f}-{T})/1.5))))"
        comun = f"fontfile=fuente.ttf:fontcolor={CREMA}:x=104:shadowcolor=black@0.45:shadowx=2:shadowy=2"
        filtros.append(f"drawtext={comun}:textfile=titulo_{k:02d}.txt:fontsize=42:y=h-164:alpha='0.94*{alfa}'")
        filtros.append(f"drawtext={comun}:textfile=artista_{k:02d}.txt:fontsize=30:y=h-112:alpha='0.78*{alfa}'")
    return ("," + ",".join(filtros)) if filtros else ""


def tramos(planos: list[dict]) -> list[tuple[int, int]]:
    """Cortes en la mitad del tramo pleno de un plano: ahi nunca hay fundido, y el empalme no se ve."""
    f = lambda t: round(t * FPS)
    total = f(planos[-1]["sale"])
    cortes = [0]
    for i in range(PLANOS_POR_TRAMO, len(planos), PLANOS_POR_TRAMO):
        p, sig = planos[i], planos[i + 1] if i + 1 < len(planos) else None
        if sig:
            cortes.append((f(p["lleno"]) + f(sig["entra"])) // 2)
    cortes.append(total)
    return list(zip(cortes[:-1], cortes[1:]))


def render_tramo(j: int, c0: int, c1: int, planos: list[dict], elegidos: dict, temas: list[dict], total: int,
                 carpeta: Path, cache: dict) -> Path:
    f = lambda t: round(t * FPS)
    salida = carpeta / f"tramo_{j:03d}.mp4"
    if salida.exists() and contar(salida) == c1 - c0:
        return salida
    args, grafo, previo, fin_prev = [], [], None, None
    visibles = [p for p in planos if f(p["entra"]) < c1 and f(p["sale"]) > c0]
    for k, p in enumerate(visibles):
        a, z = max(f(p["entra"]), c0), min(f(p["sale"]), c1)
        ent, filtro = entrada(p, elegidos[p["n"]], a - f(p["entra"]), z - a, cache)
        args += ent
        grafo.append(f"[{k}:v]{filtro},trim=end_frame={z - a}[v{k}]")
        if previo is None:
            previo = f"[v{k}]"
        else:
            o = (f(p["entra"]) - c0) / FPS
            d = (f(p["lleno"]) - f(p["entra"])) / FPS
            grafo.append(f"{previo}[v{k}]xfade=transition=fade:duration={d:.4f}:offset={o:.4f}[x{k}]")
            previo = f"[x{k}]"
    cola = textos(temas, c0 / FPS, c1 / FPS)
    if c0 == 0:
        cola += ",fade=t=in:st=0:d=2"
    if c1 == total:
        cola += f",fade=t=out:st={(c1 - c0) / FPS - 3:.3f}:d=3"
    grafo.append(f"{previo}trim=end_frame={c1 - c0},format=yuv420p{cola}[out]")
    tmp = salida.with_suffix(".tmp.mp4")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, "-filter_complex", ";".join(grafo),
                        "-map", "[out]", "-frames:v", str(c1 - c0), *CODIF, str(tmp)], cwd=carpeta,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"tramo {j}: {r.stderr[-2000:]}")
    n = contar(tmp)
    if n != c1 - c0:
        raise RuntimeError(f"tramo {j}: {n} cuadros, se esperaban {c1 - c0}")
    tmp.replace(salida)
    return salida


def contar(ruta: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", str(ruta)], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def render(nombre: str, mix: dict, master: Path, salida: Path, solo: list[int] | None, trabajos: int) -> None:
    from concurrent.futures import ThreadPoolExecutor
    import shutil
    import time
    planos = json.loads((RAIZ / "data" / "video" / f"{nombre}_planos.json").read_text(encoding="utf-8"))["planos"]
    elegidos = eleccion(nombre)
    lista = tramos(planos)
    f = lambda t: round(t * FPS)
    necesarios = planos if solo is None else [p for p in planos if any(
        f(p["entra"]) < lista[j][1] and f(p["sale"]) > lista[j][0] for j in solo)]
    faltan = [p["n"] for p in necesarios if p["n"] not in elegidos]
    if faltan:
        sys.exit(f"faltan elegir {len(faltan)} planos: {faltan[:20]}")
    usados = [elegidos[p["n"]].get("id") or elegidos[p["n"]].get("archivo") for p in necesarios]
    repetidos = {u for u in usados if usados.count(u) > 1}
    if repetidos:
        print(f"AVISO: clips repetidos {sorted(map(str, repetidos))}", flush=True)
    capitulos = json.loads((RAIZ / "data" / "video" / f"{nombre}_capitulos.json").read_text(encoding="utf-8"))["capitulos"]
    entra = [0.0] + [t["cambio_in"] for t in mix["plan"][1:]]
    # el titulo como en la prueba aprobada ("Fog Machine"): sin "(Extended Mix)" ni "(Original Mix)";
    # los remixes quedan, son parte del nombre
    limpio = lambda s: re.sub(r"\s*\((Extended|Original)( Mix)?\)\s*$", "", " ".join(s.split()), flags=re.I)
    temas = [{"t": entra[k], "titulo": limpio(c["titulo"]), "artista": c["artista"]} for k, c in enumerate(capitulos)]
    carpeta = RAIZ / "postproduction" / "video" / f"{nombre}_tramos_naturaleza"
    carpeta.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FUENTE, carpeta / "fuente.ttf")
    for k, tm in enumerate(temas):
        (carpeta / f"titulo_{k:02d}.txt").write_text(tm["titulo"], encoding="utf-8")
        (carpeta / f"artista_{k:02d}.txt").write_text(tm["artista"], encoding="utf-8")
    total = round(planos[-1]["sale"] * FPS)
    elegir =[j for j in range(len(lista)) if solo is None or j in solo]
    print(f"{len(planos)} planos en {len(lista)} tramos, {total} cuadros", flush=True)
    cache, inicio, hechos = {}, time.time(), 0
    with ThreadPoolExecutor(trabajos) as ex:
        futs = {ex.submit(render_tramo, j, *lista[j], planos, elegidos, temas, total, carpeta, cache): j for j in elegir}
        for fu in futs:
            fu.result()
            hechos += 1
            print(f"  tramo {futs[fu] + 1}/{len(lista)} listo, faltan {(time.time() - inicio) / hechos * (len(elegir) - hechos) / 60:.0f} min",
                  flush=True)
    if solo is not None:
        return
    # union en dos pasos y la mezcla entera sin recortar (ver APRENDIZAJES: el video armado por piezas)
    indice = carpeta / "tramos.txt"
    indice.write_text("".join(f"file '{(carpeta / f'tramo_{j:03d}.mp4').as_posix()}'\n" for j in range(len(lista))),
                      encoding="utf-8")
    solo_video = carpeta / "solo_video.mp4"
    for cmd in (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(indice),
                 "-c", "copy", str(solo_video)],
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(solo_video), "-i", str(master),
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "pcm_s24le", "-avoid_negative_ts", "make_zero",
                 str(salida)]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr[-2000:])
    solo_video.unlink()
    print(f"-> {salida}  ({contar(salida)} cuadros de {total}, {salida.stat().st_size / 1e9:.1f} GB)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["plan", "render"])
    ap.add_argument("--mix", required=True)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--salida")
    ap.add_argument("--tramos", type=int, nargs="*", help="render: solo estos tramos, para probar")
    ap.add_argument("--trabajos", type=int, default=2)
    a = ap.parse_args()
    mix = json.loads((RAIZ / a.mix).read_text(encoding="utf-8"))
    master = (RAIZ / a.mix).with_suffix(".wav")
    if a.accion == "render":
        salida = Path(a.salida) if a.salida else RAIZ / "postproduction" / "video" / f"{a.nombre}.mov"
        render(a.nombre, mix, master, salida, a.tramos, a.trabajos)
        return
    planos = plan(mix, master)
    salida = RAIZ / "data" / "video" / f"{a.nombre}_planos.json"
    salida.write_text(json.dumps({"fps": FPS, "compas_s": round(4 * 60 / mix["tempo"], 5), "fundido_compases": FUNDIDO,
                                  "planos": planos}, ensure_ascii=False, indent=1), encoding="utf-8")
    largos = [p["sale"] - p["lleno"] for p in planos]
    print(f"{len(planos)} planos, de {min(largos):.0f} a {max(largos):.0f} s (mediana {np.median(largos):.0f} s) -> {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
