# -*- coding: utf-8 -*-
"""Cambia SOLO los temas que el DJ rechazo, dejando el resto donde esta.

POR QUE
-------
"Fijate los que van quedando y su idea y reemplaza los que te nombro en la
proxima iteracion, voy escuchando" (2026-09-23). Rearmar el set entero cada vez
que el DJ saca un tema le cambia todo lo demas debajo de los pies: escucha el
143, nombra tres temas, y en la version siguiente ya no reconoce el set. Un set
que el DJ esta escuchando es un objeto que ya tiene una idea, y la idea vive en
los temas que NO menciono.

Asi que esto no arma un set: lo edita. Cada hueco se llena con el mejor
candidato para ESE lugar, midiendo contra los dos vecinos que se quedan.

QUE MIRA PARA ELEGIR
--------------------
En orden, todo respecto de los vecinos que quedan fijos:

1. Que se pueda mezclar: distancia Camelot y salto de BPM contra los dos lados.
2. Que la energia no haga un pozo ni un pico: el candidato se compara con el
   promedio de sus vecinos.
3. Que sea de su mundo: artista o sello que aparezca en lo que toco de verdad
   (data/mundo_propio.json). Lo ajeno paga, como en el solver.
4. En un set colorido, el brillo y la tonalidad mayor suman.

Nunca elige algo vetado, ni algo que ya suene esa noche en otro set.

LO QUE ESTE SCRIPT NO SABE
--------------------------
Por que el DJ escucha un tema como "oscuro". Medido sobre los que rechazo del
143: son MAS brillantes que los que deja (percentil 0.94 contra 0.82), y los dos
que llamo oscuros son espectralmente opuestos entre si (uno con medios 22.5 y
aire 2.3, el otro con 5.8 y 14.9). Hasta que aparezca el patron, los rechazados
salen por nombre y no por regla.

USO
---
    python scripts/reemplazar.py 143 --dry
    python scripts/reemplazar.py 143            # escribe a Rekordbox
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
import sqlcipher3  # noqa: E402

from plomo.camelot import distance as cam_dist  # noqa: E402
from plomo.rules import R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAX_CAM = R.get("armonia.max_camelot_dist", 2)
MAX_BPM = R.get("bpm.max_salto", 3.0)
PESO_AJENO = R.get("sonido_propio.peso_ajeno", 2.0)
COLORIDO = R.get("estilo.colorido") or {}
NOCHE = (139, 140, 141, 142, 143, 144, 145)


def conectar():
    con = sqlcipher3.connect(os.environ["REKORDBOX_DB_PATH"])
    con.execute(f"PRAGMA key='{os.environ['SQLCIPHER_KEY']}'")
    con.execute("PRAGMA cipher_compatibility=4")
    return con


def playlist(con, num: int):
    fila = con.execute("SELECT ID,Name FROM djmdPlaylist WHERE Name LIKE ? AND rb_local_deleted=0",
                       (f"{num}.%",)).fetchone()
    if not fila:
        sys.exit(f"no existe el set {num}")
    pid, nom = fila
    filas = con.execute("""SELECT sp.ContentID FROM djmdSongPlaylist sp
        WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0 ORDER BY sp.TrackNo""", (pid,)).fetchall()
    return pid, nom, [str(r[0]) for r in filas]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("num", type=int)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--desde", help="target JSON guardado en vez de leer la base")
    ap.add_argument("--como", nargs="*", default=[],
                    help='"tipo tal artista": descuenta a sus temas y a los de sus sellos')
    ap.add_argument("--sin", nargs="*", default=[],
                    help="artistas que no pueden entrar en este reemplazo")
    ap.add_argument("--posiciones", type=int, nargs="*", default=[],
                    help="rehacer estos lugares (1 = el primero) sin vetar lo que sale")
    args = ap.parse_args()

    POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    PERC = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
    VET = {k for k, v in PERC.items() if v.get("veto")}
    MUNDO = json.loads((RAIZ / "data/mundo_propio.json").read_text(encoding="utf-8"))
    ART, SELLO = set(MUNDO["artistas"]), set(MUNDO["sellos"])
    G = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))
    BR = G.get("brillo_pct", {})
    CU = G.get("cuerpo_pct", {})

    def E(cid):
        v = PERC.get(cid, {})
        return v.get("E", POOL.get(cid, {}).get("energy", 0.0))

    def minus(s):
        import unicodedata
        s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                    if unicodedata.category(c) != "Mn")
        return s.lower().strip()

    def ajeno(t):
        arts = {a.strip() for a in minus(t["artist"]).replace("&", ",").split(",") if a.strip()}
        return not (arts & ART) and minus(t.get("label") or "") not in SELLO

    # "pone temas mas coloridos y fiesteros tipo de Sebastian Leger": un artista
    # de referencia no es un filtro sino una direccion. Se descuenta a sus temas
    # y a los de los sellos donde el edita, que es donde vive ese sonido.
    como = [minus(x) for x in args.como]
    sellos_como = set()
    if como:
        for t in POOL.values():
            if any(c in minus(t["artist"]) for c in como) and t.get("label"):
                sellos_como.add(minus(t["label"]))
        print(f"  como {', '.join(args.como)}: {len(sellos_como)} sellos de ese mundo")

    con = conectar()
    pid, nom, ids = playlist(con, args.num)
    if args.desde:
        # rehacer los reemplazos de una version anterior sin tener que volver a
        # escribirla en Rekordbox primero
        guardado = json.loads(Path(args.desde).read_text(encoding="utf-8"))
        ids = [x["content_id"] for x in guardado["tracks"]]
        print(f"  (partiendo de {Path(args.desde).name})")
    colorido = "Colorido" in nom or "colorido" in nom

    # lo que ya suena esa noche en otro set, para no repetir
    suena = set()
    for n in NOCHE:
        if n == args.num:
            continue
        try:
            suena |= set(playlist(con, n)[2])
        except SystemExit:
            pass

    # Rehacer un lugar NO es vetar lo que estaba: el DJ puede querer otro tema
    # sin haber rechazado ese. Vetar por las dudas ensucia data/energia_percibida,
    # que es lo que define "mi sonido", con temas que nunca dijo que no le
    # gustaran.
    if args.posiciones:
        huecos = [n - 1 for n in args.posiciones if 0 < n <= len(ids)]
    else:
        huecos = [i for i, c in enumerate(ids) if c in VET]
    sin = [minus(x) for x in args.sin]
    if not huecos:
        print(f"{nom}\n  sin temas vetados, no hay nada que reemplazar")
        return
    print(f"{nom}\n{len(huecos)} temas a reemplazar\n")

    nuevos = list(ids)
    usados = set(ids) | suena
    for i in huecos:
        fuera = set(huecos)
        prev = next((nuevos[j] for j in range(i - 1, -1, -1) if j not in fuera), None)
        sig = next((nuevos[j] for j in range(i + 1, len(nuevos)) if j not in fuera), None)
        vecinos = [c for c in (prev, sig) if c]
        # El hueco hereda el ROL del tema que sale, no el promedio de sus
        # vecinos. Si no, sacar el pico del set lo reemplaza por algo del monton
        # y el set se queda sin cima: el DJ saco Alafia (E8.6) por oscuro, no
        # por grande. Lo que se cambia es el tema, no el lugar que ocupaba.
        #
        # Y el rol es la energia CALCULADA del que sale, no la que el DJ
        # escucho. Moho lo saco porque "arranca muy abajo": su calculada es 5.6
        # y el la oyo 4.2, asi que apuntar a lo que oyo reemplaza un tema flojo
        # por otro igual de flojo. Cuando lo escuchado esta por debajo de lo
        # calculado, el lugar pide MAS de lo que decia el numero, y esa
        # diferencia se reparte a la mitad.
        calc = POOL[ids[i]]["energy"]
        oido = E(ids[i])
        e_obj = calc + max(0.0, calc - oido) / 2
        mejor, mejor_c = None, 1e9
        for cid, t in POOL.items():
            if cid in usados or cid in VET or not t.get("key"):
                continue
            if sin and any(x in minus(t["artist"]) for x in sin):
                continue
            ok = True
            for v in vecinos:
                tv = POOL[v]
                if cam_dist(tv["key"], t["key"]) > MAX_CAM or abs(tv["bpm"] - t["bpm"]) > MAX_BPM:
                    ok = False
                    break
            if not ok:
                continue
            c = abs(E(cid) - e_obj) * 3.0
            if ajeno(t):
                c += PESO_AJENO
            if como:
                if any(c in minus(t["artist"]) for c in como):
                    c -= 2.5
                elif minus(t.get("label") or "") in sellos_como:
                    c -= 1.2
            if colorido:
                # CUERPO, no brillo. Y sin premio a la tonalidad mayor: de los 7
                # temas que el DJ saco del 143, el 60% eran mayores contra el
                # 11% de los que dejo. La cuota de modo que puse el 2026-09-23
                # le estuvo trayendo material que no quiere.
                c -= CU.get(cid, 0.5) * COLORIDO.get("color_peso", 1.5)
            if c < mejor_c:
                mejor, mejor_c = cid, c
        if mejor is None:
            print(f"  {i+1:2d}. SIN CANDIDATO para el lugar de {POOL[ids[i]]['title'][:40]}")
            continue
        usados.add(mejor)
        nuevos[i] = mejor
        vt, nt = POOL[ids[i]], POOL[mejor]
        print(f"  {i+1:2d}. sale  E{E(ids[i]):.1f} {vt['bpm']:.0f} {vt['key']:>3s}  "
              f"{vt['artist'][:20]} - {vt['title'][:32]}")
        print(f"      entra E{E(mejor):.1f} {nt['bpm']:.0f} {nt['key']:>3s}  "
              f"{nt['artist'][:20]} - {nt['title'][:32]}"
              f"{'  [de su mundo]' if not ajeno(nt) else '  [AJENO]'}")

    destino = RAIZ / "data/set_targets" / f"set_{args.num}.json"
    doc = json.loads(destino.read_text(encoding="utf-8"))
    doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"], "content_id": c}
                     for c in nuevos]
    doc["keep_order"] = True
    if args.dry:
        print("\n--dry: no se escribio nada")
        return
    destino.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {destino.name}")
    subprocess.run([sys.executable, str(RAIZ / "scripts/build_set.py"), str(args.num)], cwd=str(RAIZ))


if __name__ == "__main__":
    main()
