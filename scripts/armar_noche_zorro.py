# -*- coding: utf-8 -*-
"""Rearma la noche del cumple de Zorro: warm (140), Sizer (139) y cierre (141).

Los tres comparten el groove de Mindloop (Maze 28), que el DJ pidio despues de
escuchar el warm: "extremadamente bueno Mindloop, quiero el warm en este flow".
El sesgo entra como PREFERENCIA, no como filtro: en el 139 y el 141 son retoques,
no un set nuevo, y los temas que el DJ llamo "mi sonido" quedan anclados.

Orden: 139 -> 141 (excluye 139) -> 140 (excluye los dos). Ninguna cancion se
repite en la noche, ni en otra version.

Uso:
    python scripts/armar_noche_zorro.py            # regenera configs y resuelve
    python scripts/armar_noche_zorro.py --solo-config
"""
from __future__ import annotations

import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))
from plomo.rules import R  # noqa: E402
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
LIB = RAIZ / "data" / "recetas" / "lib"

POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
PERC = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
E = lambda i: PERC.get(i, {}).get("E", POOL[i].get("energy") or 0)  # noqa: E731
MINDLOOP = "177299920"


def base(t: dict) -> str:
    """El titulo sin version ni feat.: la identidad de la CANCION."""
    x = re.sub(r"\s+feat\.?.*|\s+ft\.?.*", "", t["title"], flags=re.I)
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\s*[\(\[].*", "", x).lower())


def receta(i: str) -> dict | None:
    f = LIB / f"{i}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))["referencia"]
    secs = r["secciones"]
    alta = [x["energia"] for x in secs if x["tipo"] in ("groove", "drop")]
    baja = [x["energia"] for x in secs if x["tipo"] in ("breakdown", "respiro")]
    ea = st.mean(alta) if alta else 0
    return {"medio": r["balance"]["medio"], "aire": r["balance"]["aire"],
            "bd": (min(baja) / ea if baja and ea else 1)}


def gusto_ok(i: str) -> bool:
    """Los filtros que salieron de la escucha del DJ, no reglas del oficio."""
    x = receta(i)
    return x is None or not (x["medio"] < 5 or x["aire"] < 2 or (x["bd"] < 0.30 and E(i) >= 7))


# El veto es una MARCA, no una palabra en la nota. Buscar palabras clave fallaba
# en silencio: "muy abajo" y "malisimo" no estaban en la lista, y los dos temas
# que el DJ rechazo volvieron a entrar al set sin que nada lo avisara.
VETOS = {k for k, v in PERC.items() if v.get("veto")}
# El vecindario del set 43, el que el DJ llamo increible: 24 temas de 7 artistas.
# Repetir artista es la firma de ese set, no un error (reglas 1.5.0: tope 4).
VECINDARIO = json.loads((RAIZ / "data/vecindario_maze.json").read_text(encoding="utf-8"))
VEC_ART = [a.lower() for a in VECINDARIO["artistas"]]


def del_vecindario(i: str) -> bool:
    t = POOL[i]
    texto = (t["artist"] + " " + t["title"]).lower()
    return any(a in texto for a in VEC_ART)


RANK_MIND = [r["id"] for r in
             json.loads((RAIZ / "data/parecido_mindloop.json").read_text(encoding="utf-8"))
             if r["id"] in POOL]


def ids_de(num: int) -> list[str]:
    f = RAIZ / f"data/set_targets/set_{num}.json"
    return [t["content_id"] for t in json.loads(f.read_text(encoding="utf-8"))["tracks"]] if f.exists() else []


def buscar(titulo: str, artista: str) -> str:
    return next(i for i, t in POOL.items()
                if t["title"].lower().startswith(titulo.lower()) and artista.lower() in t["artist"].lower())


def _coherente(s: dict) -> None:
    """Saca de anclas, apertura y cierre lo que la propia banda del set excluye.

    Un tema fijo que no entra al pool se ignoraba adentro del solver con un
    AVISO, o sea DESPUES de que el config ya decia una cosa que no iba a pasar.
    Tres veces en esta ronda: el pico elegido en E8.7 contra un techo de 8.6,
    y Fragma en 7.5 como ancla del warm, que corta en 7.4. Se valida acá, contra
    la banda que el mismo config declara, y se dice cual se cae y por que.
    """
    lo_e, hi_e = s.get("e_pool", [0, 99])
    lo_b, hi_b = s.get("bpm", [0, 999])
    for campo in ("anclas", "inicio_fijo", "cierre_fijo"):
        quedan = []
        for i in s.get(campo, []):
            t = POOL.get(i)
            if not t:
                print(f"  [{campo}] {i} no esta en el pool, se cae")
                continue
            if not (lo_e <= (t.get("energy") or 0) <= hi_e):
                print(f"  [{campo}] se cae E{t['energy']} fuera de [{lo_e}, {hi_e}]: "
                      f"{t['artist'][:20]} - {t['title'][:34]}")
                continue
            if not (lo_b <= t["bpm"] <= hi_b):
                print(f"  [{campo}] se cae {t['bpm']:.0f} BPM fuera de [{lo_b}, {hi_b}]: "
                      f"{t['artist'][:20]} - {t['title'][:34]}")
                continue
            quedan.append(i)
        if campo in s:
            s[campo] = quedan
    s["anclas_en"] = {k: v for k, v in s.get("anclas_en", {}).items()
                      if k in set(s.get("anclas", [])) | set(s.get("inicio_fijo", []))
                      | set(s.get("cierre_fijo", []))}


def guardar(nombre: str, cfg: dict) -> Path:
    for s_ in cfg.get("sets", []):
        _coherente(s_)
    p = RAIZ / "data/set_configs" / nombre
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def resolver(p: Path) -> None:
    subprocess.run([PY, str(RAIZ / "scripts/select_set.py"), str(p)], cwd=str(RAIZ))


# Medido sobre los 8 setlists de Maze 28 y Simon Vuarambon, en ventanas de 17
# temas (el largo de nuestros sets): repiten un artista 5 veces por ventana
# (p90 9) y mueven el BPM 8 puntos. Nuestros sets daban 0 repeticiones y 4 de
# rango: el tope de 1 por artista y bandas de 121-125 eran mucho mas rigidos que
# ellos. Se sube el tope a 2 con la separacion minima que ya aplica el solver, y
# se ensanchan las bandas.
# "Ultimamente iteramos mi sonido con mas house, metele de eso": el set de la 1
# tenia 203 temas de House entre 120 y 126 que no podia usar.
GEN_PROG = {"Progressive House", "Melodic House & Techno", "House"}
GEN_HOUSE = {"House", "Progressive House", "Melodic House & Techno", "Indie Dance"}
GEN_ORG = {"Organic House", "Organic House / Downtempo", "Progressive House"}


def permitidos(generos: set, bpm: tuple, fuera: set, tope_mind: int) -> tuple[list, list]:
    """Elegibles del set y los mas parecidos al groove de Mindloop, en ese orden."""
    ok = [i for i in RANK_MIND
          if (POOL[i].get("genre") or "") in generos and bpm[0] <= POOL[i]["bpm"] <= bpm[1]
          and i not in fuera and i not in VETOS and gusto_ok(i)]
    return ok, ok[:tope_mind]


def noche_fuera(*nums: int) -> set:
    """Todo lo que ya suena esta noche, y cualquier otra version de esas canciones."""
    ids = {i for n in nums for i in ids_de(n)}
    bases = {base(POOL[i]) for i in ids if i in POOL}
    return ids | {i for i, t in POOL.items() if base(t) in bases}


def set_139() -> Path:
    fija = {k: buscar(*v) for k, v in {
        "imentet": ("Imentet", "Morttagua"), "opensea": ("Open Sea", "Cary Crank"),
        "sizer": ("Sizer", "Pietrocola"), "fragma": ("Fragma", "Kamilo"),
        "touch": ("Touch The Sky", "Marsh"), "olimpo": ("Olimpo", "Pavicich"),
        "go": ("Go", "Arias"),
        "boxer": ("I'm Lighter With You", "Boxer")}.items()}
    # el pool tiene que dar aire: con 212 candidatos y la apertura fija, el cierre
    # fijo y cuatro anclas, la busqueda se quedaba sin ramas validas
    elig, mind = permitidos(GEN_PROG, (119, 127), set(), 150)
    # el groove vive en energia media: sesgar el pool hacia el se lleva puesto el
    # material de pico. Con Fragma fijo al cierre (E7.5) y la regla de bajar 0.6
    # del pico, el set NECESITA un tema de 8.1+; quedaba uno solo y no habia
    # solucion. Se suman los mas parecidos al groove ENTRE los intensos.
    alta = [i for i in elig if E(i) >= 7.6][:40]
    house = [i for i in elig if (POOL[i].get("genre") or "") == "House"][:60]
    perm = set(elig[:400]) | set(mind) | set(alta) | set(house) | set(fija.values())
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_PROG and i not in perm)
    s["prefer_ids"] = sorted(set(mind) | {i for i in elig if del_vecindario(i)})
    s["prefer_bonus"] = 1.0
    s["max_per_artist"] = 4
    # Tempo y energia contra la referencia (reglas 1.8.0). Los pros van en 123 de
    # mediana con p25 122, iguales en los tres tercios del set, y su p90 de
    # energia es 6.9. Nosotros ibamos 2-3 BPM abajo de su piso y 1.5 puntos de
    # energia arriba de su techo: el DJ lo escucho como "muy lentos" y "muy
    # pasados" en la misma frase. El pico sigue existiendo, pero deja de vivir
    # arriba de lo que hace la referencia.
    # El tempo se corrige con el ARCO, no con el piso de la banda. Subir el piso
    # a 122 (el p25 de los pros) dejo afuera a Open Sea en 121, a Haunted en 121
    # y a un ancla del warm, y los dos sets de pico salieron SIN SOLUCION: el 25%
    # de los temas que tocan los pros esta debajo de ese p25, prohibirlo es
    # prohibirles la cola. Lo que se busca es que la MEDIANA quede en 123, y eso
    # lo hace bpm_arco tirando del centro con la banda ancha.
    s["bpm"] = [119, 127]
    s["bpm_arco"] = [122, 124]
    s["bpm_arco_peso"] = 2.5
    # El pool deja pasar hasta 8.6 para que las anclas grandes (The Whiteroom
    # E8.5, Olimpo E7.9) sigan existiendo: lo que se escucha "pasado" es que el
    # ARCO entero viva arriba, no que haya un tema grande en su lugar. El arco
    # es el que baja a la banda de los pros.
    s["e_pool"] = [5.0, 8.6]
    s["e_lo"], s["e_hi"] = 5.4, 7.2
    s["genres"] = sorted(GEN_PROG)   # sin esto la cuota de House no entra
    s["mezcla_objetivo"] = {"Progressive House": 0.6, "Melodic House & Techno": 0.2, "House": 0.2}
    s["bpm_span"] = 6
    s["bpm_span_peso"] = 1.5
    # UN pico anclado, no un arco entero arriba. Con el arco bajado a la banda
    # de los pros (su p90 de energia es 6.9 y su mediana 5.7) el solver dejo de
    # producir temas de 8.1+, y sin uno de esos la regla de bajar 0.6 del pico
    # hace imposible cerrar con Fragma en 7.5: el set salia SIN SOLUCION. Lo que
    # el DJ escucho como "muy pasado" es la MEDIANA del set, no que exista un
    # tema grande en su lugar, asi que el pico se ancla y el resto baja.
    techo = s["e_pool"][1]
    pico = max((i for i in perm if 8.1 <= E(i) <= techo and gusto_ok(i)), key=E, default=None)
    s["anclas"] = [fija["sizer"], fija["touch"], fija["olimpo"], fija["boxer"], fija["go"]]
    s["anclas_en"] = {fija["sizer"]: [0.55, 0.75], fija["olimpo"]: [0.70, 0.95]}
    if pico:
        s["anclas"].append(pico)
        s["anclas_en"][pico] = [0.62, 0.88]
        print(f"  pico anclado: E{E(pico):.1f} {POOL[pico]['artist']} - {POOL[pico]['title'][:40]}")
    s["inicio_fijo"] = [fija["imentet"], fija["opensea"]]
    s["cierre_fijo"] = [fija["fragma"]]
    s["_identidad"] = (s["_identidad"].split(" v5 (22/9)")[0] +
                       " v6 (22/9): mismo set con el groove de Mindloop en el relleno. Quedan fijos los "
                       "que el DJ llamo mi sonido: Imentet y Open Sea para abrir, Sizer en el pico, "
                       "Touch The Sky, Boxer, Olimpo y Fragma para cerrar.")
    return guardar("cumple_zorro.json", cfg)


def set_141() -> Path:
    fija = {k: buscar(*v) for k, v in {
        "jumbo": ("Jumbo", "Paul Thomas"), "haunted": ("Haunted", "Chelakhov"),
        "whiteroom": ("The Whiteroom", "Andy Moor")}.items()}
    fuera = noche_fuera(139) - set(fija.values())
    elig, mind = permitidos(GEN_HOUSE, (120, 127), fuera, 120)
    voz = [i for i in elig if re.search(r"feat\.?|ft\.|vocal|\bvox\b", POOL[i]["artist"] + " " + POOL[i]["title"], re.I)]
    perm = set(elig[:260]) | set(mind) | set(voz) | set(fija.values())
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro_3a5.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_HOUSE and i not in perm)
    s["prefer_ids"] = sorted(set(voz) | set(mind[:60]) | {i for i in elig if del_vecindario(i)})
    s["prefer_bonus"] = 1.2
    s["max_per_artist"] = 4
    # Tempo y energia contra la referencia (reglas 1.8.0). Los pros van en 123 de
    # mediana con p25 122, iguales en los tres tercios del set, y su p90 de
    # energia es 6.9. Nosotros ibamos 2-3 BPM abajo de su piso y 1.5 puntos de
    # energia arriba de su techo: el DJ lo escucho como "muy lentos" y "muy
    # pasados" en la misma frase. El pico sigue existiendo, pero deja de vivir
    # arriba de lo que hace la referencia.
    # El tempo se corrige con el ARCO, no con el piso de la banda. Subir el piso
    # a 122 (el p25 de los pros) dejo afuera a Open Sea en 121, a Haunted en 121
    # y a un ancla del warm, y los dos sets de pico salieron SIN SOLUCION: el 25%
    # de los temas que tocan los pros esta debajo de ese p25, prohibirlo es
    # prohibirles la cola. Lo que se busca es que la MEDIANA quede en 123, y eso
    # lo hace bpm_arco tirando del centro con la banda ancha.
    s["bpm"] = [119, 128]
    s["bpm_arco"] = [123, 125]
    s["bpm_arco_peso"] = 2.5
    # El pool deja pasar hasta 8.6 para que las anclas grandes (The Whiteroom
    # E8.5, Olimpo E7.9) sigan existiendo: lo que se escucha "pasado" es que el
    # ARCO entero viva arriba, no que haya un tema grande en su lugar. El arco
    # es el que baja a la banda de los pros.
    s["e_pool"] = [5.8, 8.6]
    s["e_lo"], s["e_hi"] = 6.2, 7.3
    s["bpm_span"] = 6
    s["bpm_span_peso"] = 1.5
    s["anclas"] = [fija["jumbo"], fija["whiteroom"]]
    # The Whiteroom (E8.5) es la carta mas grande del set: sin ventana caia en el
    # tema 5 y el pico quedaba al 29%. Va junto a Jumbo, en el tramo heroico.
    s["anclas_en"] = {fija["jumbo"]: [0.70, 0.88], fija["whiteroom"]: [0.62, 0.90]}
    s["cierre_fijo"] = [fija["haunted"]]
    s["entrada_desde"] = ids_de(139)[-1]
    # medido contra los pros: con la banda en 0.30 el set era una rampa
    # (corr posicion-energia +0.55); con 0.50 baja a +0.43 sin mover el pico.
    s["arco"]["tolerancia_arco_frac"] = 0.50
    return guardar("cumple_zorro_3a5.json", cfg)


