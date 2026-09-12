"""Reordena un set YA ARMADO sin cambiarle un solo track.

Distinto de `select_set.py`, que ELIGE que entra. Aca la seleccion esta decidida
—son sets que ya se tocaron o que el DJ curo a mano— y lo unico que se busca es
el mejor orden posible para ese material exacto.

Para que sirve: al sacarle el BPM al score de energia, los 1883 tracks se
movieron de lugar y los sets armados con la formula vieja quedaron con el arco
roto. Rearmarlos desde cero perderia la curaduria; reordenarlos la conserva.

La busqueda NO es la de select_set. Aquella filtra por restricciones duras, y
con la lista de tracks ya fija casi nunca existe una permutacion que las cumpla
todas: devolvia "sin solucion" para sets que igual se podian mejorar mucho. Aca
todo candidato pasa y cada violacion cuesta caro, asi que siempre sale un orden
y sale el mejor posible.

Se reporta el salto de Camelot mas grande que quedo. Un set que necesita
distancia 4 esta diciendo que la SELECCION no es coherente, no que el orden este
mal: eso es informacion, no un error a esconder.

Uso:
    python scripts/reordenar_set.py 39 --dry
    python scripts/reordenar_set.py --todos --min-flojas 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import select_set as S  # noqa: E402
from plomo.camelot import distance as cam_dist  # noqa: E402
from plomo.matching import clave  # noqa: E402

TARGETS = RAIZ / "data" / "set_targets"


def flojas(seq: list[dict]) -> int:
    n = 0
    for a, b in zip(seq, seq[1:]):
        if cam_dist(a["key"], b["key"]) > S.MAX_CAM:
            n += 1
        elif abs(a["bpm"] - b["bpm"]) > 2.0 + S.EPS:
            n += 1
        elif abs(a["energy"] - b["energy"]) > S.MAX_E_STEP + S.EPS:
            n += 1
    return n


def reordenar(tracks: list[dict], beam: int = 1500) -> tuple[list[dict], int]:
    """El mejor orden para ESTOS tracks. Devuelve (secuencia, camelot_maximo usado).

    NO reusa el solver de seleccion. Aquel FILTRA por restricciones duras, y con
    la lista de tracks ya fija casi nunca existe una permutacion que las cumpla
    todas: devolvia "sin solucion" para sets que igual se pueden mejorar mucho.
    Aca todo pasa y cada violacion cuesta caro, asi que siempre sale un orden y
    sale el mejor de los posibles.
    """
    n = len(tracks)
    es = sorted(t["energy"] for t in tracks)
    lo, hi = es[0], es[-1]
    for t in tracks:
        t["_cam"] = S.camelot(t["key"])
        t["_names"] = S.names(t["artist"], t["title"])

    beams = [(0.0, [], set())]
    for i in range(n):
        tgt = S.arc_target(i, n, lo, hi)
        nxt = []
        for costo, seq, usados in beams:
            prev = seq[-1] if seq else None
            for idx, t in enumerate(tracks):
                if idx in usados:
                    continue
                c = costo + abs(t["energy"] - tgt) * S.PESO_ARCO
                if prev:
                    d = cam_dist(prev["key"], t["key"])
                    # las violaciones pesan un orden de magnitud mas que las
                    # preferencias: primero que la mezcla sea posible
                    c += max(0, d - S.MAX_CAM) * 10.0 + d * S.PESO_CAM
                    c += max(0.0, abs(t["bpm"] - prev["bpm"]) - 2.0) * 5.0
                    c += max(0.0, abs(t["energy"] - prev["energy"]) - S.MAX_E_STEP) * 8.0
                    paso = S._paso_firmado(prev["_cam"], t["_cam"])
                    if paso == 0:
                        c += S.PESO_QUIETO
                    if prev["_names"] & t["_names"]:
                        c += 6.0
                nxt.append((c, seq + [t], usados | {idx}))
        nxt.sort(key=lambda x: x[0])
        beams = nxt[:beam]
    seq = beams[0][1]
    peor = max((cam_dist(a["key"], b["key"]) for a, b in zip(seq, seq[1:])), default=1)
    return seq, peor


def cargar(num: int, pool_idx: dict, nombre_idx: dict) -> tuple[dict, list[dict]] | None:
    """Los tracks del set, resueltos contra el pool.

    Se cruza por NOMBRE antes que por ContentID: Rekordbox reasigna los ID
    cuando se reconstruye la biblioteca, y este proyecto la reconstruyo. Los
    set_targets viejos tienen ID que ya no existen, y cruzando por ID se perdia
    el set entero en silencio.
    """
    f = TARGETS / f"set_{num}.json"
    if not f.exists():
        return None
    tgt = json.loads(f.read_text(encoding="utf-8"))
    tracks = []
    for t in tgt["tracks"]:
        m = nombre_idx.get(clave(t.get("artist", ""), t.get("title", "")))
        if not m:
            m = pool_idx.get(t.get("content_id"))
        if m and m.get("energy") is not None and m.get("bpm") and S.camelot(m["key"]):
            tracks.append(dict(m))
    return (tgt, tracks) if len(tracks) >= 4 else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", nargs="*", type=int)
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--min-flojas", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    pool_idx = {t["id"]: t for t in pool}
    nombre_idx = {clave(t["artist"], t["title"]): t for t in pool}
    nums = args.nums or (
        sorted(int(f.stem.split("_")[1]) for f in TARGETS.glob("set_*.json"))
        if args.todos else [])
    if not nums:
        sys.exit("pasa numeros de set o --todos")

    mejorados = sin_arreglo = 0
    for num in nums:
        cargado = cargar(num, pool_idx, nombre_idx)
        if not cargado:
            continue
        tgt, tracks = cargado
        antes = flojas(tracks)
        if antes < args.min_flojas:
            continue
        seq, cam = reordenar(tracks)
        despues = flojas(seq)
        marca = "" if cam <= 1 else f"  (salto Camelot maximo: {cam})"
        if despues < antes:
            mejorados += 1
            print(f"  set {num}: {antes} -> {despues} flojas{marca}  | {tgt['name'][:44]}")
            if not args.dry:
                tgt["tracks"] = [{"artist": t["artist"], "title": t["title"],
                                  "content_id": t["id"]} for t in seq]
                tgt["keep_order"] = True
                tgt["_reordenado"] = (
                    f"Reordenado con scripts/reordenar_set.py: {antes} -> {despues} "
                    f"transiciones flojas. Los tracks son los mismos; solo cambio el orden.")
                (TARGETS / f"set_{num}.json").write_text(
                    json.dumps(tgt, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            print(f"  set {num}: {antes} flojas, no se pudo mejorar{marca}")
    print(f"\n{mejorados} sets mejorados, {sin_arreglo} sin orden posible")
    if not args.dry and mejorados:
        print("Ahora: build_set.py <num> para cada uno, y audit_sets.py")


if __name__ == "__main__":
    main()
