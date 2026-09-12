"""Ordena los sets armados en niveles, como los tiene un DJ que trabaja.

El problema: 111 playlists numeradas repartidas en siete padres distintos, dos
carpetas que solo se diferencian por un acento ("Por Posicion" y "Por Posición"),
playlists de sets colgando de "Por BPM", y la misma lista duplicada cinco veces.
Una lista plana numerada sirve para versionar, no para buscar algo a las tres de
la manana.

El criterio de los niveles NO es el numero ni la fecha: es EN QUE MOMENTO se
agarra ese set. Y eso se deduce del pico de energia, que es el dato que ya
tenemos medido track por track.

    1 Apertura          pico < 6.5   — lo que abre, sin prometer nada
    2 Prime Time        6.5 a 7.5    — la pista ya esta
    3 Peak              7.5 a 8.5    — el punto mas alto de la noche
    4 Detonante/Cierre  >= 8.5       — lo que rompe o lo que despide
    5 Referencia        los sets de otros DJs reconstruidos
    6 Archivo           lo viejo, que no se borra pero no estorba
    [POOL]              cajas de material, no son sets

Uso:
    python scripts/organizar_sets.py --dry
    python scripts/organizar_sets.py
"""
from __future__ import annotations

import argparse
import random
import re
import sys
import uuid as uuid_lib
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

E_RE = re.compile(r"E:(\d+(?:\.\d+)?)")
ES_SET = re.compile(r"^\d{1,3}\.\s")

NIVELES = [
    (0.0, 6.5, "1 Apertura"),
    (6.5, 7.5, "2 Prime Time"),
    (7.5, 8.5, "3 Peak"),
    (8.5, 99.0, "4 Detonante y Cierre"),
]
REFERENCIA = "5 Referencia — otros DJs"
ARCHIVO = "6 Archivo"
POOL = "[POOL]"
PADRE = "Sets Armados"


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def nivel_de(nombre: str, pico: float | None) -> str:
    n = nombre.lower()
    if n.startswith("[pool]"):
        return POOL
    if "[archivo]" in n:
        return ARCHIVO
    # Los reconstruidos a partir de setlists de otros DJs se llaman asi a
    # proposito: no son la secuencia de ese DJ, son material suyo ordenado.
    if "con el material de" in n:
        return REFERENCIA
    if pico is None:
        return ARCHIVO
    for lo, hi, etq in NIVELES:
        if lo <= pico < hi:
            return etq
    return ARCHIVO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    ts = _ts()

    filas = con.execute(
        "SELECT ID, Name, ParentID, Attribute, Seq FROM djmdPlaylist "
        "WHERE rb_local_deleted=0").fetchall()
    por_id = {f[0]: f for f in filas}

    # -- 1. duplicados exactos: mismo nombre y mismo padre --------------------
    grupos: dict[tuple, list] = defaultdict(list)
    for f in filas:
        grupos[(f[1], f[2])].append(f)
    borrados = 0
    for (nombre, _), fs in grupos.items():
        if len(fs) < 2:
            continue
        # se conserva la que mas tracks tiene; las otras son copias accidentales
        conteos = [(con.execute(
            "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0",
            (f[0],)).fetchone()[0], f[0]) for f in fs]
        conteos.sort(reverse=True)
        for _, pid in conteos[1:]:
            if not args.dry:
                con.execute("UPDATE djmdPlaylist SET rb_local_deleted=1, updated_at=? "
                            "WHERE ID=?", (ts, pid))
                con.execute("UPDATE djmdSongPlaylist SET rb_local_deleted=1, updated_at=? "
                            "WHERE PlaylistID=?", (ts, pid))
            borrados += 1
        print(f"  duplicada x{len(fs)}: {nombre[:56]} -> se conserva 1")
    print(f"{borrados} playlists duplicadas eliminadas\n")

    # -- 2. carpeta padre y niveles ------------------------------------------
    padre = next((f for f in filas if f[3] == 1 and f[1] == PADRE), None)
    if not padre:
        sys.exit(f"no existe la carpeta '{PADRE}' — crearla con scripts/create_folder.py")
    padre_id = padre[0]

    carpetas = {f[1]: f[0] for f in filas if f[3] == 1 and f[2] == padre_id}

    def asegurar(nombre: str, seq: int) -> str:
        if nombre in carpetas:
            return carpetas[nombre]
        nid = str(random.randint(1_500_000_000, 4_000_000_000))
        if not args.dry:
            con.execute(
                "INSERT INTO djmdPlaylist (ID, Seq, Name, ImagePath, Attribute, ParentID,"
                " SmartList, UUID, rb_data_status, rb_local_data_status, rb_local_deleted,"
                " rb_local_synced, created_at, updated_at)"
                " VALUES (?,?,?,NULL,1,?,NULL,?,0,0,0,0,?,?)",
                (nid, seq, nombre, padre_id, str(uuid_lib.uuid4()), ts, ts))
        carpetas[nombre] = nid
        print(f"  carpeta nueva: {nombre}")
        return nid

    orden = [e for _, _, e in NIVELES] + [REFERENCIA, ARCHIVO, POOL]
    for i, nombre in enumerate(orden, 1):
        asegurar(nombre, i)

    # -- 3. clasificar y mover ------------------------------------------------
    # Se considera "set" cualquier playlist que ya cuelgue del subarbol de Sets
    # Armados, tenga o no prefijo numerico: habia listas viejas llamadas
    # "hidark" y "colorido progresive" que por el prefijo quedaban afuera y
    # seguian sueltas despues de ordenar todo lo demas.
    subarbol = {padre_id}
    for _ in range(3):
        subarbol |= {f[0] for f in filas if f[3] == 1 and f[2] in subarbol}

    movidos: dict[str, int] = defaultdict(int)
    for pid, nombre, parent, attr, _ in filas:
        if attr == 1:
            continue
        if not (parent in subarbol or ES_SET.match(nombre)
                or nombre.lower().startswith("[pool]")):
            continue
        es = []
        for (c,) in con.execute(
                "SELECT c.Commnt FROM djmdSongPlaylist sp JOIN djmdContent c ON c.ID=sp.ContentID"
                " WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0", (pid,)):
            m = E_RE.match((c or "").strip())
            if m:
                es.append(float(m.group(1)))
        pico = max(es) if es else None
        destino = nivel_de(nombre, pico)
        did = carpetas[destino]
        if parent == did:
            continue
        if not args.dry:
            con.execute("UPDATE djmdPlaylist SET ParentID=?, updated_at=? WHERE ID=?",
                        (did, ts, pid))
        movidos[destino] += 1

    print("\nsets por nivel:")
    for nombre in orden:
        if movidos.get(nombre):
            print(f"  {movidos[nombre]:>3}  {nombre}")
    # -- 4. carpetas que quedaron vacias --------------------------------------
    vacias = []
    for f in filas:
        if f[3] != 1 or f[2] != padre_id or f[1] in orden:
            continue
        n = con.execute("SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0 "
                        "AND ParentID=?", (f[0],)).fetchone()[0]
        if n == 0:
            vacias.append(f)
    if vacias:
        print("\ncarpetas vacias que se eliminan:")
        for f in vacias:
            print(f"  {f[1]}")
            if not args.dry:
                con.execute("UPDATE djmdPlaylist SET rb_local_deleted=1, updated_at=? "
                            "WHERE ID=?", (ts, f[0]))

    if args.dry:
        print("\n[dry] no se escribio nada")
        return
    con.commit()
    print("\nintegridad:", con.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
