"""Selecciona un set desde un pool respetando escalera Camelot + arco de energia.

A diferencia de reordenar (que trabaja con una seleccion ya fija), aca se ELIGE
que tracks entran. Es la unica forma de que key y energia no se contradigan.

Beam search: en cada posicion se prueba cada candidato cuyo key este a distancia
<=1 del anterior, penalizando el desvio del arco. Se conservan los mejores K.
"""
import heapq
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.camelot import distance as _cam_dist_canonico  # noqa: E402
from plomo.rules import R  # noqa: E402

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
PESO_CAM = R.get("armonia.peso_salto_camelot")
PENAL_MISMA_KEY_DESDE = R.get("armonia.penal_misma_key_desde")
PESO_MISMA_KEY = R.get("armonia.penal_misma_key_desde_peso", 1.2)
PESO_QUIETO = R.get("armonia.penal_quedarse_en_la_rueda", 0.8)
MONOTONIA_DESDE = R.get("armonia.monotonia_desde", 2)
PESO_MONOTONIA = R.get("armonia.monotonia_desde_peso", 0.5)
ENERGIA_QUIETA = R.get("energia.umbral_paso_plano", 0.15)
PESO_ENERGIA_QUIETA = R.get("energia.penal_paso_plano", 0.35)
RACHA_ENERGIA_DESDE = R.get("energia.racha_misma_direccion_desde", 2)
PESO_RACHA_ENERGIA = R.get("energia.racha_misma_direccion_peso", 0.7)
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
    """Normaliza un nombre de productor quitando sufijos de version."""
    n = APODO_RE.sub(" ", name).strip().lower()
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


def _paso_firmado(ca, cb):
    """Cuanto y hacia donde se movio en la rueda: -6..+6, 0 = se quedo.

    Trabaja sobre el numero de rueda solamente. El cambio de modo (A<->B) ya lo
    cobra cam_dist; aca interesa si el set avanza o se queda clavado.
    """
    if not ca or not cb:
        return 0
    d = (cb[0] - ca[0]) % 12
    return d if d <= 6 else d - 12


def arc_en(t, lo, hi, hi_at=PICO_PCT):
    """La energia que el arco pide en el instante `t` (0 = arranque, 1 = final)."""
    t = min(1.0, max(0.0, t))
    if t <= hi_at:
        return lo + (hi - lo) * (t / hi_at)
    return hi - (hi - lo) * CAIDA_PCT * ((t - hi_at) / (1 - hi_at))


def arc_target(i, n, lo, hi, hi_at=PICO_PCT):
    """El arco por POSICION. Se mantiene para quien lo llame de afuera.

    Es la version vieja y tiene un problema: asume que todos los tracks duran lo
    mismo. Con la posicion como reloj, el pico "al 82% del set" cae en el track
    20 de 24 — pero si los primeros diecinueve son extended mixes de nueve
    minutos, ese track 20 llega a las dos horas y media de empezar. Medido sobre
    los sets armados, ocho de cada diez no entraban en el horario pedido y el
    108 duraba 2h59 con cartel de 2h. `select()` ahora usa `arc_en()` con el
    tiempo acumulado real.
    """
    return arc_en(i / (n - 1), lo, hi, hi_at)


