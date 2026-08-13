"""
Saca los loops de los archivos de analisis (.DAT/.EXT) de un pen exportado.

Por que hace falta: el CDJ lee los cues de estos archivos, no de master.db.
Rekordbox los reescribe solo cuando considera que el track cambio, asi que
borrar los loops de la base no los saca de un pen ya exportado.

Formato (Pioneer ANLZ, big-endian):
  Archivo: PMAI len_header len_file ... luego tags consecutivos
  Tag:     magic len_header len_tag [cuerpo]
  PCOB:  [12:16] type  [16:20] count  [20:24] memory_count   entradas PCPT
  PCO2:  [12:16] type  [16:18] count  [18:20] unk            entradas PCP2
  PCPT:  [8:12] len_entry  [32:36] time  [36:40] loop_time
  PCP2:  [8:12] len_entry  [20:24] time  [24:28] loop_time

Una entrada es LOOP si su loop_time no es 0xFFFFFFFF.

Uso:
  python scripts/strip_anlz_loops.py <carpeta> --dry
  python scripts/strip_anlz_loops.py <carpeta>
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NO_LOOP = 0xFFFFFFFF
CUE_TAGS = {b"PCOB", b"PCO2"}
ENTRY_MAGIC = {b"PCOB": b"PCPT", b"PCO2": b"PCP2"}
# (offset del loop_time dentro de la entrada) por tipo de entrada
LOOP_OFF = {b"PCPT": 36, b"PCP2": 24}


def u32(b: bytes, off: int) -> int:
    return struct.unpack_from(">I", b, off)[0]


def strip_tag(tag: bytes) -> tuple[bytes, int]:
    """Devuelve (tag sin loops, cantidad de loops sacados)."""
    magic = tag[:4]
    len_header = u32(tag, 4)
    emagic = ENTRY_MAGIC[magic]

    kept: list[bytes] = []
    removed = 0
    pos = len_header
    while pos + 12 <= len(tag) and tag[pos:pos + 4] == emagic:
        len_entry = u32(tag, pos + 8)
        if len_entry <= 0 or pos + len_entry > len(tag):
            raise ValueError(f"entrada invalida en {magic!r}: len={len_entry}")
        entry = tag[pos:pos + len_entry]
        if u32(entry, LOOP_OFF[emagic]) != NO_LOOP:
            removed += 1
        else:
            kept.append(entry)
        pos += len_entry

    if removed == 0:
        return tag, 0

    body = b"".join(kept)
    header = bytearray(tag[:len_header])
    if magic == b"PCOB":
        struct.pack_into(">I", header, 16, len(kept))
    else:  # PCO2
        struct.pack_into(">H", header, 16, len(kept))

    new_tag = bytearray(header + body + tag[pos:])  # tag[pos:] = relleno, si hay
    struct.pack_into(">I", new_tag, 8, len(new_tag))
    return bytes(new_tag), removed


def strip_file(data: bytes) -> tuple[bytes, int]:
    """Devuelve (contenido sin loops, cantidad de loops sacados)."""
    out = bytearray(data[: u32(data, 4)])
    pos = u32(data, 4)
    total = 0

    while pos + 12 <= len(data):
        magic = data[pos:pos + 4]
        len_tag = u32(data, pos + 8)
        if len_tag <= 0 or pos + len_tag > len(data):
            out += data[pos:]
            pos = len(data)
            break
        tag = data[pos:pos + len_tag]
        if magic in CUE_TAGS:
            tag, n = strip_tag(tag)
            total += n
        out += tag
        pos += len_tag

    struct.pack_into(">I", out, 8, len(out))  # PMAI len_file
    return bytes(out), total


def count_loops(data: bytes) -> int:
    """Cuenta loops recorriendo la estructura (para verificar)."""
    n = 0
    pos = u32(data, 4)
    while pos + 12 <= len(data):
        magic = data[pos:pos + 4]
        len_tag = u32(data, pos + 8)
        if len_tag <= 0 or pos + len_tag > len(data):
            break
        if magic in CUE_TAGS:
            emagic = ENTRY_MAGIC[magic]
            e = pos + u32(data, pos + 4)
            while data[e:e + 4] == emagic:
                le = u32(data, e + 8)
                if le <= 0:
                    break
                if u32(data, e + LOOP_OFF[emagic]) != NO_LOOP:
                    n += 1
                e += le
        pos += len_tag
    return n


def walk_ok(data: bytes) -> bool:
    """La cadena de tags cierra exactamente al final del archivo."""
    if u32(data, 8) != len(data):
        return False
    pos = u32(data, 4)
    while pos < len(data):
        if pos + 12 > len(data):
            return False
        len_tag = u32(data, pos + 8)
        if len_tag <= 0:
            return False
        pos += len_tag
    return pos == len(data)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    root = Path(sys.argv[1])
    dry = "--dry" in sys.argv

    files = sorted(root.rglob("*.DAT")) + sorted(root.rglob("*.EXT"))
    print(f"{'DRY RUN — ' if dry else ''}archivos: {len(files)}")

    tocados = loops = fallos = 0
    for f in files:
        data = f.read_bytes()
        if data[:4] != b"PMAI":
            continue
        antes = count_loops(data)
        if antes == 0:
            continue
        try:
            nuevo, n = strip_file(data)
        except Exception as exc:
            print(f"  [ERROR] {f.parent.name}/{f.name}: {exc}")
            fallos += 1
            continue

        if not walk_ok(nuevo) or count_loops(nuevo) != 0:
            print(f"  [RECHAZADO] {f.parent.name}/{f.name}: quedo inconsistente")
            fallos += 1
            continue

        tocados += 1
        loops += n
        if not dry:
            f.write_bytes(nuevo)

    print(f"\narchivos con loop: {tocados}")
    print(f"loops sacados:     {loops}")
    print(f"fallos:            {fallos}")
    if dry:
        print("\n[DRY RUN] No se escribio nada.")


if __name__ == "__main__":
    main()
