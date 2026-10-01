# -*- coding: utf-8 -*-
"""Saca de un set grabado todo lo que la animacion necesita saber, cuadro por cuadro.

POR QUE
-------
El video del set es una animacion abstracta que ESCUCHA el audio (el DJ,
2026-09-28). Para que la sincronia sea exacta el video se renderiza fuera de
tiempo real, y eso pide tener de antemano, para cada cuadro, que esta sonando.
Separar el analisis del render deja probar looks sin volver a medir, y deja el
video como una receta: master + rasgos + shader = el mismo video, siempre.

QUE SACA
--------
Del master, por cuadro (0..1, normalizado contra el propio set):
- `bombo`   un pulso por golpe en la grilla del beat, con la fuerza del bombo real
            (cae 180 ms). En un breakdown sin bombo, se apaga solo.
- `bajo`    energia 40-250 Hz, suavizada 0.4 s.
- `cuerpo`  loudness de corto plazo (3 s). La forma del set.
- `aire`    energia > 6 kHz, suavizada 1 s. Cuando el DJ cierra un filtro, cae.
- `brillo`  ataques en > 4 kHz (hats, platillos), caida de 120 ms.
Los ataques se miden cada 5 ms y el pulso se sintetiza en el cuadro exacto.

Del video del telefono de esa misma tarde, la PALETA: cuatro colores por
momento (fondo, cielo, resplandor, brillo). No es el color medio del cuadro
—eso da un gris que se apaga hasta el negro—: es el cielo de la ventana, lo mas
calido de la franja del horizonte, y las luces del equipo cuando el sol ya se
fue. Se conserva el tono y se levanta la luz de cada rol para que se lea.

Del tracklist alineado, los TEMAS: que tema manda en cada cuadro, con un
fundido durante el blend, y los capitulos para la descripcion.

USO
---
    python scripts/video_rasgos.py --master <wav> --informe <json del master>
        --alineacion <json> --telefono <mov> --desfase-telefono 19.14 --nombre 2026-09-23
    -> data/video/<nombre>_rasgos.npz  y  data/video/<nombre>_capitulos.json
"""
from __future__ import annotations

import argparse
import colorsys
import json
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.ndimage import median_filter, uniform_filter1d
from scipy.signal import butter, find_peaks, sosfilt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "video"
FPS = 30
TASA_FINA = 200                  # mediciones por segundo para los ataques (5 ms)
PASO_TELEFONO_S = 2.0            # un cuadro del telefono cada 2 s alcanza para una paleta
SUAVIZADO_PALETA_S = 30.0        # el cielo cambia en minutos, no en segundos
FUNDIDO_TEMAS_S = 20.0
CIELO_MEDIBLE = 0.05             # por debajo, el "color" del cielo es ruido del sensor
LUZ_ROL = {"fondo": 0.09, "cielo": 0.42, "resplandor": 0.82, "brillo": 0.97}


def envolvente(x: np.ndarray, sr: int, lo: float | None, hi: float | None) -> np.ndarray:
    """RMS por cuadro de video en una banda."""
    if lo is None:
        sos = butter(4, hi, "lowpass", fs=sr, output="sos")
    elif hi is None:
        sos = butter(4, lo, "highpass", fs=sr, output="sos")
    else:
        sos = butter(4, [lo, hi], "bandpass", fs=sr, output="sos")
    y = sosfilt(sos, x)
    por_cuadro = sr // FPS
    n = len(y) // por_cuadro
    return np.sqrt((y[: n * por_cuadro].reshape(n, por_cuadro) ** 2).mean(1))


def normalizar(v: np.ndarray, p_lo: float = 5, p_hi: float = 98) -> np.ndarray:
    lo, hi = np.percentile(v, [p_lo, p_hi])
    return np.clip((v - lo) / (hi - lo + 1e-12), 0, 1)


