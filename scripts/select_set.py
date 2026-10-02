"""Selecciona un set desde un pool respetando escalera Camelot + arco de energia.

A diferencia de reordenar (que trabaja con una seleccion ya fija), aca se ELIGE
que tracks entran. Es la unica forma de que key y energia no se contradigan.

Beam search: en cada posicion se prueba cada candidato cuyo key este a distancia
<=1 del anterior, penalizando el desvio del arco. Se conservan los mejores K.
"""
import heapq
import json
import re
import unicodedata
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.camelot import distance as _cam_dist_canonico  # noqa: E402
from plomo.rules import R  # noqa: E402

# `solo_sin_tocar`: saca del pool todo lo que el DJ YA TOCO, segun djmdHistory.
# Es OPT-IN POR SET y tiene que seguir siendo opt-in: medido contra el set 150,
# que el DJ llamo perfecto, un filtro asi le habria sacado 8 de 18 temas --Amnesia
# y The Silver Lily los habia tocado dos dias antes, y a The Silver Lily la pidio
# EL por nombre--. Solo se prende cuando el DJ pide "musica nueva", que es cuando
# el filtro dice lo que el quiere decir.
try:
    from plomo.tocados import toco as _toco  # noqa: E402
except Exception:                            # noqa: BLE001
    def _toco(_):
        return None

# Los numeros no viven aca: viven en rules/curaduria.json con su porque y su
# evidencia, para que el agente analista pueda medirlos y discutirlos.
BEAM = R.get("solver.beam")
MIN_GAP = R.get("repeticion.separacion_minima_codigo", 3)  # separacion entre temas del mismo productor
MAX_E_STEP = R.get("energia.max_escalon")
MAX_CAM = R.get("armonia.max_camelot_dist")
MAX_RETROCESO = R.get("energia.max_retroceso_en_subida")
PICO_PCT = R.get("energia.pico_en_pct")
CAIDA_PCT = R.get("energia.caida_post_pico_pct")
BAJA_CIERRE = R.get("energia.baja_minima_al_cierre")
PESO_ARCO = R.get("energia.peso_desvio_arco")
# El arco es una BANDA, no una linea. Cobrar |energia - arco| en cada
# posicion es, literalmente, pedir que la energia sea funcion del reloj:
# la correlacion posicion-energia daba +0.79 contra +0.13 de los sets
# reales, fuera del rango entero del corpus (max observado +0.60). Un DJ
# respeta la forma general y se mueve libre adentro de ella, asi que solo
# se cobra el desvio que se SALE de la banda.
TOL_ARCO_FRAC = R.get("energia.tolerancia_arco_frac", 0.0)
# Cuanta energia tiene que RECORRER el set de punta a punta, y cuanto vale cada
# punto de ese recorrido. El rango es una propiedad GLOBAL del set (max - min)
# pero todos los demas terminos del costo son locales —por transicion o por
# posicion—, asi que nadie lo estaba pidiendo. La banda del arco PERMITE
# alejarse; permitido no es preferido, y el solver se quedaba donde estan los
# temas armonicamente mas comodos, que es el centro denso del pool. Medido: seis
# palancas distintas (bandas, e_pool, beam, umbral de paso, tope de escalon,
# salto de BPM) dejaron el rango clavado en 2.0 contra 2.9 de los DJ reales.
SPAN_OBJETIVO = R.get("energia.span_objetivo", 0.0)
PESO_SPAN = R.get("energia.span_peso", 0.0)
PESO_CAM = R.get("armonia.peso_salto_camelot")
PENAL_MISMA_KEY_DESDE = R.get("armonia.penal_misma_key_desde")
PESO_MISMA_KEY = R.get("armonia.penal_misma_key_desde_peso", 1.2)
PESO_QUIETO = R.get("armonia.penal_quedarse_en_la_rueda", 0.8)
MONOTONIA_DESDE = R.get("armonia.monotonia_desde", 2)
PESO_MONOTONIA = R.get("armonia.monotonia_desde_peso", 0.5)
ENERGIA_QUIETA = R.get("energia.umbral_paso_plano", 0.15)
PESO_ENERGIA_QUIETA = R.get("energia.penal_paso_plano", 0.35)
RACHA_ENERGIA_DESDE = R.get("energia.racha_misma_direccion_desde", 2)
PENAL_RACHA_BAJANDO = R.get("energia.penal_racha_bajando", 0.0)
CIERRE_NO_BAJA = bool(R.get("energia.cierre_no_baja_del_inicio", False))
PESO_RACHA_ENERGIA = R.get("energia.racha_misma_direccion_peso", 0.7)
# Descuento de un tema ancla. Mayor que cualquier costo razonable de una
# posicion, para que el ancla entre salvo que rompa una restriccion dura.
# --- la jerarquia que pidio el DJ (2026-09-23), de arriba abajo ---------------
# "quiero que domine la energia y groove constante, luego lo progresivo y luego
# recien la cuota de genero; artistas le gana, productores le gana a cuota de
# genero". Estaba al reves: peso_mezcla era 8.0 hardcodeado y el desvio del arco
# 3.0, asi que el genero mandaba 2.7 veces mas que la energia, y los cuatro
# temas que el DJ rechazo escuchando entraron todos por la cuota.
PESO_GROOVE = R.get("groove.peso_continuidad", 0.0)
SALTO_GROOVE = R.get("groove.salto_tolerado", 1.25)
NUCLEO_PROG = {g.lower() for g in (R.get("estilo.nucleo_progresivo") or [])}
PESO_PROG = R.get("estilo.peso_progresivo", 0.0)
PESO_AJENO = R.get("sonido_propio.peso_ajeno", 0.0)
PESO_MEZCLA = R.get("genero.peso_mezcla", 8.0)
FRAC_FUERA_MEZCLA = R.get("genero.penal_fuera_de_mezcla_frac", 0.25)
VETO_GENEROS = {g.lower() for g in (R.get("vetos.generos") or [])}
VETO_ARTISTAS = {a.lower() for a in (R.get("vetos.artistas") or [])}


_RAIZ = Path(__file__).resolve().parent.parent


def _dato(nombre: str) -> dict:
    """Carga un JSON de data/, o vacio si no se genero todavia."""
    f = _RAIZ / "data" / nombre
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


# Generados por scripts/perfilar_gusto.py. Si faltan, los terminos que dependen
# de ellos valen cero y el solver se comporta como antes.
_GROOVE = _dato("groove_index.json")
_MUNDO = _dato("mundo_propio.json")
_GR_SD = _GROOVE.get("desvios", [1.0, 1.0])
_MUNDO_ART = set(_MUNDO.get("artistas", []))
_MUNDO_SELLO = set(_MUNDO.get("sellos", []))
# Los temas que el DJ saco escuchando. Estaban solo en armar_noche_zorro, que es
# el que arma los configs, asi que llamar al solver derecho los volvia a meter:
# rearmando el 139 aparecio Alafia, vetada por oscura. Un veto tiene que valer en
# el unico lugar por el que pasan todos los sets, y ese lugar es este.
VETO_TRACKS = {k for k, v in (_dato("energia_percibida.json") or {}).items()
               if v.get("veto")}
# COLORIDO se mide con `color_pct`: medios por una campana sobre el aire. Aca
# decia `brillo_pct`, que era medio + 2*aire, la version que los propios casos
# del DJ refutaron — Shades Of Blue, que el llama oscuro, daba 0.981 de brillo
# y 0.000 de color. O sea que TODOS los sets coloridos se armaron premiando lo
# contrario de lo que el pidio, mientras `reemplazar.py` ya usaba la buena: el
# mismo adjetivo significaba dos cosas segun que script corriera.
_COLOR = _GROOVE.get("color_pct") or _GROOVE.get("cuerpo_pct", {})


