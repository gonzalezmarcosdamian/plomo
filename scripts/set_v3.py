"""Arma el set de la v3: house progresivo, con los plugins de afuera.

Por que existe aparte de `armar_set.py`: esa receta reproduce un set que ya
existe, y esto lo CONSTRUYE por primera vez con decisiones nuevas. Cada una
sale de medir "Alex O'Rion - Tunnel" con `traducir.py` y compararlo con el
render propio, y esta anotada al lado del numero que la justifica.

Lo que cambia respecto de la v2 (que era techno):

    dimension            v2 medido    Tunnel    como se consigue
    ancho bajo medios      0.02        0.52      TAL-Chorus-LX en bajo y bajo2
    ancho melodico         0.65        0.93      TAL-Chorus-LX en los pads
    filtro melodico       quieto    1491->2755   TAL-Filter-2 sincronizado
    cola melodico          0.12        0.17      TAL-Reverb-4
    cresta bateria         13.2        10.6      OTT en las cuatro de bateria
    sidechain bajo        -10.9        -7.0      Auto Pan mas suave
    delay                   1/2         1/4      el eco de la referencia

Uso:
    python scripts/set_v3.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.live import Live  # noqa: E402

# (pista, nombre, candidatos de instrumento, rama, volumen, filtro en Hz o None)
#
# Los sintetizadores de afuera van donde el preset de fabrica era el problema:
# la atmosfera atacaba 4.25 veces por compas SIN pump, que es el LFO del Warm
# Analog Pad, y eso es parte de lo que se escucha como ringtone.
PISTAS = [
    (4,  "Atmosfera",  ["TAL-NoiseMaker", "Warm Analog Pad", "Drift"], "plugins",     0.66, 1600.0),
    (5,  "Acordes",    ["Surge XT", "Sandman Pad", "Drift"],           "plugins",     0.74, 2400.0),
    (6,  "Bajo",       ["TAL-NoiseMaker", "Deep Bass", "Drift"],       "plugins",     0.88, 1100.0),
    (7,  "Bateria",    ["AG Techno Kit", "909 Core Kit"],              "drums",       0.90, None),
    (8,  "Gancho",     ["Surge XT", "Deep Pluck", "Drift"],            "plugins",     0.70, 3200.0),
    (9,  "Bajo medio", ["Noise Bass", "Analog Bass", "Drift"],         "instruments", 0.62, 2600.0),
    (10, "Textura",    ["Broadcast Noise", "ASMR Cave Texture"],       "instruments", 0.44, 4200.0),
    (11, "Anchos",     ["Snappy Pluck", "Deep Pluck", "Drift"],        "instruments", 0.46, 3000.0),
    (12, "Sub",        ["Deep Bass", "Drift"],                         "instruments", 0.78, 180.0),
    (13, "Repiques",   ["909 Core Kit", "Drum Rack"],                  "drums",       0.60, None),
    (14, "Splash",     ["Cymbal 808 Full", "Cymbal 808 Hard"],         "drums",       0.50, 9000.0),
    (15, "Reversa",    ["Cymbal Crash Reverse Gnirob", "FX Reverse"],  "drums",       0.42, None),
    (16, "Metales",    ["AG Techno Kit", "909 Core Kit"],              "drums",       0.70, None),
    (17, "Riser",      ["Riser White Noise", "Riser Synth"],           "drums",       0.34, 6500.0),
    (18, "Hats",       ["AG Techno Kit", "909 Core Kit"],              "drums",       0.88, None),
    (19, "Abiertos",   ["Sandman Pad", "Warm Analog Pad", "Drift"],    "instruments", 0.72, 2200.0),
    (20, "Subkick",    ["Super Sub Drone Bass", "Deep Bass"],          "instruments", 0.58, 90.0),
]

BATERIA = (7, 13, 16, 18)
BAJO = (6, 9, 12, 20)
MELODICO = (4, 5, 8, 11, 19)


def _esperar(l: Live, t: int, nombre: str, seg: int = 12) -> bool:
    for _ in range(seg):
        time.sleep(1.0)
        if any(nombre.split()[0].lower() in d.lower() for d in l.dispositivos(t)):
            return True
    return False


def _efecto(l: Live, t: int, nombre: str, rama: str = "audio_effects") -> int | None:
    """Carga un efecto y devuelve su indice. None si no aparecio.

    Se espera y se VERIFICA en vez de confiar en la respuesta del browser:
    `load_item` contesta ok y mete el efecto ADENTRO del rack si el rack tiene
    algo seleccionado, y entonces no esta en la cadena ni suena.
    """
    l.cargar_instrumento(t, [nombre], rama)
    if not _esperar(l, t, nombre):
        return None
    ds = l.dispositivos(t)
    return max(i for i, d in enumerate(ds) if nombre.split()[0].lower() in d.lower())


def _par(l: Live, t: int, d: int, clave: str, frac: float) -> str:
    nombres = l.parametros(t, d)
    i = next((k for k, n in enumerate(nombres) if n.lower() == clave.lower()), None)
    if i is None:
        i = next((k for k, n in enumerate(nombres) if clave.lower() in n.lower()), None)
    if i is None:
        return f"{clave}: no existe"
    lo, hi = l.rango_parametro(t, d, i)
    l.set_parametro(t, d, i, lo + (hi - lo) * frac)
    time.sleep(0.06)
    return f"{nombres[i]}={l.valor_mostrado(t, d, i)}"


def main() -> None:
    with Live(timeout=60.0) as l:
        l.enviar("/live/song/stop_playing")
        time.sleep(0.4)
        l.tempo(123.0)

        for t, nombre, cand, rama, vol, hz in PISTAS:
            while l.n_pistas() <= t:
                l.enviar("/live/song/create_midi_track", -1)
                time.sleep(1.3)
            l.enviar("/live/track/set/arm", t, 0)
            l.enviar("/live/track/set/name", t, nombre)
            time.sleep(0.3)
            cargado = None
            for r in (rama, "instruments", "drums", "plugins", "sounds"):
                cargado = l.cambiar_instrumento(t, cand, r)
                time.sleep(0.9)
                if cargado:
                    break
            if hz is not None:
                d = _efecto(l, t, "Auto Filter")
                if d is not None:
                    l.ajustar_a_hz(t, d, 1, hz)
            l.volumen(t, vol)
            print(f"  {t:>2} {nombre:<11} {str(cargado)[:34]:<34} vol {vol:.2f}", flush=True)

        # --- el ancho. El bajo propio medía 0.02 contra 0.52 de la referencia,
        # y lo melodico 0.65 contra 0.93. Un chorus de Juno es exactamente lo
        # que ensancha sin descorrelacionar los graves.
        for t in (9,) + MELODICO:
            d = _efecto(l, t, "TAL-Chorus-LX", "plugins")
            print(f"  ancho {t}: {'TAL-Chorus-LX' if d is not None else 'NO cargo'}")

        # --- el movimiento de filtro. En la referencia el centroide melodico
        # sube de 1491 a 2755 Hz a lo largo de la seccion; el propio esta
        # QUIETO, que es la firma de un boceto. El puente OSC no llega a los
        # envelopes de los clips, asi que el movimiento lo pone un filtro que
        # se modula solo, sincronizado al tempo.
        for t in (5, 8):
            d = _efecto(l, t, "TAL-Filter-2", "plugins")
            print(f"  filtro {t}: {'TAL-Filter-2' if d is not None else 'NO cargo'}")

        # --- la cola. 0.12 s propio contra 0.17 de la referencia.
        for t in MELODICO:
            d = _efecto(l, t, "TAL Reverb 4", "plugins")
            if d is not None:
                _par(l, t, d, "Dry/Wet", 0.22)
        print("  reverb en lo melodico: TAL Reverb 4 al 22%")

        # --- la cresta. 13.2 dB propio contra 10.6 de la referencia. OTT es
        # compresion multibanda hacia arriba: es lo que hace que una bateria
        # suene producida y no grabada.
        for t in BATERIA:
            d = _efecto(l, t, "OTT", "plugins")
            if d is not None:
                _par(l, t, d, "Depth", 0.35)
        print("  OTT en las cuatro de bateria al 35%")

        # --- el pump. -7.0 dB en la referencia contra -10.9 propio: en
        # progresivo el sidechain respira, no bombea. Sine y no Saw Up, que
        # tiene un salto instantaneo cada negra y el detector lo lee como un
        # golpe.
        for t in BAJO + MELODICO:
            d = _efecto(l, t, "Auto Pan")
            if d is None:
                continue
            for k, v in (("Mode", 1.0), ("Waveform", 0.0), ("Time Mode", 1.0),
                         ("16th", 4.0), ("Phase", 0.0)):
                nombres = l.parametros(t, d)
                i = next((x for x, n in enumerate(nombres) if n == k), None)
                if i is not None:
                    l.set_parametro(t, d, i, v)
                    time.sleep(0.05)
            _par(l, t, d, "Amount", 0.62 if t in BAJO else 0.55)
        print("  pump suave (Sine, 62% en el bajo y 55% en lo melodico)")

        print(f"\n  {l.n_pistas()} pistas · ahora: python scripts/montar.py v3")


if __name__ == "__main__":
    main()
