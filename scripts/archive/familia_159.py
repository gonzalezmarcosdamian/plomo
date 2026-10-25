# -*- coding: utf-8 -*-
"""Reemplaza lugares del set 159 por "la familia de los que van quedando".

POR QUE
-------
El DJ escucha el 159 de a poco y va nombrando temas: "cambia el primero por algun
parecidos a estos. Para adelante te voy a ir indicando cambios y reemplazas por la
familia de los que van quedando" (2026-10-25). Rearmar con select_set cambiaria lo
que ya aprobo; reemplazar.py mira solo a los vecinos, y en el 157 eso metio temas
lejanos que el DJ saco. Aca el candidato se mide contra LOS APROBADOS.

QUE ES LA FAMILIA (data/set_configs/159_work_organic_brillo.json -> _escucha.aprobados)
  forma    distancia media a los aprobados en los rasgos de parecido_forma.py
           (breakdown, drop, secciones, sub/medio/aire, rango dinamico)
  groove   distancia a la mediana de los aprobados en densidad y graves (groove_index)
  color    diferencia con el color mediano de los aprobados (x3)
  nombres  -0.5 si comparte sello con un aprobado, -0.5 si comparte artista o remixer.
           Medio punto y no uno: el SONIDO manda y el nombre desempata. Con -1 el #6 de la
           v2 lo ganaba Distant Blips (Univack, progressive, breakdown 0.31) solo por nombre,
           contra The Observer, mas cerca en forma, groove, color y breakdown (leccion del
           157: lo que sumo yo se ordena por parecido con lo del DJ)
  ajeno    +1 si ni artista ni sello aparecen en lo que el DJ toco (mundo_propio)
  menor puntaje = mas de la familia.

DURO (sin esto no entra)
  - data/pool_159.json: organic + orbita con brillo (ver pool_159_2026-10-25.py)
  - sin veto, no esta en el set, no salio en una escucha (_escucha.cambiados), no esta
    en el 158 (repetidos_entre_sets_consecutivos = 0)
  - mezcla con los vecinos: rueda <= max_camelot del config, BPM <= max_bpm_jump
  - energia dentro de e_pool; el que abre no pasa al segundo, los demas a +-1.0 del
    promedio de sus vecinos
  - topes de 4 por artista (contando remixer) y 4 por sello, sin el tema que sale
  - voz: data/voces.json. 'cantado' no entra, ni presencia de voz > 45% (VOZ_MAX); 'sin medir'
    se mide con --medir.

LEJOS DE LO OSCURO (v4, 2026-10-25: "The observer tambien muy oscuro para este set aprende
cambia" / "Hymnotize lo mismo y cambia")
  Lo que se aprendio, medido sobre la capa melodica (stem `other` de Demucs, 30 s al 45% del
  tema, el mismo fragmento que la voz; data/capa_melodica.json):
    centroide   de la capa melodica, en Hz
    medio_1_4k  fraccion de su energia entre 1 y 4 kHz
  En el 159: los 6 aprobados dan centroide 533-765 Hz y 1-4 kHz 0.078-0.212; los dos que el
  DJ llamo oscuros, 303 y 379 Hz y 0.022 y 0.028. Fuera del 159, la ZONA OSCURA (centroide
  < 400 Hz o 1-4 kHz < 0.035) la tienen 3 de los 8 temas que el DJ llamo oscuros en otros sets
  (Low Era, Shades Of Blue, Emerge) y 3 de los 40 que aprobo (el 150 y sus favoritos). O sea:
  es UN tipo de oscuro --la melodia abajo--, no todos; los otros 5 oscuros son otra cosa.
  Descartado al medir: 'bajo' del balance y medio/aire (estilo.oscuro_del_dj) separaban a los
  2 oscuros de los aprobados del 159 pero no fuera (P(oscuro<aprobado) 0.45 y 0.53 sobre 8
  contra 40), y la densidad dejo de separar en cuanto se sumaron Ouverture y Spring Embers.
  Como se usa:
    zona oscura (centroide < 400 o 1-4k < 0.035)             -> no entra
    debajo de los aprobados (centroide o 1-4k < su minimo)    -> +2 por medida
  'SIN CAPA' = falta medir: --medir mide voz y capa del mismo stem.

Uso:
    python scripts/archive/familia_159.py --posiciones 1              # ranking
    python scripts/archive/familia_159.py --posiciones 1 --medir 8    # mide la voz de los 8 primeros sin medir
    python scripts/archive/familia_159.py --poner 1=<content_id>      # escribe el target
Despues: build_set.py 159, spotify_sync.py 159, spotify_validar.py 159.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from parecido_forma import RASGOS, rasgos  # noqa: E402
from plomo.camelot import distance  # noqa: E402
from plomo.rules import R  # noqa: E402
from plomo.tocados import etiqueta  # noqa: E402
from select_set import VETO_TRACKS, _minus, names  # noqa: E402

D = RAIZ / "data"
CFG_F = D / "set_configs" / "159_work_organic_brillo.json"
TARGET_F = D / "set_targets" / "set_159.json"
CAPA_F = D / "capa_melodica.json"
# "sin voz" en este set: el coordinador descarto Whale Voices en la v3 por 'algo de voz' al 53%;
# el aprobado con mas voz es Rogelito, 30%
VOZ_MAX = 0.45
ZONA_CENTROIDE = 400.0   # Hz: los dos oscuros del 159 dan 303 y 379; el aprobado mas bajo, 533
ZONA_1_4K = 0.035        # los dos oscuros 0.022 y 0.028; el aprobado mas bajo, 0.078
TOPE_ART = R.get("repeticion.max_por_artista_en_set")
TOPE_SELLO = R.get("repeticion.max_por_sello_en_set")


def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def cargar() -> dict:
    cfg = _j(CFG_F)
    spec = cfg["sets"][0]
    pool = {t["id"]: t for t in _j(D / "pool_159.json")}
    perc = _j(D / "energia_percibida.json")
    for i, t in pool.items():
        if "E" in perc.get(i, {}):
            t["energy"] = perc[i]["E"]
    g = _j(D / "groove_index.json")
    forma = {}
    for i in pool:
        f = D / "recetas" / "lib" / f"{i}.json"
        if f.exists():
            x = rasgos(_j(f))
            if x:
                forma[i] = x
    desv = {k: (st.pstdev(v[k] for v in forma.values()) or 1.0) for k in RASGOS}
    mundo = _j(D / "mundo_propio.json")
    t158 = D / "set_targets" / "set_158.json"
    return {"spec": spec, "esc": spec.get("_escucha", {}), "pool": pool, "groove": g,
            "forma": forma, "desv": desv, "voz": _j(D / "voces.json")["tracks"],
            "mundo": (set(mundo["artistas"]), set(mundo["sellos"])),
            "set": [t["content_id"] for t in _j(TARGET_F)["tracks"]],
            "capa": _j(CAPA_F)["tracks"] if CAPA_F.exists() else {},
            "s158": {t["content_id"] for t in _j(t158)["tracks"]} if t158.exists() else set()}


def _sello(t: dict) -> str:
    return (t.get("label") or "").strip().lower()


def puntaje(c: str, fam: list[str], X: dict) -> dict:
    pool, g, forma, desv = X["pool"], X["groove"], X["forma"], X["desv"]
    t = pool[c]
    fd = [math.sqrt(sum(((forma[c][k] - forma[a][k]) / desv[k]) ** 2 for k in RASGOS))
          for a in fam if a in forma and c in forma]
    d_forma = st.mean(fd) if fd else 3.0
    sd = g["desvios"]
    gr = {i: (v[0] / sd[0], v[1] / sd[1]) for i, v in g["tracks"].items()}
    fam_g = [gr[a] for a in fam if a in gr]
    if c in gr and fam_g:
        med = (st.median(x[0] for x in fam_g), st.median(x[1] for x in fam_g))
        d_groove = math.dist(gr[c], med)
    else:
        d_groove = 1.5
    col = g["color_pct"]
    d_color = abs(col.get(c, 0.5) - st.median(col.get(a, 0.5) for a in fam))
    sellos = {_sello(pool[a]) for a in fam}
    gente = set().union(*(names(pool[a]["artist"], pool[a]["title"]) for a in fam))
    b_sello = -0.5 if _sello(t) in sellos else 0.0
    b_gente = -0.5 if names(t["artist"], t["title"]) & gente else 0.0
    art = {a.strip() for a in _minus(t["artist"]).replace("&", ",").split(",") if a.strip()}
    ajeno = 1.0 if not (art & X["mundo"][0]) and _minus(t.get("label") or "") not in X["mundo"][1] else 0.0
    total = d_forma + d_groove + 3 * d_color + b_sello + b_gente + ajeno
    return {"total": round(total, 2), "forma": round(d_forma, 2), "groove": round(d_groove, 2),
            "color": round(col.get(c, 0.5), 2), "sello": b_sello, "gente": b_gente, "ajeno": ajeno}


def _medidas_oscuro(i: str, X: dict) -> dict | None:
    c = X["capa"].get(i)
    f = D / "recetas" / "lib" / f"{i}.json"
    if not c or not f.exists():
        return None
    return {"centroide": c["centroide"], "medio_1_4k": c["medio_1_4k"]}


def lado_oscuro(i: str, X: dict) -> list[str] | None:
    """Que medidas de `i` pasan el borde de los aprobados hacia los oscuros de este set."""
    osc = [m for m in (_medidas_oscuro(o, X) for o in X["esc"].get("oscuros", [])) if m]
    apr = [m for m in (_medidas_oscuro(a, X) for a in X["esc"].get("aprobados", [])) if m]
    yo = _medidas_oscuro(i, X)
    if not osc or not apr or yo is None:
        return None
    fuera = []
    for k in ("centroide", "medio_1_4k"):
        if yo[k] < min(m[k] for m in apr):
            fuera.append(k)
    return fuera


def zona_oscura(i: str, X: dict) -> bool:
    """Melodia en registro grave: 2/2 oscuros del 159, 3/8 oscuros de otros sets, 3/40 aprobados."""
    m = _medidas_oscuro(i, X)
    return bool(m) and (m["centroide"] < ZONA_CENTROIDE or m["medio_1_4k"] < ZONA_1_4K)


def candidatos(pos: int, X: dict) -> list[tuple[str, dict]]:
    """pos es 1-based. Devuelve [(id, puntaje)] ordenado, solo los que pasan lo duro."""
    spec, pool, s = X["spec"], X["pool"], X["set"]
    sale = s[pos - 1]
    resto = [i for i in s if i != sale]
    fam = [a for a in X["esc"].get("aprobados", []) + X.get("extra", []) if a in pool]
    if not fam:
        sys.exit("no hay aprobados en _escucha del config: la familia no existe todavia")
    vec = [s[k] for k in (pos - 2, pos) if 0 <= k < len(s)]
    e_lo, e_hi = spec["e_pool"]
    max_cam, max_bpm = spec.get("max_camelot", 2), spec.get("max_bpm_jump", 2.0)
    art = collections.Counter(n for i in resto for n in names(pool[i]["artist"], pool[i]["title"]))
    sel = collections.Counter(_sello(pool[i]) for i in resto)
    fuera = set(X["esc"].get("cambiados", [])) | X["s158"] | set(s) | VETO_TRACKS
    out = []
    for c, t in pool.items():
        if c in fuera or not (spec["bpm"][0] <= t["bpm"] <= spec["bpm"][1]):
            continue
        v = X["voz"].get(c, {})
        if v.get("etiqueta") == "cantado" or v.get("presencia", 0) > VOZ_MAX:
            continue
        if any(distance(t["key"], pool[v]["key"]) > max_cam or abs(t["bpm"] - pool[v]["bpm"]) > max_bpm
               for v in vec):
            continue
        e = t["energy"]
        if not e_lo <= e <= e_hi:
            continue
        if pos == 1 and len(s) > 1 and e > pool[s[1]]["energy"]:
            continue
        if pos > 1 and abs(e - st.mean(pool[v]["energy"] for v in vec)) > 1.0:
            continue
        if any(art[n] >= TOPE_ART for n in names(t["artist"], t["title"])):
            continue
        if _sello(t) and sel[_sello(t)] >= TOPE_SELLO:
            continue
        if zona_oscura(c, X):
            continue
        p = puntaje(c, fam, X)
        lo = lado_oscuro(c, X)
        p["oscuro"] = lo
        if lo:
            p["total"] = round(p["total"] + 2.0 * len(lo), 2)
        out.append((c, p))
    return sorted(out, key=lambda x: x[1]["total"])


def guardar_capa(i: str, carpeta: Path, t: dict) -> None:
    """Centroide y 1-4 kHz de la capa melodica (stem `other`), en data/capa_melodica.json."""
    import librosa
    import numpy as np
    y, sr = librosa.load(carpeta / "other.wav", sr=22050, mono=True)
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=1024)) ** 2
    fr = librosa.fft_frequencies(sr=sr, n_fft=4096)
    tot = S.sum() + 1e-12
    doc = _j(CAPA_F) if CAPA_F.exists() else {
        "_que_es": ("La capa melodica de cada tema: el stem `other` de Demucs sobre 30 s al 45% del tema "
                    "(el mismo fragmento que data/voces.json). centroide = centroide espectral en Hz; "
                    "medio_1_4k = fraccion de su energia entre 1 y 4 kHz. Mide en que registro esta la "
                    "melodia: los dos temas que el DJ llamo 'muy oscuros' en el set 159 la tienen abajo."),
        "tracks": {}}
    doc["tracks"][i] = {"artist": t["artist"], "title": t["title"],
                        "centroide": round(float((fr[:, None] * S).sum() / tot), 1),
                        "medio_1_4k": round(float(S[(fr >= 1000) & (fr < 4000)].sum() / tot), 3)}
    CAPA_F.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def medir(ids: list[str], X: dict) -> None:
    """Mide la voz con Demucs (como voces.py, sobre el archivo exacto de la DB) y la guarda."""
    import librosa
    import sqlcipher3
    from plomo import config
    from separar import separar
    from voces import SEGUNDOS, _voz
    con = sqlcipher3.connect(f"file:{config.REKORDBOX_DB_PATH}?mode=ro", uri=True)
    con.execute(f"PRAGMA key='{config.SQLCIPHER_KEY}'")
    con.execute("PRAGMA cipher_compatibility=4")
    rutas = {str(i): p for i, p in con.execute(
        f"SELECT ID, FolderPath FROM djmdContent WHERE ID IN ({','.join('?' * len(ids))})", ids)}
    con.close()
    vf = D / "voces.json"
    doc = _j(vf)
    for i in ids:
        f = Path(rutas.get(i, ""))
        if not f.exists():
            continue
        stems = separar(f, librosa.get_duration(path=str(f)) * 0.45, SEGUNDOS)
        r = _voz(stems["other"].parent / "vocals.wav", f)
        if not r:
            continue
        et = ("cantado" if r["presencia"] > 0.60 and r["peso"] > 0.08
              else "algo de voz" if r["presencia"] > 0.30 else "instrumental")
        t = X["pool"][i]
        if i in doc["tracks"]:            # la voz ya estaba: solo faltaba la capa
            guardar_capa(i, stems["other"].parent, t)
            X["capa"][i] = _j(CAPA_F)["tracks"][i]
            continue
        doc["tracks"][i] = {"artist": t["artist"], "title": t["title"],
                            "presencia": round(r["presencia"], 3), "peso": round(r["peso"], 3),
                            "etiqueta": et, "medido": "familia_159.py, voces.separar + voces._voz"}
        X["voz"][i] = doc["tracks"][i]
        vf.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        guardar_capa(i, stems["other"].parent, t)
        X["capa"][i] = _j(CAPA_F)["tracks"][i]


def mostrar(pos: int, X: dict, top: int) -> None:
    pool, s = X["pool"], X["set"]
    print(f"\n#{pos}: sale {pool[s[pos - 1]]['artist']} - {pool[s[pos - 1]]['title']}")
    for c, p in candidatos(pos, X)[:top]:
        t, v = pool[c], X["voz"].get(c)
        voz = f"{v['etiqueta']} {v['presencia']:.0%}" if v else "SIN MEDIR"
        lo = p.get("oscuro")
        osc = "SIN CAPA" if lo is None else ("claro" if not lo else "OSCURO:" + "+".join(lo))
        print(f"  {p['total']:5.2f} | f{p['forma']:.2f} g{p['groove']:.2f} c{p['color']:.2f} "
              f"s{p['sello']:+.1f} a{p['gente']:+.1f}{' AJENO' if p['ajeno'] else ''} | "
              f"E{t['energy']:.1f} {t['bpm']:.0f} {t['key']:>3} | {voz:16} | {osc:24} | {c} {t['artist'][:24]} - "
              f"{t['title'][:40]} [{t['label'][:14]}] [{etiqueta(t['title'])}]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--posiciones", type=int, nargs="*", default=[])
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--medir", type=int, default=0, help="mide la voz de los N primeros sin medir")
    ap.add_argument("--poner", nargs="*", default=[], help="POS=content_id, escribe el target")
    ap.add_argument("--familia-extra", nargs="*", default=[],
                    help="ids que suman a la familia SOLO en esta corrida (p. ej. un reemplazo que el DJ "
                         "todavia no escucho); no los marca como aprobados")
    a = ap.parse_args()
    X = cargar()
    X["extra"] = a.familia_extra
    for pos in a.posiciones:
        if a.medir:
            falta = [c for c, _ in candidatos(pos, X)
                     if c not in X["voz"] or c not in X["capa"]][: a.medir]
            medir(falta, X)
        mostrar(pos, X, a.top)
    if a.poner:
        doc = _j(TARGET_F)
        for par in a.poner:
            pos, cid = par.split("=")
            t = X["pool"][cid]
            doc["tracks"][int(pos) - 1] = {"artist": t["artist"], "title": t["title"], "content_id": cid}
        TARGET_F.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"target escrito: {TARGET_F}")


if __name__ == "__main__":
    main()