def _indice_housero() -> dict:
    """Cuanto EMPUJA un tema, en z-scores de la biblioteca.

    "Mas housera pero progresive" (el DJ, 2026-09-28). Housero no es un genero:
    medido sobre 1353 tracks, el genero "House" tiene MENOS densidad que
    "Progressive House" (12.8 contra 14.1), asi que filtrar por genero da lo
    contrario de lo que pide. Lo que separa es el sonido:

        groove alto  (densidad de golpes por compas)
      + bajo presente (energia en el sub)
      - protagonismo melodico (el mismo `color_pct` del set colorido)

    Es el eje OPUESTO al colorido, y por eso comparte el termino: un set no
    puede ser las dos cosas a la vez. Comprobado en los extremos: arriba quedan
    Impending Storm (Navar Remix), Power Pink y Quantum Touch; abajo Paramour de
    Jody Wisternoff, Once a Day de Ezequiel Arias y el Wind Down de Cattaneo,
    que son exactamente los temas de los que el DJ NO quiere que se trate.
    """
    tr = _GROOVE.get("tracks") or {}
    if not tr:
        return {}
    dens = [v[0] for v in tr.values()]
    sub = [v[1] for v in tr.values()]
    md = sum(dens) / len(dens)
    ms = sum(sub) / len(sub)
    sd = (sum((x - md) ** 2 for x in dens) / len(dens)) ** 0.5 or 1.0
    ss = (sum((x - ms) ** 2 for x in sub) / len(sub)) ** 0.5 or 1.0
    crudo = {c: (v[0] - md) / sd + (v[1] - ms) / ss - (_COLOR.get(c, 0.5) - 0.5) * 2
             for c, v in tr.items()}
    # PERCENTIL, no z-score, por la misma razon que `color_pct`: el peso del
    # solver tiene que significar lo mismo en los dos ejes. En crudo el indice va
    # de -8.1 a +4.8 y el color de 0 a 1, asi que housero_peso=1.5 pesaba seis
    # veces mas que color_peso=1.5 y se comia el arco de energia: el set salia
    # con la cima a la mitad y dos temas bajando seguidos, no porque faltara
    # material --hay 58 temas de E>=7.4 en el pool-- sino porque el groove
    # compraba cualquier desvio.
    orden = sorted(crudo.values())
    n = len(orden)
    return {c: round(sum(1 for x in orden if x < val) / n, 3) for c, val in crudo.items()}


def _indice_empuje() -> dict:
    """El groove SOLO: densidad y bajo, sin descontarle la melodia.

    "Mas brillo y progresivo lindo" (el DJ, 2026-09-28), pedido sobre el set
    housero. Housero le RESTA el color --es su definicion-- asi que pedirle
    brillo al mismo indice es pedirle que se contradiga: el tema que empuja y
    ademas tiene medios queda castigado por tener medios.

    Este eje corta esa parte: mide cuanto empuja y nada mas. El brillo se pide
    aparte, con `color_peso`, que es lo que ya hace el set colorido. Asi los dos
    se pueden pedir a la vez sin que uno anule al otro.
    """
    tr = _GROOVE.get("tracks") or {}
    if not tr:
        return {}
    dens = [v[0] for v in tr.values()]
    sub = [v[1] for v in tr.values()]
    md, ms = sum(dens) / len(dens), sum(sub) / len(sub)
    sd = (sum((x - md) ** 2 for x in dens) / len(dens)) ** 0.5 or 1.0
    ss = (sum((x - ms) ** 2 for x in sub) / len(sub)) ** 0.5 or 1.0
    crudo = {c: (v[0] - md) / sd + (v[1] - ms) / ss for c, v in tr.items()}
    orden = sorted(crudo.values())
    n = len(orden)
    return {c: round(sum(1 for x in orden if x < val) / n, 3) for c, val in crudo.items()}


_HOUSERO = _indice_housero()
_EMPUJE = _indice_empuje()
VENTANA_ARCO = R.get("energia.ventana_arco", 1)
BONUS_ARTISTA = R.get("repeticion.bonus_artista_repetido", 0.0)
MODO_OBJETIVO = R.get("armonia.modo_mayor_objetivo", 0.0)
PESO_MODO = R.get("armonia.peso_modo", 0.0)

BONUS_ANCLA = 25.0
# Costo por BPM de desvio de la rampa de `bpm_arco`, con 1 BPM de tolerancia.
PESO_BPM_ARCO = 1.5
SPLIT = (",", "&", " feat", " ft", " vs", " x ")
# Margen para las comparaciones contra los topes. abs(7.0 - 8.3) da
# 1.3000000000000007 en punto flotante, asi que un escalon que es exactamente
# el limite se rechazaba: se perdian vecinos musicalmente legales y el solver
# terminaba pidiendo relajar una regla que no hacia falta tocar.
EPS = 1e-9


REMIX_RE = re.compile(
    r"[(\[]([^)\]]*?)\s+(?:Remix|Mix|Edit|Version|Reinterpretation|Rework|Re-?shape|Dub)[)\]]",
    re.I,
)
NOISE = {"original", "extended", "club", "dub", "instrumental", "radio", "vocal",
         "re-shape", "the", "a", "feat", "ft"}
# Sufijos que ensucian el nombre del remixer: "Marsh Extended" / "Marsh's" no
# matcheaban con "marsh", asi que el solver metia dos temas del mismo productor.
QUALIFIERS = ("extended", "original", "club", "radio", "vocal", "instrumental",
              "dub", "long", "short", "re-shape", "reshape", "12\"", "'s")
# Apodo entre comillas dentro del nombre del remixer: "Jonathan Kaspar
# 'Midnight' Remix" y "... 'Sunrise' Remix" son la misma mano, y sin sacarlo el
# dedup los tomaba por dos productores distintos y metia las dos versiones del
# mismo tema en el mismo set.
APODO_RE = re.compile(r"\s*['‘’\"][^'‘’\"]{2,}['‘’\"]\s*")


def _clean(name: str) -> str:
    """Normaliza un nombre de productor: sin acentos y sin sufijos de version.

    Los acentos importan porque Rekordbox guarda el mismo productor de las dos
    formas segun de donde vino el archivo: "Sebastien Leger, Roy Rosenfeld" en
    Panko Day y "Sébastien Léger, Lost Miracle" en Dodonpachi. Sin normalizar
    son dos productores distintos y el tope por artista los deja convivir, que
    es justo lo que la regla existe para evitar. Aparecio el 2026-09-29 buscando
    un equivalente para Go: el candidato mas alto era otro Leger con Leger ya en
    el set.
    """
    n = "".join(c for c in unicodedata.normalize("NFD", name or "")
                if unicodedata.category(c) != "Mn")
    n = APODO_RE.sub(" ", n).strip().lower()
    changed = True
    while changed:
        changed = False
        for q in QUALIFIERS:
            if q == "'s":
                if n.endswith("'s") or n.endswith("’s"):
                    n, changed = n[:-2].strip(), True
            elif n.endswith(" " + q):
                n, changed = n[: -len(q) - 1].strip(), True
            elif n.startswith(q + " "):
                n, changed = n[len(q) + 1:].strip(), True
    return n


