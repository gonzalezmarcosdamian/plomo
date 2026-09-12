"""Busca sets de DJs de referencia en YouTube y se queda con los que traen tracklist.

Por que existe: `data/setlists/` es el unico corpus que puede refutar una regla de
curaduria sin circularidad, y llenarlo a mano es el cuello de botella del
proyecto. 1001tracklists esta detras de un Turnstile de Cloudflare y no se puede
leer. Pero el tracklist casi siempre esta igual — en la descripcion del video
(los canales de sello y de radio lo ponen siempre) o en los comentarios (en los
sets de club lo transcribe la gente).

Este script hace las dos cosas: busca por consulta, mira descripcion y
comentarios, y guarda solo lo que parece una secuencia de verdad.

NO ingiere nada: deja los candidatos en archivos de texto para revisar antes de
cargarlos con ingest_setlist.py. Un tracklist mal transcrito envenena el corpus,
y el corpus es lo que despues justifica cambiar una regla.

Uso:
    python scripts/buscar_setlists.py "hernan cattaneo resident" --max 8
    python scripts/buscar_setlists.py --djs   # barre la lista de referencia
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "setlists_candidatos"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Content-Type": "application/json"}
CTX = {"client": {"clientName": "WEB", "clientVersion": "2.20240814.00.00",
                  "hl": "es", "gl": "AR"}}

# Los DJs cuyo repertorio se solapa con la biblioteca. Fuera de esta lista el
# setlist entra con cobertura de datos baja y casi no aporta transiciones.
DJS = [
    "Hernan Cattaneo Resident tracklist",
    "John Digweed Transitions tracklist",
    "Nick Warren The Soundgarden tracklist",
    "Guy J live set tracklist",
    "Emi Galvan live set tracklist",
    "Kamilo Sanclemente dj set tracklist",
    "Mariano Mellino dj set tracklist",
    "Maze 28 dj mix tracklist",
    "Simon Vuarambon dj set tracklist",
    "Ezequiel Arias dj set tracklist",
    "Sasha live set tracklist progressive",
    "Cid Inc dj mix tracklist",
]

LINEA_TL = re.compile(
    r"^\s*(?:\[?\d{1,2}[:.]\d{2}(?::\d{2})?\]?)?\s*(?:\d{1,3}[.)]?\s+)?"
    r".{2,60}?\s+[-–—]\s+.{2,70}\s*$")


def walk(o, key):
    if isinstance(o, dict):
        if key in o:
            yield o[key]
        for v in o.values():
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def _api_key(s: requests.Session) -> str:
    t = s.get("https://www.youtube.com/", headers=H).text
    return re.search(r'"INNERTUBE_API_KEY":"(.*?)"', t).group(1)


def buscar(s: requests.Session, key: str, consulta: str, maximo: int) -> list[dict]:
    r = s.post(f"https://www.youtube.com/youtubei/v1/search?key={key}",
               headers=H, json={"context": CTX, "query": consulta}).json()
    out = []
    for v in walk(r, "videoRenderer"):
        tit = "".join(x.get("text", "") for x in v.get("title", {}).get("runs", []))
        dur = v.get("lengthText", {}).get("simpleText", "")
        # un set dura horas; un tema dura minutos. Filtrar por duracion evita
        # traerse cien singles con el nombre del DJ.
        largo = dur.count(":") >= 2 or (dur[:2].isdigit() and int(dur[:2]) >= 40)
        if v.get("videoId") and largo:
            out.append({"id": v["videoId"], "titulo": tit, "duracion": dur})
        if len(out) >= maximo:
            break
    return out


def descripcion(s: requests.Session, vid: str) -> tuple[str, str]:
    t = s.get(f"https://www.youtube.com/watch?v={vid}", headers=H).text
    m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", t, re.S)
    if not m:
        return "", ""
    d = json.loads(m.group(1)).get("videoDetails", {})
    return d.get("title", ""), d.get("shortDescription", "") or ""


def comentarios(s: requests.Session, key: str, vid: str, paginas: int = 6) -> list[str]:
    t = s.get(f"https://www.youtube.com/watch?v={vid}", headers=H).text
    m = re.search(r"var ytInitialData\s*=\s*(\{.*?\});</script>", t, re.S)
    if not m:
        return []
    cont = None
    for ep in walk(json.loads(m.group(1)), "continuationItemRenderer"):
        tok = list(walk(ep, "token"))
        if tok:
            cont = tok[0]
    out = []
    for _ in range(paginas):
        if not cont:
            break
        r = s.post(f"https://www.youtube.com/youtubei/v1/next?key={key}",
                   headers=H, json={"context": CTX, "continuation": cont}).json()
        for c in walk(r, "commentEntityPayload"):
            # el campo viene como string o como {"content": "..."} segun version
            cont_txt = c.get("properties", {}).get("content", "")
            if isinstance(cont_txt, dict):
                cont_txt = cont_txt.get("content", "")
            if isinstance(cont_txt, str) and cont_txt:
                out.append(cont_txt)
        nxt = None
        for ep in walk(r, "continuationItemRenderer"):
            tok = list(walk(ep, "token"))
            if tok:
                nxt = tok[0]
        cont = nxt
    return out


def parece_tracklist(texto: str, minimo: int = 8) -> int:
    """Cuantas lineas del texto parecen 'Artista - Titulo'."""
    n = sum(1 for ln in texto.splitlines() if LINEA_TL.match(ln))
    return n if n >= minimo else 0


def procesar(s, key, consulta: str, maximo: int) -> list[dict]:
    hallazgos = []
    for v in buscar(s, key, consulta, maximo):
        try:
            tit, desc = descripcion(s, v["id"])
        except Exception:
            continue
        n = parece_tracklist(desc)
        fuente, texto = "descripcion", desc
        if not n:
            try:
                cs = comentarios(s, key, v["id"])
            except Exception:
                cs = []
            mejor = max(cs, key=parece_tracklist, default="")
            n = parece_tracklist(mejor)
            fuente, texto = "comentario", mejor
        if n:
            hallazgos.append({"id": v["id"], "titulo": tit or v["titulo"],
                              "duracion": v["duracion"], "lineas": n,
                              "fuente": fuente, "texto": texto})
            print(f"    [{n:>2} lineas, {fuente}] {(tit or v['titulo'])[:66]}")
        time.sleep(0.3)
    return hallazgos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("consulta", nargs="?")
    ap.add_argument("--djs", action="store_true", help="barrer la lista de referencia")
    ap.add_argument("--max", type=int, default=6, help="videos por consulta")
    args = ap.parse_args()

    consultas = DJS if args.djs else ([args.consulta] if args.consulta else [])
    if not consultas:
        sys.exit("pasa una consulta o --djs")

    SALIDA.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    key = _api_key(s)
    total = 0
    for q in consultas:
        print(f"\n>> {q}")
        for h in procesar(s, key, q, args.max):
            nombre = re.sub(r"[^a-z0-9]+", "-", h["titulo"].lower()).strip("-")[:70]
            f = SALIDA / f"{nombre}__{h['id']}.txt"
            f.write_text(
                f"# {h['titulo']}\n# https://youtu.be/{h['id']}  ({h['duracion']})\n"
                f"# {h['lineas']} lineas, desde {h['fuente']}\n\n{h['texto']}\n",
                encoding="utf-8")
            total += 1
    print(f"\n{total} candidatos en {SALIDA.relative_to(RAIZ)}")
    print("Revisalos y cargalos con: python scripts/ingest_setlist.py --dj ... --archivo ...")


if __name__ == "__main__":
    main()