def set_140() -> Path:
    fav = [i for i, x in PERC.items() if x.get("favorito") and i in POOL and 117 <= POOL[i]["bpm"] <= 125]
    fuera = noche_fuera(139, 141) - set(fav)
    elig, mind = permitidos(GEN_ORG, (116, 123), fuera, 170)
    lentos = [i for i in elig if POOL[i]["bpm"] < 119.0]
    alta = [i for i in elig if E(i) >= 6.5][:30]
    perm = set(mind) | set(lentos) | set(alta) | {i for i in fav if i in elig}
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro_warm.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_ORG and i not in perm)
    s["prefer_ids"] = sorted(set(mind[:60]) | {i for i in elig if del_vecindario(i)})
    s["prefer_bonus"] = 1.2
    s["max_per_artist"] = 4
    # Tempo y energia contra la referencia (reglas 1.8.0). Los pros van en 123 de
    # mediana con p25 122, iguales en los tres tercios del set, y su p90 de
    # energia es 6.9. Nosotros ibamos 2-3 BPM abajo de su piso y 1.5 puntos de
    # energia arriba de su techo: el DJ lo escucho como "muy lentos" y "muy
    # pasados" en la misma frase. El pico sigue existiendo, pero deja de vivir
    # arriba de lo que hace la referencia.
    # El tempo se corrige con el ARCO, no con el piso de la banda. Subir el piso
    # a 122 (el p25 de los pros) dejo afuera a Open Sea en 121, a Haunted en 121
    # y a un ancla del warm, y los dos sets de pico salieron SIN SOLUCION: el 25%
    # de los temas que tocan los pros esta debajo de ese p25, prohibirlo es
    # prohibirles la cola. Lo que se busca es que la MEDIANA quede en 123, y eso
    # lo hace bpm_arco tirando del centro con la banda ancha.
    s["bpm"] = [117, 125]
    s["bpm_arco"] = [120, 124]
    s["bpm_arco_peso"] = 2.5
    s["e_pool"] = [4.0, 7.4]
    s["e_lo"], s["e_hi"] = 4.8, 6.8
    s["bpm_span"] = 6
    s["bpm_span_peso"] = 1.5
    # "mis temas no muy al principio en warm, asi aprovecho la ultima hora a tirar
    # los mejores": los favoritos van de la mitad para adelante (00:00 en un warm
    # de 23 a 1). El mas bajo de todos queda libre: es el unico que puede abrir.
    anc = [i for i in fav if i in perm]
    abre = min(anc, key=E) if anc else None
    s["anclas"] = anc
    s["anclas_en"] = {i: [0.45, 1.0] for i in anc if i != abre}
    # el DJ tambien puede decir DONDE no va un tema sin vetarlo ("flojo ahi,
    # iria antes"): la ventana vale aunque el tema no sea ancla.
    s["anclas_en"].update({i: v["ubicacion"] for i, v in PERC.items()
                           if v.get("ubicacion") and i in perm})
    s["salida_hacia"] = ids_de(139)[0]
    # "dale mas onda al principio": los temas de la radio de It's Only Lightning
    # que ya estan en la biblioteca, anclados en el primer tramo del warm.
    onda = [i for i, t in POOL.items()
            if any(t["title"].startswith(k) for k in ("Ariana", "Astro World", "Homeboy"))
            and (t.get("genre") or "") in GEN_ORG
            and s["bpm"][0] <= t["bpm"] <= s["bpm"][1]
            and i not in fuera and i not in VETOS]
    perm |= set(onda)   # entran al pool aunque no vengan del ranking del groove
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_ORG and i not in perm)
    s["anclas"] = s["anclas"] + onda
    s["anclas_en"].update({i: [0.05, 0.40] for i in onda})
    return guardar("cumple_zorro_warm.json", cfg)



