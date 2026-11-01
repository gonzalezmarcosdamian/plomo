"""Session 05: asigna un clip a cada uno de los 76 planos, escribe session_05_etapa_<n>.json y arma
la hoja de recorrido (una imagen por etapa) con un cuadro real de cada plano, con encuadre y grado, y
una hoja con solo los planos que cambiaron contra los JSON del ultimo commit.

    .venv/Scripts/python.exe elegir_session_05.py [--sin-hojas]

Lo escribio y corrio el editor el 2026-11-01 desde un scratchpad; queda aca para que la eleccion
se pueda rehacer. Vuelta 2 (mismo dia): lo que bloqueo el revisor, P16, P20, P28/31, P33/50 y
las etapas 4 y 5 sin carrusel. Los cuadros temporales van a cuadros_05/, al lado del script: borrarlos despues.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(r"C:\Users\gonza\Documents\plomo")
VIDEO = RAIZ / "data" / "video"
STOCK = RAIZ / "postproduction" / "stock" / "pixabay"
TMP = Path(__file__).parent / "cuadros_05"
HOJA = r"C:\Users\gonza\Pictures\plomo_session_05_recorrido_etapa_{}.jpg"
CAMBIOS = r"C:\Users\gonza\Pictures\plomo_session_05_cambios.jpg"
FPS_SALIDA, FACTOR_MAX = 30, 3.0
AFUERA = {116206, 119242, 218961, 285882, 221728, 230409,
          128295, 128296, 128298, 178700, 154643, 91392, 116205, 146169,
          # vuelta 2: camino (103195, 168612, 178711, 128220, 132720), estela (41093, 378038, 204990),
          # halo magenta (221999), sol en el horizonte (119784, 117745, 178707, 269567, 267172, 30218),
          # sol visible antes y despues de un tramo sin sol demasiado corto (19409), pescador (134382),
          # estela y sol en la bruma despues de la puesta (203676)
          103195, 168612, 178711, 128220, 132720, 41093, 378038, 204990, 221999, 119784, 117745,
          178707, 269567, 267172, 30218, 19409, 134382, 203676}
# Tramo del clip por plano (desde, hasta); None es hasta el final. 197435 se corta antes de que el sol
# llegue al horizonte; las segundas veces usan otra parte del clip, no el clip entero espejado.
TRAMO = {31: (20.0, None), 65: (0.0, 31.0), 72: (22.0, None)}
# 200121 va recortado arriba a la izquierda: abajo hay un valle que puede ser un pueblo y a la
# derecha, sobre el horizonte, asoma el sol (despues de la puesta no puede verse)
ENC_CLIP = {200121: "crop=2400:1350:0:0,scale=2560:1440:flags=lanczos"}
ENCUADRE = "scale=2560:1440:force_original_aspect_ratio=increase:flags=lanczos,crop=2560:1440"
FASES = "ABCDEFG"


def curva(master, r=None, b=None):
    s = f"curves=master='{master}'"
    if r:
        s += f":r='0/0 0.5/{r} 1/1'"
    if b:
        s += f":b='0/0 0.5/{b} 1/1'"
    return s


# Un grado base por etapa: calido y suave, altas apenas bajadas, negros firmes. Lo de la 04.
GRADO = {
    1: curva("0/0 0.05/0.04 0.5/0.5 0.92/0.91 1/0.98", "0.506", "0.494")
       + ",huesaturation=saturation=-0.08:colors=g+y:strength=1",
    2: curva("0/0 0.05/0.04 0.5/0.5 0.92/0.91 1/0.98", "0.508", "0.492")
       + ",huesaturation=saturation=-0.08:colors=g+y:strength=1",
    3: curva("0/0 0.05/0.038 0.5/0.5 0.93/0.92 1/0.98", "0.512", "0.488")
       + ",huesaturation=saturation=-0.06:colors=g:strength=1",
    4: curva("0/0 0.06/0.045 0.5/0.5 0.9/0.88 1/0.96", "0.51", "0.49")
       + ",huesaturation=saturation=-0.05:colors=r+y:strength=1",
    5: curva("0/0 0.06/0.045 0.5/0.49 0.92/0.9 1/0.97")
       + ",huesaturation=saturation=-0.08:colors=r+y+m:strength=1",
}
# Ajustes por clip, solo donde lo pide
GRADO_CLIP = {
    # nubes pastel que vienen claras: medios abajo y un pelo de azul para que sea la hora azul
    146169: curva("0/0 0.06/0.04 0.5/0.43 0.9/0.8 1/0.92", None, "0.51"),
    # discos blancos: altas tibias para que se lean como sol y no como luna
    169565: "curves=master='0/0 0.06/0.045 0.5/0.5 0.9/0.88 1/0.96':r='0/0 0.5/0.53 1/1'"
            ":g='0/0 0.5/0.5 1/0.97':b='0/0 0.5/0.465 1/0.88'",
    133185: "curves=master='0/0 0.06/0.045 0.5/0.5 0.9/0.88 1/0.96':r='0/0 0.5/0.515 1/1'"
            ":g='0/0 1/0.985':b='0/0 0.5/0.48 1/0.92'",
    # cielos de dia que tienen que leerse como hora azul: medios abajo y un pelo de azul
    292383: curva("0/0 0.06/0.04 0.5/0.44 0.9/0.8 1/0.9", None, "0.51"),
    9153: curva("0/0 0.06/0.035 0.5/0.4 0.9/0.74 1/0.85", "0.49", "0.52"),
}

DESC = {
    168620: "copa de roble desde abajo con el sol alto entre las hojas",
    340939: "piso de bosque verde con lirios del valle y sol entre los troncos",
    295782: "hojas al sol contra el cielo claro desenfocado",
    327220: "eucaliptos desde abajo contra el cielo azul",
    215884: "claro de bosque con pasto alto, digitales y troncos",
    340940: "otro tramo del bosque verde, troncos y lirios",
    168614: "copa de roble desde abajo con el sol entre las hojas",
    340938: "hojas de roble encendidas por el sol de costado, el bosque en sombra detras",
    122802: "helechos y troncos con luz filtrada",
    103195: "rayos de sol entre los arboles del bosque",
    230417: "troncos de bosque abierto con el sol mas bajo y sombras largas: la tarde avanza",
    210173: "rio turquesa bajo arboles con las hojas encendidas, sol alto",
    356398: "poza turquesa entre arboles, sol alto",
    206997: "arroyo de bosque con piedras y verde",
    133179: "rocas con musgo y el agua corriendo en el bosque",
    206998: "otro tramo del arroyo de bosque",
    119784: "turbera con algodoncillo y charcos, el sol bajo en la bruma sobre el bosque",
    291385: "arroyo de agua calida con hojas, luz de tarde",
    272431: "ondas del rio con el reflejo dorado de la tarde",
    152739: "espigas de pasto al viento con luz calida",
    197946: "juncos secos dorados de cerca",
    146586: "pasto verde a contraluz, de cerca",
    154639: "juncal seco sobre el agua quieta",
    154643: "pasto seco dorado de cerca",
    217947: "pasto verde alto al viento, el bosque desenfocado detras",
    91388: "algodoncillo blanco en el pastizal junto al agua",
    230414: "brezo florecido con el sol bajo entre los arboles",
    117503: "algodoncillo de cerca con el sol bajo detras de nubes finas",
    137113: "juncos rosados a contraluz sobre fondo oscuro: la luz rosada que queda",
    66817: "flor amarilla entre el pasto, de cerca, con el dia claro desenfocado detras",
    275876: "trigal verde al viento bajo cumulos, sol alto",
    318222: "rapidos de agua clara entre rocas al sol",
    301800: "lomas de brezal con luz calida y rasante bajo un cielo de altocumulos",
    133185: "el sol todavia alto sobre un banco de nubes",
    48899: "rayos de sol entre nubes doradas",
    128222: "llanura con una laguna y el sol bajo en la bruma",
    264472: "cerros sobre un mar de nubes encendido de naranja, el sol fuera de cuadro",
    197435: "el sol bajando a un banco de nubes, cortado antes de que llegue al horizonte",
    91942: "nubes oscuras con la franja de luz del sol que se va, sin el disco",
    292383: "cirros en el cielo azul que se apaga",
    9153: "cumulos en el azul de la hora azul",
    119781: "turbera con algodoncillo y el sol bajo en la bruma",
    128296: "aereo de la llanura con el sol bajo en la neblina",
    128295: "aereo de una laguna en la llanura con el sol bajo en la neblina",
    292703: "arbol en silueta con el sol rojo bajo detras de las ramas",
    273806: "ramas de sauce en silueta con el sol naranja bajo",
    169565: "el disco del sol bajo en la bruma entre pastos, sin tocar el horizonte",
    178710: "LA PUESTA: el brezal con robles y el sol tocando la linea de arboles",
    18503: "todo el cielo con nubes rosadas y naranjas: el arrebol",
    203676: "pantano que refleja el cielo anaranjado, sin sol a la vista",
    200121: "nubes rojas y naranjas sobre el horizonte oscuro",
    146169: "nubes suaves, el rosa que se apaga",
    221999: "laguna de bosque con plantas de agua y cumulos de verano",
    323231: "plumeros de cortadera con luz de costado contra el cielo azul",
    200121: "nubes rojas y naranjas del arrebol, recortado al cielo",
    210790: "nubes rosadas sobre el bosque en silueta, el cielo pasando a azul",
}

# (plano, id, espejado, fase). La segunda vez de un clip va espejada.
ASIG = [
    (1, 168620, 0, "A"), (2, 340939, 0, "A"), (3, 295782, 0, "A"), (4, 327220, 0, "A"),
    (5, 215884, 0, "A"), (6, 340940, 0, "A"), (7, 168614, 0, "A"), (8, 340938, 0, "A"),
    (9, 122802, 0, "A"), (10, 327220, 1, "A"), (11, 295782, 1, "A"), (12, 340939, 1, "A"),
    (13, 168620, 1, "A"), (14, 215884, 1, "A"), (15, 340940, 1, "A"), (16, 66817, 0, "A"),
    (17, 168614, 1, "A"), (18, 122802, 1, "A"), (19, 340938, 1, "A"), (20, 275876, 0, "A"),
    (21, 210173, 0, "A"), (22, 356398, 0, "A"), (23, 206997, 0, "A"), (24, 133179, 0, "A"),
    (25, 206998, 0, "A"), (26, 210173, 1, "A"), (27, 206997, 1, "A"), (28, 318222, 0, "A"),
    (29, 356398, 1, "A"), (30, 133179, 1, "A"), (31, 318222, 1, "A"), (32, 206998, 1, "A"),
    (33, 230417, 0, "B"),
    (34, 323231, 0, "B"), (35, 146586, 0, "B"), (36, 291385, 0, "B"), (37, 91388, 0, "B"),
    (38, 323231, 1, "B"), (39, 152739, 0, "B"), (40, 146586, 1, "B"), (41, 154639, 0, "B"),
    (42, 197946, 0, "B"), (43, 217947, 0, "B"), (44, 272431, 0, "B"), (45, 152739, 1, "B"),
    (46, 291385, 1, "B"), (47, 91388, 1, "B"), (48, 154639, 1, "B"), (49, 217947, 1, "B"),
    # P50: 301800 tenia techos en el valle (revisor, vuelta 2); 275876 espejado, a 30 planos de P20
    (50, 275876, 1, "B"), (51, 197946, 1, "B"), (52, 272431, 1, "B"), (53, 230417, 1, "B"),
    (54, 230414, 0, "C"), (55, 117503, 0, "C"), (56, 119781, 0, "C"),
    # etapa 4: cada clip una vez, el sol bajando parejo hasta la puesta
    (57, 133185, 0, "C"), (58, 48899, 0, "C"), (59, 230414, 1, "C"), (60, 128222, 0, "C"),
    (61, 117503, 1, "C"), (62, 264472, 0, "C"), (63, 273806, 0, "C"), (64, 169565, 0, "C"),
    (65, 197435, 0, "C"), (66, 292703, 0, "C"), (67, 91942, 0, "C"), (68, 178710, 0, "D"),
    # etapa 5: ordenada por luz, dos repetidos (137113, 18503) a 3 planos; cierra en el azul mas oscuro
    (69, 137113, 0, "E"), (70, 200121, 0, "E"), (71, 18503, 0, "E"), (72, 137113, 1, "E"),
    (73, 210790, 0, "E"), (74, 18503, 1, "E"), (75, 9153, 0, "F"), (76, 292383, 0, "F"),
]


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def chequear(planos, info):
    """Las reglas del encargo, antes de escribir nada."""
    errores, usos = [], {}
    assert [a[0] for a in ASIG] == [p["n"] for p in planos], "falta o sobra un plano"
    for i, (n, id_, flip, fase) in enumerate(ASIG):
        usos.setdefault(id_, []).append(n)
        if id_ in AFUERA:
            errores.append(f"{n}: {id_} esta afuera")
        if i and ASIG[i - 1][1] == id_:
            errores.append(f"{n}: {id_} repite en el plano vecino")
        if i and FASES.index(fase) < FASES.index(ASIG[i - 1][3]):
            errores.append(f"{n}: la fase vuelve de [{ASIG[i - 1][3]}] a [{fase}]")
        if id_ not in DESC:
            errores.append(f"{n}: {id_} sin nota")
    for id_, ns in usos.items():
        if len(ns) > 2:
            errores.append(f"{id_} va {len(ns)} veces: {ns}")
        if len(ns) == 2 and not ASIG[ns[1] - 1][2]:
            errores.append(f"{id_}: la segunda vez (plano {ns[1]}) no va espejada")
    pares = {}
    for a, b in zip(ASIG, ASIG[1:]):
        if b[0] >= 57 and (a[1], b[1]) in pares:  # el carrusel se mira en las etapas 4 y 5
            errores.append(f"{b[0]}: el par {a[1]}-{b[1]} ya va en el plano {pares[(a[1], b[1])]}")
        pares[(a[1], b[1])] = b[0]
    etapa = {p["n"]: p["etapa"] for p in planos}
    e4 = [a[1] for a in ASIG if etapa[a[0]] == 4]
    if len(e4) != len(set(e4)):
        errores.append("la etapa 4 repite un clip")
    e5 = {}
    for a in ASIG:
        if etapa[a[0]] == 5:
            e5.setdefault(a[1], []).append(a[0])
    dobles = {k: v for k, v in e5.items() if len(v) > 1}
    if len(dobles) > 2:
        errores.append(f"etapa 5 con {len(dobles)} repetidos")
    errores += [f"etapa 5: {k} a menos de 3 planos {v}" for k, v in dobles.items() if v[1] - v[0] < 3]
    puestas = [a[0] for a in ASIG if a[3] == "D"]
    if puestas != [68]:
        errores.append(f"puestas en {puestas}")
    for p in planos:
        dur, fps = info[p["id_"]]
        p["desde"], p["hasta"] = TRAMO.get(p["n"], (0.0, None))
        p["factor"] = (p["segundos_de_clip"] + 1) * FPS_SALIDA / (((p["hasta"] or dur) - p["desde"]) * fps)
        if p["factor"] > FACTOR_MAX:
            errores.append(f"{p['n']}: x{p['factor']:.2f}")
    return errores, usos


def main():
    plan = json.loads((VIDEO / "session_05_planos.json").read_text(encoding="utf-8"))["planos"]
    rev = json.loads((VIDEO / "session_05_revision.json").read_text(encoding="utf-8"))
    info = {r["id"]: (r["largo"]["duracion_s"], r["largo"]["fps"]) for r in rev}
    por_n = {a[0]: a for a in ASIG}
    planos = [dict(p, id_=por_n[p["n"]][1], flip=por_n[p["n"]][2], fase=por_n[p["n"]][3]) for p in plan]
    errores, usos = chequear(planos, info)
    if errores:
        sys.exit("NO:\n" + "\n".join(errores))

    cambiados = []
    for e in range(1, 6):
        viejo = subprocess.run(["git", "-C", str(RAIZ), "show", f"HEAD:data/video/session_05_etapa_{e}.json"],
                               capture_output=True, text=True, encoding="utf-8").stdout
        viejos = {q["n"]: firma(q) for q in json.loads(viejo)["planos"]} if viejo else {}
        salida = []
        for p in (q for q in planos if q["etapa"] == e):
            vez = "; segunda vez, espejado" if p["flip"] else ""
            q = {"n": p["n"], "id": p["id_"], "desde": p["desde"],
                 "encuadre": ENC_CLIP.get(p["id_"], ENCUADRE) + (",hflip" if p["flip"] else ""),
                 "grado": GRADO_CLIP.get(p["id_"], GRADO[e]),
                 "nota": f"[{p['fase']}] {DESC[p['id_']]}{vez}"}
            if p["hasta"] is not None:
                q["hasta"] = p["hasta"]
            if firma(q) != viejos.get(p["n"]):
                cambiados.append(p["n"])
            salida.append(q)
        (VIDEO / f"session_05_etapa_{e}.json").write_text(
            json.dumps({"etapas": [e], "planos": salida}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for e in range(1, 6):
        ps = [p for p in planos if p["etapa"] == e]
        dos = sorted({p["id_"] for p in ps if len(usos[p["id_"]]) == 2})
        print(f"etapa {e}: planos {ps[0]['n']}-{ps[-1]['n']} ({len(ps)}), {len({p['id_'] for p in ps})} clips, "
              f"max x{max(p['factor'] for p in ps):.2f} (plano {max(ps, key=lambda p: p['factor'])['n']}), "
              f"dos veces en total: {dos}")
    for e in (4, 5):
        cuenta = {}
        for p in planos:
            if p["etapa"] == e:
                cuenta[p["id_"]] = cuenta.get(p["id_"], 0) + 1
        print(f"etapa {e}, veces por clip:", cuenta)
    print("cambiaron:", cambiados)
    print("sobre x2.2:", [(p["n"], p["id_"], round(p["factor"], 2)) for p in planos if p["factor"] > 2.2])
    if "--sin-hojas" not in sys.argv:
        hojas(planos, info, json.loads((VIDEO / "session_05_recorrido.json").read_text(encoding="utf-8")))
        hoja_cambios([p for p in planos if p["n"] in cambiados])


def firma(q):
    s = q.get("fuente", q)
    return (s.get("id"), s.get("encuadre"), q.get("grado"), float(s.get("desde", 0)), s.get("hasta"))


def fuente(tam, b=False):
    return ImageFont.truetype(f"C:/Windows/Fonts/arial{'bd' if b else ''}.ttf", tam)


def hoja_cambios(ps):
    """Solo los planos que cambiaron: 5 por fila, 1600 de ancho."""
    cols, tw, th = 5, 312, 176
    img = Image.new("RGB", (1600, 46 + ((len(ps) + cols - 1) // cols) * (th + 26)), (14, 14, 14))
    d = ImageDraw.Draw(img)
    d.text((10, 10), f"Session 05, vuelta 2: los {len(ps)} planos que cambiaron (cuadro real con encuadre y grado; "
                     f"en los tramos cortados, el ultimo segundo)", font=fuente(19, True), fill=(240, 240, 240))
    for i, p in enumerate(ps):
        x, y = 8 + (i % cols) * 318, 46 + (i // cols) * (th + 26)
        img.paste(Image.open(TMP / f"{p['n']:02d}.jpg").resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x + 2, y + th + 3), f"P{p['n']}  {mmss(p['entra'])}  [{p['fase']}]  {p['id_']}"
                                    f"{'  esp' if p['flip'] else ''}  x{p['factor']:.2f}", font=fuente(15, True),
               fill=(255, 255, 255))
    img.save(CAMBIOS, quality=90)
    print("hoja", CAMBIOS, img.size)


def cuadro(p, info, e):
    dur = info[p["id_"]][0]
    t = p["hasta"] - 0.5 if p["hasta"] else (p["desde"] + dur) / 2
    out = TMP / f"{p['n']:02d}.jpg"
    vf = f"{ENC_CLIP.get(p['id_'], ENCUADRE)}{',hflip' if p['flip'] else ''},{GRADO_CLIP.get(p['id_'], GRADO[e])},scale=392:220:flags=area"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(STOCK / f"{p['id_']}.mp4"),
                    "-vf", vf, "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    return out


def hojas(planos, info, receta):
    TMP.mkdir(exist_ok=True)
    f = fuente
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda p: cuadro(p, info, p["etapa"]), planos))
    for e in range(1, 6):
        ps = [p for p in planos if p["etapa"] == e]
        temas = list(dict.fromkeys(p["tema"].replace("\ufffd", "e") for p in ps))
        et = receta["etapas"][e - 1]
        cab = 70 + 22 * len(temas)
        filas = (len(ps) + 3) // 4
        img = Image.new("RGB", (1600, cab + filas * 252), (14, 14, 14))
        d = ImageDraw.Draw(img)
        d.text((12, 10), f"Etapa {e}: {et['nombre']}   {mmss(ps[0]['entra'])} a {mmss(ps[-1]['sale'])}   "
                         f"planos {ps[0]['n']}-{ps[-1]['n']}   estado: elegido, sin estirar", font=f(24, True),
               fill=(240, 240, 240))
        d.text((12, 42), et["luz"], font=f(17), fill=(230, 190, 120))
        for i, t in enumerate(temas):
            d.text((12, 66 + 22 * i), f"- {t}", font=f(17), fill=(200, 200, 200))
        for i, p in enumerate(ps):
            x, y = 8 + (i % 4) * 398, cab + (i // 4) * 252
            img.paste(Image.open(TMP / f"{p['n']:02d}.jpg"), (x, y))
            rot = f"P{p['n']}  {mmss(p['entra'])}  [{p['fase']}]  {p['id_']}{'  esp' if p['flip'] else ''}  x{p['factor']:.2f}"
            d.text((x + 2, y + 224), rot, font=f(17, True), fill=(255, 255, 255))
        img.save(HOJA.format(e), quality=90)
        print("hoja", HOJA.format(e), img.size)


if __name__ == "__main__":
    main()
