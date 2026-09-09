"""Mide cuanto tiempo hay algo sonando, en los temas de referencia y en el propio.

Por que existe: "suena cortado" es una queja precisa que no se resuelve
ajustando duraciones a ojo. La pregunta abajo es una sola y se puede contar:
**que fraccion del tiempo hay sonido sonando en cada capa**.

En los temas de referencia se mide sobre los stems de Demucs: se calcula la
envolvente y se cuenta que fraccion de los cuadros esta por encima de un piso
relativo al propio maximo del tramo. En el MIDI propio se mide distinto y a
proposito: se cuenta que fraccion de la grilla esta cubierta por alguna nota
sonando. Son dos formas de contar lo mismo — cuanto silencio hay.

No son directamente comparables al decimal: un stem arrastra colas de reverb que
el MIDI no tiene, asi que el stem siempre va a dar mas alto. Lo que importa es
el orden de magnitud y sobre todo la DISTANCIA entre capas. Si el pad de la
referencia cubre el 90% y el propio el 25%, no hay ajuste fino que valga: hay un
error de concepto.

Uso:
    python scripts/continuidad.py --midi postproduction/bocetos/boceto_medido
    python scripts/continuidad.py --stems --cuantos 6
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.midi import TICKS_POR_NEGRA, leer  # noqa: E402

STEMS = RAIZ / "postproduction" / "stems" / "htdemucs"
SR = 22050
# Piso relativo al maximo del tramo. -32 dB deja afuera el ruido de fondo de la
# separacion pero conserva las colas, que es lo que hace a un tema continuo.
PISO_DB = -32.0


def continuidad_audio(ruta: Path, segundos: float = 20.0) -> float | None:
    y, _ = librosa.load(ruta, sr=SR, offset=5.0, duration=segundos)
    if np.abs(y).max() < 1e-4:
        return None
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    db = librosa.amplitude_to_db(rms, ref=np.max(rms))
    return float((db > PISO_DB).mean())


def continuidad_midi(archivo: Path, resolucion: int = 16) -> tuple[float, float, int]:
    """Fraccion de la grilla cubierta, duracion mediana en pulsos, y notas."""
    _, _, notas = leer(archivo)
    if not notas:
        return 0.0, 0.0, 0
    fin = max(n[0] + n[1] for n in notas)
    pasos = int(np.ceil(fin * resolucion))
    ocupado = np.zeros(pasos, dtype=bool)
    for inicio, dur, _, _ in notas:
        a = int(inicio * resolucion)
        b = min(pasos, max(a + 1, int(np.ceil((inicio + dur) * resolucion))))
        ocupado[a:b] = True
    return float(ocupado.mean()), statistics.median(n[1] for n in notas), len(notas)


def solapes_y_huecos(archivo: Path) -> tuple[int, int]:
    """Cuantas veces una altura se re-ataca sonando, y cuantos huecos deja.

    Existe porque la herramienta TENIA el dato y no avisaba. Reportaba 6% de
    cobertura y 0.90 pulsos de duracion mediana en una capa sostenida desde
    hacia rato, y la unica alarma miraba si la duracion bajaba de 0.25 — 0.90
    pasaba el filtro.

    Lo que fallaba era invisible para esa alarma: escribir la misma altura
    solapada NO la sostiene. En MIDI el stream queda `on, on, off, off` y el
    primer note-off apaga la nota; el resto quedan huerfanos. Una capa que se
    creia sostenida sonaba el 41% del tiempo.
    """
    _, _, notas = leer(archivo)
    por_altura: dict[int, list[tuple[float, float]]] = {}
    for inicio, dur, altura, _ in notas:
        por_altura.setdefault(altura, []).append((inicio, inicio + dur))
    solapes = 0
    for tramos in por_altura.values():
        tramos.sort()
        solapes += sum(1 for a, b in zip(tramos, tramos[1:]) if b[0] < a[1] - 1e-6)
    if not notas:
        return solapes, 0
    tramos = sorted((n[0], n[0] + n[1]) for n in notas)
    huecos, fin = 0, tramos[0][1]
    for a, b in tramos[1:]:
        if a > fin + 1e-6:
            huecos += 1
        fin = max(fin, b)
    return solapes, huecos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--midi", type=Path, help="carpeta con los .mid propios")
    ap.add_argument("--stems", action="store_true", help="medir los temas de referencia")
    ap.add_argument("--cuantos", type=int, default=8)
    args = ap.parse_args()

    if args.stems:
        print(f"  REFERENCIA — fraccion del tiempo con sonido (piso {PISO_DB:.0f} dB)\n")
        print(f"  {'tema':<34} {'armonia':>8} {'bajo':>7} {'bateria':>8}")
        acum: dict[str, list[float]] = {"other": [], "bass": [], "drums": []}
        for d in sorted(STEMS.iterdir())[:args.cuantos]:
            fila = []
            for stem in ("other", "bass", "drums"):
                f = d / f"{stem}.wav"
                v = continuidad_audio(f) if f.exists() else None
                fila.append(v)
                if v is not None:
                    acum[stem].append(v)
            if all(v is None for v in fila):
                continue
            texto = "  ".join(f"{v:6.0%}" if v is not None else "    --" for v in fila)
            print(f"  {d.name[:34]:<34}  {texto}")
        print()
        for stem, etiqueta in (("other", "armonia"), ("bass", "bajo"), ("drums", "bateria")):
            if acum[stem]:
                print(f"  mediana {etiqueta:9} {statistics.median(acum[stem]):5.0%}")

    if args.midi:
        print(f"\n  PROPIO — fraccion de la grilla cubierta por alguna nota\n")
        print(f"  {'capa':<12} {'cubierto':>9} {'dur mediana':>12} {'notas':>7}")
        # Una capa de percusion se mide distinto: en un Drum Rack el sample se
        # dispara entero y el largo de la nota no cambia lo que se escucha. Un
        # 16% de cobertura ahi no significa nada, y marcarlo como problema seria
        # hacer sonar una alarma que despues hay que aprender a ignorar.
        PERCUSIVAS = {"bateria", "percusion", "repiques", "subida"}
        for f in sorted(args.midi.glob("*.mid")):
            capa = f.stem.split("_", 1)[-1]
            cobertura, dur, n = continuidad_midi(f)
            # La alarma mira la DURACION, no la cobertura. Sobre el tema entero
            # la cobertura mide el arreglo —el gancho suena en 6 de 11 secciones
            # y da 13% sin estar cortado— asi que marcarla avisaba mal. Lo que
            # se escucha como staccato es la nota corta, y eso no depende de en
            # cuantas secciones toque la capa.
            solapes, huecos = solapes_y_huecos(f)
            if capa in PERCUSIVAS:
                aviso = "   (percusiva: el largo no cambia nada)"
            elif solapes:
                aviso = f"   <- {solapes} RE-ATAQUES sobre nota sonando"
            elif dur < 0.25:
                aviso = "   <- staccato"
            elif cobertura > 0.9 and huecos:
                aviso = f"   <- {huecos} huecos"
            else:
                aviso = ""
            print(f"  {capa:<12} {cobertura:8.0%} {dur:11.2f}p {n:7d}{aviso}")
        print("\n  (una nota de 0.25 pulsos es una semicorchea: por debajo de eso"
              "\n   todo suena a staccato por mas que las notas esten bien puestas)")


if __name__ == "__main__":
    main()
