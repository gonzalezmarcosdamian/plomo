# -*- coding: utf-8 -*-
"""Dos datos que al solver le faltaban: de que mundo viene un tema, y su groove.

MUNDO PROPIO (data/mundo_propio.json)
-------------------------------------
Artistas y sellos que aparecen en lo que el DJ EFECTIVAMENTE TOCO (djmdHistory)
mas los que marco como favoritos. Es la evidencia menos circular que hay: el
historial no lo escribio el solver, lo escribio el CDJ.

Sirve para contestar una pregunta que el solver no se hacia: este tema, de que
escena viene. Medido el 2026-09-23 sobre los cuatro temas que el DJ rechazo
escuchando (Llego La Hora, Meduza - Friends, y dos de Afro House): los CUATRO
tenian artista y sello ajenos a su historial. El set 140, el unico que elogio
entero, tiene cero ajenos en 17 temas. Ningun otro rasgo medido los separaba:
por FORMA del audio estaban a 2.6-3.7 de sus favoritos contra una mediana de
2.40 de la biblioteca, o sea indistinguibles.

GROOVE (data/groove_index.json)
-------------------------------
Densidad ritmica media y peso de graves de cada tema indexado, con los desvios
de la biblioteca para normalizar. Con eso el solver puede cobrar el SALTO de
groove entre dos temas consecutivos, que es lo que se escucha como "se corta".

El numero de referencia sale de los setlists reales: sobre 236 pares
consecutivos donde los dos temas estan indexados, el salto mediano es 1.25.
Nuestros sets del cumple estaban entre 1.68 y 2.37, y el mejor de todos segun
el oido del DJ (el 140) era justo el mas cercano al pro.

Uso:
    python scripts/perfilar_gusto.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
import sqlcipher3  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LIB = RAIZ / "data" / "recetas" / "lib"
SPLIT = re.compile(r"\s*(?:,|&| feat\.?| ft\.?| vs\.?| x )\s*", re.I)


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def artistas(txt: str) -> set[str]:
    """'A, B & C' -> {a, b, c}. El tag trae varios artistas en un solo campo."""
    return {p.strip() for p in SPLIT.split(norm(txt)) if len(p.strip()) > 2}


def conectar():
    con = sqlcipher3.connect(os.environ["REKORDBOX_DB_PATH"])
    con.execute(f"PRAGMA key='{os.environ['SQLCIPHER_KEY']}'")
    con.execute("PRAGMA cipher_compatibility=4")
    return con


def mundo_propio(con) -> dict:
    arts, sellos = set(), set()
    n = 0
    for a, l in con.execute("""
            SELECT ar.Name, lb.Name FROM djmdSongHistory sh
            JOIN djmdContent c ON sh.ContentID = c.ID
            LEFT JOIN djmdArtist ar ON c.ArtistID = ar.ID
            LEFT JOIN djmdLabel lb ON c.LabelID = lb.ID
            WHERE sh.rb_local_deleted = 0"""):
        n += 1
        arts |= artistas(a)
        if l:
            sellos.add(norm(l))

    perc = json.loads((RAIZ / "data" / "energia_percibida.json").read_text(encoding="utf-8"))
    favs = [v for v in perc.values() if not v.get("veto")]
    for v in favs:
        arts |= artistas(v.get("artist", ""))

    return {
        "generado": "scripts/perfilar_gusto.py",
        "fuente": f"djmdHistory ({n} reproducciones) + data/energia_percibida.json",
        "artistas": sorted(arts),
        "sellos": sorted(sellos),
    }


def groove_index() -> dict:
    tracks, brillo, cuerpo = {}, {}, {}
    for f in LIB.glob("*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))["referencia"]
        if not r.get("secciones"):
            continue
        dens = float(np.mean([s["densidad"] for s in r["secciones"]]))
        tracks[f.stem] = [round(dens, 3), round(r["balance"]["sub"], 3)]
        # brillo: cuanta energia vive arriba del bajo. Es la mitad medible de
        # "colorido"; la otra mitad es el modo, que sale de la key y no de aca.
        brillo[f.stem] = round(r["balance"]["medio"] + 2 * r["balance"]["aire"], 2)
        # CUERPO: medios y aire tiran para lados opuestos, y el rango dinamico
        # suma. Medido el 2026-09-23 sobre el set 143, que el DJ escucho entero:
        # los 10 temas que dejo tienen medios 14.5 y aire 5.4; los 7 que saco
        # llamandolos "oscuros", medios 11.4 y aire 7.4, con la mitad del rango
        # dinamico (3.7 dB contra 5.1). Para su oido "oscuro" no es falta de
        # agudos sino falta de CUERPO: un tema finito y comprimido. La formula
        # de brillo hacia exactamente lo contrario, porque pesaba el aire al
        # doble.
        cuerpo[f.stem] = round(r["balance"]["medio"] - r["balance"]["aire"]
                               + r["rango_dinamico_db"], 2)
    if not tracks:
        return {"tracks": {}, "desvios": [1.0, 1.0]}
    arr = np.array(list(tracks.values()))
    return {
        "generado": "scripts/perfilar_gusto.py",
        "referencia_salto_mediano": 1.25,
        "referencia_fuente": "236 pares consecutivos de data/setlists/ con los dos temas indexados",
        "desvios": [float(arr[:, 0].std() or 1.0), float(arr[:, 1].std() or 1.0)],
        "tracks": tracks,
        # percentil de brillo en la biblioteca: 0 es lo mas oscuro que hay, 1 lo
        # mas claro. Se guarda el percentil y no el valor crudo para que el peso
        # del solver signifique lo mismo aunque cambie la biblioteca.
        "brillo_pct": {k: round(float((np.array(list(brillo.values())) < v).mean()), 3)
                       for k, v in brillo.items()},
        "cuerpo_pct": {k: round(float((np.array(list(cuerpo.values())) < v).mean()), 3)
                       for k, v in cuerpo.items()},
    }


def main() -> None:
    con = conectar()
    mundo = mundo_propio(con)
    (RAIZ / "data" / "mundo_propio.json").write_text(
        json.dumps(mundo, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"mundo propio: {len(mundo['artistas'])} artistas, {len(mundo['sellos'])} sellos")

    g = groove_index()
    (RAIZ / "data" / "groove_index.json").write_text(
        json.dumps(g, ensure_ascii=False), encoding="utf-8")
    print(f"groove: {len(g['tracks'])} temas, desvios dens={g['desvios'][0]:.2f} sub={g['desvios'][1]:.2f}")


if __name__ == "__main__":
    main()
