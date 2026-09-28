# Archivado 2026-09-28: alinea los temas identificados contra la grabacion, fragmentos de 8 s
# cada 4 s. Los ratios de A New Beginning e In Space se corrigieron despues a mano (1.0088 y
# 1.0084, ajuste del agente mezclador): el resultado bueno es data/video/2026-09-23_alineacion.json.
"""Alinea cada tema identificado contra la grabacion: fragmentos de 8 s cada 4 s, mejor posicion y tempo."""
import sys, json
from pathlib import Path
import numpy as np, librosa
from scipy.ndimage import uniform_filter1d
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SP = Path(sys.argv[1]); ROOT = Path(r"C:\Users\gonza\Documents\plomo")
ident = {d["tit"].strip(): d for d in json.loads((SP / "ident3.json").read_text(encoding="utf-8"))}
TEMAS = ["Wait for Me (Original Mix)", "A New Beginning", "In Space", "Mindloop (Original Mix)"]
SR, HOP, NM, QS, PASO = 22050, 512, 48, 8.0, 4.0
fps = SR / HOP
def mel(y):
    return np.log(librosa.feature.melspectrogram(y=y, sr=SR, hop_length=HOP, n_mels=NM, fmax=10000) + 1e-6)
rec, _ = librosa.load(str(ROOT / "grabaciones/2026-09-23_set_consola_REC001.wav"), sr=SR, mono=True)
R = mel(rec); T = R.shape[1]; W = int(QS * fps)
mu = uniform_filter1d(R, W, axis=1, mode="nearest")
sd = np.sqrt(np.maximum(uniform_filter1d(R**2, W, axis=1, mode="nearest") - mu**2, 0))
sd = np.maximum(sd, 0.2 * np.median(sd, axis=1, keepdims=True)); Rn = (R - mu) / sd
NF = 1 << int(np.ceil(np.log2(T + 2 * W))); FR = np.fft.rfft(Rn, n=NF, axis=1)
def corr(Q):
    L = Q.shape[1]; Qn = (Q - Q.mean(1, keepdims=True)) / (Q.std(1, keepdims=True) + 1e-6)
    full = np.fft.irfft((FR * np.fft.rfft(Qn[:, ::-1], n=NF, axis=1)).sum(0), n=NF)
    return full[L-1:L-1+T-L+1] / (L * NM)
salida = []
for tit in TEMAS:
    d = ident[tit]; y, _ = librosa.load(d["fp"], sr=SR, mono=True); M = mel(y); n = M.shape[1]
    # tempo: el ratio que mejor puntua en los fragmentos buenos
    ratios = [e["ratio"] for e in d["exc"] if e["score"] > 0.75] or [1.0]
    r = float(np.median(ratios))
    pts = []
    for s in np.arange(0, n / fps - QS, PASO):
        Q0 = M[:, int(s*fps): int(s*fps) + W]; L = int(round(Q0.shape[1] / r))
        Q = np.stack([np.interp(np.linspace(0, Q0.shape[1]-1, L), np.arange(Q0.shape[1]), Q0[b]) for b in range(NM)])
        c = corr(Q); j = int(np.argmax(c)); pts.append((float(s), j / fps, float(c[j])))
    pts = np.array(pts)
    # linea rec = a + track/r con los puntos fuertes; RANSAC simple sobre a
    fuertes = pts[pts[:, 2] > 0.6]
    a_cands = fuertes[:, 1] - fuertes[:, 0] / r
    best_a, best_n = 0, 0
    for a in a_cands:
        k = np.sum(np.abs(a_cands - a) < 0.5)
        if k > best_n: best_a, best_n = a, k
    enlinea = pts[np.abs(pts[:, 1] - (best_a + pts[:, 0] / r)) < 0.5]
    enlinea = enlinea[enlinea[:, 2] > 0.45]
    t_ini, t_fin = enlinea[:, 0].min(), enlinea[:, 0].max() + QS
    salida.append({"titulo": tit, "artista": d["art"], "fp": d["fp"], "largo_s": d["len"], "ratio": r,
                   "offset_rec_s": float(best_a), "track_desde_s": float(t_ini), "track_hasta_s": float(t_fin),
                   "rec_desde_s": float(best_a + t_ini / r), "rec_hasta_s": float(best_a + t_fin / r),
                   "puntos_en_linea": int(len(enlinea)), "puntos": pts.round(2).tolist()})
    print(f"{d['art']} - {tit}: ratio {r}  suena del {t_ini/60:.2f}m al {t_fin/60:.2f}m del tema  ->  "
          f"grabacion {(best_a + t_ini/r)/60:.2f}m a {(best_a + t_fin/r)/60:.2f}m  ({len(enlinea)} puntos en linea de {len(pts)})", flush=True)
(SP / "alineacion.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
