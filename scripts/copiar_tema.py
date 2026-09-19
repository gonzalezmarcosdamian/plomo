"""Transcribe un fragmento de un tema real a clips MIDI, para meterlo en Live.

Por que existe: cuando un boceto propio suena mal hay dos culpables posibles y
escuchando no se distinguen. Puede ser la cadena — los instrumentos elegidos,
como entra el MIDI a Live, la mezcla — o puede ser la composicion. Este script
separa las dos cosas: transcribe un tema que ya suena bien y lo manda por
exactamente la misma cadena.

Trabaja sobre stems, no sobre la mezcla. La primera version analizaba la mezcla
completa y fallo de forma medible: la banda grave contiene el bajo tanto como el
bombo, asi que salieron 43 golpes irregulares donde hay 32 parejos, y pyin
seguia armonicos del pad en vez de la fundamental del bajo, con 23% de notas
fuera de tonalidad en un tema que no se sale nunca. Ver `separar.py`.

Lo que NO es: esto no reconstruye el tema. Saca armonia, bajo y patron ritmico;
el sonido de un track es sobre todo produccion — el filtro que se abre, la
reverb, el sample exacto del bombo — y nada de eso vive en el MIDI. Una
transcripcion pobre no prueba que el tema sea pobre. Sirve para comparar dos
esqueletos entre si, que es la pregunta que tenemos.

Uso:
    python scripts/copiar_tema.py "<archivo.mp3>" --desde 180 --compases 8
"""
from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import butter, sosfiltfilt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from plomo.midi import Pista  # noqa: E402
from separar import MARGEN_S, separar  # noqa: E402

SR = 22050
HOP = 256

# Bandas dentro del stem de bateria: (lo, hi, nota MIDI, velocidad).
# Ahora que el stem no trae bajo ni pad, las bandas separan piezas de la
# bateria entre si en vez de pelear contra el resto de la mezcla.
BANDAS = {
    "kick": (30, 120, 36, 104),
    "clap": (200, 1400, 39, 88),
    "hat": (6000, 11000, 42, 64),
}

# El vocabulario de acordes, con septimas y novenas.
#
# La version anterior se restringia a dos triadas, y el motivo estaba bien
# diagnosticado: puntuando por SUMA de la energia del croma adentro del acorde,
# el de mas notas gana siempre porque cubre mas croma. Medido sobre estos mismos
# 16 compases de "Tunnel", con septimas y novenas habilitadas la suma elige un
# acorde de CINCO notas en los dieciseis compases. El sesgo es real.
#
# Pero la cura mataba al paciente. Con solo triadas, doce de esos dieciseis
# compases salian "F" —incluidos los que el croma muestra claramente en D— y la
# progresion entera se aplastaba en un acorde. Un pad de progressive con la
# fundamental, la septima y la novena sonando a la vez no ES una triada, y
# obligarlo a serlo no da la triada mas parecida: da cualquier cosa.
#
# Lo que saca el sesgo sin perder el vocabulario esta en `_puntaje`.
ACORDES = {
    "":     [0, 4, 7],
    "m":    [0, 3, 7],
    "sus4": [0, 5, 7],
    "m7":   [0, 3, 7, 10],
    "maj7": [0, 4, 7, 11],
    "7":    [0, 4, 7, 10],
    "m9":   [0, 3, 7, 10, 2],
    "add9": [0, 2, 4, 7],
}
NOMBRES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MENOR = [0, 2, 3, 5, 7, 8, 10]
MAYOR = [0, 2, 4, 5, 7, 9, 11]


def _banda(y: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    sos = butter(4, [lo / (sr / 2), min(hi, sr / 2 - 1) / (sr / 2)],
                 btype="band", output="sos")
    return sosfiltfilt(sos, y)


def _envolvente(y: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    env = librosa.onset.onset_strength(y=_banda(y, sr, lo, hi), sr=sr, hop_length=HOP)
    return env / (env.max() or 1.0)


def _golpes(env: np.ndarray, sr: int) -> np.ndarray:
    return librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=HOP,
                                      units="time", delta=0.25, wait=2)


def _fase(golpes: np.ndarray, periodo: float) -> float:
    """Fase promedio de una serie de golpes, en circular.

    Circular y no promedio comun: las fases viven en un circulo, y un golpe a
    0.01 y otro a 0.49 de un periodo de 0.50 estan pegados, pero el promedio
    aritmetico los manda al medio. Ese error ponia la grilla a media negra.
    """
    ang = 2 * np.pi * (golpes % periodo) / periodo
    medio = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean()) % (2 * np.pi)
    return periodo * medio / (2 * np.pi)