# --- versiones coloridas -----------------------------------------------------
# "Haceme las versiones coloridas de cada set". Color = melodia y brillo, que en
# la receta del audio son los medios y el aire. Son ALTERNATIVAS: comparten los
# empalmes de la noche y los temas que definen la identidad del set, pero el
# relleno lo elige el color en vez del groove.
# Que cambia un set "colorido" respecto de su base, segun rules/curaduria.json:
# la cuota de tonalidad mayor sube de 11% (mediana de los pros) a 25% (Ezequiel
# Arias, el mas colorido de la referencia) y el brillo entra al costo.
COLORIDO = R.get("estilo.colorido") or {}


def color_score(i: str) -> float:
    x = receta(i)
    return (x["medio"] + 2 * x["aire"]) if x else 0.0


def variante_color(base_cfg: str, num: int, nombre: str, quita: list, otros: list) -> Path:
    """La colorida arma SU pool: heredar el del base la dejaba identica, porque
    ese pool ya estaba recortado al groove y el color solo podia reordenarlo."""
    cfg = json.loads((RAIZ / "data/set_configs" / base_cfg).read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    fuera = noche_fuera(*otros)
    fijos = set(s.get("anclas", [])) | set(s.get("inicio_fijo", [])) | set(s.get("cierre_fijo", []))
    fijos -= set(quita)
    elegibles = [i for i, t in POOL.items()
                 if (t.get("genre") or "") in set(s["genres"])
                 and s["bpm"][0] <= t["bpm"] <= s["bpm"][1]
                 and s["e_pool"][0] <= (t.get("energy") or 0) <= s["e_pool"][1]
                 and i not in fuera and i not in VETOS and gusto_ok(i)]
    color = sorted(elegibles, key=color_score, reverse=True)[:220]
    altos = [i for i in sorted(elegibles, key=color_score, reverse=True)
             if E(i) >= 7.6][:40]   # el color vive en energia media: el pico aparte
    # Todo lo que este en tonalidad MAYOR entra al pool aunque no sea de los 220
    # mas brillantes. Sin esto la cuota de modo es una orden imposible: el 84%
    # de la biblioteca es menor, y recortar por brillo antes de elegir dejaba
    # al solver sin un solo tema mayor para cumplirla. Es el mismo error que la
    # cuota de genero pidiendo House con House fuera de `genres`.
    mayores = [i for i in elegibles if (POOL[i].get("key") or "").endswith("B")]
    perm = set(color) | set(altos) | set(mayores) | fijos
    s["num"] = num
    s["name"] = nombre
    s["grupo"] = s["grupo"] + " color"
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in set(s["genres"]) and i not in perm)
    # El brillo ahora lo cobra el costo (color_peso), no una lista de preferidos
    # por afuera. Con la lista, el 143 salia con dos temas del percentil 33 y 43
    # de brillo abriendo el set: los preferidos empujaban, pero nada impedia
    # arrancar oscuro.
    for k, v in COLORIDO.items():
        s[k] = v
    s.pop("prefer_ids", None)
    s.pop("prefer_bonus", None)
    # La colorida NO hereda el arranque fijo del base. Imentet y Open Sea son la
    # apertura que el DJ eligio para el 139 y estan bien ahi, pero son los dos
    # temas mas oscuros del 143, y en un set que se llama colorido abren en el
    # percentil 33 y 43. El empalme con el set vecino lo sostienen `entrada` y
    # `salida`, que no obligan a ningun tema en particular.
    s.pop("inicio_fijo", None)
    s["anclas"] = [i for i in s.get("anclas", []) if i not in quita]
    s["anclas_en"] = {k: v for k, v in s.get("anclas_en", {}).items() if k not in quita}
    s["_identidad"] = (s["_identidad"].split(" v5")[0].split(" v6")[0] +
                       " VERSION COLORIDA: mismo horario y mismos empalmes, pero el pool" + 
                       " lo ordena la melodia y el brillo (medios y aire) en vez del groove.")
    return guardar(base_cfg.replace(".json", "_color.json"), cfg)