def select(pool, n, e_lo, e_hi, max_bpm_jump=2.0, prefer=(), bonus=6.0,
           max_per_artist=1, beam=BEAM, mezcla=None, peso_mezcla=8.0,
           objetivo_seg=None):
    """Devuelve la mejor secuencia de n tracks, o None.

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
    """
    prefer = set(prefer)
    # names() y camelot() dependen solo del track: calcularlos una vez evita
    # millones de regex dentro del doble loop (beam x candidatos x posiciones).
    for t in pool:
        if "_names" not in t:
            t["_names"] = names(t["artist"], t["title"])
            t["_cam"] = camelot(t["key"])

    # -- indice por vecindario de Camelot --------------------------------------
    # El loop probaba los ~1300 tracks del pool en cada posicion de cada rama y
    # descartaba adentro los que no eran vecinos. Precalcular que indices estan a
    # distancia <=MAX_CAM de cada key deja ~1/6. Se guardan los INDICES en orden
    # ascendente para que el orden de evaluacion sea identico al de recorrer el
    # pool entero: el desempate del beam depende del orden de insercion, asi que
    # alterarlo cambiaria los sets sin cambiar una sola regla.
    vecinos: dict[str, list[int]] = {}
    for k in {t["key"] for t in pool}:
        vecinos[k] = [j for j, u in enumerate(pool) if cam_dist(k, u["key"]) <= MAX_CAM]
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
    tol_arco = (e_hi - e_lo) * TOL_ARCO_FRAC
    paso_natural = (e_hi - e_lo) / max(2, n - 1)
    # El piso sale de la regla, no de un 0.08 escrito aca. `ENERGIA_QUIETA` se
    # leia de rules/curaduria.json y no se usaba en ningun lado: una regla con
    # su porque y su evidencia que no hacia nada. Importa porque de este umbral
    # depende el tamano del escalon tipico — el del solver era 0.20 contra 0.90
    # de los DJ reales, y de ahi salia el rango corto de los sets.
    umbral_plano = max(ENERGIA_QUIETA, paso_natural * 0.55)
    beams = [(0.0, None, None, 0, {}, 0, None, 0, {}, float("-inf"), 0.0, 0, 0)]
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
             gen_cnt, max_e, segs, e_signo, e_racha) = nodo
            frac = segs / objetivo_seg
            tgt = arc_en(frac, e_lo, e_hi)
            # "antes del pico" tambien se mide con el reloj: si los primeros
            # temas son largos, el pico llega antes en numero de track.
            subiendo = frac <= PICO_PCT
            candidatos = vecinos[prev["key"]] if prev is not None else todos
            for j in candidatos:
                t = pool[j]
                if ids >> j & 1:
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
                    if abs(t["bpm"] - prev["bpm"]) > max_bpm_jump + EPS:
                        continue
                    # no retroceder energia durante la subida
                    if (subiendo
                            and t["energy"] < prev["energy"] - MAX_RETROCESO - EPS):
                        continue
                    # ningun escalon brusco: el crowd tiene que no notar el cambio
                    if abs(t["energy"] - prev["energy"]) > MAX_E_STEP + EPS:
                        continue
                    # el cierre siempre baja del pico — nunca terminar arriba
                    if ultima and t["energy"] > max_e - BAJA_CIERRE:
                        continue
                    # quedarse clavado en la misma key aburre: penalizar la
                    # tercera repeticion en adelante, premiar el movimiento.
                    # `run_num` viene contado desde la rama: es el largo de la
                    # corrida de tracks con el mismo numero de rueda que termina
                    # en `prev`. Antes esto se recalculaba recorriendo el set
                    # entero en cada candidato.
                    same = run_num if prev["_cam"][0] == t["_cam"][0] else 0
                    step = d * PESO_CAM + max(0, same - PENAL_MISMA_KEY_DESDE + 1) * PESO_MISMA_KEY
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
                            step += (n_racha - RACHA_ENERGIA_DESDE) * PESO_RACHA_ENERGIA
                    paso = _paso_firmado(prev["_cam"], t["_cam"])
                    if paso == 0:
                        step += PESO_QUIETO
                    else:
                        # Subir siempre un paso hacia el mismo lado aburre igual
                        # que no moverse. Se penaliza desde la tercera seguida.
                        # `mono_run` es el largo de la corrida de pasos iguales
                        # que termina en el paso que entro a `prev`; si ese paso
                        # es el mismo que este, la corrida continua.
                        corrida = mono_run if paso == ult_paso else 0
                        if corrida >= MONOTONIA_DESDE:
                            step += (corrida - MONOTONIA_DESDE + 1) * PESO_MONOTONIA
                else:
                    paso = None
                    step = 0.0
                desvio = max(0.0, abs(t["energy"] - tgt) - tol_arco)
                c = cost + desvio * PESO_ARCO + step
                if t["id"] in prefer:
                    c -= bonus
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
                        c += peso_mezcla * 0.25
                # El estado viaja en la rama en vez de recalcularse: antes cada
                # candidato volvia a recorrer el set entero cuatro veces (misma
                # key, monotonia, conteo de generos, maximo de energia), y eso
                # convertia un loop de 37 millones en uno de 900.
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
                             n_racha if prev is not None else 0)
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


if __name__ == "__main__":
    RAIZ = Path(__file__).parent.parent

    def ruta(p: str) -> Path:
        """Las rutas del config son relativas a la raiz del repo."""
        q = Path(p)
        return q if q.is_absolute() else RAIZ / q

    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    pool_all = json.loads(ruta(cfg["pool"]).read_text(encoding="utf-8"))
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
            and (not spec.get("keys") or t["key"] in spec["keys"])
            and camelot(t["key"])
            and not (names(t["artist"], t["title"]) & taken)
            and t["id"] not in excluidos
        ]
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
                print(f"  duracion {spec['duration_h']}h / {med/60:.1f} min por track "
                      f"-> {n_tracks} tracks (el config decia {spec['n']})")
        best = select(
            pool, n_tracks, spec["e_lo"], spec["e_hi"],
            max_bpm_jump=spec.get("max_bpm_jump", 2.0),
            prefer=set(spec.get("prefer_ids", [])),
            bonus=spec.get("prefer_bonus", 6.0),
            max_per_artist=spec.get("max_per_artist", 1),
            beam=spec.get("beam", BEAM),
            mezcla=spec.get("mezcla_objetivo"),
            peso_mezcla=spec.get("peso_mezcla", 8.0),
            objetivo_seg=objetivo_seg,
        )
        print(f"\n{'='*72}\n{spec['name']}  (pool {len(pool)})")
        if not best:
            print("  SIN SOLUCION — relajar restricciones")
            continue
        show(best[1], spec.get("prefer_ids", []))
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
        out = ruta(cfg["targets_dir"]) / f"set_{spec['num']}.json"
        out.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {out.name}")
        # Por defecto cada set del config estrena artistas: se acumulan para que
        # el siguiente no los repita. Una serie de videos independientes puede
        # querer lo contrario — cada uno lleva lo mejor de su concepto.
        for t in best[1]:
            g = usos.setdefault(t["id"], {})
            g[grupo] = g.get(grupo, 0) + 1
        if not cfg.get("permitir_repetir_entre_sets"):
            for t in best[1]:
                taken |= names(t["artist"], t["title"])