def db_fino(x: np.ndarray, sr: int, lo: float | None, hi: float | None) -> np.ndarray:
    """Nivel en dB cada 5 ms. A 30 cuadros por segundo un ataque cae repartido entre dos
    cuadros y la mitad de las veces no pasa el umbral: medido, el bombo salia uno si y uno no."""
    sos = (butter(4, [lo, hi], "bandpass", fs=sr, output="sos") if hi
           else butter(4, lo, "highpass", fs=sr, output="sos"))
    y = sosfilt(sos, x)
    hop = sr // TASA_FINA
    n = len(y) // hop
    return 20 * np.log10(np.sqrt((y[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-7)


def sintetizar(tiempos: np.ndarray, fuerzas: np.ndarray, caida_s: float, n_cuadros: int) -> np.ndarray:
    """Un pulso por evento, en el cuadro exacto, con caida exponencial."""
    out = np.zeros(n_cuadros, dtype=np.float32)
    cola = np.exp(-np.arange(int(caida_s * FPS * 4)) / (caida_s * FPS))
    for t, f in zip(tiempos, fuerzas):
        i = int(round(t * FPS))
        tramo = out[i: i + len(cola)]
        np.maximum(tramo, f * cola[: len(tramo)], out=tramo)
    return out


def pulso_de_bombo(mono: np.ndarray, sr: int, n_cuadros: int) -> tuple[np.ndarray, np.ndarray]:
    """Pulso en la grilla del beat, con la fuerza del bombo real en cada golpe.

    Detectar ataques sueltos en 40-120 Hz mete las notas del bajo entre bombo y bombo
    (51 ataques en 20 s donde hay 40). La grilla nunca cae a destiempo; la fuerza de cada
    golpe es cuanto sube el grave respecto del valle anterior, por el nivel: en un
    breakdown sin bombo da cerca de cero y el pulso se apaga solo.
    """
    db = db_fino(mono, sr, 40, 120)
    flujo = np.convolve(np.maximum(np.diff(db, prepend=db[0]), 0), np.ones(3), "same")
    flujo = np.maximum(flujo - median_filter(flujo, TASA_FINA + 1), 0)
    _, beats = librosa.beat.beat_track(onset_envelope=flujo, sr=sr, hop_length=sr // TASA_FINA,
                                       start_bpm=120, tightness=400, units="frames")
    pico = np.array([db[max(0, f - 6): f + 12].max() for f in beats])            # -30..+60 ms
    valle = np.array([db[max(0, f - 40): max(1, f - 6)].min() for f in beats])   # -200..-30 ms
    subida = np.clip((pico - valle) / np.percentile(pico - valle, 90), 0, 1)
    fuerza = subida * normalizar(pico)
    tiempos = beats / TASA_FINA
    return sintetizar(tiempos, fuerza, 0.18, n_cuadros), np.stack([tiempos, fuerza]).astype(np.float32)


def pulso_de_brillo(mono: np.ndarray, sr: int, n_cuadros: int) -> np.ndarray:
    """Ataques de hats y platillos (> 4 kHz), sueltos: aca no hace falta grilla."""
    db = db_fino(mono, sr, 4000, None)
    flujo = np.convolve(np.maximum(np.diff(db, prepend=db[0]), 0), np.ones(3), "same")
    flujo = flujo - median_filter(flujo, TASA_FINA + 1)
    picos, prop = find_peaks(flujo, height=np.percentile(flujo, 90), distance=int(0.09 * TASA_FINA))
    fuerza = normalizar(prop["peak_heights"], 5, 95)
    return sintetizar(picos / TASA_FINA, fuerza, 0.12, n_cuadros)


def rasgos_de_audio(master: Path) -> tuple[dict[str, np.ndarray], np.ndarray]:
    x, sr = sf.read(master, dtype="float32", always_2d=True)
    mono = x.mean(1)
    bajo = envolvente(mono, sr, 40, 250)
    aire = envolvente(mono, sr, 6000, None)
    todo = envolvente(mono, sr, 30, None)
    n = len(todo)
    bombo, beats = pulso_de_bombo(mono, sr, n)
    return {
        "bombo": bombo,
        "bajo": normalizar(uniform_filter1d(bajo, int(0.4 * FPS))),
        "cuerpo": normalizar(20 * np.log10(uniform_filter1d(todo, 3 * FPS) + 1e-9)),
        "aire": normalizar(20 * np.log10(uniform_filter1d(aire, FPS) + 1e-9), 2, 98),
        "brillo": pulso_de_brillo(mono, sr, n),
    }, beats


def cuadros_del_telefono(video: Path) -> np.ndarray:
    """Un cuadro chico cada 2 s. Solo keyframes: decodificar el 4K60 entero son 40 minutos.
    Aun asi son dos minutos, asi que se guardan al lado de los rasgos y se reusan."""
    w, h = 96, 54
    cache = DEST / f"{video.stem}_{w}x{h}_cada{PASO_TELEFONO_S:g}s.npy"
    if cache.exists():
        return np.load(cache).astype(np.float32) / 255
    crudo = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-skip_frame", "nokey", "-i", str(video),
         "-vf", f"fps={1 / PASO_TELEFONO_S},scale={w}:{h}:flags=area",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    cuadros = np.frombuffer(crudo, dtype=np.uint8).reshape(-1, h, w, 3)
    DEST.mkdir(parents=True, exist_ok=True)
    np.save(cache, cuadros)
    return cuadros.astype(np.float32) / 255


def paleta_de_cuadro(img: np.ndarray) -> dict[str, np.ndarray | float]:
    h = img.shape[0]
    arriba = img[: int(h * 0.38)].reshape(-1, 3)
    abajo = img[int(h * 0.45):].reshape(-1, 3)
    luz_arr = arriba.mean(1)
    # el cielo es lo MAS AZUL de arriba, no lo mas brillante: lo brillante es el horizonte
    # y los reflejos, y con eso la paleta salia toda naranja
    azul = arriba[:, 2] - arriba[:, 0]
    cielo = arriba[azul >= np.percentile(azul, 95)].mean(0)
    calidez = (arriba[:, 0] - arriba[:, 2]) * (0.3 + luz_arr)
    horizonte = arriba[calidez >= np.percentile(calidez, 97)].mean(0)
    luz_ab = abajo.mean(1)
    luces = abajo[luz_ab >= np.percentile(luz_ab, 98)].mean(0)
    # el resplandor es lo que mas brilla entre el horizonte y las luces del equipo
    resplandor = horizonte if horizonte.mean() >= luces.mean() else luces
    return {"cielo": cielo, "resplandor": resplandor, "brillo": luces, "luz": float(luz_arr.mean())}


def levantar(rgb: np.ndarray, luz: float, sat_extra: float = 1.25) -> np.ndarray:
    """Mismo tono, saturacion un poco arriba, luz fija por rol."""
    hh, s, _ = colorsys.rgb_to_hsv(*np.clip(rgb, 1e-4, 1))
    return np.array(colorsys.hsv_to_rgb(hh, min(1.0, s * sat_extra), luz), dtype=np.float32)


def paleta(video: Path, n_cuadros: int, desfase_s: float) -> tuple[np.ndarray, np.ndarray]:
    """(n_cuadros, 4, 3) colores por cuadro del video final, y la luz del cielo medida (0..1)."""
    imgs = cuadros_del_telefono(video)
    crudas = [paleta_de_cuadro(im) for im in imgs]
    roles = np.stack([np.stack([c["cielo"], c["resplandor"], c["brillo"]]) for c in crudas])
    # de noche el cielo queda negro y su tono es ruido del sensor: se sostiene el ultimo
    # azul que se pudo medir
    medible = roles[:, 0].mean(1) >= CIELO_MEDIBLE
    ultimo = int(np.argmax(medible))
    for j in range(len(roles)):
        if medible[j]:
            ultimo = j
        else:
            roles[j, 0] = roles[ultimo, 0]
    luz = normalizar(np.array([c["luz"] for c in crudas]), 0, 100)
    k = int(SUAVIZADO_PALETA_S / PASO_TELEFONO_S)
    roles = uniform_filter1d(roles, k, axis=0, mode="nearest")
    luz = uniform_filter1d(luz, k, mode="nearest")
    t_tel = np.arange(len(imgs)) * PASO_TELEFONO_S
    t_video = np.arange(n_cuadros) / FPS + desfase_s    # segundo del telefono para cada cuadro
    idx = np.clip(np.searchsorted(t_tel, t_video), 0, len(t_tel) - 1)
    por_muestra = {}
    for j in np.unique(idx):
        cielo, resp, brillo = roles[j]
        oscurece = 0.55 + 0.45 * luz[j]      # el cielo baja con la noche, sin apagarse
        por_muestra[j] = np.stack([
            levantar(cielo, LUZ_ROL["fondo"] * oscurece, 2.2),
            levantar(cielo, LUZ_ROL["cielo"] * oscurece, 1.8),
            levantar(resp, LUZ_ROL["resplandor"]), levantar(brillo, LUZ_ROL["brillo"], 1.1)])
    pal = np.stack([por_muestra[j] for j in idx]).astype(np.float32)
    luz_video = np.interp(t_video, t_tel, luz)
    return pal, luz_video.astype(np.float32)


def temas(alineacion: list[dict], recorte_s: float, n_cuadros: int) -> tuple[np.ndarray, list[dict]]:
    """Peso de cada tema por cuadro (fundido en el blend) y los capitulos."""
    capitulos = []
    for k, a in enumerate(alineacion):
        ini = a["rec_desde_s"] - recorte_s
        if k > 0:   # el capitulo arranca en la mitad del blend
            ini = (alineacion[k - 1]["rec_hasta_s"] - recorte_s + ini) / 2
        capitulos.append({"t": round(max(0.0, ini), 1) if k else 0.0, "artista": a["artista"].strip(),
                          "titulo": a["titulo"].strip(), "tempo": a["ratio"]})
    t = np.arange(n_cuadros) / FPS
    bordes = [c["t"] for c in capitulos] + [t[-1] + 1]
    pesos = np.stack([((t >= bordes[k]) & (t < bordes[k + 1])) for k in range(len(capitulos))], 1)
    pesos = uniform_filter1d(pesos.astype(np.float32), int(FUNDIDO_TEMAS_S * FPS), axis=0, mode="nearest")
    return pesos / pesos.sum(1, keepdims=True), capitulos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--informe", help="el JSON que escribe pulir_master.py (grabaciones)")
    ap.add_argument("--alineacion", help="el tracklist alineado (grabaciones)")
    ap.add_argument("--mix", help="el JSON que escribe mezclar.py: reemplaza --informe y --alineacion")
    ap.add_argument("--telefono", required=True)
    ap.add_argument("--desfase-telefono", type=float, default=0.0,
                    help="segundos que la consola arranco ANTES que el telefono")
    ap.add_argument("--noche", action="store_true",
                    help="paleta fija del final del video del telefono: para un set nocturno")
    ap.add_argument("--nombre", required=True)
    a = ap.parse_args()

    if a.mix:
        # un mix armado no tiene recorte; cada tema arranca su capitulo en su cambio de bajos
        plan = json.loads(Path(a.mix).read_text(encoding="utf-8"))["plan"]
        recorte, alineacion = 0.0, []
        for k, c in enumerate(plan):
            artista, _, titulo = c["tema"].partition(" - ")
            cambio = c["cambio_in"] or 0.0
            sigue = plan[k + 1]["cambio_in"] if k + 1 < len(plan) else c["hasta"]
            alineacion.append({"artista": artista, "titulo": titulo, "ratio": c["factor"],
                               "rec_desde_s": cambio, "rec_hasta_s": sigue})
    elif a.informe and a.alineacion:
        recorte = json.loads(Path(a.informe).read_text(encoding="utf-8"))["recorte_inicio_s"]
        alineacion = json.loads(Path(a.alineacion).read_text(encoding="utf-8"))
    else:
        sys.exit("hace falta --mix, o --informe y --alineacion")
    audio, beats = rasgos_de_audio(Path(a.master))
    n = min(len(v) for v in audio.values())
    audio = {k: v[:n].astype(np.float32) for k, v in audio.items()}
    # segundo del telefono = segundo del master + recorte - desfase. Con --noche, todo cae
    # despues del final del video y la paleta queda fija en el ultimo cuadro: la noche.
    desfase = recorte - a.desfase_telefono + (10 ** 6 if a.noche else 0)
    pal, luz = paleta(Path(a.telefono), n, desfase)
    pesos, capitulos = temas(alineacion, recorte, n)

    DEST.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DEST / f"{a.nombre}_rasgos.npz", fps=FPS, paleta=pal, luz_cielo=luz,
                        temas=pesos, beats=beats, **audio)
    (DEST / f"{a.nombre}_capitulos.json").write_text(
        json.dumps({"fps": FPS, "duracion_s": n / FPS, "capitulos": capitulos}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{n} cuadros ({n / FPS / 60:.2f} min)")
    for c in capitulos:
        print(f"  {int(c['t'] // 60)}:{int(c['t'] % 60):02d}  {c['artista']} - {c['titulo']}")
    for k, v in audio.items():
        print(f"  {k:7s} media {v.mean():.2f}  p90 {np.percentile(v, 90):.2f}")
    print(f"-> {DEST / (a.nombre + '_rasgos.npz')}")


if __name__ == "__main__":
    main()
