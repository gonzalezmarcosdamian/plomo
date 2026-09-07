"""Convierte el historial de Rekordbox en un corpus de sets REALMENTE tocados.

Es el corpus que le faltaba al proyecto y estaba adentro de la casa.
`djmdHistory` / `djmdSongHistory` guardan que se puso, en que orden y a que hora,
con la key y el BPM que Rekordbox ya calculo. Nada de eso hay que matchear
contra nada: sale de la misma tabla que el resto de la biblioteca.

Por que importa mas que los `set_targets`: los sets armados los produjo
`select_set.py`, que impone las reglas como restriccion dura. Medir las reglas
contra ellos es circular — siempre dan 100% de cumplimiento. Lo tocado, en
cambio, es donde Gonzalo se desvio del plan arriba del escenario. Ahi si hay
informacion.

El filtro separa una sesion de un browsing: cargar decks en casa deja tracks con
segundos de diferencia; tocar deja huecos de cuatro a ocho minutos.

Uso:
    python scripts/ingest_history.py --dry
    python scripts/ingest_history.py
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DEST = RAIZ / "data" / "tocados"

# Umbrales que separan una sesion tocada de una carga de decks.
MIN_TRACKS = 8
# Una tanda partida no se juzga con la misma vara que una sesion entera: si la
# sesion califica, un tramo de 5 tracks seguidos con pulso real sigue siendo
# material tocado. Con el piso de 8 para todo se perdian tres sesiones reales.
MIN_TRACKS_TANDA = 5
MIN_DURACION_MIN = 45
MIN_DURACION_TANDA_MIN = 25
MIN_HUECO_MEDIANO_MIN = 2.0   # debajo de esto nadie escucho nada
MAX_HUECO_MEDIANO_MIN = 20.0  # arriba de esto no es un set, es una carpeta


def _cargar() -> dict[int, dict]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    sesiones: dict[int, dict] = {}
    for hid, nombre in con.execute(
            "SELECT ID, Name FROM djmdHistory WHERE rb_local_deleted=0"):
        filas = con.execute(
            """SELECT s.TrackNo, s.created_at, a.Name, c.Title, k.ScaleName,
                      c.BPM/100.0, c.Commnt, l.Name
               FROM djmdSongHistory s
               LEFT JOIN djmdContent c ON c.ID = s.ContentID
               LEFT JOIN djmdArtist  a ON a.ID = c.ArtistID
               LEFT JOIN djmdKey     k ON k.ID = c.KeyID
               LEFT JOIN djmdLabel   l ON l.ID = c.LabelID
               WHERE s.HistoryID = ? AND s.rb_local_deleted = 0
               ORDER BY s.TrackNo""", (hid,)).fetchall()
        if filas:
            sesiones[hid] = {"nombre": nombre, "filas": filas}
    con.close()
    return sesiones


def _energia(comentario: str | None) -> float | None:
    txt = comentario or ""
    if not txt.startswith("E:"):
        return None
    try:
        return float(txt[2:].split()[0].split("|")[0])
    except (ValueError, IndexError):
        return None


def _partir(filas: list) -> list[list]:
    """Corta la sesion donde hay un hueco largo.

    Rekordbox deja una sola entrada de historial por dia, asi que una "sesion"
    de 23 horas es en realidad dos tandas con una vida en el medio. El track que
    sigue a una pausa de tres horas no es una transicion: es un arranque.
    """
    tandas, actual, previa = [], [], None
    for f in filas:
        try:
            hora = datetime.fromisoformat(str(f[1])[:19])
        except ValueError:
            hora = previa
        if previa and hora and (hora - previa).total_seconds() / 60 > MAX_HUECO_MEDIANO_MIN:
            tandas.append(actual)
            actual = []
        actual.append(f)
        previa = hora or previa
    if actual:
        tandas.append(actual)
    return tandas


def _evaluar(filas: list, partida: bool = False) -> tuple[bool, str, dict]:
    """Decide si la tanda es un set tocado, y devuelve por que."""
    min_tracks = MIN_TRACKS_TANDA if partida else MIN_TRACKS
    min_dur = MIN_DURACION_TANDA_MIN if partida else MIN_DURACION_MIN
    horas = []
    for f in filas:
        try:
            horas.append(datetime.fromisoformat(str(f[1])[:19]))
        except ValueError:
            pass
    if len(filas) < min_tracks:
        return False, f"solo {len(filas)} tracks", {}
    if len(horas) < 2:
        return False, "sin timestamps", {}

    duracion = (max(horas) - min(horas)).total_seconds() / 60
    huecos = [(b - a).total_seconds() / 60
              for a, b in zip(sorted(horas), sorted(horas)[1:])]
    mediano = st.median(huecos) if huecos else 0.0
    stats = {"duracion_min": round(duracion, 1), "hueco_mediano_min": round(mediano, 1)}

    if duracion < min_dur:
        return False, f"dura {duracion:.0f} min", stats
    if mediano < MIN_HUECO_MEDIANO_MIN:
        return False, f"huecos de {mediano:.1f} min — es carga de decks", stats
    return True, "ok", stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--min-tracks", type=int, default=MIN_TRACKS)
    args = ap.parse_args()

    sesiones = _cargar()
    print(f"{len(sesiones)} sesiones en el historial de Rekordbox\n")

    aceptadas, rechazadas, total_tracks = 0, 0, 0
    for hid, s in sorted(sesiones.items()):
        tandas = _partir(s["filas"])
        # La sesion entera tiene que calificar antes de aflojar el piso de sus
        # tandas: si no, una carga de decks partida en pedacitos entraria.
        sesion_ok, _, _ = _evaluar(s["filas"])
        for t_i, filas in enumerate(tandas, 1):
            etiqueta = (f"{s['nombre']} [{t_i}/{len(tandas)}]" if len(tandas) > 1
                        else s["nombre"])
            ok, motivo, stats = _evaluar(filas, partida=len(tandas) > 1 and sesion_ok)
            if not ok:
                rechazadas += 1
                print(f"  [-] {etiqueta[:38]:<38} {len(filas):3d} tracks  {motivo}")
                continue

            tracks = []
            for i, (_, creado, artista, titulo, key, bpm, comentario, sello) in \
                    enumerate(filas, 1):
                tracks.append({
                    "pos": i,
                    "artist": artista or "?",
                    "title": titulo or "?",
                    "key": key or None,      # ya viene en Camelot desde Rekordbox
                    "bpm": bpm or None,
                    "energy": _energia(comentario),
                    "label": sello or "",
                    "hora": str(creado)[:19],
                    "fuente_datos": "rekordbox",
                })
            con_key = sum(1 for t in tracks if t["key"])
            doc = {
                "dj": "Gonzalo",
                "evento": etiqueta,
                "fecha": tracks[0]["hora"][:10],
                "fuente": "djmdHistory",
                "tipo": "tocado",
                "orden_confiable": True,
                "n": len(tracks),
                "cobertura_datos": round(con_key / len(tracks), 3),
                **stats,
                "tracks": tracks,
            }
            aceptadas += 1
            total_tracks += len(tracks)
            print(f"  [+] {etiqueta[:38]:<38} {len(tracks):3d} tracks  "
                  f"{stats['duracion_min']:5.0f} min  "
                  f"hueco {stats['hueco_mediano_min']:4.1f} min  "
                  f"key {con_key}/{len(tracks)}")
            if not args.dry:
                DEST.mkdir(parents=True, exist_ok=True)
                (DEST / f"{doc['fecha']}_{hid}_{t_i}.json").write_text(
                    json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  {aceptadas} tandas aceptadas ({total_tracks} tracks, "
          f"~{total_tracks - aceptadas} transiciones), {rechazadas} descartadas")
    if args.dry:
        print("  Dry-run: no se escribio nada. Sacar --dry para generar el corpus.")
    else:
        print(f"  -> {DEST}")
        print("  Ahora: scripts/backtest_rules.py lo mide como corpus TOCADO.")


if __name__ == "__main__":
    main()
