# Archivado 2026-09-28: identifico los temas de grabaciones/2026-09-23_set_consola_REC001.wav
# (mel + busqueda de tempo contra 615 candidatos). Uso: python <este> <carpeta de salida>.
# Ver docs/APRENDIZAJES.md "Un tema se reconoce en una mezcla por su coherencia".
"""Identifica los temas de la grabacion: mel normalizado localmente + correlacion en frecuencia + busqueda de tempo."""
import sys, json, re, time
from pathlib import Path
from urllib.parse import quote
import numpy as np, librosa
from scipy.ndimage import uniform_filter1d
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\gonza\Documents\plomo"); SP = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "src"))
import sqlcipher3
from plomo import config
uri = "file:///" + quote(str(config.REKORDBOX_DB_PATH).replace("\\", "/")) + "?mode=ro"
con = sqlcipher3.connect(uri, uri=True, timeout=5)
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
cands = {}
q1 = """select distinct a.Name, c.Title, c.FolderPath, c.Length from djmdHistory h
       join djmdSongHistory sh on sh.HistoryID = h.ID join djmdContent c on c.ID = sh.ContentID
       left join djmdArtist a on a.ID = c.ArtistID where h.DateCreated >= '2026-09-10'"""
q2 = """select distinct a.Name, c.Title, c.FolderPath, c.Length, p.Name from djmdPlaylist p
       join djmdSongPlaylist sp on sp.PlaylistID = p.ID join djmdContent c on c.ID = sp.ContentID
       left join djmdArtist a on a.ID = c.ArtistID"""
for art, tit, fp, ln in con.execute(q1): cands.setdefault(fp, (art, tit, ln))
for art, tit, fp, ln, pn in con.execute(q2):
    m = re.match(r"\s*(\d+)\.", pn or "")
    if m and 130 <= int(m.group(1)) <= 149: cands.setdefault(fp, (art, tit, ln))
print(len(cands), "candidatos", flush=True)

SR, HOP, NM, QS = 22050, 1024, 48, 16.0
fps = SR / HOP
def mel(y):
    M = librosa.feature.melspectrogram(y=y, sr=SR, hop_length=HOP, n_mels=NM, fmax=10000)
    return np.log(M + 1e-6)
rec, _ = librosa.load(str(ROOT / "grabaciones/2026-09-23_set_consola_REC001.wav"), sr=SR, mono=True)
R = mel(rec); T = R.shape[1]
W = int(QS * fps)
mu = uniform_filter1d(R, W, axis=1, mode="nearest")
sd = np.sqrt(np.maximum(uniform_filter1d(R**2, W, axis=1, mode="nearest") - mu**2, 0))
sd = np.maximum(sd, 0.2 * np.median(sd, axis=1, keepdims=True))
Rn = (R - mu) / sd
rms = librosa.feature.rms(y=rec, frame_length=2048, hop_length=HOP)[0][:T]
vivo = uniform_filter1d((20*np.log10(rms+1e-9) > -45).astype(float), W) > 0.9
NF = 1 << int(np.ceil(np.log2(T + 2 * W)))
FR = np.fft.rfft(Rn, n=NF, axis=1)
def corr(Q):
    L = Q.shape[1]
    Qn = (Q - Q.mean(1, keepdims=True)) / (Q.std(1, keepdims=True) + 1e-6)
    FQ = np.fft.rfft(Qn[:, ::-1], n=NF, axis=1)
    full = np.fft.irfft((FR * FQ).sum(0), n=NF)
    c = full[L-1:L-1+T-L+1] / (L * NM)
    centro = np.minimum(np.arange(len(c)) + L//2, T-1)
    c[~vivo[centro]] = -1
    return c
def excerpt(fp, ln, frac):
    y, _ = librosa.load(fp, sr=SR, mono=True, offset=ln*frac, duration=QS)
    return mel(y)
def buscar(Q0, ratios):
    best = (-1.0, 0.0, 1.0)
    for r in ratios:
        L = int(round(Q0.shape[1] / r))
        x0 = np.linspace(0, Q0.shape[1]-1, L)
        Q = np.stack([np.interp(x0, np.arange(Q0.shape[1]), Q0[b]) for b in range(NM)])
        cc = corr(Q); j = int(np.argmax(cc))
        if cc[j] > best[0]: best = (float(cc[j]), j / fps, float(r))
    return best
t0 = time.time()
etapa1 = []
for i, (fp, (art, tit, ln)) in enumerate(cands.items()):
    try: Q = excerpt(fp, ln, 0.5)
    except Exception as e: print("ERR", art, tit, e, flush=True); continue
    s, pos, r = buscar(Q, np.round(np.arange(0.97, 1.031, 0.01), 3))
    etapa1.append((s, pos, r, fp, art, tit, ln))
    if i % 50 == 0: print(f"{i}/{len(cands)} {time.time()-t0:.0f}s", flush=True)
etapa1.sort(key=lambda t: -t[0])
print("---- etapa 1 (top 40)", flush=True)
for s, pos, r, fp, art, tit, ln in etapa1[:40]:
    print(f"{s:.3f} @{pos/60:6.2f}m r{r}  {art} - {tit}", flush=True)
print("mediana etapa1 %.3f  p90 %.3f" % (np.median([e[0] for e in etapa1]), np.percentile([e[0] for e in etapa1], 90)), flush=True)
fin = []
for s1, pos1, r1, fp, art, tit, ln in etapa1[:40]:
    exc = []
    for frac in (0.25, 0.4, 0.55, 0.7, 0.85):
        s, pos, r = buscar(excerpt(fp, ln, frac), np.round(np.arange(0.97, 1.0301, 0.005), 3))
        exc.append({"frac": frac, "track_s": ln*frac, "score": s, "rec_s": pos, "ratio": r})
    # posicion implicita del inicio del tema en la grabacion segun cada fragmento
    for e in exc: e["inicio_rec_s"] = e["rec_s"] - e["track_s"] / e["ratio"]
    buenos = [e for e in exc if e["score"] > 0.3]
    fin.append({"art": art, "tit": tit, "fp": fp, "len": ln, "exc": exc, "n_buenos": len(buenos),
                "inicio_rec_s": float(np.median([e["inicio_rec_s"] for e in buenos])) if buenos else None,
                "dispersion_s": float(np.std([e["inicio_rec_s"] for e in buenos])) if len(buenos) > 1 else None})
fin.sort(key=lambda d: (d["inicio_rec_s"] if d["inicio_rec_s"] is not None else 1e9))
(SP / "ident3.json").write_text(json.dumps(fin, ensure_ascii=False, indent=1), encoding="utf-8")
print("---- etapa 2 (ordenado por inicio implicito)")
for d in fin:
    ini = "   -   " if d["inicio_rec_s"] is None else f"{d['inicio_rec_s']/60:6.2f}m"
    disp = "" if d["dispersion_s"] is None else f"±{d['dispersion_s']:.1f}s"
    print(f"{ini} {disp:>8} buenos {d['n_buenos']}/5  {d['art']} - {d['tit']}  " + " ".join(f"{e['score']:.2f}@{e['rec_s']/60:.1f}" for e in d["exc"]))
print(f"total {time.time()-t0:.0f}s")