def _grilla(drums: np.ndarray, sr: int, bpm: float) -> np.ndarray:
    """Semicorcheas alineadas al compas, a partir del stem de bateria.

    La fase del pulso sale del bombo. La fase del COMPAS sale del clap: en house
    el bombo pega en las cuatro negras, asi que no dice cual es el uno —
    cualquier corrimiento de un tiempo le calza igual de bien. El clap pega en el
    dos y el cuatro, y eso si desambigua. Sin esto el loop queda corrido un
    tiempo y se siente mal aunque cada golpe este exactamente en la grilla.
    """
    negra = 60.0 / bpm
    kicks = _golpes(_envolvente(drums, sr, *BANDAS["kick"][:2]), sr)
    cero = _fase(kicks, negra) if len(kicks) else 0.0

    claps = _golpes(_envolvente(drums, sr, *BANDAS["clap"][:2]), sr)
    if len(claps):
        mejor, puntaje = 0, -1
        for corrimiento in range(4):
            base = cero + corrimiento * negra
            impares = sum(1 for t in claps if round((t - base) / negra) % 2 == 1)
            if impares > puntaje:
                mejor, puntaje = corrimiento, impares
        cero += mejor * negra
    while cero >= negra * 4:
        cero -= negra * 4
    return cero + np.arange(0, 4000) * (negra / 4)


def _afinar_bpm(drums: np.ndarray, sr: int, bpm: float) -> float:
    """Elige el BPM que deja los bombos mas cerca de la grilla.

    El beat tracker de librosa da el tempo por autocorrelacion del onset y en
    progressive se equivoca por un par de BPM: mide bien la periodicidad pero la
    envolvente es blanda y el pico queda ancho. En Afrika decia 123 con el tema a
    121, y a 123 el 60% de los bombos caia a mas de 20 ms de la grilla — que es
    justo el error que se escucha como destiempo.

    El criterio es directo: la grilla existe para poner notas encima, asi que el
    mejor BPM es el que minimiza la distancia de los golpes reales a la grilla.
    """
    kicks = _golpes(_envolvente(drums, sr, *BANDAS["kick"][:2]), sr)
    if len(kicks) < 8:
        return bpm
    candidatos = np.arange(bpm - 4.0, bpm + 4.01, 0.05)
    desvios = [np.abs(kicks[:, None] - _grilla(drums, sr, float(c))[None, :])
               .min(axis=1).mean() for c in candidatos]
    return float(candidatos[int(np.argmin(desvios))])


def _cuantizar(tiempos: np.ndarray, grilla: np.ndarray) -> set[int]:
    """A que semicorchea cae cada golpe.

    Devuelve indices y descarta el desvio a proposito: el desvio de una
    deteccion automatica es error de medicion, no groove. Conservarlo seria
    copiar el ruido del detector creyendo que se copia el feeling del tema.
    """
    if len(tiempos) == 0:
        return set()
    idx = np.clip(np.searchsorted(grilla, tiempos), 1, len(grilla) - 1)
    izq = np.abs(tiempos - grilla[idx - 1])
    der = np.abs(tiempos - grilla[idx])
    return set((idx - (izq < der).astype(int)).tolist())