def set_145() -> Path:
    """Alternativa para la franja de 1 a 3, al estilo del set 43: un vecindario
    chico recorrido a fondo. No sale de subir el tope por artista —eso solo lo
    permite— sino de achicar el pool a los siete artistas de ese set."""
    fuera = noche_fuera(140, 141)
    elig = [i for i, t in POOL.items()
            if del_vecindario(i) and (t.get("genre") or "") in GEN_PROG
            and 119 <= t["bpm"] <= 126 and 4.5 <= (t.get("energy") or 0) <= 7.8
            and i not in fuera and i not in VETOS and gusto_ok(i)]
    cfg = {"pool": "data/pool.json", "targets_dir": "data/set_targets",
           "exclude_artists": [], "permitir_repetir_entre_sets": True,
           "_comentario": ("Cumple de Zorro, alternativa de 1 a 3 al estilo del set 43: "
                           "solo los artistas de ese set, hasta 4 temas cada uno."),
           "sets": [{"num": 145, "grupo": "Cumple Zorro vecindario", "n": 17,
                     "name": "145. Cumple Zorro " + chr(183) + " Vecindario " + chr(183) + " 1 a 3 AM " + chr(8212) + " 2h " + chr(8212) + " 2026-09-22",
                     "_identidad": ("El recorrido por un vecindario, no una coleccion de temas "
                                    "sueltos: Cendryma, Gai Barone, Rockka, Maze 28, Hobin Rude, "
                                    "Chelakhov y Cary Crank, hasta cuatro temas cada uno. Es la "
                                    "forma del set 43, el que el DJ llamo increible."),
                     "duration_h": 2.0, "bpm": [119, 126], "bpm_arco": [122, 124], "bpm_arco_peso": 2.5, "e_pool": [4.5, 7.8],
                     "e_lo": 5.2, "e_hi": 7.2, "max_per_artist": 4,
                     "artists": ["*"], "genres": sorted(GEN_PROG),
                     "beam": 4000,
                     # el pool chico hace que el set se quede clavado en la rueda:
                     # daba 50% contra el 22% del set 43, que es el modelo
                     "arco": {"pico_en_pct": 0.8, "caida_post_pico_pct": 0.15,
                              "tolerancia_arco_frac": 0.35,
                              "penal_quedarse_en_la_rueda": 2.0},
                     "exclude_ids": sorted(i for i in POOL if i not in set(elig)),
                     "prefer_ids": elig, "prefer_bonus": 0.8}]}
    print("vecindario elegible:", len(elig), "temas")
    return guardar("cumple_zorro_vecindario.json", cfg)


