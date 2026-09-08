"""Mide como estan arreglados los temas que mas se tocan.

Por que existe: `make_sketch.py` escribe 44 notas por compas repartidas en cinco
capas que suenan las ocho compases enteras, y eso se escucha como una maquina.
La correccion obvia es "poner menos notas", pero cuanto menos es una opinion —
y ya erre dos veces poniendo mi criterio.

Esto lo reemplaza por una medicion. Toma los temas mas tocados de la propia
historia de Rekordbox, los separa en stems, los transcribe y cuenta: cuantas
notas por compas lleva cada capa, cada cuanto cambia el acorde, donde cae el
bajo respecto del bombo. El resultado son los numeros con los que hay que
escribir, sacados de lo que efectivamente funciona en la pista.

Ojo con la circularidad: esto NO es evidencia de que estos numeros sean buenos
en general. Es evidencia de que asi estan hechos los temas que este DJ elige
tocar, que para escribir un boceto propio es exactamente lo que se quiere.

Uso:
    python scripts/medir_arreglos.py --cuantos 8
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import re
import unicodedata
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import (BANDAS, MARGEN_S, SR, _afinar_bpm, _armonia,  # noqa: E402
                         _bajo, _bateria, _envolvente, _golpes, _grilla, separar)
from plomo import config  # noqa: E402
from plomo.matching import clave  # noqa: E402

DEPOSITO = config.MUSIC_LIBRARY_ROOT / "Biblioteca"
COMPASES = 8
SALIDA = RAIZ / "data" / "arreglos_medidos.json"


def _normal(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c for c in s.lower() if c.isalnum())


_SELLO = re.compile(r"\s*\[[^\]]*\]\s*$")


def _partir(stem: str) -> tuple[str, str]:
    """'Artista - Titulo (Mix) [Sello]' -> ('Artista', 'Titulo (Mix)').

    El sello se saca ANTES de armar la clave: `clave()` trata los corchetes igual
    que los parentesis, asi que un '[UV Noir]' entraria como si fuera el nombre
    de un remixer y ningun titulo cruzaria.
    """
    limpio = _SELLO.sub("", stem)
    artista, _, titulo = limpio.partition(" - ")
    return (artista, titulo) if titulo else ("", limpio)


def _buscar(artista: str, titulo: str, indice: dict[str, Path]) -> Path | None:
    """Cruza por la clave del proyecto, que conserva el remixer.

    Cruzar por ContentID no sirve: los ID de Rekordbox cambian con cada
    reimportacion y descartan la mayoria de la muestra. Pero cruzar por
    subcadena tampoco — se quedaba con la primera coincidencia y devolvia la
    version equivocada: "Cardamom (Original Mix)" traia el FAERO Remix,
    "Deflator (Original Mix)" el Montw Remix, "The Landing (Original Mix)" el
    Club Mix. Los numeros salian de un tema parecido pero distinto.

    `clave()` descarta los calificativos genericos de version y conserva el
    nombre propio del remixer, que es justo la diferencia que hacia falta.
    """
    buscada = clave(artista, titulo)
    exacta = indice.get(buscada)
    if exacta is not None:
        return exacta
    # Sin coincidencia exacta se cae a subcadena, pero avisando: es el modo que
    # devuelve versiones equivocadas y quien lea el resultado tiene que saberlo.
    nucleo = _normal(titulo.split("(")[0])
    primer = _normal(artista.split(",")[0])
    if len(nucleo) < 4:
        return None
    for ruta in indice.values():
        plano = _normal(ruta.stem)
        if nucleo in plano and primer in plano:
            print(f"    (por subcadena, puede ser otra version: {ruta.stem[:50]})")
            return ruta
    return None


def _mejor_momento(archivo: Path) -> float:
    """Segundo donde arrancar el fragmento: el pico de energia del medio.

    En progressive los primeros y los ultimos minutos son intro y outro, donde
    suena la mitad de los elementos. Medir ahi daria una densidad artificialmente
    baja y el boceto saldria vacio.
    """
    y, sr = librosa.load(archivo, sr=8000, mono=True)
    rms = librosa.feature.rms(y=y, hop_length=1024)[0]
    veces = librosa.times_like(rms, sr=sr, hop_length=1024)
    medio = (veces > veces[-1] * 0.25) & (veces < veces[-1] * 0.80)
    if not medio.any():
        return max(0.0, veces[-1] / 2)
    return float(veces[medio][int(np.argmax(rms[medio]))])


def _posiciones(pista, altura: int | None = None) -> list[int]:
    """Semicorchea del compas (0-15) de cada nota encendida."""
    from plomo.midi import TICKS_POR_NEGRA
    fuera = []
    for e in pista._eventos:
        if e.datos[0] & 0xF0 != 0x90 or e.datos[2] == 0:
            continue
        if altura is not None and e.datos[1] != altura:
            continue
        fuera.append(int(round(e.tick / (TICKS_POR_NEGRA / 4))) % 16)
    return fuera


def _medir(archivo: Path, artista: str, titulo: str) -> dict | None:
    desde = _mejor_momento(archivo)
    dur = COMPASES * 4 * 60.0 / 121.0 + 4.0
    try:
        rutas = separar(archivo, desde, dur)
    except SystemExit as e:
        print(f"    {e}")
        return None

    recorte = min(desde, MARGEN_S)
    stems = {n: librosa.load(p, sr=SR, offset=recorte, duration=dur)[0]
             for n, p in rutas.items()}

    crudo = float(np.atleast_1d(librosa.beat.beat_track(y=stems["drums"], sr=SR)[0])[0])
    while crudo < 100:
        crudo *= 2
    while crudo > 145:
        crudo /= 2
    bpm = _afinar_bpm(stems["drums"], SR, crudo)
    grilla = _grilla(stems["drums"], SR, bpm)
    semis = COMPASES * 16

    acordes, elegidos = _armonia(stems["other"], SR, grilla, semis, bpm)
    bajo = _bajo(stems["bass"], SR, grilla, semis, bpm)
    bateria = _bateria(stems["drums"], SR, grilla, semis, bpm)

    kicks = _golpes(_envolvente(stems["drums"], SR, *BANDAS["kick"][:2]), SR)
    enganche = float((np.abs(kicks[:, None] - grilla[None, :]).min(axis=1) < 0.020).mean())

    pos_bajo = _posiciones(bajo)
    en_pulso = sum(1 for p in pos_bajo if p % 4 == 0)
    en_contra = sum(1 for p in pos_bajo if p % 4 == 2)

    reales = [a for a in elegidos if a != "-"]
    cambios = sum(1 for a, b in zip(reales, reales[1:]) if a != b)

    n = {c: len(_posiciones(bateria, a)) for c, (_, _, a, _) in
         zip(BANDAS, BANDAS.values())}
    return {
        "artista": artista, "titulo": titulo, "bpm": round(bpm, 1),
        "desde_s": round(desde), "enganche_bombo": round(enganche, 2),
        "kick_x_compas": round(n["kick"] / COMPASES, 2),
        "clap_x_compas": round(n["clap"] / COMPASES, 2),
        "hat_x_compas": round(n["hat"] / COMPASES, 2),
        "bajo_x_compas": round(len(pos_bajo) / COMPASES, 2),
        "bajo_en_pulso": round(en_pulso / max(len(pos_bajo), 1), 2),
        "bajo_en_contratiempo": round(en_contra / max(len(pos_bajo), 1), 2),
        "notas_bajo_distintas": len({e.datos[1] for e in bajo._eventos
                                     if e.datos[0] & 0xF0 == 0x90}),
        "cambios_de_acorde": cambios,
        "acordes": " ".join(elegidos),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuantos", type=int, default=8)
    args = ap.parse_args()

    mas = json.loads((RAIZ / "data" / "mi_sonido.json").read_text(encoding="utf-8"))
    indice = {clave(*_partir(p.stem)): p for p in DEPOSITO.rglob("*.mp3")}
    print(f"  {len(indice)} archivos en el deposito")

    filas: list[dict] = []
    for t in mas["mas_sonados"]:
        if len(filas) >= args.cuantos:
            break
        archivo = _buscar(t["artist"], t["title"], indice)
        if archivo is None:
            print(f"  - sin archivo: {t['artist']} - {t['title']}")
            continue
        print(f"\n  [{len(filas) + 1}/{args.cuantos}] {archivo.stem[:60]}")
        fila = _medir(archivo, t["artist"], t["title"])
        if fila is None:
            continue
        # Dos filtros, no uno. El enganche solo dice que lo detectado cae en la
        # grilla, no que haya bombo: Minicube paso con 0.2 golpes por compas
        # enganchando el 70%, porque el 70% de casi nada sigue siendo casi nada.
        if fila["enganche_bombo"] < 0.70:
            print(f"    descartado: el bombo engancha {fila['enganche_bombo']:.0%}")
            continue
        if not 3.5 <= fila["kick_x_compas"] <= 4.5:
            print(f"    descartado: {fila['kick_x_compas']:.1f} bombos por compas, "
                  "no es un cuatro por cuatro detectado")
            continue
        filas.append(fila)
        print(f"    kick {fila['kick_x_compas']:.1f}  hat {fila['hat_x_compas']:.1f}  "
              f"bajo {fila['bajo_x_compas']:.1f}/compas  "
              f"({fila['bajo_en_contratiempo']:.0%} en contratiempo)  "
              f"acordes: {fila['cambios_de_acorde']} cambios")

    if not filas:
        sys.exit("  ningun tema medible")

    def med(k: str) -> float:
        return round(statistics.median(f[k] for f in filas), 2)

    # `clap_x_compas` queda guardado por tema pero NO entra en el resumen: dio
    # entre 5 y 14.6 por compas cuando un clap en house son 2. La banda de
    # 200-1400 Hz del stem de bateria agarra el cuerpo del bombo, los toms y la
    # percusion, asi que mide "energia en el medio" y no claps. Es una metrica
    # rota, no una metrica que haya que calibrar.
    #
    # La mediana del bajo se toma solo sobre los temas donde hay bajo: el
    # fragmento se elige por pico de energia y a veces cae en un tramo sin bajo
    # (Pacifist dio 0.6 por compas). Promediar eso con temas que si lo tienen
    # baja el numero por una razon que no es musical.
    con_bajo = [f for f in filas if f["bajo_x_compas"] >= 1.0]

    def med_bajo(k: str) -> float:
        return round(statistics.median(f[k] for f in con_bajo), 2) if con_bajo else 0.0

    resumen = {k: med(k) for k in
               ("kick_x_compas", "hat_x_compas", "cambios_de_acorde")}
    resumen.update({k: med_bajo(k) for k in
                    ("bajo_x_compas", "bajo_en_pulso", "bajo_en_contratiempo",
                     "notas_bajo_distintas")})
    resumen["n_con_bajo"] = len(con_bajo)
    SALIDA.write_text(json.dumps({"n": len(filas), "mediana": resumen,
                                  "temas": filas}, indent=2, ensure_ascii=False),
                      encoding="utf-8")

    print(f"\n  === mediana de {len(filas)} temas ===")
    for k, v in resumen.items():
        print(f"    {k:24} {v}")
    print(f"\n  {SALIDA}")


if __name__ == "__main__":
    main()