def _bateria(drums: np.ndarray, sr: int, grilla: np.ndarray, semis: int,
             bpm: float) -> Pista:
    p = Pista("Bateria", bpm, canal=9)
    for lo, hi, nota, vel in BANDAS.values():
        golpes = _cuantizar(_golpes(_envolvente(drums, sr, lo, hi), sr), grilla)
        for i in sorted(x for x in golpes if 0 <= x < semis):
            p.nota(i // 16, (i % 16) * 0.25, nota, 0.12, vel)
    return p


def _puntaje(perfil: np.ndarray, raiz: int, grados: list[int]) -> float:
    """Pearson entre el perfil de croma y la plantilla binaria del acorde.

    Centrar las DOS series es lo que saca el sesgo de tamano. Una plantilla con
    mas unos tiene media mas alta, asi que al centrarla le baja el aporte de
    cada nota: un acorde de cinco notas solo gana si esas cinco explican el
    compas mejor, no por ser cinco.

    Y lo importante, que la suma no hacia: la correlacion PENALIZA la energia
    que el acorde deja afuera. La formula anterior era `dentro/3 - fuera/9`, y
    como `fuera = total - dentro` con `total` constante por compas, eso se
    reduce a maximizar `dentro` a secas — el "menos la energia de afuera" que
    prometia el comentario era algebraicamente cero.

    Verificado sobre 16 compases de "Tunnel": puntuando por suma, con este
    vocabulario, el acorde elegido tiene cinco notas en los dieciseis compases.
    Con la correlacion, ninguno: cuatro triadas y doce cuatriadas.
    """
    t = np.zeros(12)
    for g in grados:
        t[(raiz + g) % 12] = 1.0
    a, b = perfil - perfil.mean(), t - t.mean()
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float((a * b).sum() / den) if den else -1.0


def _armonia(other: np.ndarray, sr: int, grilla: np.ndarray, semis: int,
             bpm: float) -> tuple[Pista, list[str]]:
    """Un acorde por compas, por correlacion del croma contra plantillas."""
    croma = librosa.feature.chroma_cqt(y=other, sr=sr, hop_length=HOP)
    veces = librosa.times_like(croma, sr=sr, hop_length=HOP)

    p = Pista("Acordes", bpm, canal=0)
    elegidos: list[str] = []
    for compas in range(semis // 16):
        franja = croma[:, (veces >= grilla[compas * 16]) &
                          (veces < grilla[(compas + 1) * 16])]
        if franja.size == 0:
            elegidos.append("-")
            continue
        perfil = franja.mean(axis=1)
        v, raiz, sufijo = max((_puntaje(perfil, r, g), r, n)
                              for n, g in ACORDES.items() for r in range(12))
        p.acorde(compas=compas, pulso=0,
                 alturas=[48 + raiz + g for g in ACORDES[sufijo]],
                 duracion=3.9, velocidad=64)
        elegidos.append(NOMBRES[raiz] + sufijo)
    return p, elegidos


def _alturas_por_semi(bass: np.ndarray, sr: int, grilla: np.ndarray,
                      semis: int) -> list[int | None]:
    """El semitono de cada semicorchea, o None si el detector no se decidio.

    Por que la MODA de los semitonos y no la mediana de los Hz. La version
    anterior hacia `median(f0)` sobre el tramo y despues redondeaba a semitono.
    Eso funciona si el detector es estable, y pyin sobre un stem de Demucs no lo
    es: tira frames sueltos una octava arriba o abajo. La mediana de un tramo
    con frames en 55 Hz y en 110 Hz no da ninguna de las dos alturas — da algo
    en el medio, que cae en cualquier semitono. Medido sobre Alex O'Rion
    "Tunnel", eso daba 70% de notas fuera de tonalidad: las alturas no eran del
    tema, eran el promedio de los errores del detector.

    La moda de los semitonos redondeados no tiene ese problema: los frames
    equivocados no arrastran a los buenos, solo pierden la votacion. Y si NINGUNA
    altura junta la mitad de los frames, el detector no se decidio y no hay nota
    — silencio honesto en vez de una altura inventada.
    """
    f0, sonoro, _ = librosa.pyin(bass, sr=sr, fmin=35, fmax=260,
                                 frame_length=2048, hop_length=HOP)
    veces = librosa.times_like(f0, sr=sr, hop_length=HOP)

    # La correccion de afinacion, que no es un detalle.
    #
    # El stem de bajo de "Tunnel" mide -28 cents contra el temperamento igual, y
    # los frames de pyin dan -32 de mediana. Un tercio de semitono. Redondear
    # sin corregir eso tira sistematicamente al semitono de ABAJO en cuanto el
    # detector agrega unos cents de su propio ruido, y se ve en el resultado:
    # la transcripcion daba D x7 y C# x7 empatados, con C# un semitono debajo de
    # la tonica de un tema que no se sale de Re menor.
    #
    # No es que el tema este desafinado: un master pasado por time-stretch o
    # por una cinta corre unos cents, y el oido no lo registra porque todo corre
    # junto. El redondeo a semitono si lo registra, porque es absoluto.
    afinacion = float(librosa.estimate_tuning(y=bass, sr=sr))
    midi = librosa.hz_to_midi(f0) - afinacion

    fuera: list[int | None] = []
    for i in range(semis):
        # `sonoro` solo, sin filtrar por voiced_prob. La version que filtraba
        # por `prob > 0.5` se quedaba con el 4.7% de los frames donde
        # voiced_flag da 88.7%: el umbral estaba puesto sin mirar la
        # distribucion y tiraba casi todo el bajo a la basura.
        m = (veces >= grilla[i]) & (veces < grilla[i + 1]) & sonoro
        v = midi[m]
        v = v[~np.isnan(v)]
        if len(v) < 3:
            fuera.append(None)
            continue
        cuenta = Counter(int(np.clip(round(x), 24, 55)) for x in v)
        altura, votos = cuenta.most_common(1)[0]
        fuera.append(altura if votos >= 0.5 * len(v) else None)
    return fuera


def _sin_octavas(alturas: list[int | None]) -> list[int | None]:
    """Baja los saltos de octava sueltos del detector.

    Una semicorchea que esta exactamente a 12 semitonos de sus dos vecinas, y
    esas dos vecinas son iguales entre si, no es una nota: es pyin agarrando el
    segundo armonico por un instante. El bajo del genero no salta una octava
    para volver en 120 ms.
    """
    fuera = list(alturas)
    for i in range(1, len(fuera) - 1):
        a, b, c = fuera[i - 1], fuera[i], fuera[i + 1]
        if None in (a, b, c) or a != c:
            continue
        if abs(b - a) == 12:
            fuera[i] = a
    return fuera


def _bajo(bass: np.ndarray, sr: int, grilla: np.ndarray, semis: int,
          bpm: float) -> Pista:
    """Transcribe el bajo con su DURACION real, no una semicorchea por nota.

    La version anterior escribia cada nota con duracion 0.22 pulsos fijos y se
    salteaba las repeticiones. El resultado eran 55 notas todas de una
    semicorchea: un bajo que en el disco sostiene dos compases quedaba como un
    pinchazo y un silencio. Se perdia justo lo que define al bajo del genero,
    que es cuanto se queda.

    Ahora las semicorcheas con la misma altura se AGRUPAN en una nota sola del
    largo que ocupen. El 0.92 del final es el respiro entre notas: dos notas de
    la misma altura pegadas se solapan en el tick, y en MIDI el note-off de la
    segunda mata a la primera en vez de sostenerla.
    """
    alturas = _sin_octavas(_alturas_por_semi(bass, sr, grilla, semis))

    p = Pista("Bajo", bpm, canal=1)
    i = 0
    while i < semis:
        if alturas[i] is None:
            i += 1
            continue
        largo = 1
        while i + largo < semis and alturas[i + largo] == alturas[i]:
            largo += 1
        p.nota(i // 16, (i % 16) * 0.25, alturas[i], largo * 0.25 * 0.92, 92)
        i += largo
    return p


def _verificar(drums: np.ndarray, sr: int, grilla: np.ndarray, bpm: float,
               bateria: Pista, bajo: Pista, acordes: list[str],
               compases: int) -> None:
    """Chequeo de sanidad antes de hacer escuchar nada.

    Una transcripcion mala se escucha mal, pero escuchandola no se sabe si esta
    mal la transcripcion o el tema. Estos tres numeros lo dicen antes: si el
    bombo no da 4 por compas o el bajo tiene un cuarto de notas fuera de escala,
    lo que salio es ruido del detector y no hay nada que escuchar todavia.
    """
    print("\n  verificacion:")

    kicks = _golpes(_envolvente(drums, sr, *BANDAS["kick"][:2]), sr)
    dentro = (np.abs(kicks[:, None] - grilla[None, :]).min(axis=1) < 0.020).mean()
    n_kick = sum(1 for e in bateria._eventos if e.datos[0] & 0xF0 == 0x90
                 and e.datos[1] == BANDAS["kick"][2])
    print(f"    bombo    {n_kick / compases:4.2f} por compas   "
          f"(4.00 es lo esperado en house)")
    print(f"    grilla   {dentro * 100:3.0f}% de los bombos a menos de 20 ms")

    # La tonalidad se BUSCA, no se supone.
    #
    # Esta verificacion decia "80% de notas fuera de F menor" sobre una
    # transcripcion que estaba bien. El error: tomaba el acorde mas repetido
    # —que era F MAYOR— y le armaba una escala MENOR sobre esa raiz. Fa menor y
    # Re menor comparten tres notas de siete, asi que medir contra la primera
    # cuando el tema esta en la segunda da un numero de basura. El archivo, que
    # lleva el Camelot en el nombre, decia 7A = Re menor desde el principio.
    #
    # Se prueban las veinticuatro escalas y se reporta la que mejor explica lo
    # que hay. Si la mejor explica poco, ahi si el detector fallo; si explica
    # mucho pero no es la que uno esperaba, aprendimos algo del tema.
    notas = [e.datos[1] % 12 for e in bajo._eventos if e.datos[0] & 0xF0 == 0x90]
    if notas:
        escalas = [(sum(1 for n in notas if n in {(pc + g) % 12 for g in grados})
                    / len(notas), f"{NOMBRES[pc]} {nombre}")
                   for pc in range(12)
                   for nombre, grados in (("menor", MENOR), ("mayor", MAYOR))]
        dentro, cual = max(escalas)
        print(f"    bajo     {dentro * 100:3.0f}% de las notas entran en {cual} "
              f"({len(notas)} notas, la escala que mejor explica)")
        if dentro < 0.85:
            print("             OJO: ninguna escala explica el bajo. Eso es "
                  "ruido del detector, no un tema raro.")
    reales = [a for a in acordes if a != "-"]
    if reales:
        raiz = max(set(reales), key=reales.count)
        estable = reales.count(raiz) / len(reales)
        print(f"    acordes  {estable * 100:3.0f}% de los compases en {raiz}")

    if dentro < 0.7 or not 3.5 <= n_kick / compases <= 4.5:
        print("\n    OJO: el bombo no engancha. Lo que sigue es ruido del "
              "detector, no el tema.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--desde", type=float, default=180.0,
                    help="segundo donde empieza el fragmento (default 3:00, que "
                         "en progressive suele caer adentro del groove)")
    ap.add_argument("--compases", type=int, default=8)
    ap.add_argument("--bpm", type=float, help="pisa el BPM detectado")
    ap.add_argument("--forzar", action="store_true", help="reseparar, ignorar cache")
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")

    bpm = args.bpm or 121.0
    dur = args.compases * 4 * 60.0 / bpm + 4.0
    rutas = separar(args.archivo, args.desde, dur, args.forzar)

    # los stems traen MARGEN_S de contexto adelante: se descuenta para que el
    # tiempo 0 del analisis sea el mismo --desde que se pidio
    recorte = min(args.desde, MARGEN_S)
    stems = {n: librosa.load(p, sr=SR, offset=recorte, duration=dur)[0]
             for n, p in rutas.items()}

    if args.bpm is None:
        crudo = float(np.atleast_1d(
            librosa.beat.beat_track(y=stems["drums"], sr=SR)[0])[0])
        while crudo < 100:          # el tracker suele dar la mitad o el doble
            crudo *= 2
        while crudo > 145:
            crudo /= 2
        bpm = _afinar_bpm(stems["drums"], SR, crudo)
        print(f"  BPM: {bpm:.1f}  (el tracker decia {crudo:.1f})")
    else:
        print(f"  BPM: {bpm:.1f}  (forzado)")

    grilla = _grilla(stems["drums"], SR, bpm)
    semis = args.compases * 16
    print(f"  fragmento: {args.desde:.0f}s, {args.compases} compases, "
          f"grilla desde {grilla[0]:.3f}s")

    acordes, elegidos = _armonia(stems["other"], SR, grilla, semis, bpm)
    bajo = _bajo(stems["bass"], SR, grilla, semis, bpm)
    bateria = _bateria(stems["drums"], SR, grilla, semis, bpm)
    print("  acordes: " + " | ".join(elegidos))

    _verificar(stems["drums"], SR, grilla, bpm, bateria, bajo, elegidos,
               args.compases)

    salida = args.salida or (Path("postproduction/bocetos") /
                             ("copia_" + "".join(
                                 c if c.isalnum() else "_"
                                 for c in args.archivo.stem.lower())[:36].strip("_")))
    salida.mkdir(parents=True, exist_ok=True)
    for viejo in salida.glob("*.mid"):
        viejo.unlink()
    print()
    for n, p in enumerate([acordes, bajo, bateria], start=1):
        destino = salida / f"{n:02d}_{p.nombre.lower()}.mid"
        p.guardar(destino)
        print(f"  {destino.name:16} {len(p._eventos) // 2:3d} notas")
    print(f"\n  python scripts/a_live.py {salida}")


if __name__ == "__main__":
    main()
