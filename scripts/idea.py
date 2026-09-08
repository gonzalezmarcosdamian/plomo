"""Un loop corto construido alrededor de UNA idea. Otra estrategia.

Por que existe: el generador anterior componia desde estadisticas. Se median
densidades, colocacion del bajo, color del timbre, continuidad, y se escribia lo
que cumpliera todos esos numeros. El resultado cumplia cada restriccion medida y
no decia nada.

La razon, en una linea: **una restriccion es una forma de no estar equivocado, no
una idea.** Acertar todas las restricciones del genero y no tener una idea da
exactamente lo que dio — un tema correcto y vacio. El promedio de muchos temas
buenos no es un tema bueno: es la ausencia de cualquier idea en particular.

Asi que esto arranca al reves. Primero la idea, despues las restricciones, y solo
las que no la peleen.

LA IDEA son dos cosas concretas:

1. **El ritmo del bajo**, sacado del bajo de `Cendryma, THMS (US) - Moonflare`,
   que es un tema que a este DJ le gusta y lo dijo. No se copian las alturas
   —esas son propias— sino la celula ritmica, que es lo que carga la identidad
   en este genero:

       . . X . . X X . . X . . . . X .

   Deja el uno vacio, tropieza en el par de la 5-6, y cae en la 14. Un bajo que
   marca el uno es una marcha; este empuja.

2. **Un gancho con forma de pregunta y respuesta.** Una nota larga que abre y
   tres cortas que contestan, dos veces, la segunda mas arriba y resolviendo
   para abajo. Eso es lo que hace que una melodia se recuerde: que tenga una
   pregunta y una respuesta, no que tenga las notas correctas de la escala.

Son 32 compases —poco mas de un minuto— a proposito. Un boceto que dura ocho
minutos no se puede iterar: para cuando termina ya no te acordas del principio.

Uso:
    python scripts/idea.py --camelot 11A --bpm 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.humano import Humano  # noqa: E402
from plomo.midi import (  # noqa: E402
    MAYOR, MENOR, Pista, grado, nombre_tonalidad, tonica_de_camelot, triada,
)

COMPASES = 32
KICK, CLAP, CHH, OHH, SHAKER, RIM = 36, 39, 42, 46, 70, 37
CONGA_ALTA, CONGA_BAJA = 63, 64

# El ultimo compas de cada bloque de 8: el que anuncia que algo cambia.
#
# La queja fue "es como brusco todo", y medido era literal: el compas 8 era
# identico al 7 y el 9 era otro tema — 1225 de velocidad sumada contra 2411 sin
# una sola nota en el medio que preparara el salto. Lo mismo en el 16 y en el
# 24. Un cambio de seccion se anuncia; nadie lo descubre cuando ya paso.
COMPASES_DE_PASO = (7, 15, 23)

# Cuanto se estira una nota del pad dentro del bloque siguiente, en pulsos.
# 0.9 pulsos son 440 ms a 123 BPM: alcanza para que la cola del acorde viejo
# tape el ataque del nuevo, que es todo lo que se le pide.
SOLAPE = 0.9

# El bajo, en semicorcheas, como FRASE DE CUATRO COMPASES y no como celula de
# uno repetida. Medido sobre el stem de `Kamilo Sanclemente - Sunset Love`, que
# es de donde salio esta iteracion.
#
#   c1  ..X.XX.X..X..X..
#   c2  X...X..X..X.....
#   c3  ..X....X..X..X..
#   c4  X......X..X.....
#
# Lo importante no son las posiciones sino la forma: las semicorcheas 7 y 10
# estan en los CUATRO compases y el resto cambia. Eso es un ancla mas variacion,
# que es distinto de un compas repetido cuatro veces — el oido reconoce el ancla
# y percibe lo demas como que la linea se mueve.
#
# Y baja de densidad hacia el final de la frase: 6, 4, 4, 3 notas. La frase
# respira sola, sin que haga falta sacarle nada al arreglo.
FRASE_BAJO = [
    [2, 4, 5, 7, 10, 13],
    [0, 4, 7, 10],
    [2, 7, 10, 13],
    [0, 7, 10],
]

# Alturas del bajo por posicion, en grados de la escala. Propias, no de Kamilo.
# La septima en el 13 es la que tira hacia el compas siguiente.
GRADOS_BAJO = {0: 0, 2: 0, 4: 0, 5: 0, 7: 0, 10: 0, 13: 6}

# Progresion: i cuatro compases, iv cuatro compases.
#
# El iv es la idea que se trae de Sunset Love, que va Am - Dm sosteniendo el Dm
# cuatro compases enteros. La version anterior usaba i - VI y NUNCA tocaba el iv
# — el auditor lo habia marcado. El iv es el acorde calido del modo menor: no
# tensa como el VII ni resuelve como el VI, abre.
PROGRESION = [0, 3]

# El gancho, en (compas del grupo de 4, pulso, grado, duracion en pulsos).
#
# Pregunta: una blanca. Respuesta: tres negras bajando. Se repite un grado mas
# arriba y resuelve. Ocho notas en cuatro compases — si hicieran falta mas para
# que se entienda, no seria un gancho.
GANCHO = [
    (0, 0.0, 4, 2.0),
    (1, 0.0, 7, 0.7), (1, 1.0, 6, 0.7), (1, 2.0, 4, 1.4),
    (2, 0.0, 5, 2.0),
    (3, 0.0, 4, 0.7), (3, 1.0, 3, 0.7), (3, 2.0, 1, 1.8),
]


def _empuje(compas: int) -> float:
    """Cuanto crece lo que YA suena hacia el final del bloque de 8 compases.

    Devuelve 0 en los primeros seis compases, 0.5 en el septimo y 1.0 en el
    octavo. Es el unico crescendo real del loop y es a proposito el mas barato
    que hay: no suma una nota: le sube la velocidad a las semicorcheas del
    shaker y de los hats que ya estaban ahi.

    Existe porque antes no habia forma de saber que venia un cambio hasta que
    el cambio ya habia entrado. Agregar cosas nuevas para preparar habria
    sumado densidad justo donde hace falta lo contrario — antes de que algo se
    sienta grande, lo anterior tiene que ser chico. Subir lo que ya esta no
    engorda nada.
    """
    posicion = compas % 8
    return 0.0 if posicion < 6 else (posicion - 5) / 2.0


def _bajo(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    p = Pista("Bajo", bpm, canal=0)
    for c in range(COMPASES):
        celula = FRASE_BAJO[c % 4]
        # La duracion llega hasta la proxima nota: el bajo es una linea, no
        # golpes sueltos. Cuanto llega depende de si hay bombo: en la intro el
        # bajo es lo unico armonico que suena y tiene que SOSTENER (92% del
        # hueco, casi legato); con el bombo abajo pasa a MARCAR y se cierra al
        # 72%, que deja aire entre nota y nota.
        #
        # Eso pasaba de golpe en el compas 9 — 92% a 72% de un compas al otro,
        # en el mismo compas donde entraba el bombo y entraban los acordes. El
        # bajo cambiaba de articulacion en el peor momento posible y sumaba al
        # corte en vez de tapararlo. Ahora se cierra a lo largo de cuatro
        # compases: para cuando la mano suelta, el oido ya se acostumbro.
        if c < 8:
            apertura = 0.92
        elif c < 12:
            apertura = 0.92 - 0.05 * (c - 7)      # 0.87, 0.82, 0.77, 0.72
        else:
            apertura = 0.72
        for i, k in enumerate(celula):
            siguiente = celula[i + 1] if i + 1 < len(celula) else 16 + celula[0]
            dur = max(0.22, (siguiente - k) * 0.25 * apertura)
            alt = grado(tonica, escala, GRADOS_BAJO[k], octava=1)
            pulso = k * 0.25
            p.nota(c, h.pulso("bajo", c, pulso), alt, dur,
                   h.vel("bajo", c, pulso, 104 if k in (2, 9) else 88))
    return p


def _bateria(bpm: float, h: Humano) -> Pista:
    """Lo minimo que sostiene el groove. Nada mas."""
    p = Pista("Bateria", bpm, canal=9)
    for c in range(COMPASES):
        emp = _empuje(c)
        paso = c in COMPASES_DE_PASO
        if c >= 8:                       # el bombo entra en el compas 9
            for pulso in range(4):
                if c == COMPASES - 1 and pulso == 3:
                    continue
                p.nota(c, pulso, KICK, 0.25, h.vel("kick", c, pulso, 108))
        # El clap entra recien en el 13, cuatro compases DESPUES del bombo.
        #
        # Antes el 9 traia bombo, clap y acordes juntos: tres elementos nuevos
        # en el mismo tiempo 1, y el bajo cambiando de articulacion encima. Un
        # cambio se escucha; tres a la vez se escuchan como un corte de cinta.
        # Bombo solo cuatro compases y despues el contratiempo es el orden de
        # siempre del genero, y ademas le da al compas 13 un evento propio
        # donde antes no pasaba nada.
        if c >= 12:
            for pulso in (1, 3):
                p.nota(c, h.pulso("clap", c, pulso), CLAP, 0.25,
                       h.vel("clap", c, pulso, 90))
        # Hats: abierto y cerrado ALTERNADOS en los contratiempos de corchea.
        #
        # Antes el cerrado iba en 0.75, 1.75, 2.75, 3.75 — la semicorchea justo
        # ANTES de cada pulso. Eso no se escucha como un hat sino como un
        # adelanto del golpe que viene, casi un flam contra el bombo. Era el hat
        # raro.
        #
        # El contratiempo de corchea es donde vive el hat en house: abierto en el
        # 1 y el 3, cerrado en el 2 y el 4. Alternar los dos es lo que arma el
        # vaiven, y ademas evita que los dos caigan encima como pasaba antes.
        for pulso in (0.5, 2.5):
            if c % 8 >= 4 or c >= 8:
                p.nota(c, h.pulso("hat_abierto", c, pulso), OHH, 0.20,
                       h.vel("hat_abierto", c, pulso, 58 + int(10 * emp)))
        for pulso in (1.5, 3.5):
            if paso and pulso == 3.5:
                continue                 # ese lugar es del abierto del repique
            p.nota(c, h.pulso("hat", c, pulso), CHH, 0.10,
                   h.vel("hat", c, pulso, (40 if c < 8 else 54) + int(10 * emp)))
        # fantasmas de semicorchea, bien abajo: dan movimiento sin sumar golpes
        for pulso in (1.75, 3.75):
            p.nota(c, h.pulso("hat", c, pulso), CHH, 0.08,
                   h.vel("hat", c, pulso, 26 if c < 8 else 34))
        # Shaker en semicorcheas corridas. Es textura, no golpes: continuo y muy
        # abajo, es lo que llena sin que se escuche como un elemento mas.
        #
        # Y es el crescendo del tema. Sobre los dos ultimos compases de cada
        # bloque de 8 la velocidad sube dentro del compas —de la semicorchea 1
        # a la 16— hasta 26 puntos. No hay una nota mas que antes: son las
        # mismas y crecen. Un shaker que se abre es la forma mas vieja y mas
        # barata que hay de decir "viene algo", y es exactamente lo que el loop
        # no tenia.
        if c >= 4:
            for k in range(16):
                if k % 4 == 0:
                    continue             # el pulso es del bombo
                base = (24 if c < 8 else 32) + int(round(26 * emp * k / 15))
                p.nota(c, h.pulso("percusion", c, k * 0.25), SHAKER, 0.07,
                       h.vel("percusion", c, k * 0.25, base))
        # Percusion en el registro medio. Sunset Love lleva 8 golpes por compas
        # ahi y nosotros teniamos 2 (los claps). Ese registro es el que le da
        # cuerpo al groove sin sumar brillo arriba ni peso abajo — es donde vive
        # lo organico del genero.
        #
        # Va en tresillos contra las semicorcheas del hat: dos grillas distintas
        # sonando juntas es lo que hace que un loop de un compas no se escuche
        # como un compas.
        for pulso, alt in ((0.33, CONGA_BAJA), (1.0, CONGA_ALTA),
                           (1.66, CONGA_BAJA), (2.33, CONGA_ALTA),
                           (3.0, CONGA_BAJA), (3.66, CONGA_ALTA)):
            if c < 4:
                continue                 # entra en el compas 5
            if paso and pulso >= 3.0:
                continue                 # el cuarto tiempo lo ocupa el repique
            p.nota(c, h.pulso("percusion", c, pulso), alt, 0.12,
                   h.vel("percusion", c, pulso, (48 if c < 8 else 60)
                         + int(12 * emp)))
        # segunda voz de conga desde el 17: la percusion se acumula con el tema
        if c >= 16:
            for pulso in (0.66, 2.0, 3.33):
                if paso and pulso >= 3.0:
                    continue
                p.nota(c, h.pulso("percusion", c, pulso), CONGA_ALTA, 0.10,
                       h.vel("percusion", c, pulso, 46 + int(12 * emp)))
        # Repique de paso: cuatro semicorcheas que crecen sobre el cuarto tiempo
        # del ultimo compas de cada bloque, mas el hat abierto encima.
        #
        # Es el gesto que faltaba y que hacia que todo sonara cortado. El oido
        # necesita medio compas de aviso para leer un cambio como llegada y no
        # como salto; sin eso, el compas 9 no era el drop, era un empalme.
        if paso:
            for i, k in enumerate((3.0, 3.25, 3.5, 3.75)):
                p.nota(c, h.pulso("percusion", c, k),
                       CONGA_BAJA if i % 2 == 0 else CONGA_ALTA, 0.12,
                       h.vel("percusion", c, k, 52 + 12 * i))
            p.nota(c, h.pulso("hat_abierto", c, 3.5), OHH, 0.35,
                   h.vel("hat_abierto", c, 3.5, 74))
        # el rim marca el uno mientras no hay bombo
        if c < 8:
            p.nota(c, h.pulso("percusion", c, 0), RIM, 0.10,
                   h.vel("percusion", c, 0, 42))
    return p


def _acordes(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """Dos acordes, cuatro compases cada uno. i - iv.

    Golpes cortos en el contratiempo mas una fundamental larga abajo: la triada
    sostenida con reverb es lo que suena a organo.
    """
    p = Pista("Acordes", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        g = PROGRESION[bloque % len(PROGRESION)]
        notas = triada(tonica, escala, g, octava=3, septima=False)
        # La fundamental dura 16 pulsos + solape en vez de 15.5. Antes dejaba
        # 244 ms de silencio en cada frontera de cuatro compases y volvia a
        # atacar en el uno siguiente: un corte audible en la nota mas grave que
        # hay sonando, y justo donde cambia la seccion.
        p.nota(bloque * 4, 0, notas[0], 4 * 4 + SOLAPE, 40 + 2 * bloque)
        if bloque < 2:                   # los acordes entran en el compas 9
            continue
        for c in range(bloque * 4, bloque * 4 + 4):
            emp = _empuje(c)
            for pulso in (1.5, 3.5):
                # 0.55 pulsos y no 0.32. A 123 BPM 0.32 son 156 ms: eso no es
                # un golpe de acorde, es un click con altura. 0.55 sigue siendo
                # corto —268 ms, media negra— asi que no se vuelve el organo
                # sostenido que estos golpes existen para evitar, pero ahora
                # cada uno tiene cola. Un ataque sin cola es literalmente lo
                # que se escucha como brusco.
                p.acorde(c, h.pulso("acordes", c, pulso), notas[1:], 0.55,
                         h.vel("acordes", c, pulso,
                               (62 if pulso == 1.5 else 54) + int(10 * emp)))
    return p


def _atmosfera(bpm: float, tonica: int, escala: list[int]) -> Pista:
    """Triada sostenida, muy abajo de volumen, los 32 compases.

    Es lo unico que no golpea. Sin esto la intro son bajo corto, hat y rim —
    tres cosas que atacan y ninguna que sostenga— y eso se escucha percusivo y
    vacio a la vez, que parece una contradiccion y no lo es: lo que falta no son
    eventos, es algo que dure entre evento y evento.

    Entra desde el compas 1 y no se va nunca. La capa que sostiene no es un
    elemento del arreglo que aparece y desaparece: es el piso.
    """
    p = Pista("Atmosfera", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        g = PROGRESION[bloque % len(PROGRESION)]
        notas = triada(tonica, escala, g, octava=3, septima=False)
        # El piso crece parejo en vez de dar un salto. Antes iba 34 en la intro
        # y 44 desde el compas 9: un escalon de golpe en la unica capa que
        # tendria que ser lo que no se mueve. Ahora sube de a poco, bloque a
        # bloque, y no hay ningun momento en que "sube el pad".
        vel = 30 + round(24 * bloque / (COMPASES // 4 - 1))
        # Y dura 16 pulsos + solape, no 15.7.
        #
        # Con 15.7 quedaban 146 ms de silencio en cada frontera de 4 compases:
        # siete huecos en la capa cuyo trabajo, escrito tres parrafos mas
        # arriba, es no irse nunca — y siete ataques de pad al descubierto
        # exactamente en los compases donde cambia la seccion. Un ataque de pad
        # tapado por la cola del acorde anterior no se escucha; al descubierto
        # es un golpe, y era el golpe que estaba abajo de los cuatro cambios.
        #
        # Los 440 ms en que se pisan el i y el iv no son un choque: juntos dan
        # F#-A-B-C#-D, cinco notas de la misma escala. Es una suspension, que es
        # como suena un pad cuando lo toca alguien y no cuando lo corta una
        # grilla.
        p.acorde(compas=bloque * 4, pulso=0, alturas=notas,
                 duracion=4 * 4 + SOLAPE, velocidad=vel)
    return p


def _gancho(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """La melodia. Entra sola en el 17 y se abre en dos pasos, no en uno.

    Las alturas del gancho no se tocaron: las de los ultimos ocho compases son
    exactamente las mismas tres voces de antes. Lo que cambio es CUANDO llega
    cada una y cual de las tres lleva la melodia.

    Antes, en el compas 25, pasaban tres cosas en el mismo tiempo 1: la voz
    principal saltaba una octava entera (73 -> 85), se le sumaba la tercera
    arriba y se le sumaba la octava abajo. Tres movimientos de desarrollo
    gastados en un golpe, y peor: la linea que el oido venia siguiendo ocho
    compases desaparecia de donde estaba y reaparecia arriba, mientras su
    registro viejo quedaba ocupado por la voz mas floja de las tres. Eso no se
    escucha como que la melodia crecio: se escucha como un corte de cinta.

    Ahora la voz principal NO se mueve nunca de la octava 4. Es la misma linea
    de punta a punta, sin un solo salto:

        17-24  sola
        25-28  se le suma la octava arriba  (registro: se abre el rango)
        29-32  se le suma la tercera arriba (cuerpo: pasa a ser dos voces)

    Es la escalera de desarrollo en orden y de a un escalon por vez, que es
    para lo que sirve tener cuatro formas distintas de repetir con una
    diferencia. Si se gastan dos en el mismo compas queda un salto, y despues
    no queda a donde crecer.
    """
    p = Pista("Gancho", bpm, canal=0)
    for bloque in (4, 5, 6, 7):          # compases 17-32
        doble = bloque >= 6              # 25-32: octava arriba
        cuerpo = bloque >= 7             # 29-32: y ademas la tercera
        for compas, pulso, g, dur in GANCHO:
            c = bloque * 4 + compas
            if c >= COMPASES:
                continue
            largo = dur > 1.2
            # La voz que lleva la melodia. Siempre la misma octava, y sube de
            # nivel en cada paso: la melodia se abre creciendo ella, no
            # cediendole el protagonismo a una voz nueva.
            base = (92 if largo else 76) + (4 if doble else 0) + (6 if cuerpo else 0)
            p.nota(c, h.pulso("gancho", c, pulso),
                   grado(tonica, escala, g, octava=4), dur,
                   h.vel("gancho", c, pulso, base))
            if doble:
                # la octava arriba, mas floja: abre el registro sin robarle la
                # linea a la voz principal
                p.nota(c, h.pulso("gancho", c, pulso + 0.01),
                       grado(tonica, escala, g, octava=5), dur,
                       h.vel("gancho", c, pulso, 74 if largo else 60))
            if cuerpo:
                # la tercera arriba es la que da el color: recien aca la
                # melodia deja de ser una linea y pasa a ser dos voces
                p.nota(c, h.pulso("gancho", c, pulso + 0.02),
                       grado(tonica, escala, g + 2, octava=5), dur,
                       h.vel("gancho", c, pulso, 62 if largo else 50))
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camelot", default="11A")
    ap.add_argument("--bpm", type=float, default=123.0)
    ap.add_argument("--nombre", default="idea")
    ap.add_argument("--semilla", type=int, default=7,
                    help="misma semilla, mismo archivo: sirve para comparar versiones")
    args = ap.parse_args()

    tonica, menor = tonica_de_camelot(args.camelot)
    escala = MENOR if menor else MAYOR
    destino = Path("postproduction/bocetos") / args.nombre
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob("*.mid"):
        viejo.unlink()

    h = Humano(args.semilla)
    pistas = [("01_atmosfera.mid", _atmosfera(args.bpm, tonica, escala)),
              ("02_acordes.mid", _acordes(args.bpm, tonica, escala, h)),
              ("03_bajo.mid", _bajo(args.bpm, tonica, escala, h)),
              ("04_bateria.mid", _bateria(args.bpm, h)),
              ("05_gancho.mid", _gancho(args.bpm, tonica, escala, h))]

    print(f"  {nombre_tonalidad(args.camelot)} a {args.bpm:.0f} BPM, "
          f"{COMPASES} compases = {COMPASES * 4 * 60 / args.bpm:.0f} segundos\n")
    print("  1-8    bajo y percusion, sin bombo")
    print("  9-12   entra el bombo solo, y la armonia")
    print("  13-16  entra el clap")
    print("  17-24  entra el gancho, solo")
    print("  25-28  al gancho se le suma la octava arriba")
    print("  29-32  y ademas la tercera: la melodia queda en dos voces")
    print("  8/16/24  repique y crescendo de paso hacia cada cambio")
    print()
    for archivo, p in pistas:
        p.guardar(destino / archivo)
        n = sum(1 for e in p._eventos if e.datos[0] & 0xF0 == 0x90)
        print(f"  {archivo:16} {n:4d} notas = {n / COMPASES:4.1f} por compas")
    print(f"\n  python scripts/a_live.py {destino} --bpm {args.bpm:.0f}")


if __name__ == "__main__":
    main()
