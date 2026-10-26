# -*- coding: utf-8 -*-
"""Lee el arbol de listas del pen desde export.pdb (la Device Library).

export.pdb es DeviceSQL de Pioneer (spec rekordbox_pdb.ksy): no es SQLite y
pyrekordbox no lo lee. exportLibrary.db (OneLibrary) va cifrado con otra clave
que master.db. Rekordbox escribe los dos RECIEN AL CERRARSE: leer despues de
cerrarlo, o se ve el pen de antes.

Uso:
    python scripts/read_pen_playlists.py                  # el arbol, con temas por lista
    python scripts/read_pen_playlists.py Session Sunset   # y los temas de esas listas
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PDB = Path("D:/PIONEER/rekordbox/export.pdb")
T_TRACKS, T_PLAYLIST_TREE, T_PLAYLIST_ENTRIES = 0, 7, 8
HEAP = 0x28
RAIZ = 0
MAX_NIVEL = 20


def cadena(b: bytes, o: int) -> str:
    """DeviceSQL string: corta ASCII (bit 0 en 1), larga ASCII (0x40) o UTF-16 (0x90)."""
    k = b[o]
    if k & 1:
        n = k >> 1
        return b[o + 1:o + n].decode("ascii", "replace")
    n = struct.unpack_from("<H", b, o + 1)[0]
    txt = b[o + 4:o + n]
    return txt.decode("utf-16-le" if k == 0x90 else "ascii", "replace")


def filas(b: bytes, lp: int, primera: int, ultima: int):
    """Offsets de las filas presentes de una tabla, recorriendo sus paginas."""
    p, vistas = primera, set()
    while p not in vistas:
        vistas.add(p)
        base = p * lp
        sig = struct.unpack_from("<I", b, base + 12)[0]
        chicas, flags = b[base + 0x18], b[base + 0x1B]
        grandes = struct.unpack_from("<H", b, base + 0x22)[0]
        n = grandes if (grandes > chicas and grandes != 0x1FFF) else chicas
        if flags & 0x40 == 0 and n:
            for g in range((n - 1) // 16 + 1):
                fin = base + lp - g * 0x24
                presentes = struct.unpack_from("<H", b, fin - 4)[0]
                for k in range(16):
                    if g * 16 + k >= n:
                        break
                    if presentes & (1 << k):
                        ofs = struct.unpack_from("<H", b, fin - 6 - 2 * k)[0]
                        yield base + HEAP + ofs
        if p == ultima:
            break
        p = sig


def leer(ruta: Path) -> tuple[dict, dict, dict]:
    """(titulos {tid: titulo}, listas {pid: (nombre, padre, es_carpeta, orden)}, entradas {pid: [(i, tid)]})."""
    b = ruta.read_bytes()
    lp, ntab = struct.unpack_from("<II", b, 4)
    tablas = {}
    for i in range(ntab):
        tipo, _, prim, ult = struct.unpack_from("<IIII", b, 0x1C + 16 * i)
        tablas[tipo] = (prim, ult)

    titulos = {}
    for r in filas(b, lp, *tablas[T_TRACKS]):
        tid = struct.unpack_from("<I", b, r + 72)[0]
        ofs = struct.unpack_from("<21H", b, r + 0x5E)
        titulos[tid] = cadena(b, r + ofs[17])

    listas = {}
    for r in filas(b, lp, *tablas[T_PLAYLIST_TREE]):
        padre, _, orden, pid, carpeta = struct.unpack_from("<IIIII", b, r)
        listas[pid] = (cadena(b, r + 20), padre, bool(carpeta), orden)

    entradas = {}
    for r in filas(b, lp, *tablas[T_PLAYLIST_ENTRIES]):
        i, tid, pid = struct.unpack_from("<III", b, r)
        entradas.setdefault(pid, []).append((i, tid))
    return titulos, listas, entradas


def arbol(listas: dict, entradas: dict, padre: int = RAIZ, nivel: int = 0) -> list[str]:
    """Lineas indentadas del arbol en el orden del pen; cada lista con su cantidad de temas."""
    if nivel > MAX_NIVEL:
        return []
    lineas = []
    for pid in sorted((p for p, l in listas.items() if l[1] == padre and p != padre), key=lambda p: listas[p][3]):
        nombre, _, carpeta, _ = listas[pid]
        lineas.append("  " * nivel + nombre + ("" if carpeta else f"  ({len(entradas.get(pid, []))})"))
        if carpeta:
            lineas += arbol(listas, entradas, pid, nivel + 1)
    return lineas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prefijos", nargs="*", help="listas cuyos temas mostrar")
    ap.add_argument("--pdb", type=Path, default=PDB)
    args = ap.parse_args()
    if not args.pdb.exists():
        raise SystemExit(f"no esta {args.pdb}: el pen no esta enchufado o no tiene export de Rekordbox")

    titulos, listas, entradas = leer(args.pdb)
    print(f"{args.pdb}: {len(titulos)} temas, {len(listas)} listas y carpetas\n")
    print("\n".join(arbol(listas, entradas)))
    for pid, (nombre, padre, carpeta, _) in listas.items():
        if carpeta or not any(nombre.startswith(p) for p in args.prefijos):
            continue
        print(f"\n{nombre}  [en {listas.get(padre, ('la raiz',))[0]}]")
        for i, tid in sorted(entradas.get(pid, [])):
            print(f"  {i:2d}. {titulos.get(tid, '?')}")


if __name__ == "__main__":
    main()
