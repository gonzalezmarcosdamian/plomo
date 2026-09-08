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

# Solo triadas. Agregar septimas y novenas hace que el matching elija siempre el
# acorde con mas notas, porque cubre mas energia del croma: la comparacion deja
# de medir cual acorde suena y pasa a medir cual acorde es mas grande.
TRIADAS = {"maj": [0, 4, 7], "min": [0, 3, 7]}
NOMBRES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MENOR = [0, 2, 3, 5, 7, 8, 10]


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


def _armonia(other: np.ndarray, sr: int, grilla: np.ndarray, semis: int,
             bpm: float) -> tuple[Pista, list[str]]:
    """Un acorde por compas, por correlacion del croma contra triadas."""
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
        mejor, puntaje = (0, "min"), -1e9
        for raiz in range(12):
            for calidad, grados in TRIADAS.items():
                # energia dentro del acorde menos energia afuera: premia al que
                # explica el compas, no al que toca las notas mas frecuentes
                dentro = sum(perfil[(raiz + g) % 12] for g in grados)
                fuera = perfil.sum() - dentro
                v = dentro / len(grados) - fuera / (12 - len(grados))
                if v > puntaje:
                    mejor, puntaje = (raiz, calidad), v
        raiz, calidad = mejor
        p.acorde(compas=compas, pulso=0,
                 alturas=[48 + raiz + g for g in TRIADAS[calidad]],
                 duracion=3.9, velocidad=64)
        elegidos.append(NOMBRES[raiz] + ("m" if calidad == "min" else ""))
    return p, elegidos


def _bajo(bass: np.ndarray, sr: int, grilla: np.ndarray, semis: int,
          bpm: float) -> Pista:
    """Altura del bajo por semicorchea, con pyin sobre el stem de bajo."""
    f0, sonoro, _ = librosa.pyin(bass, sr=sr, fmin=35, fmax=260,
                                 frame_length=2048, hop_length=HOP)
    veces = librosa.times_like(f0, sr=sr, hop_length=HOP)

    p = Pista("Bajo", bpm, canal=1)
    anterior = None
    for i in range(semis):
        tramo = f0[(veces >= grilla[i]) & (veces < grilla[i + 1]) & sonoro]
        tramo = tramo[~np.isnan(tramo)]
        if len(tramo) < 3:
            anterior = None
            continue
        altura = int(np.clip(round(librosa.hz_to_midi(float(np.median(tramo)))), 24, 55))
        if altura == anterior:      # nota sostenida: se deja sonar, no se repica
            continue
        p.nota(i // 16, (i % 16) * 0.25, altura, 0.22, 92)
        anterior = altura
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

    # tonalidad implicita: la raiz mas repetida entre los acordes elegidos
    reales = [a for a in acordes if a != "-"]
    if reales:
        raiz = max(set(reales), key=reales.count)
        pc = NOMBRES.index(raiz.rstrip("m"))
        escala = {(pc + g) % 12 for g in MENOR}
        notas = [e.datos[1] % 12 for e in bajo._eventos if e.datos[0] & 0xF0 == 0x90]
        fuera = sum(1 for n in notas if n not in escala) / max(len(notas), 1)
        print(f"    bajo     {fuera * 100:3.0f}% de notas fuera de {raiz} menor "
              f"({len(notas)} notas)")
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