def names(artist, title=""):
    """Nombres involucrados: campo artista + remixer citado en el titulo.

    El remixer cuenta como artista — 'Kyotto - Trigger' y 'Cary Crank - Inner
    Atlas (Kyotto Remix)' son el mismo productor dos veces en el set.
    Los sufijos de version se limpian: "Marsh's Extended Mix" -> "marsh".
    """
    raw = [artist]
    for m in REMIX_RE.finditer(title or ""):
        raw.append(m.group(1))
    parts = raw
    for sep in SPLIT:
        parts = [p for chunk in parts for p in chunk.split(sep)]
    out = set()
    for p in parts:
        p = _clean(p)
        if p and p not in NOISE:
            out.add(p)
    return out


def camelot(key):
    m = re.match(r"^(\d{1,2})([AB])$", (key or "").strip())
    return (int(m.group(1)), m.group(2)) if m else None


# Habia DOS definiciones de distancia Camelot en el repo: esta, que daba 0 al
# cambio de relativa (8A -> 8B), y la de src/plomo/camelot.py, que le da 1. El
# solver optimizaba con una y el auditor y el backtest median con la otra. El
# impacto medido es chico —ese caso aparece en el 0% de las transiciones de
# referencia y el 3% de las tocadas— pero no se pueden discutir los pesos con
# dos varas distintas. Queda la de plomo.camelot, que es la que usa todo lo demas.
cam_dist = _cam_dist_canonico


def _primera(nodo):
    """Energia del primer tema de la rama. Sube por los padres hasta la raiz."""
    prev, padre = nodo[1], nodo[2]
    if prev is None:
        return None
    while padre is not None and padre[1] is not None:
        prev, padre = padre[1], padre[2]
    return prev["energy"]


def _paso_firmado(ca, cb):
    """Cuanto y hacia donde se movio en la rueda: -6..+6, 0 = se quedo.

    Trabaja sobre el numero de rueda solamente. El cambio de modo (A<->B) ya lo
    cobra cam_dist; aca interesa si el set avanza o se queda clavado.
    """
    if not ca or not cb:
        return 0
    d = (cb[0] - ca[0]) % 12
    return d if d <= 6 else d - 12


def arc_en(t, lo, hi, hi_at=PICO_PCT, caida=None):
    """La energia que el arco pide en el instante `t` (0 = arranque, 1 = final)."""
    caida = CAIDA_PCT if caida is None else caida
    t = min(1.0, max(0.0, t))
    if t <= hi_at:
        return lo + (hi - lo) * (t / hi_at)
    return hi - (hi - lo) * caida * ((t - hi_at) / (1 - hi_at))


def arc_target(i, n, lo, hi, hi_at=PICO_PCT):
    """El arco por POSICION. Se mantiene para quien lo llame de afuera.

    Es la version vieja y tiene un problema: asume que todos los tracks duran lo
    mismo. Con la posicion como reloj, el pico que pide `energia.pico_en_pct`
    cae en un NUMERO de track — pero si los primeros diecinueve son extended mixes de nueve
    minutos, ese track 20 llega a las dos horas y media de empezar. Medido sobre
    los sets armados, ocho de cada diez no entraban en el horario pedido y el
    108 duraba 2h59 con cartel de 2h. `select()` ahora usa `arc_en()` con el
    tiempo acumulado real.
    """
    return arc_en(i / (n - 1), lo, hi, hi_at)