def colores() -> None:
    q = {k: buscar(*v) for k, v in {
        "touch": ("Touch The Sky", "Marsh"), "boxer": ("I" + chr(39) + "m Lighter With You", "Boxer"),
        "olimpo": ("Olimpo", "Pavicich"), "white": ("The Whiteroom", "Andy Moor")}.items()}
    for base_cfg, num, otros, nom, quita in (
            ("cumple_zorro_warm.json", 142, [139, 141],
             "142. Cumple Zorro " + chr(183) + " Warm Colorido " + chr(183) + " 23 a 1 AM " + chr(8212) + " 2h " + chr(8212) + " 2026-09-22", []),
            ("cumple_zorro.json", 143, [140, 141],
             "143. Cumple Zorro " + chr(183) + " Colorido " + chr(183) + " 1 a 3 AM " + chr(8212) + " 2h " + chr(8212) + " 2026-09-22",
             [q["touch"], q["boxer"], q["olimpo"]]),
            ("cumple_zorro_3a5.json", 144, [140, 139],
             "144. Cumple Zorro " + chr(183) + " Colorido " + chr(183) + " 3 a 5 AM " + chr(8212) + " 2h " + chr(8212) + " 2026-09-22", [q["white"]])):
        ruta = variante_color(base_cfg, num, nom, quita, otros)
        print("===== set " + str(num) + ": " + ruta.name)
        resolver(ruta)


if __name__ == "__main__":
    solo = "--solo-config" in sys.argv
    if "--vecindario" in sys.argv:
        resolver(set_145())
        sys.exit()
    if "--color" in sys.argv:
        colores()
        sys.exit()
    for nombre, hacer in (("139", set_139), ("141", set_141), ("140", set_140)):
        p = hacer()
        print(f"\n===== set {nombre}: {p.name}")
        if not solo:
            resolver(p)
