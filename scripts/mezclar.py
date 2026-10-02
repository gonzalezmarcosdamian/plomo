# -*- coding: utf-8 -*-
"""Mezcla un set de Rekordbox de punta a punta, con la tecnica del DJ, y verifica lo que sale.

POR QUE
-------
"Dale el 148, hacelo completo" (el DJ, 2026-10-01). No es un set tocado: es un mix
armado en estudio con el orden, los temas y la forma de mezclar del DJ, medida en
su grabacion de consola (ver `plomo.mezcla_motor`). Lo escucha el antes de que se
publique nada.

QUE VERIFICA (y reporta tambien cuando sale bien)
------------------------------------------------
- Bombos juntos: en los 8 compases antes de cada cambio suenan los dos temas; se
  correlacionan los ataques de cada uno por separado y se reporta el desfase.
  Mas de 5 ms se escucha como bombo doble.
- Volumen parejo: loudness de corto plazo alrededor de cada cambio contra el cuerpo
  de los temas. Un salto de mas de 2 dB se nota.
- Estructura contra cues: lo medido compas por compas contra los cues de Rekordbox.

USO
---
    python scripts/mezclar.py 148                       # el set entero
    python scripts/mezclar.py 148 --transicion 3        # solo el cambio del 3 al 4, para escuchar
    python scripts/mezclar.py 148 --tempo 123
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from plomo.mezcla import en_compases, leer_set, medir  # noqa: E402
from plomo.mezcla_motor import SR, Plantilla, masterizar, planificar, renderizar_tema  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEST = RAIZ / "postproduction" / "mixes"
LUFS_FINAL = -14.0
TECHO_DBTP = -1.0
FLAMEO_MAX_MS = 5.0
SALTO_MAX_DB = 2.0
POZO_DB = (-12.0, -2.0)        # el pozo del cambio de bajos; el del DJ es de -3 a -10
DOBLE_BAJO_MAX_DB = 3.0        # el grave antes del cambio no sube: nunca dos bajos llenos

GOLPE = (1000.0, 8000.0)   # el click: lo que marca la grilla y lo que tiene que coincidir
# el cuerpo grave NO se verifica por correlacion: en esa banda estan tambien las lineas de bajo
# de los dos temas y la correlacion encuentra cualquier pico (dio 47 ms donde el golpe daba 1)


def envolvente_de_ataques(audio: np.ndarray, t0: float, desde: float, hasta: float,
                          banda: tuple[float, float]) -> np.ndarray:
    """Subida de la envolvente en una banda, a 1 ms, en un tramo del mix."""
    i, j = int((desde - t0) * SR), int((hasta - t0) * SR)
    x = sosfilt(butter(2, banda, "bandpass", fs=SR, output="sos"), audio[max(0, i):max(0, j)].mean(1))
    env = np.abs(x)[: (len(x) // 44) * 44].reshape(-1, 44).mean(1)            # 1 ms
    return np.maximum(np.diff(env, prepend=env[:1]), 0)


def desfase_entre(a: tuple[np.ndarray, float], b: tuple[np.ndarray, float], desde: float, hasta: float,
                  banda: tuple[float, float] = GOLPE) -> float:
    """Milisegundos que B va corrido respecto de A: el pico de la correlacion de sus ataques (+-50 ms).

    En la grabacion del DJ (agente `bajo`, 2026-09-28) los golpes le quedan a 4.5-6.6 ms y los
    cuerpos graves a 10-20 ms, por el diseno distinto de cada bombo: se verifica el golpe.
    """
    ea, eb = envolvente_de_ataques(*a, desde, hasta, banda), envolvente_de_ataques(*b, desde, hasta, banda)
    n = min(len(ea), len(eb))
    ea, eb = ea[:n] - ea[:n].mean(), eb[:n] - eb[:n].mean()
    lags = np.arange(-50, 51)
    corr = [np.dot(ea[max(0, -lag): n - max(0, lag)], eb[max(0, lag): n - max(0, -lag)]) for lag in lags]
    return float(lags[int(np.argmax(corr))])


def salto_de_nivel(tiempos: np.ndarray, curva: np.ndarray, plan, k: int) -> dict:
    """Si un tema entra mas alto o mas bajo que el otro, o si el blend se va de nivel.

    El nivel de cada tema es el de su parte FUERTE mientras suena SOLO: el percentil 70 del
    loudness de 3 s entre que se fue el anterior y entra el siguiente. Dos definiciones
    anteriores median otra cosa: ventanas sueltas (caian en fills del arreglo) y "los 90 s
    antes de que entre el otro" (caian en el breakdown del saliente).
    """
    def solo(j: int) -> np.ndarray:
        d = plan[j - 1].hasta + 3 if j > 0 else plan[j].desde + 20
        h = plan[j + 1].desde - 3 if j + 1 < len(plan) else plan[j].hasta - 20
        return curva[(tiempos > d) & (tiempos < h) & np.isfinite(curva)]
    a, b = plan[k], plan[k + 1]
    na, nb = solo(k), solo(k + 1)
    en_blend = (tiempos > b.desde) & (tiempos < a.hasta) & np.isfinite(curva) & (np.abs(tiempos - b.cambio_in) > 3)
    blend = curva[en_blend]
    if not (len(na) and len(nb) and len(blend)):
        return {"salto_db": float("nan"), "blend_db": float("nan")}
    ca, cb, cl = np.percentile(na, 70), np.percentile(nb, 70), np.percentile(blend, 70)
    return {"salto_db": round(float(abs(cb - ca)), 1), "blend_db": round(float(cl - (ca + cb) / 2), 1)}


def pozo_de_grave(mix: np.ndarray, t0: float, x: float) -> tuple[float, float]:
    """El grave (< 90 Hz) alrededor del cambio, contra el cuerpo del entrante despues.

    Devuelve (el nivel en los 3 s del cambio, el percentil 95 de los 60 s previos), en dB. En
    la grabacion del DJ el pozo es de -3 a -10 dB; mas hondo es un agujero. Si el grave antes
    del cambio sube mucho, suenan dos bajos llenos a la vez.
    """
    # ventanas de 1 s que se corren de a 0.25: siempre contienen dos golpes. Con ventanas de
    # 0.5 s el nivel alternaba entre golpe y hueco (+3/-8 dB) y el "pozo" era el peor hueco
    # entre dos bombos (-15.7) en vez del nivel del cambio (-7.8)
    ancho, salto = SR, SR // 4
    a, b = max(0, int((x - 60 - t0) * SR)), max(0, int((x + 30 - t0) * SR))
    sub = sosfilt(butter(4, 90, "lowpass", fs=SR, output="sos"), mix[a:b].mean(1))
    acumulado = np.concatenate([[0.0], np.cumsum(sub.astype(np.float64) ** 2)])
    inicios = np.arange(0, len(sub) - ancho, salto)
    db = 10 * np.log10((acumulado[inicios + ancho] - acumulado[inicios]) / ancho + 1e-18)
    t = a / SR + t0 + (inicios + ancho / 2) / SR
    ref = np.median(db[(t > x + 10) & (t < x + 30)])
    # el nivel DURANTE el cambio (3 s), que es lo que se midio en la grabacion del DJ
    # ("-8 a -10 dB durante unos 3 s"); el fondo de un solo segundo es otra medida
    cerca = db[np.abs(t - x) <= 1.5] - ref
    antes = db[(t > x - 60) & (t < x - 6)] - ref
    return round(float(np.median(cerca)), 1), round(float(np.percentile(antes, 95)), 1)


def informe_estructura(temas, estructuras) -> list[dict]:
    filas = []
    for t, e in zip(temas, estructuras):
        cue = {k: round(en_compases(t, v), 1) for k, v in t.cues.items()}
        filas.append({"tema": f"{t.artista} - {t.titulo}", "bpm": t.bpm, "medido": {
            "bass_in": e.bass_in, "breakdown": e.breakdown, "drop": e.drop, "mix_out": e.mix_out(),
            "fin_bombo": e.fin_bombo}, "crudo": e.crudo, "cues_en_compases": cue})
    return filas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("set", help="el numero de la playlist, ej. 148")
    ap.add_argument("--tempo", type=float, help="por defecto, la mediana del set")
    ap.add_argument("--transicion", type=int, help="renderiza solo el cambio del tema N al N+1 (1 = primero)")
    a = ap.parse_args()

    t_arranque = time.time()
    # que Windows no suspenda mientras mezcla: el reposo moderno corto un render el 2026-10-02
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    temas = leer_set(a.set)
    print(f"{len(temas)} temas del {a.set}; midiendo la estructura...", flush=True)
    estructuras = [medir(t) for t in temas]
    tempo = a.tempo or float(np.median([t.bpm for t in temas]))
    p = Plantilla()
    plan = planificar(temas, estructuras, tempo, p)

    print(f"\ntempo {tempo:.2f} BPM\n{'#':>2} {'entra':>7} {'cambio':>7} {'sale':>7}  estira  tema")
    mmss = lambda s: f"{int(s // 60)}:{int(s % 60):02d}" if s is not None else "   -"
    for i, c in enumerate(plan, 1):
        print(f"{i:2d} {mmss(c.desde):>7} {mmss(c.cambio_in):>7} {mmss(c.hasta):>7}  {(c.factor - 1) * 100:+5.2f}%  "
              f"{c.tema.artista} - {c.tema.titulo}")
    print(f"duracion del mix: {mmss(plan[-1].hasta)}")

    if a.transicion:
        k = a.transicion - 1
        if not 0 <= k < len(plan) - 1:
            sys.exit(f"--transicion va de 1 a {len(plan) - 1}")
        elegidos = [k, k + 1]
        ventana = (plan[k + 1].desde - 8, plan[k].hasta + 8)
    else:
        elegidos = list(range(len(plan)))
        ventana = (0.0, plan[-1].hasta)

    n = int((ventana[1] - ventana[0]) * SR) + SR
    mix = np.zeros((n, 2), dtype=np.float32)
    compas = 240.0 / tempo
    tramos, desfases, empujes = {}, {}, {}
    arrastre = 0.0              # lo que se empujo a los anteriores se arrastra a los siguientes
    for k in elegidos:
        c = plan[k]
        inicio, audio, lag, sin_eq = renderizar_tema(c, tempo, p)
        desfases[k] = round(lag * 1000, 1)
        inicio += int(round(arrastre * SR))
        if k - 1 in tramos:
            # el empujon al plato: el entrante se engancha con el saliente en los 8 compases
            # previos al cambio. Corregir cada tema contra su grilla no alcanza: en Adrift y
            # Fogbows el primer ataque no es el bombo y la grilla queda 14 ms corrida
            x = plan[k].cambio_in
            empuje = desfase_entre(tramos[k - 1], (sin_eq, inicio / SR), x - 8 * compas, x) / 1000
            inicio -= int(round(empuje * SR))
            arrastre -= empuje
            empujes[k] = round(empuje * 1000, 1)
        a0 = inicio - int(ventana[0] * SR)
        i0, j0 = max(0, a0), max(0, -a0)
        largo = min(len(audio) - j0, n - i0)
        if largo > 0:
            mix[i0:i0 + largo] += audio[j0:j0 + largo]
        tramos[k] = (sin_eq, inicio / SR)
        print(f"  {k + 1:2d} renderizado (grilla {desfases[k]:+.1f} ms, empujon {empujes.get(k, 0):+.1f} ms)"
              f"  {time.time() - t_arranque:5.0f} s", flush=True)

    # --- verificar: bombos juntos, en TRES ventanas que no se tocan. El empujon se calculo en
    # los 8 compases previos al cambio; medir solo ahi seria medir contra el propio paso. Si el
    # enganche es real, tiene que sostenerse antes, justo antes y despues del cambio.
    chequeo = []
    for k in elegidos[:-1]:
        x = plan[k + 1].cambio_in
        ventanas = [(x - 8 * compas, x - 4 * compas), (x - 4 * compas, x), (x, x + 4 * compas)]
        lags = [desfase_entre(tramos[k], tramos[k + 1], d, h) for d, h in ventanas]
        flameo = max(abs(v) for v in lags)
        pozo, doble = pozo_de_grave(mix, ventana[0], x)
        chequeo.append({"cambio": f"{k + 1}->{k + 2}", "minuto": mmss(x), "flameo_ms": round(flameo, 1),
                        "ventanas_ms": lags, "empujon_ms": empujes.get(k + 1, 0.0),
                        "pozo_db": pozo, "doble_bajo_db": doble,
                        "ok": bool(flameo <= FLAMEO_MAX_MS and POZO_DB[0] <= pozo <= POZO_DB[1]
                                   and doble <= DOBLE_BAJO_MAX_DB)})

    # --- volumen parejo alrededor de cada cambio: contra el cuerpo, lejos de los cambios
    medidor = pyln.Meter(SR)

    def corto(t: float) -> float:
        i, j = int((t - ventana[0]) * SR), int((t - ventana[0] + 3) * SR)
        if i < 0 or j > len(mix):
            return float("nan")
        v = medidor.integrated_loudness(mix[i:j])
        return v if np.isfinite(v) else float("nan")

    tiempos = np.arange(ventana[0] + 1, ventana[1] - 4, 3.0)
    curva = np.array([corto(t) for t in tiempos])
    cambios = np.array([plan[int(ch["cambio"].split("->")[0])].cambio_in for ch in chequeo])
    lejos = np.all(np.abs(tiempos[:, None] - cambios[None, :]) > 30, axis=1) if len(cambios) else np.ones_like(tiempos, bool)
    informe_curva = [(round(float(x), 1), None if np.isnan(v) else round(float(v), 1)) for x, v in zip(tiempos, curva)]
    referencia = float(np.nanmedian(curva[lejos])) if np.any(lejos & np.isfinite(curva)) else float(np.nanmedian(curva))
    for ch, x in zip(chequeo, cambios):
        k = int(ch["cambio"].split("->")[0]) - 1
        ch.update(salto_de_nivel(tiempos, curva, plan, k))
        ch["ok"] = ch["ok"] and ch["salto_db"] <= SALTO_MAX_DB and abs(ch["blend_db"]) <= SALTO_MAX_DB

    # --- master: -14 LUFS, picos sueltos al limitador, true peak verificado. `masterizar`
    # levanta un error si no cumple, y el archivo se escribe DESPUES: el 2026-10-01 un master
    # sin verificar piso el mix bueno con uno a -2 LUFS
    mix, master = masterizar(mix, LUFS_FINAL, TECHO_DBTP)
    print(f"  master: {master}")

    DEST.mkdir(parents=True, exist_ok=True)
    sufijo = f"_transicion_{a.transicion}" if a.transicion else ""
    salida = DEST / f"{a.set}_mix{sufijo}.wav"
    sf.write(salida, mix, SR, subtype="PCM_24")
    informe = {"set": a.set, "tempo": tempo, "plantilla": p.__dict__, "duracion_s": round(len(mix) / SR, 1),
               "plan": [{"tema": f"{c.tema.artista} - {c.tema.titulo}", "desde": round(c.desde, 2),
                         "cambio_in": c.cambio_in and round(c.cambio_in, 2), "hasta": round(c.hasta, 2),
                         "factor": round(c.factor, 5)} for c in plan],
               "desfase_grilla_ms": desfases, "empujones_ms": empujes, "master": master, "transiciones": chequeo, "loudness_3s": informe_curva,
               "estructura": informe_estructura(temas, estructuras)}
    salida.with_suffix(".json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'cambio':>7} {'minuto':>7} {'golpe':>8} {'volumen':>8} {'pozo':>7} {'2 bajos':>8}")
    for ch in chequeo:
        print(f"{ch['cambio']:>7} {ch['minuto']:>7} {ch['flameo_ms']:>6.1f}ms {ch['salto_db']:>6.1f}dB "
              f"{ch['pozo_db']:>5.1f}dB {ch['doble_bajo_db']:>6.1f}dB  {'ok' if ch['ok'] else 'REVISAR'}")
    print(f"\n-> {salida}  ({len(mix) / SR / 60:.1f} min, {time.time() - t_arranque:.0f} s)")


if __name__ == "__main__":
    main()
