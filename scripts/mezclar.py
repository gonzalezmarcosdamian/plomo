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
  miden los ataques de grave de cada uno por separado y se reporta el desfase.
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
from plomo.mezcla_motor import SR, Plantilla, ataques_cerca, planificar, renderizar_tema  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEST = RAIZ / "postproduction" / "mixes"
LUFS_FINAL = -14.0
TECHO_DBTP = -1.0
FLAMEO_MAX_MS = 5.0
SALTO_MAX_DB = 2.0


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
    ataques, desfases = {}, {}
    for k in elegidos:
        c = plan[k]
        inicio, audio, lag, sin_eq = renderizar_tema(c, tempo, p)
        desfases[k] = round(lag * 1000, 1)
        a0 = inicio - int(ventana[0] * SR)
        i0, j0 = max(0, a0), max(0, -a0)
        largo = min(len(audio) - j0, n - i0)
        if largo > 0:
            mix[i0:i0 + largo] += audio[j0:j0 + largo]
        beats_mix = c.offset + c.tema.beats / c.factor
        ataques[k] = (beats_mix, ataques_cerca(sin_eq, inicio / SR, beats_mix)[0])
        print(f"  {k + 1:2d} renderizado (grilla corrida {desfases[k]:+.1f} ms)  {time.time() - t_arranque:5.0f} s",
              flush=True)

    # --- verificar: bombos juntos en los 8 compases antes de cada cambio
    compas = 240.0 / tempo
    chequeo = []
    for k in elegidos[:-1]:
        x = plan[k + 1].cambio_in
        ba, ta = ataques[k]
        bb, tb = ataques[k + 1]
        difs = []
        for b, t in zip(bb, tb):
            if x - 8 * compas <= b <= x and not np.isnan(t):
                j = int(np.argmin(np.abs(ba - b)))
                if not np.isnan(ta[j]):
                    difs.append((t - ta[j]) * 1000)
        flameo = float(np.median(np.abs(difs))) if difs else float("nan")
        chequeo.append({"cambio": f"{k + 1}->{k + 2}", "minuto": mmss(x), "flameo_ms": round(flameo, 1),
                        "ok": bool(flameo <= FLAMEO_MAX_MS)})

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
        cerca = (np.abs(tiempos - x) <= 24) & np.isfinite(curva)
        ch["salto_db"] = round(float(np.max(np.abs(curva[cerca] - referencia))), 1) if np.any(cerca) else float("nan")
        ch["ok"] = ch["ok"] and ch["salto_db"] <= SALTO_MAX_DB

    # --- master: -14 LUFS y true peak
    lufs = medidor.integrated_loudness(mix)
    mix *= 10 ** ((LUFS_FINAL - lufs) / 20)
    pico = float(np.abs(mix).max())
    if 20 * np.log10(pico) > TECHO_DBTP:
        mix *= 10 ** ((TECHO_DBTP - 0.3 - 20 * np.log10(pico)) / 20)
        print(f"  pico a {20 * np.log10(pico):.1f} dBFS: se bajo a {TECHO_DBTP - 0.3} (queda por debajo de -14 LUFS)")

    DEST.mkdir(parents=True, exist_ok=True)
    sufijo = f"_transicion_{a.transicion}" if a.transicion else ""
    salida = DEST / f"{a.set}_mix{sufijo}.wav"
    sf.write(salida, mix, SR, subtype="PCM_24")
    informe = {"set": a.set, "tempo": tempo, "plantilla": p.__dict__, "duracion_s": round(len(mix) / SR, 1),
               "plan": [{"tema": f"{c.tema.artista} - {c.tema.titulo}", "desde": round(c.desde, 2),
                         "cambio_in": c.cambio_in and round(c.cambio_in, 2), "hasta": round(c.hasta, 2),
                         "factor": round(c.factor, 5)} for c in plan],
               "desfase_grilla_ms": desfases, "transiciones": chequeo, "loudness_3s": informe_curva,
               "estructura": informe_estructura(temas, estructuras)}
    salida.with_suffix(".json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'cambio':>7} {'minuto':>7} {'bombos':>8} {'volumen':>8}")
    for ch in chequeo:
        print(f"{ch['cambio']:>7} {ch['minuto']:>7} {ch['flameo_ms']:>6.1f}ms {ch['salto_db']:>6.1f}dB  "
              f"{'ok' if ch['ok'] else 'REVISAR'}")
    print(f"\n-> {salida}  ({len(mix) / SR / 60:.1f} min, {time.time() - t_arranque:.0f} s)")


if __name__ == "__main__":
    main()