def _minus(s: str) -> str:
    """Minusculas sin acentos, igual que scripts/perfilar_gusto.py."""
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def select(pool, n, e_lo, e_hi, max_bpm_jump=None, prefer=(), bonus=6.0,
           max_per_artist=1, beam=BEAM, mezcla=None, peso_mezcla=PESO_MEZCLA,
           objetivo_seg=None, arco=None, anclas=(), inicio_fijo=(),
           anclas_en=None, entrada=None, salida=None, bpm_arco=None,
           cierre_fijo=(), bpm_arco_peso=PESO_BPM_ARCO,
           bpm_span=None, bpm_span_peso=0.0,
           modo_objetivo=None, peso_modo=None, color_peso=0.0, housero_peso=0.0,
           empuje_peso=0.0,
           max_cam=None, max_retro=None):
    """Devuelve la mejor secuencia de n tracks, o None.

    `arco` pisa, SOLO para este set, la forma de la noche que fijan las reglas:
    {"pico_en_pct", "caida_post_pico_pct", "tolerancia_arco_frac",
    "penal_quedarse_en_la_rueda", "monotonia_peso"}. Existe por
    las fechas puntuales. Las reglas globales se calibraron para que la
    COLECCION entera se parezca a los DJ reales —la banda de 0.9 deja a la
    energia moverse libre—, y en una fecha con un arco obligatorio esa libertad
    lo desarma: el set del cumple de Zorro, que recibe la pista y la entrega
    arriba, salio con el pico en el tema 2 y terminando en E5.7.

    `inicio_fijo` son los primeros temas en el orden que decidio el DJ. En esas
    posiciones no se aplica ninguna restriccion dura: si el DJ quiere pasar de
    1A a 4A para abrir, lo decidio con el oido, y el 36% de los pasos de los
    profesionales saltan 3 o mas lugares en la rueda.

    `bpm_span` es cuanto tempo tiene que RECORRER el set, con `bpm_span_peso`
    como premio por cada BPM ganado. Mismo problema que el rango de energia: es
    una propiedad global y todos los demas terminos son locales. Medido sobre
    los 8 setlists de Maze 28 y Simon Vuarambon en ventanas de 17 temas, ellos
    recorren 8 BPM y nuestros sets recorrian 4, con pools que llegaban a 6.

    `cierre_fijo` son los ULTIMOS temas, en orden: el set termina con ellos. Una
    ventana de horario no alcanza para "cortar a cero con Haunted": se cumple
    con Haunted anteultimo.

    `entrada` y `salida` son {key, bpm} del ultimo tema del set ANTERIOR y del
    primero del SIGUIENTE: en una noche de sets encadenados, el primero tiene
    que empalmar con lo que viene sonando y el ultimo con lo que sigue.

    `bpm_arco` es [desde, hasta]: el BPM sigue una rampa en el tiempo. Un warm
    que arranca en 118 y tiene que entregar a 122 no puede elegir el tempo
    tema por tema sin mirar el reloj.

    `anclas_en` es {id: [desde, hasta]} en fraccion del tiempo del set: DONDE
    tiene que caer un ancla. Sin esto el ancla garantiza que el tema este pero
    no donde: Sizer quedaba a la 1:49 cuando el DJ lo pidio en el pico.

    `anclas` son ids con un descuento fijo y grande (BONUS_ANCLA): el tema
    modelo de una fecha tiene que estar, no solo convenir. No se escala con
    `prefer_bonus`: bajar la prioridad general no puede sacar al ancla.

    `prefer` son ids con descuento en el costo — sirve para forzar que el set
    estrene material nuevo sin romper las restricciones duras.

    `mezcla` es la proporcion objetivo por genero: {"Progressive House": 0.5,
    "Deep House": 0.3}. Existe porque el filtro de `genres` es binario —un
    genero entra o no entra— y eso no sabe contestar el pedido mas comun que
    hace un DJ: "un poco mas progressive". La unica forma de inclinar la balanza
    era sacar generos enteros, que es un martillazo: se perdia el groove junto
    con lo comercial. Aca cada genero paga solo cuando YA SE PASO de su cuota,
    asi que el set se acomoda a la proporcion pedida sin que nada quede vedado.

    Los generos que no figuran en `mezcla` no pagan nada: la cuota es un piso
    que se persigue, no un techo que se impone.

    `modo_objetivo` es que fraccion del set va en tonalidad MAYOR, con la misma
    mecanica simetrica que la cuota de genero. Existe porque los siete sets del
    cumple salieron con 0% de temas en mayor, y el DJ escucho el que se llamaba
    "colorido" y dijo que habia temas oscuros. Un set entero en tonalidad menor
    no es colorido, se llame como se llame. Los DJ de referencia van en 11% de
    mediana (p75 20%), y Ezequiel Arias, que es de los que el DJ sigue, en 25%;
    cambian de modo en el 25% de las transiciones y nosotros en el 0%. Nada lo
    prohibia —8A a 8B es distancia 1 y estaba permitido— pero tampoco nada lo
    premiaba, y el 84% del pool es menor.

    `color_peso` premia el COLOR: los medios pesados por una campana sobre el
    aire, como percentil de la biblioteca (data/groove_index.json). Oscuro es
    cualquiera de los dos extremos —sin aire suena apagado, sin medios hueco—,
    asi que no es una suma sino un punto justo. Es la otra mitad de "colorido".
    """
    prefer = set(prefer)
    anclas = set(anclas)
    # Un ancla, una apertura o un cierre que no esta en el pool se ignoraba en
    # silencio: el set salia sin el tema que el DJ pidio y nada lo decia.
    _ids = {t["id"] for t in pool}
    for _que, _lista in (("ancla", anclas), ("inicio_fijo", inicio_fijo),
                         ("cierre_fijo", cierre_fijo)):
        _faltan = [x for x in _lista if x not in _ids]
        if _faltan:
            print(f"  AVISO: {len(_faltan)} {_que} fuera del pool, se ignoran: {_faltan}")
    pos_de = {t['id']: k for k, t in enumerate(pool)}
    fijo_idx = [pos_de[x] for x in inicio_fijo if x in pos_de]
    anclas_en = anclas_en or {}
    cierre_idx = [pos_de[x] for x in cierre_fijo if x in pos_de]
    cierre_set = set(cierre_idx)
    arco = arco or {}
    pico = arco.get("pico_en_pct", PICO_PCT)
    caida = arco.get("caida_post_pico_pct", CAIDA_PCT)
    tol_frac = arco.get("tolerancia_arco_frac", TOL_ARCO_FRAC)
    # con el arco apretado quedarse en la rueda sale relativamente barato: el
    # set 139 dio 31% de pasos quietos contra ~14% de la referencia
    peso_quieto = arco.get("penal_quedarse_en_la_rueda", PESO_QUIETO)
    # y al subir el castigo por quedarse quieto, la salida barata es la escalera:
    # el 139 paso de 31% quieto a una corrida de 5 pasos para el mismo lado
    peso_mono = arco.get("monotonia_peso", PESO_MONOTONIA)
    # oscilar ADENTRO del arco: con la banda apretada por el horario del pico, lo
    # unico que baja la correlacion posicion-energia es exigir pasos mas grandes y
    # castigar las rachas en la misma direccion.
    umbral_plano_set = arco.get("umbral_paso_plano", ENERGIA_QUIETA)
    peso_racha = arco.get("racha_peso", PESO_RACHA_ENERGIA)
    # La key HOGAR: el set orbita alrededor de una tonalidad en vez de caminar la
    # rueda en una direccion. Medido en el set 43 del DJ, el que llama increible:
    # 6A aparece 8 veces de 24 y el set VUELVE a ella ocho veces. El solver, sin
    # esto, se aleja y no vuelve: la misma cantidad de 6A pero solo 5 regresos.
    # El salto de BPM sale de las reglas si nadie lo pide distinto: bpm.max_salto
    # valia 3.0 desde la version 1.4.0 y nunca se aplicaba, porque el default de
    # la firma era 2.0 y ademas los configs lo escribian a mano. Tercer override
    # silencioso de la misma familia que peso_mezcla.
    if max_bpm_jump is None:
        max_bpm_jump = R.get("bpm.max_salto", 2.0)
    # La distancia maxima en la rueda es global, pero REORDENAR un set cerrado
    # es otro problema: hay que usar los 18 temas que ya estan, y si un solo par
    # no cierra a distancia 2 no hay solucion posible. Poder aflojarla por set
    # deja pedir "ordena esto lo mejor que puedas" sin cambiar la regla para
    # todos los demas.
    tope_cam = MAX_CAM if max_cam is None else max_cam
    # Lo mismo que el tope de rueda, por el mismo motivo: reordenar un set
    # cerrado es un problema distinto de armarlo. Con los 18 temas del 143 no
    # existe ningun orden que respete un retroceso de 1.8 mientras sube, asi que
    # o se afloja aca o no hay set. Armando desde la biblioteca entera el 1.8
    # sigue valiendo, que es donde se midio.
    tope_retro = MAX_RETROCESO if max_retro is None else max_retro
    modo_obj = MODO_OBJETIVO if modo_objetivo is None else modo_objetivo
    p_modo = PESO_MODO if peso_modo is None else peso_modo
    key_hogar = arco.get("key_hogar")
    peso_hogar = arco.get("peso_hogar", 0.0)
    # names() y camelot() dependen solo del track: calcularlos una vez evita
    # millones de regex dentro del doble loop (beam x candidatos x posiciones).
    for t in pool:
        if "_names" not in t:
            t["_names"] = names(t["artist"], t["title"])
            t["_cam"] = camelot(t["key"])
            # groove: densidad ritmica y peso de graves, ya normalizados
            g = _GROOVE.get("tracks", {}).get(t["id"])
            t["_gr"] = (g[0] / _GR_SD[0], g[1] / _GR_SD[1]) if g else None
            t["_prog"] = (t.get("genre") or "").strip().lower() in NUCLEO_PROG
            # de que mundo viene: el artista o el sello aparecen en lo que el DJ
            # TOCO de verdad (djmdHistory) o en sus favoritos
            _art = {a.strip() for a in _minus(t["artist"]).replace("&", ",").split(",") if a.strip()}
            t["_ajeno"] = (not (_art & _MUNDO_ART)
                           and _minus(t.get("label") or "") not in _MUNDO_SELLO)

    # -- indice por vecindario de Camelot --------------------------------------
    # El loop probaba los ~1300 tracks del pool en cada posicion de cada rama y
    # descartaba adentro los que no eran vecinos. Precalcular que indices estan a
    # distancia <=MAX_CAM de cada key deja ~1/6. Se guardan los INDICES en orden
    # ascendente para que el orden de evaluacion sea identico al de recorrer el
    # pool entero: el desempate del beam depende del orden de insercion, asi que
    # alterarlo cambiaria los sets sin cambiar una sola regla.
    vecinos: dict[str, list[int]] = {}
    for k in {t["key"] for t in pool}:
        vecinos[k] = [j for j, u in enumerate(pool) if cam_dist(k, u["key"]) <= tope_cam]
    todos = list(range(len(pool)))

    # (costo, track, padre, ids_mask, arts, run_num, ultimo_paso, mono_run,
    #  generos, max_e)
    # El ultimo campo son los SEGUNDOS acumulados de la rama: el arco se
    # mide contra el reloj, no contra el numero de track.
    dur_med = sorted(t.get("dur_seg") or 0 for t in pool)[len(pool) // 2] or 300
    if not objetivo_seg:
        objetivo_seg = n * dur_med
    # El umbral de "paso plano" no puede ser absoluto. Un set de 13 tracks con
    # banda de 1.5 puntos tiene un paso natural de 0.12: con el umbral fijo en
    # 0.15 el arco entero contaba como plano y la penalizacion empujaba a dar
    # pasos grandes en una sola direccion. Medido: la autocorrelacion de los
    # saltos salia +0.5 en los sets cortos, peor que el +0.0 original.
    tol_arco = (e_hi - e_lo) * tol_frac
    paso_natural = (e_hi - e_lo) / max(2, n - 1)
    # El piso sale de la regla, no de un 0.08 escrito aca. `ENERGIA_QUIETA` se
    # leia de rules/curaduria.json y no se usaba en ningun lado: una regla con
    # su porque y su evidencia que no hacia nada. Importa porque de este umbral
    # depende el tamano del escalon tipico — el del solver era 0.20 contra 0.90
    # de los DJ reales, y de ahi salia el rango corto de los sets.
    umbral_plano = max(umbral_plano_set, paso_natural * 0.55)
    beams = [(0.0, None, None, 0, {}, 0, None, 0, {}, float("-inf"), 0.0, 0, 0,
          float("inf"), float("-inf"), float("inf"), 0, ())]
    for i in range(n):
        tgt = arc_target(i, n, e_lo, e_hi)
        # Monticulo acotado en vez de lista completa. Antes se acumulaban
        # todos los candidatos de todas las ramas —unas 240 mil tuplas por
        # posicion— y recien despues se ordenaban para quedarse con `beam`.
        # Construir y ordenar esa lista era el costo dominante. Ahora se
        # conserva el peor de los `beam` mejores y todo lo que no le gana se
        # descarta SIN construir el nodo, que es la parte cara.
        nxt = []            # monticulo: el peor de los mejores queda arriba
        orden = 0           # desempate por orden de insercion, como el sort estable
        ultima = i == n - 1
        for nodo in beams:
            (cost, prev, _padre, ids, arts, run_num, ult_paso, mono_run,
             gen_cnt, max_e, segs, e_signo, e_racha, min_e, bpm_hi, bpm_lo,
             may_cnt, ventana) = nodo
            # la energia del primer tema de esta rama, para el piso del cierre
            e_primero = _primera(nodo)
            frac = segs / objetivo_seg
            tgt = arc_en(frac, e_lo, e_hi, pico, caida)
            # "antes del pico" tambien se mide con el reloj: si los primeros
            # temas son largos, el pico llega antes en numero de track.
            subiendo = frac <= pico
            fijo = i < len(fijo_idx)
            k_cierre = i - (n - len(cierre_idx))
            if k_cierre >= 0:
                candidatos = [cierre_idx[k_cierre]]
            elif fijo:
                candidatos = [fijo_idx[i]]
            elif prev is None and entrada:
                candidatos = [j for j in todos
                              if cam_dist(entrada["key"], pool[j]["key"]) <= MAX_CAM
                              and abs(pool[j]["bpm"] - entrada["bpm"]) <= max_bpm_jump + EPS]
            else:
                candidatos = vecinos[prev["key"]] if prev is not None else todos
            for j in candidatos:
                t = pool[j]
                if ids >> j & 1:
                    continue
                # los temas del cierre esperan su lugar: no pueden entrar antes
                if j in cierre_set and k_cierre < 0:
                    continue
                # el tema anterior al cierre fijo tiene que empalmar con el: sin
                # esto el 141 llegaba a Haunted con un salto de 5 en la rueda
                if (k_cierre == -1 and cierre_idx and (
                        cam_dist(t["key"], pool[cierre_idx[0]]["key"]) > MAX_CAM
                        or abs(t["bpm"] - pool[cierre_idx[0]]["bpm"]) > max_bpm_jump + EPS)):
                    continue
                if ultima and salida and (
                        cam_dist(t["key"], salida["key"]) > MAX_CAM
                        or abs(t["bpm"] - salida["bpm"]) > max_bpm_jump + EPS):
                    continue
                ven = anclas_en.get(t["id"])
                if ven and not (ven[0] <= frac <= ven[1]):
                    continue
                na = t["_names"]
                # tope por productor + separacion minima: un showcase se banca
                # repetir artista, pero no dos seguidos ni tres en cinco tracks
                if any(len(arts.get(a, ())) >= max_per_artist for a in na):
                    continue
                if any(i - p < MIN_GAP for a in na for p in arts.get(a, ())):
                    continue
                if prev is not None:
                    d = cam_dist(prev["key"], t["key"])
                    if not fijo and abs(t["bpm"] - prev["bpm"]) > max_bpm_jump + EPS:
                        continue
                    # no retroceder energia durante la subida
                    if not fijo and (subiendo
                            and t["energy"] < prev["energy"] - tope_retro - EPS):
                        continue
                    # ningun escalon brusco: el crowd tiene que no notar el cambio
                    if not fijo and abs(t["energy"] - prev["energy"]) > MAX_E_STEP + EPS:
                        continue
                    # El cierre ya no esta obligado a bajar del pico: la regla
                    # baja_minima_al_cierre quedo en 0.0 porque le imponia el
                    # mismo final a los ocho sets de la noche. Con 0.0 esto no
                    # descarta nada y el filtro de abajo es el que manda.
                    if BAJA_CIERRE and ultima and t["energy"] > max_e - BAJA_CIERRE:
                        continue
                    # "Quiero que no baje": el ultimo tema no puede quedar
                    # debajo del primero. Un set que termina mas abajo de donde
                    # empezo entrego la pista peor de lo que la recibio.
                    if CIERRE_NO_BAJA and ultima and t["energy"] < e_primero:
                        continue
                    # quedarse clavado en la misma key aburre: penalizar la
                    # tercera repeticion en adelante, premiar el movimiento.
                    # `run_num` viene contado desde la rama: es el largo de la
                    # corrida de tracks con el mismo numero de rueda que termina
                    # en `prev`. Antes esto se recalculaba recorriendo el set
                    # entero en cada candidato.
                    same = run_num if prev["_cam"][0] == t["_cam"][0] else 0
                    step = d * PESO_CAM + max(0, same - PENAL_MISMA_KEY_DESDE + 1) * PESO_MISMA_KEY
                    # [2026-09-21: el 14% de referencia citado abajo era de una medicion vieja;
                    # medido contra 11 DJs es 29%. Ver armonia.penal_quedarse_en_la_rueda.]
                    # Quedarse en la misma rueda costaba CERO, y por eso pasaba
                    # el 38% de las veces contra el 23% de lo que el DJ toca de
                    # verdad y el 14% de los sets de referencia. El set no sonaba
                    # mal transicion por transicion: sonaba igual de punta a punta.
                    # Un set real OSCILA; el nuestro era una rampa. Medido:
                    # correlacion posicion-energia +0.64 en los sets del solver
                    # contra +0.11 en los de referencia, y el 45% de nuestras
                    # transiciones no movia la energia contra el 19.6% de ellos
                    # (n=163). Quedarse quieto en energia cuesta, igual que
                    # quedarse quieto en la rueda.
                    de = t["energy"] - prev["energy"]
                    if abs(de) < umbral_plano:
                        step += PESO_ENERGIA_QUIETA
                        n_signo, n_racha = 0, 0
                    else:
                        # Un DJ real sube y baja: la autocorrelacion de sus
                        # saltos de energia es -0.36. La nuestra era -0.05, o
                        # sea una rampa. Penalizar SOLO lo plano no alcanzo —
                        # daba una rampa mas suave (correlacion posicion-energia
                        # +0.76, peor que el +0.64 original). Lo que falta es
                        # cobrar la RACHA en la misma direccion.
                        n_signo = 1 if de > 0 else -1
                        n_racha = e_racha + 1 if n_signo == e_signo else 1
                        if n_racha > RACHA_ENERGIA_DESDE:
                            step += (n_racha - RACHA_ENERGIA_DESDE) * peso_racha
                        # "Quiero que no baje" (el DJ, 2026-09-23). Una bajada
                        # sola entre dos temas que sostienen es un respiro y no
                        # paga nada; dos seguidas ya es el set apagandose, y
                        # desde ahi cada una cuesta. Es asimetrico a proposito:
                        # subir dos veces seguidas no tiene nada de malo, y el
                        # termino de racha que esta arriba, que si es simetrico,
                        # castiga las dos direcciones por igual.
                        # Desde la TERCERA bajada seguida, no desde la segunda:
                        # una soltada de verdad son dos pasos (-1.5 y despues
                        # -0.8) y la referencia nunca encadena mas de dos.
                        # Cobrando desde la segunda se bloqueaba justo el gesto
                        # que a estos sets les faltaba.
                        if PENAL_RACHA_BAJANDO and n_signo < 0 and n_racha >= 3:
                            step += (n_racha - 2) * PENAL_RACHA_BAJANDO
                    paso = _paso_firmado(prev["_cam"], t["_cam"])
                    if paso == 0:
                        step += peso_quieto
                    else:
                        # Subir siempre un paso hacia el mismo lado aburre igual
                        # que no moverse. Se penaliza desde la tercera seguida.
                        # `mono_run` es el largo de la corrida de pasos iguales
                        # que termina en el paso que entro a `prev`; si ese paso
                        # es el mismo que este, la corrida continua.
                        corrida = mono_run if paso == ult_paso else 0
                        if corrida >= MONOTONIA_DESDE:
                            step += (corrida - MONOTONIA_DESDE + 1) * peso_mono
                else:
                    paso = None
                    step = 0.0
                if key_hogar and peso_hogar:
                    step += cam_dist(key_hogar, t["key"]) * peso_hogar
                # GROOVE CONSTANTE. No es que los pasos de energia sean chicos
                # --en los setlists reales la mediana del paso es 0.90 y el p90
                # es 2.50, o sea que un pro se mueve--: es que el groove no se
                # corte. Medido sobre 236 pares consecutivos de referencia con
                # los dos temas indexados, el salto mediano de densidad + graves
                # es 1.25. Nuestros sets del cumple daban 1.68 a 2.37, y el
                # unico que el DJ elogio entero era el mas cercano al pro.
                # Los temas sin receta indexada no pagan: no se castiga a un
                # tema por no estar medido.
                if PESO_GROOVE and prev is not None and t["_gr"] and prev["_gr"]:
                    salto = (abs(t["_gr"][0] - prev["_gr"][0])
                             + abs(t["_gr"][1] - prev["_gr"][1]))
                    if salto > SALTO_GROOVE:
                        step += (salto - SALTO_GROOVE) * PESO_GROOVE
                # EL ARCO RIGE LA TENDENCIA, NO CADA TEMA. Con el desvio medido
                # sobre el tema suelto y un peso de 8.0, el set camina pegado a
                # la curva: pasos de energia de 0.55 de mediana contra 1.00 de
                # los pros, que es la diferencia que quedaba sin explicar. Un
                # DJ real oscila ALREDEDOR de la tendencia. Medido en el set de
                # Maze en La Biblioteca: tres horas dentro de una banda de +-0.3
                # z, con variedad local alta adentro. Con ventana 1 esto es
                # identico al comportamiento viejo.
                if VENTANA_ARCO > 1:
                    prev_e = ventana + (t["energy"],)
                    media = sum(prev_e) / len(prev_e)
                    desvio = max(0.0, abs(media - tgt) - tol_arco)
                else:
                    desvio = max(0.0, abs(t["energy"] - tgt) - tol_arco)
                # premio por ensanchar el recorrido, capado en el objetivo: una
                # vez que el set ya cubre SPAN_OBJETIVO, estirar mas no paga
                if PESO_SPAN:
                    hi_n = t["energy"] if t["energy"] > max_e else max_e
                    lo_n = t["energy"] if t["energy"] < min_e else min_e
                    if max_e > float("-inf"):
                        ganado = (min(hi_n - lo_n, SPAN_OBJETIVO)
                                  - min(max_e - min_e, SPAN_OBJETIVO))
                        step -= ganado * PESO_SPAN
                c = cost + desvio * PESO_ARCO + step
                if bpm_span_peso:
                    bh = t["bpm"] if t["bpm"] > bpm_hi else bpm_hi
                    bl = t["bpm"] if t["bpm"] < bpm_lo else bpm_lo
                    if bpm_hi > float("-inf"):
                        c -= (min(bh - bl, bpm_span) - min(bpm_hi - bpm_lo, bpm_span)) * bpm_span_peso
                if bpm_arco:
                    tb = bpm_arco[0] + (bpm_arco[1] - bpm_arco[0]) * frac
                    c += max(0.0, abs(t["bpm"] - tb) - 1.0) * bpm_arco_peso
                # COLORIDO, medido y no declarado. Dos mitades: el modo de la
                # tonalidad y el color del audio.
                if p_modo and modo_obj:
                    # Simetrico sobre las DOS caras, como la cuota de genero.
                    # La primera version contaba solo los mayores, y con eso un
                    # tema MENOR se abarataba justo cuando faltaban mayores: la
                    # cuota empujaba para el lado contrario y el set colorido
                    # paso de 0% a 6% en vez de 25%. Con una variable binaria
                    # hay que cobrarle a las dos caras o no se cobra ninguna.
                    if t["key"].endswith("B"):
                        c += ((may_cnt + 1) / (i + 1) - modo_obj) * p_modo
                    else:
                        men = (i - may_cnt) + 1
                        c += (men / (i + 1) - (1 - modo_obj)) * p_modo
                if color_peso:
                    c -= _COLOR.get(t["id"], 0.5) * color_peso
                # HOUSERO: el eje contrario. Se premia el empuje en vez del
                # color, y por eso los dos pesos no deberian usarse juntos.
                if housero_peso:
                    c -= _HOUSERO.get(t["id"], 0.0) * housero_peso
                # EMPUJE: el groove sin descontar la melodia, para cuando se
                # quiere un set que empuje Y tenga brillo. Se usa junto con
                # color_peso, no en lugar de el.
                if empuje_peso:
                    c -= _EMPUJE.get(t["id"], 0.0) * empuje_peso
                # LO PROGRESIVO, tercero: descuenta, no veda.
                if PESO_PROG and t["_prog"]:
                    c -= PESO_PROG
                # ARTISTAS Y PRODUCTORES, cuarto y arriba de la cuota de genero.
                # Un tema cuyo artista Y sello no aparecen nunca en lo que el DJ
                # toco paga. Los cuatro temas que rechazo escuchando el 23/09
                # eran los cuatro ajenos; el set 140, el unico que elogio entero,
                # tiene cero ajenos en 17. Por forma del audio eran
                # indistinguibles del resto de la biblioteca, asi que este es el
                # unico eje que los ve venir.
                if PESO_AJENO and t["_ajeno"]:
                    c += PESO_AJENO
                # Los pros no tocan 17 artistas distintos: sus 5 mas repetidos
                # son el 47-50% del set y el nuestro andaba en 29-41%. Un set
                # tiene un nucleo y satelites. El tope por artista y la
                # separacion minima siguen valiendo; esto solo abarata volver a
                # alguien que ya sono.
                if BONUS_ARTISTA and (t["_names"] & set(arts)):
                    c -= BONUS_ARTISTA
                if t["id"] in prefer:
                    c -= bonus
                if t["id"] in anclas:
                    c -= BONUS_ANCLA
                if mezcla:
                    g = (t.get("genre") or "").strip()
                    objetivo = mezcla.get(g)
                    if objetivo is not None:
                        ya = gen_cnt.get(g, 0)
                        # El desvio es SIMETRICO a proposito. La primera version
                        # solo cobraba el exceso, y con eso la cuota nunca se
                        # alcanzaba: el genero que iba corto no pagaba, pero
                        # tampoco ganaba nada, asi que el solver no tenia motivo
                        # para elegirlo. Pedir "45% progressive" daba 25%. Ahora
                        # ir corto descuenta igual que pasarse cobra, y la cuota
                        # tira desde los dos lados.
                        c += ((ya + 1) / (i + 1) - objetivo) * peso_mezcla
                    elif mezcla:
                        # Un genero que no figura en la mezcla no es gratis: si
                        # lo fuera, el solver lo usaria para esquivar la cuota.
                        c += peso_mezcla * FRAC_FUERA_MEZCLA
                # El estado viaja en la rama en vez de recalcularse: antes cada
                # candidato volvia a recorrer el set entero cuatro veces (misma
                # key, monotonia, conteo de generos, maximo de energia), y eso
                # convertia un loop de 37 millones en uno de 900.
                n_may = may_cnt + (1 if t["key"].endswith("B") else 0)
                if prev is None:
                    n_run, n_paso, n_mono = 1, None, 0
                elif prev["_cam"][0] == t["_cam"][0]:
                    n_run = run_num + 1
                    n_paso, n_mono = paso, (mono_run + 1 if paso == ult_paso else 1)
                else:
                    n_run = 1
                    n_paso, n_mono = paso, (mono_run + 1 if paso == ult_paso else 1)
                gk = (t.get("genre") or "").strip()
                if len(nxt) >= beam:
                    pc, po = -nxt[0][0], -nxt[0][1]
                    if c > pc or (c == pc and orden > po):
                        continue
                na_pos = {a: arts.get(a, ()) + (i,) for a in na}
                gc = dict(gen_cnt)
                gc[gk] = gc.get(gk, 0) + 1
                nodo_hijo = (c, t, nodo, ids | (1 << j), {**arts, **na_pos},
                             n_run, n_paso, n_mono, gc,
                             t["energy"] if t["energy"] > max_e else max_e,
                             segs + (t.get("dur_seg") or dur_med),
                             n_signo if prev is not None else 0,
                             n_racha if prev is not None else 0,
                             t["energy"] if t["energy"] < min_e else min_e,
                             t["bpm"] if t["bpm"] > bpm_hi else bpm_hi,
                             t["bpm"] if t["bpm"] < bpm_lo else bpm_lo,
                             n_may,
                             (ventana + (t["energy"],))[-(VENTANA_ARCO - 1):]
                             if VENTANA_ARCO > 1 else ())
                entrada = (-c, -orden, nodo_hijo)
                orden += 1
                if len(nxt) < beam:
                    heapq.heappush(nxt, entrada)
                else:
                    heapq.heappushpop(nxt, entrada)
        if not nxt:
            return None
        # ascendente por costo y, en empate, por orden de insercion: es lo mismo
        # que daba el sort estable de antes.
        beams = [e[2] for e in sorted(nxt, key=lambda e: (-e[0], -e[1]))]
    # La secuencia no se guarda en cada rama: cada nodo apunta a su padre y se
    # reconstruye una sola vez al final. Copiar la lista en cada candidato era
    # la asignacion de memoria mas cara del loop.
    mejor = beams[0]
    seq, nodo = [], mejor
    while nodo is not None and nodo[1] is not None:
        seq.append(nodo[1])
        nodo = nodo[2]
    seq.reverse()
    return (mejor[0], seq)


def show(seq, prefer=()):
    prev = None
    for i, t in enumerate(seq, 1):
        flag = "  [NUEVO]" if t["id"] in set(prefer) else ""
        if prev:
            d = cam_dist(prev["key"], t["key"])
            if d >= 2:
                flag += f"  <-- CAMELOT {d}"
            if abs(t["bpm"] - prev["bpm"]) > 2:
                flag += f"  <-- BPM +{abs(t['bpm']-prev['bpm']):.0f}"
        print(
            f"  {i:2d}. E{t['energy']:.1f} {t['bpm']:5.1f} {t['key']:>4} {t['label'][:15]:15} | "
            f"{t['artist']} - {t['title']}"[:112] + flag
        )
        prev = t


def correr(cfg_ruta, escribir: bool = True, callado: bool = False) -> list:
    """Arma todos los sets de un config. Devuelve [(spec, secuencia), ...].

    `escribir=False` no toca data/targets: sirve para el loop de entrenamiento
    (scripts/entrenar_criterio.py), que arma cientos de sets solo para medirlos.
    """
    RAIZ = Path(__file__).parent.parent
    hechos = []
    _print = (lambda *a, **k: None) if callado else print

    def ruta(p: str) -> Path:
        """Las rutas del config son relativas a la raiz del repo."""
        q = Path(p)
        return q if q.is_absolute() else RAIZ / q

    cfg = json.loads(Path(cfg_ruta).read_text(encoding="utf-8"))

    def _vecino(cid):
        """key y BPM de un tema de OTRO set, para empalmar con el."""
        if not cid:
            return None
        t = next((x for x in pool_all if x["id"] == cid), None)
        return {"key": t["key"], "bpm": t["bpm"]} if t else None
    pool_all = json.loads(ruta(cfg["pool"]).read_text(encoding="utf-8"))
    # La energia que el DJ ESCUCHO pisa la calculada. La calculada sale de donde
    # caen los cues, no de lo que suena: en el set 139 daba Sizer 5.2 (el mas
    # bajo) cuando el DJ lo siente de pico, y Low Era 7.5 cuando lo siente
    # oscuro y bajo. Cada correccion queda en data/energia_percibida.json y es
    # dato para recalibrar la formula cuando haya suficientes.
    _perc = RAIZ / "data" / "energia_percibida.json"
    if _perc.exists():
        _ov = json.loads(_perc.read_text(encoding="utf-8"))
        for t in pool_all:
            if t["id"] in _ov and "E" in _ov[t["id"]]:
                t["energy_calc"] = t["energy"]
                t["energy"] = _ov[t["id"]]["E"]
    # artistas ya comprometidos en otros sets — cada set mantiene identidad propia
    taken = {a.lower() for a in cfg.get("exclude_artists", [])}
    # Cuantas veces puede aparecer un mismo track en toda la tanda. Sin tope, con
    # paletas parecidas el optimizador converge al mismo optimo y salen sets
    # identicos con nombres distintos.
    tope = cfg.get("max_apariciones_por_track", 0)
    # El tope se cuenta DENTRO de un grupo, y entre grupos distintos un track no
    # se repite nunca. Los tres sets de un mismo momento son alternativas —se
    # toca una de las tres— asi que pueden compartir tracks; dos momentos
    # distintos se tocan la MISMA noche, asi que compartir ahi es escuchar el
    # mismo tema dos veces. Un `tope` global no distingue las dos cosas: puesto
    # en 3 dejaba 67 tracks repetidos entre momentos y solo 5 entre variantes,
    # exactamente al reves de lo que hace falta. Un set sin `grupo` es su propio
    # grupo, que es el comportamiento de siempre.
    usos: dict[str, dict[str, int]] = {}
    for spec in cfg["sets"]:
        grupo = str(spec.get("grupo", spec["num"]))
        artistas = spec.get("artists") or ["*"]
        e_pool = spec.get("e_pool")  # [min, max] — acota el pool por energia
        generos = [g.lower() for g in spec.get("genres", [])]
        excluidos = set(spec.get("exclude_ids", []))
        # fuera de este grupo el track ya se uso -> prohibido, sin importar el tope
        excluidos |= {i for i, g in usos.items() if any(o != grupo for o in g)}
        if tope:
            excluidos |= {i for i, g in usos.items() if g.get(grupo, 0) >= tope}
        pool = [
            t for t in pool_all
            if (artistas == ["*"]
                or any(a.lower() in t["artist"].lower() for a in artistas))
            and spec["bpm"][0] <= t["bpm"] <= spec["bpm"][1]
            and (not e_pool or e_pool[0] <= t["energy"] <= e_pool[1])
            and (not generos or (t.get("genre", "") or "").lower() in generos)
            and (not spec.get("solo_sin_usar") or not t.get("usado"))
            and (not spec.get("solo_sin_tocar") or not _toco(t["title"]))
            and (not spec.get("keys") or t["key"] in spec["keys"])
            and camelot(t["key"])
            and not (names(t["artist"], t["title"]) & taken)
            and t["id"] not in excluidos
            and t["id"] not in VETO_TRACKS
            and (t.get("genre") or "").strip().lower() not in VETO_GENEROS
            and not any(a in _minus(t["artist"]) for a in VETO_ARTISTAS)
        ]
        # Un veto de track no ensenaba nada de sus vecinos: sacado un tema de
        # Afro House volvia otro del mismo palo. Los vetos de
        # rules/curaduria.json son por CATEGORIA y se aplican aca, antes de que
        # el costo pueda pedirlos.
        if VETO_GENEROS or VETO_ARTISTAS:
            _fuera = len([t for t in pool_all
                          if (t.get("genre") or "").strip().lower() in VETO_GENEROS
                          or any(a in _minus(t["artist"]) for a in VETO_ARTISTAS)])
            if _fuera:
                _print(f"  vetos por categoria: {_fuera} tracks fuera del pool")
        _vt = len([t for t in pool_all if t["id"] in VETO_TRACKS])
        if _vt:
            _print(f"  vetos del DJ: {_vt} tracks fuera del pool")
        # Cuantos tracks entran de verdad en el horario pedido. La regla vieja
        # era 12 por hora (5 min cada uno) y el material real tiene mediana 7.2:
        # un set de 2h con 24 tracks daba 2h52. Si el config trae duration_h se
        # recalcula contra la mediana del POOL de ese set, que es lo que se va a
        # usar; `n` del config queda como tope por si se quiere acotar.
        objetivo_seg = int(spec.get("duration_h", 0) * 3600) or None
        n_tracks = spec["n"]
        if objetivo_seg and pool:
            med = sorted(t.get("dur_seg") or 0 for t in pool)[len(pool) // 2] or 300
            # Un track no suena entero: se mezcla entrando y saliendo. Medido
            # sobre los timestamps de djmdHistory, suena el 93% del archivo y el
            # hueco mediano entre temas es 6.8 min. La regla vieja decia 12 por
            # hora (5 min) y la realidad son 8.8.
            n_tracks = max(4, round(objetivo_seg / (med * 0.93)))
            if n_tracks != spec["n"]:
                _print(f"  duracion {spec['duration_h']}h / {med/60:.1f} min por track "
                      f"-> {n_tracks} tracks (el config decia {spec['n']})")
        # una cuota de un genero que el filtro no deja entrar es una orden que
        # nadie cumple: el set 139 pedia 20% de House con House fuera de `genres`.
        _gen = {g.lower() for g in spec.get("genres", [])}
        _sin = [g for g in (spec.get("mezcla_objetivo") or {}) if _gen and g.lower() not in _gen]
        if _sin:
            _print(f"  AVISO: mezcla_objetivo pide {_sin} pero no estan en genres")

        best = select(
            pool, n_tracks, spec["e_lo"], spec["e_hi"],
            max_bpm_jump=spec.get("max_bpm_jump"),
            prefer=set(spec.get("prefer_ids", [])),
            bonus=spec.get("prefer_bonus", 6.0),
            max_per_artist=spec.get("max_per_artist", 1),
            beam=spec.get("beam", BEAM),
            mezcla=spec.get("mezcla_objetivo"),
            peso_mezcla=spec.get("peso_mezcla", PESO_MEZCLA),
            objetivo_seg=objetivo_seg,
            arco=spec.get("arco"),
            anclas=set(spec.get("anclas", [])),
            inicio_fijo=spec.get("inicio_fijo", []),
            anclas_en=spec.get("anclas_en"),
            entrada=_vecino(spec.get("entrada_desde")),
            salida=_vecino(spec.get("salida_hacia")),
            bpm_arco=spec.get("bpm_arco"),
            cierre_fijo=spec.get("cierre_fijo", []),
            bpm_arco_peso=spec.get("bpm_arco_peso", PESO_BPM_ARCO),
            bpm_span=spec.get("bpm_span", 0),
            bpm_span_peso=spec.get("bpm_span_peso", 0.0),
            modo_objetivo=spec.get("modo_mayor_objetivo"),
            peso_modo=spec.get("peso_modo"),
            color_peso=spec.get("color_peso", 0.0),
            housero_peso=spec.get("housero_peso", 0.0),
            empuje_peso=spec.get("empuje_peso", 0.0),
            max_cam=spec.get("max_camelot"),
            max_retro=spec.get("max_retroceso"),
        )
        _print(f"\n{'='*72}\n{spec['name']}  (pool {len(pool)})")
        if not best:
            _print("  SIN SOLUCION — relajar restricciones")
            continue
        if not callado:
            show(best[1], spec.get("prefer_ids", []))
        hechos.append((spec, best[1]))
        target = {
            "name": spec["name"],
            # carpeta destino en Rekordbox; build_set la resuelve por nombre
            **({"carpeta": spec["carpeta"]} if spec.get("carpeta") else {}),
            "duration_h": spec["duration_h"],
            "bpm_range": spec["bpm"],
            "max_per_artist": spec.get("max_per_artist", 1),
            "keep_order": True,
            "tracks": [
                {"artist": t["artist"], "title": t["title"], "content_id": t["id"]}
                for t in best[1]
            ],
        }
        if escribir:
            out = ruta(cfg["targets_dir"]) / f"set_{spec['num']}.json"
            out.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
            _print(f"  -> {out.name}")
        # Por defecto cada set del config estrena artistas: se acumulan para que
        # el siguiente no los repita. Una serie de videos independientes puede
        # querer lo contrario — cada uno lleva lo mejor de su concepto.
        for t in best[1]:
            g = usos.setdefault(t["id"], {})
            g[grupo] = g.get(grupo, 0) + 1
        if not cfg.get("permitir_repetir_entre_sets"):
            for t in best[1]:
                taken |= names(t["artist"], t["title"])
    return hechos


if __name__ == "__main__":
    correr(sys.argv[1])
