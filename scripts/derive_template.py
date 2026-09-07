"""Deriva una plantilla de arreglo a partir de un corpus de tracks reales.

`reverse_engineer.py` mide un track. Esto mide muchos del mismo autor o registro
y devuelve la mediana: cuantos compases dura la intro, en que porcentaje del
track cae el breakdown, cuanto dura el drop, que LUFS y que balance espectral
tiene la familia.

Una plantilla derivada de 30 tracks del tipo vale mas que cualquier receta
generica de "como se hace progressive house", porque sale del material que se
esta persiguiendo.

Uso:
    python scripts/derive_template.py --artista "Ezequiel Arias"
    python scripts/derive_template.py --lista rutas.txt --nombre "organico"
    python scripts/derive_template.py --artista Vuarambon --json data/plantillas/vuarambon.json
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402
from reverse_engineer import analizar  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def rutas_por_artista(patron: str) -> list[tuple[str, Path]]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    rows = con.execute(
        """SELECT a.Name, c.Title, c.FolderPath, k.ScaleName, c.BPM/100.0
           FROM djmdContent c
           LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
           LEFT JOIN djmdKey k ON k.ID = c.KeyID
           WHERE c.rb_local_deleted = 0 AND c.FolderPath IS NOT NULL
             AND (a.Name LIKE ? OR c.Title LIKE ?)""",
        (f"%{patron}%", f"%{patron}%")).fetchall()
    con.close()
    return [(f"{r[0]} - {r[1]}", Path(r[2])) for r in rows if Path(r[2]).exists()]


def _med(vals: list[float]) -> float:
    return round(st.median(vals), 2) if vals else 0.0


def resumir(recetas: list) -> dict:
    """Mediana de todo lo medible, y la forma tipica del arreglo."""
    out: dict = {
        "n_tracks": len(recetas),
        "bpm": _med([r.bpm for r in recetas]),
        "duracion_min": _med([r.duracion_seg / 60 for r in recetas]),
        "compases": _med([float(r.compases) for r in recetas]),
        "lufs": _med([r.lufs for r in recetas]),
        "rango_dinamico_db": _med([r.rango_dinamico_db for r in recetas]),
        "balance": {k: _med([r.balance[k] for r in recetas]) for k in recetas[0].balance},
        "ancho": {k: _med([r.ancho[k] for r in recetas]) for k in recetas[0].ancho},
        "confiables": sum(1 for r in recetas if r.confiable),
    }

    # forma del arreglo: largo de cada tipo de seccion y donde arranca
    largos: dict[str, list[float]] = {}
    inicio_pct: dict[str, list[float]] = {}
    cuenta: Counter = Counter()
    for r in recetas:
        for s in r.secciones:
            largos.setdefault(s.tipo, []).append(float(s.compases))
            inicio_pct.setdefault(s.tipo, []).append((s.compas_inicio - 1) / max(r.compases, 1))
        cuenta.update({s.tipo for s in r.secciones})

    out["secciones"] = {
        tipo: {
            "aparece_en": f"{cuenta[tipo]}/{len(recetas)}",
            "compases_mediana": _med(largos[tipo]),
            "compases_rango": [round(min(largos[tipo])), round(max(largos[tipo]))],
            "arranca_en_pct": _med([p * 100 for p in inicio_pct[tipo]]),
        }
        for tipo in sorted(largos, key=lambda t: _med(inicio_pct[t]))
    }
    out["linea_tiempo"] = _linea_tiempo(recetas)
    # Se guarda lo medido de cada track (sin la curva, que es larga) para que
    # --recalcular pueda rehacer las cuentas sin volver a analizar el audio:
    # medir 32 tracks son ocho minutos, rehacer la estadistica es instantaneo.
    out["tracks"] = [
        {"archivo": r.archivo, "bpm": r.bpm, "compases": r.compases,
         "duracion_seg": r.duracion_seg, "lufs": r.lufs,
         "rango_dinamico_db": r.rango_dinamico_db, "balance": r.balance,
         "ancho": r.ancho, "confiable": r.confiable,
         "secciones": [[s.tipo, s.compas_inicio, s.compases] for s in r.secciones]}
        for r in recetas
    ]
    return out


def desde_json(ruta: Path) -> list:
    """Reconstruye lo medido desde una plantilla guardada, sin tocar el audio."""
    d = json.loads(ruta.read_text(encoding="utf-8"))
    if not d.get("tracks"):
        sys.exit(f"{ruta} no guarda el detalle por track — hay que volver a medir")
    return [
        SimpleNamespace(
            **{k: v for k, v in t.items() if k != "secciones"},
            secciones=[SimpleNamespace(tipo=x[0], compas_inicio=x[1], compases=x[2])
                       for x in t["secciones"]],
        )
        for t in d["tracks"]
    ]


def _linea_tiempo(recetas: list, slots: int = 100) -> list[dict]:
    """Forma tipica del arreglo, por votacion posicion a posicion.

    Las medianas de "donde arranca" y "cuanto dura" cada seccion no encajan
    entre si: son distribuciones independientes y dejan huecos. Aca cada track
    se normaliza a 100 posiciones, cada posicion vota que tipo de seccion es, y
    gana la mayoria. El resultado si es una linea de tiempo continua.
    """
    votos: list[Counter] = [Counter() for _ in range(slots)]
    for r in recetas:
        total = max(r.compases, 1)
        for s in r.secciones:
            desde = int((s.compas_inicio - 1) / total * slots)
            hasta = min(int((s.compas_inicio - 1 + s.compases) / total * slots), slots)
            for k in range(desde, max(hasta, desde + 1)):
                if k < slots:
                    votos[k][s.tipo] += 1

    ganadores = [(v.most_common(1)[0] if v else ("groove", 0)) for v in votos]
    tramos: list[dict] = []
    for k, (tipo, n) in enumerate(ganadores):
        if tramos and tramos[-1]["tipo"] == tipo:
            tramos[-1]["hasta_pct"] = k + 1
            tramos[-1]["_acuerdo"].append(n)
        else:
            tramos.append({"tipo": tipo, "desde_pct": k, "hasta_pct": k + 1,
                           "_acuerdo": [n]})
    for t in tramos:
        t["acuerdo_pct"] = round(st.mean(t.pop("_acuerdo")) / len(recetas) * 100)
    return tramos


def imprimir(nombre: str, r: dict) -> None:
    print(f"\n{'=' * 74}")
    print(f"PLANTILLA  {nombre}   (derivada de {r['n_tracks']} tracks medidos)")
    print(f"{'=' * 74}")
    print(f"\n  {r['bpm']} BPM   {r['duracion_min']} min   {r['compases']:.0f} compases")
    print(f"  {r['lufs']} LUFS   rango dinamico {r['rango_dinamico_db']} dB")
    print("  balance   " + "  ".join(f"{k} {v:>4.1f}%" for k, v in r["balance"].items()))
    print("  ancho     " + "  ".join(f"{k} {v:>5.2f}" for k, v in r["ancho"].items()))
    if r["confiables"] < r["n_tracks"]:
        print(f"  ({r['n_tracks'] - r['confiables']} tracks con segmentacion poco "
              "confiable, igual entran en el promedio)")

    total = int(r["compases"])
    if r.get("linea_tiempo"):
        print(f"\n  LINEA DE TIEMPO   votacion posicion a posicion sobre {total} compases")
        print(f"  {'seccion':<11} {'compases':>12} {'largo':>7} {'acuerdo':>9}")
        for t in r["linea_tiempo"]:
            desde = int(t["desde_pct"] / 100 * total) + 1
            hasta = int(t["hasta_pct"] / 100 * total)
            tramo = f"{desde}-{hasta}"
            print(f"  {t['tipo']:<11} {tramo:>12} {hasta - desde + 1:>7} "
                  f"{t['acuerdo_pct']:>8}%")

    print(f"\n  SECCIONES POR SEPARADO   medianas independientes: no encajan entre si")
    print(f"  {'seccion':<11} {'aparece':>9} {'compases':>10} {'rango':>12} {'arranca':>9}")
    for tipo, s in r["secciones"].items():
        rango = f"{s['compases_rango'][0]}-{s['compases_rango'][1]}"
        print(f"  {tipo:<11} {s['aparece_en']:>9} {s['compases_mediana']:>10.0f} "
              f"{rango:>12} {s['arranca_en_pct']:>8.0f}%")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artista", help="patron a buscar en artista o titulo")
    ap.add_argument("--lista", type=Path, help="archivo con una ruta por linea")
    ap.add_argument("--nombre", default="", help="nombre de la plantilla")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--recalcular", type=Path,
                    help="rehace las cuentas desde una plantilla ya medida")
    args = ap.parse_args()

    if args.recalcular:
        recetas = desde_json(args.recalcular)
        nombre = args.nombre or json.loads(
            args.recalcular.read_text(encoding="utf-8")).get("nombre", args.recalcular.stem)
        print(f"recalculando desde {args.recalcular.name} ({len(recetas)} tracks medidos)")
        resumen = resumir(recetas)
        imprimir(nombre, resumen)
        destino = args.json or args.recalcular
        destino.write_text(json.dumps({"nombre": nombre, **resumen},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  plantilla -> {destino}")
        return

    if args.artista:
        items = rutas_por_artista(args.artista)[:args.max]
        nombre = args.nombre or args.artista
    elif args.lista:
        items = [(p.stem, p) for p in
                 (Path(l.strip()) for l in args.lista.read_text(encoding="utf-8").splitlines())
                 if p.name and p.exists()][:args.max]
        nombre = args.nombre or args.lista.stem
    else:
        sys.exit("hace falta --artista o --lista")

    if not items:
        sys.exit("no se encontro ningun archivo")

    print(f"midiendo {len(items)} tracks...\n")
    recetas = []
    for i, (etiqueta, p) in enumerate(items, 1):
        try:
            r = analizar(p)
            recetas.append(r)
            marca = "" if r.confiable else "  (segmentacion dudosa)"
            print(f"  {i:2d}/{len(items)}  {r.bpm:5.1f} BPM  {r.compases:3d}c  "
                  f"{r.lufs:6.1f} LUFS  {etiqueta[:48]}{marca}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  {i:2d}/{len(items)}  ERROR  {etiqueta[:48]}: {e}", flush=True)

    if not recetas:
        sys.exit("no se pudo medir ningun track")

    resumen = resumir(recetas)
    imprimir(nombre, resumen)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"nombre": nombre, **resumen}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  plantilla -> {args.json}")


if __name__ == "__main__":
    main()
