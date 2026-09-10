"""Traduce un tema entero: que suena, cuando, como esta tocado y con que efectos.

Por que existe. El proyecto ya tenia tres medidores y ninguno contestaba la
pregunta completa. `estructura.py` dice donde empieza cada seccion pero no que
suena adentro. `instrumentos.py` dice como esta tocada cada pieza pero cuenta
ATAQUES, y eso deja ciego todo lo que no golpea: sobre el remix de Kebin Van
Reeken devolvio "bajo: 0.88 notas por compas", que en un tema de techno no es
una medicion sino el detector avisando que ahi no hay ataques — el bajo esta
sostenido. Y ninguno de los tres mide un solo EFECTO, que es la mitad de por que
un tema suena como suena.

Las tres cosas que agrega, y por que cada una:

**Cobertura ademas de ataques.** Una capa se describe con dos numeros, no con
uno: cuantas veces ataca y que fraccion del tiempo esta sonando. Un bajo de
techno ataca una vez cada dos compases y suena el 95% del tiempo; un bajo de
house ataca seis veces por compas y suena el 40%. Con un solo numero los dos son
"poco bajo", que es exactamente lo que estaba pasando.

**El sidechain, medido.** Es el efecto que mas define el genero y no se estaba
midiendo. Se mide promediando la envolvente de cada capa a lo largo de UN pulso,
alineada al bombo: si hay ducking, ese promedio tiene un pozo en el golpe. Da la
profundidad en dB y cuanto tarda en recuperar.

**Los otros efectos por su huella.** La reverb por la cola despues del ataque, el
delay por autocorrelacion de la envolvente contra las divisiones musicales, el
ancho por la relacion lado/medio en tres bandas, la saturacion por el factor de
cresta, y el movimiento de filtro por como se corre el centroide espectral a lo
largo de la seccion.

Un aviso que vale para todo el archivo: esto mide un FRAGMENTO, no el tema. Los
efectos cambian de seccion en seccion —el sidechain de un breakdown no es el del
drop— asi que el fragmento se elige por pico de energia y lo que sale describe
la parte mas llena. Con `--desde` se mira otra.

Uso:
    python scripts/traducir.py "<mp3>"
    python scripts/traducir.py "<mp3>" --desde 283
    python scripts/traducir.py "<mp3>" --forma      # ademas, el mapa de secciones
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import (HOP, MARGEN_S, SR, _afinar_bpm, _banda,  # noqa: E402
                         _envolvente, _golpes, _grilla)
from medir_arreglos import _mejor_momento  # noqa: E402
from separar import separar  # noqa: E402

COMPASES = 16          # el doble que `instrumentos.py`: el movimiento de filtro
                       # y el delay no se ven en ocho

# Cada pieza con su banda y su stem. Son anchas a proposito: no se busca aislar
# el instrumento sino saber que pasa en ese registro.
PIEZAS: dict[str, tuple[str, float, float]] = {
    "bombo":     ("drums", 30, 120),
    "clap":      ("drums", 200, 1400),
    "percusion": ("drums", 1400, 4000),
    "hat":       ("drums", 6000, 11000),
    "bajo":      ("bass", 35, 260),
    "medio":     ("other", 300, 1200),
    "melodia":   ("other", 1200, 5000),
    "aire":      ("other", 5000, 11000),
}
PERCUSIVAS = {"bombo", "clap", "percusion", "hat"}

# Divisiones donde puede vivir un eco, en negras.
DIVISIONES = {"1/16": 0.25, "1/8": 0.5, "3/16": 0.75, "1/4": 1.0,
              "3/8": 1.5, "1/2": 2.0}


# --------------------------------------------------------------------- capas
def _cobertura(y: np.ndarray, sr: int, lo: float, hi: float) -> float:
    """Fraccion del tiempo en que esa banda esta sonando de verdad.

    El umbral es relativo al propio material —la mediana de lo que suena— y no
    absoluto, porque un tema mezclado bajo y uno mezclado fuerte tienen la misma
    forma y compararlos contra un numero fijo diria que el primero esta vacio.
    """
    b = np.abs(_banda(y, sr, lo, hi))
    if not b.size or b.max() <= 0:
        return 0.0
    marco = max(1, sr // 100)
    rms = np.array([b[i:i + marco].mean() for i in range(0, len(b) - marco, marco)])
    if not rms.size:
        return 0.0
    return float((rms > np.quantile(rms, 0.92) * 0.10).mean())


def _patron(tiempos: np.ndarray, grilla: np.ndarray,
            compases: int) -> tuple[list[int], list[int], float]:
    pos = [int(np.argmin(np.abs(grilla - t))) for t in tiempos]
    pos = [k for k in pos if k < compases * 16]
    if not pos:
        return [], [], 0.0
    por_compas: dict[int, set[int]] = {}
    for k in pos:
        por_compas.setdefault(k // 16, set()).add(k % 16)
    filas = [v for v in por_compas.values() if v]
    cuenta = Counter(p for f in filas for p in f)
    anclas = sorted(p for p, n in cuenta.items() if n >= len(filas) * 0.8)
    var = sorted(p for p, n in cuenta.items() if n < len(filas) * 0.8)
    return anclas, var, len(pos) / compases


def _feel(tiempos: np.ndarray, grilla: np.ndarray, bpm: float) -> tuple[float, float]:
    if not len(tiempos):
        return 0.0, 0.0
    limite = (60.0 / bpm / 4) / 2
    d = [(t - grilla[np.argmin(np.abs(grilla - t))]) * 1000.0 for t in tiempos]
    d = [x for x in d if abs(x) < limite * 1000.0]
    return (float(np.median(d)), float(np.std(d))) if d else (0.0, 0.0)


# ------------------------------------------------------------------- efectos
def _sidechain(y: np.ndarray, sr: int, lo: float, hi: float,
               cero: float, bpm: float) -> tuple[float, float]:
    """Profundidad del ducking en dB y cuanto tarda en recuperar, en ms.

    Se promedia la envolvente a lo largo de UN pulso, alineada al bombo. Si la
    capa esta comprimida contra el bombo, ese promedio tiene un pozo justo en el
    golpe; si no lo esta, es plano. Promediar muchos pulsos es lo que separa el
    ducking de una nota que casualmente empezaba fuerte.
    """
    negra = 60.0 / bpm
    b = np.abs(_banda(y, sr, lo, hi))
    marco = max(1, sr // 200)
    rms = np.array([b[i:i + marco].mean() for i in range(0, len(b) - marco, marco)])
    if rms.size < 20 or rms.max() <= 0:
        return 0.0, 0.0
    x_pulso = int(round(negra * sr / marco))
    if x_pulso < 8:
        return 0.0, 0.0
    inicio = int(round(cero * sr / marco))
    n = (len(rms) - inicio) // x_pulso
    if n < 4:
        return 0.0, 0.0
    ciclo = np.mean([rms[inicio + i * x_pulso:inicio + (i + 1) * x_pulso]
                     for i in range(n)], axis=0)
    if ciclo.max() <= 0:
        return 0.0, 0.0
    # el pozo se busca en el primer tercio del pulso: un ducking tarda menos que
    # eso en recuperar, y mas alla ya es otra cosa que paso en el medio
    tercio = max(2, len(ciclo) // 3)
    piso = ciclo[:tercio].min()
    techo = ciclo.max()
    prof = 20 * np.log10(max(piso, 1e-9) / techo)
    if prof > -1.0:
        return 0.0, 0.0
    donde = int(np.argmin(ciclo[:tercio]))
    recupera = next((i for i in range(donde, len(ciclo))
                     if ciclo[i] >= techo * 0.9), len(ciclo) - 1)
    return float(prof), float((recupera - donde) * marco / sr * 1000.0)


def _cola(y: np.ndarray, sr: int, lo: float, hi: float) -> float:
    """Cuanto tarda en caer 20 dB despues de un ataque, en segundos.

    Es la huella de la reverb, pero no solo: un pad con release largo mide
    parecido. Lo que dice de verdad es cuanto DURA el sonido despues del golpe,
    que para decidir un arreglo es la pregunta util.
    """
    env = _envolvente(y, sr, lo, hi)
    golpes = _golpes(env, sr)
    if len(golpes) < 3:
        return 0.0
    x_seg = sr / HOP
    caidas = []
    for t in golpes[:24]:
        i = int(t * x_seg)
        tramo = env[i:i + int(x_seg * 2.0)]
        if tramo.size < 8 or tramo[0] <= 0:
            continue
        objetivo = tramo[0] * 0.1                 # -20 dB
        bajo = np.where(tramo < objetivo)[0]
        if bajo.size:
            caidas.append(bajo[0] / x_seg)
    return float(np.median(caidas)) if caidas else 0.0


def _delay(y: np.ndarray, sr: int, lo: float, hi: float,
           bpm: float) -> tuple[str, float]:
    """Busca un eco: autocorrelacion de la envolvente contra las divisiones."""
    env = _envolvente(y, sr, lo, hi)
    if env.size < 64:
        return "", 0.0
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    if ac[0] <= 0:
        return "", 0.0
    ac = ac / ac[0]
    negra = 60.0 / bpm
    mejor, valor = "", 0.0
    for nombre, div in DIVISIONES.items():
        i = int(round(div * negra * sr / HOP))
        if 2 <= i < len(ac) and ac[i] > valor:
            mejor, valor = nombre, float(ac[i])
    return (mejor, valor) if valor > 0.30 else ("", valor)


def _ancho(estereo: np.ndarray, sr: int) -> dict[str, float]:
    """Relacion lado/medio por banda. 0 = mono, 1 = muy abierto."""
    if estereo.ndim != 2 or estereo.shape[0] < 2:
        return {}
    medio = (estereo[0] + estereo[1]) / 2
    lado = (estereo[0] - estereo[1]) / 2
    fuera = {}
    for nombre, (lo, hi) in (("graves", (20, 200)), ("medios", (200, 3000)),
                             ("agudos", (3000, 11000))):
        m = np.sqrt((_banda(medio, sr, lo, hi) ** 2).mean())
        s = np.sqrt((_banda(lado, sr, lo, hi) ** 2).mean())
        fuera[nombre] = float(s / m) if m > 1e-9 else 0.0
    return fuera


def _cresta(y: np.ndarray) -> float:
    """Pico sobre RMS en dB. Bajo = comprimido o saturado; alto = con dinamica."""
    r = np.sqrt((y ** 2).mean())
    return float(20 * np.log10(np.abs(y).max() / r)) if r > 1e-9 else 0.0


def _filtro(y: np.ndarray, sr: int, compases: int, bpm: float) -> tuple[float, float]:
    """Centroide espectral al principio y al final de la seccion, en Hz.

    Si se mueve mucho hay un filtro barriendo; si no, el timbre esta quieto.
    """
    c = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=HOP)[0]
    if c.size < 8:
        return 0.0, 0.0
    n = max(2, c.size // 8)
    return float(np.median(c[:n])), float(np.median(c[-n:]))


# ------------------------------------------------------------------ el pase
def traducir(archivo: Path, desde: float | None = None) -> dict:
    desde = _mejor_momento(archivo) if desde is None else desde
    dur = COMPASES * 4 * 60.0 / 121.0 + 4.0
    rutas = separar(archivo, desde, dur)
    recorte = min(desde, MARGEN_S)
    mono = {n: librosa.load(p, sr=SR, offset=recorte, duration=dur)[0]
            for n, p in rutas.items()}
    est = {n: librosa.load(p, sr=SR, mono=False, offset=recorte, duration=dur)[0]
           for n, p in rutas.items()}

    crudo = float(np.atleast_1d(librosa.beat.beat_track(y=mono["drums"], sr=SR)[0])[0])
    while crudo < 100:
        crudo *= 2
    while crudo > 145:
        crudo /= 2
    bpm = _afinar_bpm(mono["drums"], SR, crudo)
    grilla = _grilla(mono["drums"], SR, bpm)
    cero = float(grilla[0]) if len(grilla) else 0.0
    # Los compases se cuentan sobre el audio que HAY, no sobre los que se
    # pidieron. Un render propio de ocho compases medido como si fueran
    # dieciseis daba "bombo 1.94 por compas" — la mitad de los 4 reales— y eso
    # se leia como un bombo enterrado cuando era un divisor equivocado.
    compases = max(1, min(COMPASES, int(len(mono["drums"]) / SR / (4 * 60.0 / bpm))))

    def _dbfs(y):
        return float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9))
    ref_drums = _dbfs(mono["drums"]) if "drums" in mono else 0.0
    niveles = {n: _dbfs(mono[n]) - ref_drums for n in ("bass", "other") if n in mono}
    fuera: dict = {"archivo": archivo.stem, "bpm": bpm, "desde": desde,
                   "compases": compases, "niveles": niveles,
                   "piezas": {}, "efectos": {}}
    for pieza, (stem, lo, hi) in PIEZAS.items():
        if stem not in mono:
            continue
        env = _envolvente(mono[stem], SR, lo, hi)
        tiempos = _golpes(env, SR)
        anclas, var, x_compas = _patron(tiempos, grilla, compases)
        desvio, disp = _feel(tiempos, grilla, bpm)
        picos = np.array([env[min(len(env) - 1,
                                  int(t * SR / HOP))] for t in tiempos])
        fuera["piezas"][pieza] = {
            "x_compas": x_compas, "cobertura": _cobertura(mono[stem], SR, lo, hi),
            "anclas": anclas, "variables": var,
            "desvio_ms": desvio, "dispersion_ms": disp,
            "dinamica": float(picos.std() / picos.max()) if picos.size > 2
                        and picos.max() > 0 else 0.0,
            "n": len(tiempos),
        }

    for stem in ("bass", "other", "drums"):
        if stem not in mono:
            continue
        lo, hi = (35, 260) if stem == "bass" else (300, 6000)
        prof, rec = _sidechain(mono[stem], SR, lo, hi, cero, bpm)
        div, fuerza = _delay(mono[stem], SR, lo, hi, bpm)
        c0, c1 = _filtro(mono[stem], SR, compases, bpm)
        fuera["efectos"][stem] = {
            "sidechain_db": prof, "recupera_ms": rec,
            "cola_s": _cola(mono[stem], SR, lo, hi),
            "delay": div, "delay_fuerza": fuerza,
            "cresta_db": _cresta(mono[stem]),
            "centroide_hz": (c0, c1),
            "ancho": _ancho(est[stem], SR),
        }
    return fuera


def _mostrar(d: dict) -> None:
    print(f"\n  {d['archivo'][:70]}")
    print(f"  {d['bpm']:.1f} BPM · fragmento desde {d['desde']:.0f}s\n")
    print(f"  {'capa':<11} {'x compas':>9} {'suena':>7} {'feel':>9} {'disp':>7}"
          f" {'dinam':>7}   patron")
    base = d["piezas"].get("bombo", {}).get("desvio_ms", 0.0)
    for pieza, v in d["piezas"].items():
        if not v["n"] and v["cobertura"] < 0.02:
            print(f"  {pieza:<11} {'—':>9} {'—':>7}   (no hay nada en esa banda)")
            continue
        dib = "".join("A" if k in v["anclas"] else "x" if k in v["variables"]
                      else "." for k in range(16))
        marca = " " if pieza in PERCUSIVAS else "?"
        # Un ataque cada dos compases con 90% de cobertura no es "casi nada":
        # es una capa sostenida, y decirlo evita leer un bajo de techno como
        # que no esta.
        forma = "sostenida" if v["cobertura"] > 0.75 and v["x_compas"] < 2 else ""
        print(f"  {pieza:<11} {v['x_compas']:9.2f} {v['cobertura']:6.0%}"
              f" {v['desvio_ms'] - base:+7.1f}ms{marca} {v['dispersion_ms']:6.1f}ms"
              f" {v['dinamica']:7.2f}   {dib} {forma}")
    print("\n  feel relativo al bombo. El '?' marca donde no es confiable: el")
    print("  detector marca donde la envolvente crece, y en un bajo o un pad eso")
    print("  tarda 10 a 30 ms, asi que mezcla el toque con el ataque del sonido.")

    print("\n  EFECTOS\n")
    NOM = {"bass": "bajo", "other": "melodico", "drums": "bateria"}
    for stem, e in d["efectos"].items():
        print(f"  {NOM[stem]}")
        if e["sidechain_db"] < -1.0:
            print(f"    sidechain    {e['sidechain_db']:.1f} dB en el golpe, "
                  f"recupera en {e['recupera_ms']:.0f} ms")
        else:
            print("    sidechain    no hay ducking medible")
        print(f"    cola         {e['cola_s']:.2f} s hasta -20 dB")
        if e["delay"]:
            print(f"    delay        eco a {e['delay']} "
                  f"(correlacion {e['delay_fuerza']:.2f})")
        else:
            print("    delay        sin eco claro")
        c0, c1 = e["centroide_hz"]
        cambio = "sube" if c1 > c0 * 1.25 else "baja" if c1 < c0 * 0.8 else "quieto"
        print(f"    filtro       {c0:.0f} -> {c1:.0f} Hz ({cambio})")
        print(f"    cresta       {e['cresta_db']:.1f} dB "
              f"({'comprimido' if e['cresta_db'] < 10 else 'con dinamica'})")
        a = e["ancho"]
        if a:
            print(f"    ancho        graves {a['graves']:.2f}  "
                  f"medios {a['medios']:.2f}  agudos {a['agudos']:.2f}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--desde", type=float)
    ap.add_argument("--forma", action="store_true",
                    help="ademas, el mapa de secciones con estructura.py")
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")
    _mostrar(traducir(args.archivo, args.desde))
    if args.forma:
        from estructura import _mostrar as mostrar_forma, medir
        mostrar_forma(medir(args.archivo))
    print()


if __name__ == "__main__":
    main()
