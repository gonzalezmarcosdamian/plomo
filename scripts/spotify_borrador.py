# -*- coding: utf-8 -*-
"""Iterar una lista SOLO en Spotify, con candidatos de todo el catalogo.

POR QUE
-------
"Continuemos solo Spotify y luego pasamos a descargas y rekor una vez cerrado
Spotify y no te cierres a mi musica usa todo Spotify" (2026-10-25). Mientras el DJ
escucha, la lista vive en Spotify: cada cambio se publica ahi al toque, y lo que
no esta en la biblioteca se baja e importa recien cuando la lista se cierra.

El borrador es data/set_borradores/<num>.json: los temas en orden con su
spotify_id, su estado (aprobado / sin_escuchar / nuevo) y los cambiados con lo
que dijo el DJ, textual. La lista de Spotify se reescribe desde el borrador.

COMO BUSCA PARECIDOS (Spotify ya no da recomendaciones, audio-features, artistas
relacionados ni top-tracks a apps nuevas: 404/403, probado 2026-10-25)
  coaparicion  temas que estan en las mismas playlists de organic que los aprobados
  sello        catalogo de los sellos de los aprobados (search label:"X")
  artista      discografia de los artistas de los aprobados
BPM, key y genero salen de Muzpa (sin bajar nada): sirven para que mezcle con los
vecinos y avisan si despues se va a poder bajar. Lo que no esta en Muzpa no entra:
la lista termina en Rekordbox.

LO QUE NO SABE: la energia y si la melodia va grave ("oscuro", ver APRENDIZAJES).
Sin audio no se mide; eso lo decide la escucha del DJ.

Uso:
    python scripts/spotify_borrador.py importar 159
    python scripts/spotify_borrador.py candidatos 159 6 [--top 8]
    python scripts/spotify_borrador.py poner 159 6=<spotify_id> --textual "lo que dijo"
    python scripts/spotify_borrador.py estado 159
    python scripts/spotify_borrador.py aprobar 159 9 10 --textual "lo que dijo"
    python scripts/spotify_borrador.py publicar 159      # lo pendiente, cuando vuelve la cuota

CUOTA: la app del proyecto tiene una cuota diaria. Una busqueda de candidatos sin
cache la agoto el 2026-10-25 (Retry-After 85569 s). Por eso el pool de candidatos se
guarda por dia (data/set_borradores/<num>_pool_<fecha>.json) y `poner` funciona sin
Spotify: anota el cambio como pendiente y `publicar` lo sube despues.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from plomo.camelot import distance as cam_dist, from_musical  # noqa: E402

API = "https://api.spotify.com/v1"
BORRADORES = RAIZ / "data" / "set_borradores"
GENEROS_OK = ("organic", "downtempo", "progressive", "melodic", "deep house", "afro house")
PISTAS_VOZ = re.compile(r"\b(feat\.?|ft\.?|vocal|vox|featuring)\b", re.I)
CONSULTAS_PLAYLISTS = ("organic house", "organic downtempo", "organic progressive house",
                       "melodic organic house", "organic house sunset")


# --------------------------------------------------------------- funciones puras


def norm(s: str) -> str:
    """Sin acentos ni signos: Spotify escribe 'André Moret' y Muzpa 'Andre Moret'."""
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def clave_nombre(artista: str, titulo: str) -> str:
    """Primer artista + titulo sin la version generica: el mismo tema en dos ediciones."""
    a1 = re.split(r"[,&]| feat", artista or "")[0]
    t = re.sub(r"\((original|extended)[^)]*\)|\s-\s(original|extended).*$", "", titulo or "", flags=re.I)
    return norm(a1) + "|" + norm(t)


def escucha_de(cfg: dict) -> dict:
    """El `_escucha` del set, donde sea que este en el config (sets[0] o la raiz)."""
    if "_escucha" in cfg:
        return cfg["_escucha"]
    for s in cfg.get("sets", []):
        if isinstance(s, dict) and "_escucha" in s:
            return s["_escucha"]
    return {}


def mezcla_ok(key: str | None, bpm: float | None, vecinos: list[dict],
              max_cam: int = 1, max_bpm: float = 2.0) -> bool:
    """Mezcla con cada vecino que tenga dato: rueda y BPM dentro del tope."""
    for v in vecinos:
        if key and v.get("key") and cam_dist(key, v["key"]) > max_cam:
            return False
        if bpm and v.get("bpm") and abs(float(bpm) - float(v["bpm"])) > max_bpm:
            return False
    return bool(key and bpm)


def puntaje(c: dict) -> float:
    """Mayor = mas de la familia. La coaparicion manda; el nombre suma menos."""
    p = 2.0 * c.get("coaparicion", 0) + 1.0 * c.get("por_sello", 0) + 0.5 * c.get("por_artista", 0)
    if c.get("voz_probable"):
        p -= 2.0
    return p


def genero_ok(cat: str | None) -> bool:
    return bool(cat) and any(g in cat.lower() for g in GENEROS_OK)


def sello_de_copyright(copyrights: list[dict]) -> str | None:
    """'(P) 2026 Closure' -> 'Closure'. Spotify saco `label` del album (2026); queda en el copyright."""
    for c in copyrights or []:
        txt = re.sub(r"^\s*(?:\(?[CP℗©]\)?\s*)*(?:\d{4}\s*)?", "", c.get("text") or "").strip()
        txt = txt.split(",")[0].strip()
        if txt:
            return txt
    return None


# ----------------------------------------------------------------- spotify


def _spotify():
    import requests
    from spotify_sync import acceso
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {acceso()}"
    return s


class CuotaAgotada(RuntimeError):
    """Spotify devolvio 429. NO es que el tema no exista: no se pudo preguntar."""


def _get(s, url, **params):
    r = s.get(url if url.startswith("http") else API + url, params=params or None, timeout=25)
    if r.status_code == 429:
        # Medido el 2026-10-25: una busqueda de candidatos sin cache gasto la cuota
        # diaria de la app y Spotify pidio 85569 s (casi 24 h). Se corta todo aca.
        horas = int(r.headers.get("Retry-After", "0")) / 3600
        raise CuotaAgotada(f"Spotify corto por cuota: vuelve en {horas:.1f} h")
    return r.json() if r.status_code == 200 else {}


def _items_playlist(s, pid: str) -> list[dict]:
    out, url = [], f"{API}/playlists/{pid}/items?limit=100"
    while url:
        d = _get(s, url)
        for it in d.get("items", []):
            t = it.get("item") or it.get("track")
            if t and t.get("id"):
                out.append(t)
        url = d.get("next")
    return out


def _tema(t: dict) -> dict:
    return {"spotify_id": t["id"], "artista": ", ".join(a["name"] for a in t["artists"]),
            "titulo": t["name"], "album_id": t.get("album", {}).get("id"),
            "artistas_ids": [a["id"] for a in t["artists"]], "ms": t.get("duration_ms")}


# ------------------------------------------------------------------- muzpa


def _muzpa():
    from muzpa_download import MUZPA_API, get_session
    return get_session(), MUZPA_API


def muzpa_info(sm, api, artista: str, titulo: str) -> dict | None:
    """BPM, key (Camelot), genero y duracion del mejor match en Muzpa, o None."""
    base = re.sub(r"\s*[\(\[].*?[\)\]]|\s+-\s+.*$", "", titulo).strip()
    a1 = re.split(r"[,&]| feat", artista)[0].strip()
    mix = re.search(r"\(([^)]*)\)|\s-\s(.*)$", titulo)
    mix_txt = norm((mix.group(1) or mix.group(2)) if mix else "")
    mejor = None
    try:
        d = sm.get(f"{api}/a/ms/media/search?format=mp3&matchonly=true&page=0&popularorder=true"
                   f"&text={quote_plus(a1 + ' ' + base)}", timeout=25).json() or {}
    except Exception:  # noqa: BLE001 — sin Muzpa el candidato queda sin dato
        return None
    for alb in d.get("albums") or []:
        for t in alb.get("tracks") or []:
            fn = t.get("fullnm_html") or ""
            if not t.get("satisfies") or norm(base) not in norm(fn) or norm(a1) not in norm(fn):
                continue
            puntos = 2 if mix_txt and mix_txt in norm(fn) else (1 if "extended" in fn.lower() else 0)
            if mejor is None or puntos > mejor[0]:
                mejor = (puntos, t, fn)
    if not mejor:
        return None
    t = mejor[1]
    return {"muzpa_id": t["id"], "muzpa_nombre": mejor[2], "bpm": t.get("bpm"),
            "key": from_musical(t.get("initial_key") or ""), "genero": t.get("category_nm"),
            "duracion": t.get("playtime")}


# ----------------------------------------------------------------- borrador


def ruta(num: int) -> Path:
    return BORRADORES / f"{num}.json"


def cargar(num: int) -> dict:
    return json.loads(ruta(num).read_text(encoding="utf-8"))


def guardar(num: int, b: dict) -> None:
    BORRADORES.mkdir(parents=True, exist_ok=True)
    ruta(num).write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")


def publicar(s, b: dict) -> bool:
    """Reescribe la lista de Spotify desde el borrador. False si no hubo cuota."""
    uris = [f"spotify:track:{t['spotify_id']}" for t in b["temas"]]
    r = s.put(f"{API}/playlists/{b['playlist']}/items", json={"uris": uris[:100]}, timeout=25)
    if r.status_code == 429:
        horas = int(r.headers.get("Retry-After", "0")) / 3600
        print(f"  NO publicada: Spotify corto por cuota, vuelve en {horas:.1f} h. "
              "Queda pendiente en el borrador: `publicar` cuando vuelva.")
        return False
    if r.status_code not in (200, 201):
        raise SystemExit(f"Spotify no acepto la lista: {r.status_code} {r.text[:200]}")
    leida = [t["id"] for t in _items_playlist(s, b["playlist"])]
    esperada = [t["spotify_id"] for t in b["temas"]]
    print(f"  publicada: {len(leida)} temas, {'en orden' if leida == esperada else 'NO COINCIDE'}")
    return leida == esperada


def _del_pool_guardado(num: int, sid: str) -> dict | None:
    """El tema tal como quedo en el ultimo pool del dia: sirve sin cuota de Spotify."""
    for f in sorted(BORRADORES.glob(f"{num}_pool_*.json"), reverse=True):
        pool = json.loads(f.read_text(encoding="utf-8"))["pool"]
        if sid in pool:
            return pool[sid]
    return None


def cmd_importar(num: int) -> None:
    """Arma el borrador desde la lista de Spotify y lo escuchado del config del set."""
    s = _spotify()
    pid = json.loads((RAIZ / "data/spotify_playlists.json").read_text(encoding="utf-8"))[str(num)]
    temas = [_tema(t) for t in _items_playlist(s, pid)]
    target = json.loads((RAIZ / f"data/set_targets/set_{num}.json").read_text(encoding="utf-8"))
    ids = [str(x.get("content_id") or x.get("id")) for x in (target.get("tracks") or [])]
    cfgs = list((RAIZ / "data/set_configs").glob(f"{num}_*.json"))
    esc = escucha_de(json.loads(cfgs[0].read_text(encoding="utf-8"))) if cfgs else {}
    aprobados = set(esc.get("aprobados", []))
    # Para lo que ya esta en la biblioteca manda la key y el BPM de Rekordbox: es
    # con lo que el DJ mezcla (Coral: 8A en Rekordbox, 9A en Muzpa).
    pool = {str(x["id"]): x for x in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    sm, api = _muzpa()
    for i, t in enumerate(temas):
        cid = ids[i] if i < len(ids) else None
        t["content_id"] = cid
        t["estado"] = "aprobado" if cid in aprobados else "sin_escuchar"
        t.update(muzpa_info(sm, api, t["artista"], t["titulo"]) or {})
        if cid in pool:
            t["bpm"], t["key"] = pool[cid].get("bpm"), pool[cid].get("key")
    previos = [{"spotify_id": None, "content_id": c, "artista": pool[c]["artist"], "titulo": pool[c]["title"],
                "textual": "(vuelta anterior, ver _escucha del config)"}
               for c in esc.get("cambiados", []) if c in pool]
    b = {"num": num, "playlist": pid, "temas": temas, "cambiados": previos, "rondas": [],
         "_que_es": "Borrador de la lista mientras se itera en Spotify (spotify_borrador.py). "
                    "Al cerrarla: lo que no tiene content_id se baja de Muzpa e importa."}
    guardar(num, b)
    print(f"borrador {ruta(num)}: {len(temas)} temas, {sum(t['estado'] == 'aprobado' for t in temas)} aprobados")


def _buscar(s, q: str, tipo: str, paginas: int = 2) -> list[dict]:
    """Search de a 10: Spotify da 'Invalid limit' con mas de 10 (2026)."""
    out = []
    for p in range(paginas):
        d = _get(s, "/search", q=q, type=tipo, limit=10, offset=10 * p)
        out += [x for x in (d.get(tipo + "s") or {}).get("items", []) if x]
    return out


def _familia(s, b: dict) -> tuple[Counter, dict, set, set]:
    """Coapariciones en playlists de organic, sellos y artistas de los aprobados.

    Devuelve tambien los temas de esas playlists ya completos: pedir varios temas
    juntos (/tracks?ids=) da 403 a apps nuevas.
    """
    aprob = [t for t in b["temas"] if t["estado"] == "aprobado"]
    ids_aprob = {t["spotify_id"] for t in aprob}
    co: Counter = Counter()
    objetos: dict[str, dict] = {}
    vistas, con_aprob = set(), 0
    consultas = list(CONSULTAS_PLAYLISTS) + [f"{t['titulo'].split(' - ')[0]} {t['artista'].split(',')[0]}" for t in aprob]
    for q in consultas:
        for p in _buscar(s, q, "playlist", paginas=1):
            if p["id"] in vistas or p["id"] == b["playlist"]:
                continue
            vistas.add(p["id"])
            items = _items_playlist(s, p["id"])
            comunes = ids_aprob & {t["id"] for t in items}
            if comunes:
                con_aprob += 1
                for t in items:
                    co[t["id"]] += len(comunes)
                    objetos.setdefault(t["id"], t)
    sellos = set()
    for t in aprob:
        alb = _get(s, f"/albums/{t['album_id']}") if t.get("album_id") else {}
        sello = alb.get("label") or sello_de_copyright(alb.get("copyrights"))
        if sello:
            sellos.add(sello)
    artistas = {a for t in aprob for a in t.get("artistas_ids", [])}
    print(f"  familia: {len(aprob)} aprobados, {len(vistas)} playlists ({con_aprob} con aprobados), "
          f"sellos {sorted(sellos)}, {len(artistas)} artistas")
    return co, objetos, sellos, artistas


def _pool_crudo(s, b: dict, refrescar: bool = False) -> dict[str, dict]:
    """Todos los candidatos de la familia, sin filtrar. Se guarda por dia.

    Armarlo son cientos de llamadas (playlists, catalogos de sellos, discografias)
    y una corrida sin cache por cada lugar agoto la cuota diaria de la app. Los
    aprobados cambian poco entre una vuelta y otra: el pool del dia alcanza.
    """
    from datetime import date
    cache = BORRADORES / f"{b['num']}_pool_{date.today().isoformat()}.json"
    aprob = sorted(t["spotify_id"] for t in b["temas"] if t["estado"] == "aprobado")
    if cache.exists() and not refrescar:
        guardado = json.loads(cache.read_text(encoding="utf-8"))
        if set(guardado["aprobados"]) <= set(aprob):
            print(f"  pool del dia en cache ({len(guardado['pool'])} temas); --refrescar para rehacerlo")
            return guardado["pool"]
    co, objetos, sellos, artistas = _familia(s, b)
    pool: dict[str, dict] = {}

    def sumar(t: dict, campo: str) -> None:
        if not t or not t.get("id"):
            return
        c = pool.setdefault(t["id"], {**_tema(t), "coaparicion": co.get(t["id"], 0), "por_sello": 0, "por_artista": 0})
        c[campo] = 1

    for i, n in co.most_common(150):
        if i in objetos:
            pool.setdefault(i, {**_tema(objetos[i]), "coaparicion": n, "por_sello": 0, "por_artista": 0})
    for sello in sellos:
        for alb in _buscar(s, f'label:"{sello}"', "album", paginas=2):
            for t in _get(s, f"/albums/{alb['id']}/tracks", limit=50).get("items", []):
                t["album"] = {"id": alb["id"]}
                sumar(t, "por_sello")
    for aid in list(artistas)[:12]:
        for alb in _get(s, f"/artists/{aid}/albums", include_groups="album,single", limit=10).get("items", []):
            for t in _get(s, f"/albums/{alb['id']}/tracks", limit=50).get("items", []):
                t["album"] = {"id": alb["id"]}
                sumar(t, "por_artista")
    for c in pool.values():
        c["voz_probable"] = bool(PISTAS_VOZ.search(c["titulo"]))
    BORRADORES.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"aprobados": aprob, "pool": pool}, ensure_ascii=False), encoding="utf-8")
    return pool


def cmd_candidatos(num: int, pos: int, top: int, refrescar: bool = False) -> None:
    b = cargar(num)
    s = _spotify()
    pool = _pool_crudo(s, b, refrescar)
    excluir = {t["spotify_id"] for t in b["temas"]} | {c["spotify_id"] for c in b["cambiados"] if c["spotify_id"]}
    # Por nombre tambien: los cambiados de vueltas anteriores no tienen spotify_id,
    # y una misma version puede tener varios ids en Spotify (single, EP, compilado).
    nombres_fuera = {clave_nombre(t["artista"], t["titulo"]) for t in b["temas"] + b["cambiados"]}
    orden = sorted((c for i, c in pool.items() if i not in excluir), key=puntaje, reverse=True)

    temas = b["temas"]
    vecinos = [temas[j] for j in (pos - 2, pos) if 0 <= j < len(temas)]
    sm, api = _muzpa()
    print(f"\n#{pos}: sale {temas[pos - 1]['artista']} - {temas[pos - 1]['titulo']}")
    print("  vecinos: " + " | ".join(f"{v['artista'][:20]} - {v['titulo'][:28]} {v.get('bpm')} {v.get('key')}" for v in vecinos))
    vistos = 0
    casi: list[dict] = []
    orden = [c for c in orden if clave_nombre(c["artista"], c["titulo"]) not in nombres_fuera]
    for c in orden[:120]:
        info = muzpa_info(sm, api, c["artista"], c["titulo"])
        if not info or not genero_ok(info.get("genero")):
            continue
        if not mezcla_ok(info["key"], info["bpm"], vecinos):
            # Los que mezclan con rueda 2 o BPM 3 se muestran aparte: con un hueco
            # de 121-122 BPM y 6A-7A, lo perfecto puede no existir.
            if mezcla_ok(info["key"], info["bpm"], vecinos, max_cam=2, max_bpm=3):
                casi.append({**c, **info})
            continue
        c.update(info)
        motivos = [m for m, v in (("coaparece x%d" % c["coaparicion"], c["coaparicion"]),
                                  ("sello de un aprobado", c["por_sello"]), ("artista de un aprobado", c["por_artista"]))
                   if v]
        print(f"  {puntaje(c):4.1f} | {c['bpm']} {c['key']:>3} {c['genero'][:22]:22} | {c['artista'][:28]} - "
              f"{c['titulo'][:40]} | {', '.join(motivos)}{' | ojo: voz' if c['voz_probable'] else ''}")
        print(f"         spotify:{c['spotify_id']}  muzpa: {c['muzpa_nombre'][:60]} {c.get('duracion')}")
        vistos += 1
        if vistos >= top:
            break
    if not vistos:
        print("  ninguno mezcla con los dos vecinos dentro de rueda 1 / BPM 2")
    if casi and vistos < top:
        print("  casi (rueda <= 2 o BPM <= 3 con algun vecino):")
        for c in casi[:top - vistos]:
            print(f"  {puntaje(c):4.1f} | {c['bpm']} {c['key']:>3} {c['genero'][:22]:22} | {c['artista'][:28]} - "
                  f"{c['titulo'][:40]} | spotify:{c['spotify_id']}")


def cmd_poner(num: int, asignaciones: list[str], textual: str) -> None:
    b = cargar(num)
    s = _spotify()
    sm, api = _muzpa()
    ronda = {"textual": textual, "cambios": []}
    for a in asignaciones:
        pos, sid = a.split("=", 1)
        pos = int(pos)
        try:
            t = _get(s, f"/tracks/{sid}")
            nuevo = _tema(t) if t else None
        except CuotaAgotada:
            nuevo = _del_pool_guardado(num, sid)
            if nuevo:
                nuevo = {k: v for k, v in nuevo.items() if k in ("spotify_id", "artista", "titulo", "album_id",
                                                                 "artistas_ids", "ms")}
        if not nuevo:
            raise SystemExit(f"no pude confirmar el tema {sid} (no esta en Spotify o no hay cuota y "
                             "tampoco esta en el pool guardado)")
        viejo = b["temas"][pos - 1]
        b["cambiados"].append({k: viejo.get(k) for k in ("spotify_id", "artista", "titulo", "content_id")}
                              | {"textual": textual})
        nuevo = nuevo | {"estado": "nuevo", "content_id": None}
        nuevo.update(muzpa_info(sm, api, nuevo["artista"], nuevo["titulo"]) or {})
        b["temas"][pos - 1] = nuevo
        ronda["cambios"].append(f"#{pos}: {viejo['artista']} - {viejo['titulo']} -> {nuevo['artista']} - {nuevo['titulo']}")
        print("  " + ronda["cambios"][-1])
    b["rondas"].append(ronda)
    b["pendiente_publicar"] = True
    guardar(num, b)
    if publicar(s, b):
        b["pendiente_publicar"] = False
        guardar(num, b)


def cmd_publicar(num: int) -> None:
    b = cargar(num)
    if publicar(_spotify(), b):
        b["pendiente_publicar"] = False
        guardar(num, b)


def cmd_aprobar(num: int, posiciones: list[int], textual: str) -> None:
    b = cargar(num)
    for p in posiciones:
        b["temas"][p - 1]["estado"] = "aprobado"
    b["rondas"].append({"textual": textual, "aprueba": [f"#{p}: {b['temas'][p - 1]['titulo']}" for p in posiciones]})
    guardar(num, b)
    print("  aprobados: " + ", ".join(f"#{p}" for p in posiciones))


def cmd_estado(num: int) -> None:
    b = cargar(num)
    for i, t in enumerate(b["temas"], 1):
        print(f"{i:2d} {t['estado']:12} {t.get('bpm') or '?':>4} {t.get('key') or '?':>3}  {t['artista'][:30]} - {t['titulo'][:45]}")
    print(f"cambiados: {len(b['cambiados'])}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("importar").add_argument("num", type=int)
    c = sub.add_parser("candidatos")
    c.add_argument("num", type=int)
    c.add_argument("pos", type=int)
    c.add_argument("--top", type=int, default=8)
    c.add_argument("--refrescar", action="store_true", help="rehacer el pool del dia (gasta cuota)")
    sub.add_parser("publicar").add_argument("num", type=int)
    p = sub.add_parser("poner")
    p.add_argument("num", type=int)
    p.add_argument("asignaciones", nargs="+", help="POS=spotify_id")
    p.add_argument("--textual", default="", help="lo que dijo el DJ")
    sub.add_parser("estado").add_argument("num", type=int)
    ap_ = sub.add_parser("aprobar")
    ap_.add_argument("num", type=int)
    ap_.add_argument("posiciones", type=int, nargs="+")
    ap_.add_argument("--textual", default="")
    a = ap.parse_args()
    if a.cmd == "importar":
        cmd_importar(a.num)
    elif a.cmd == "aprobar":
        cmd_aprobar(a.num, a.posiciones, a.textual)
    elif a.cmd == "candidatos":
        cmd_candidatos(a.num, a.pos, a.top, a.refrescar)
    elif a.cmd == "publicar":
        cmd_publicar(a.num)
    elif a.cmd == "poner":
        cmd_poner(a.num, a.asignaciones, a.textual)
    else:
        cmd_estado(a.num)


if __name__ == "__main__":
    main()
