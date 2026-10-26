# -*- coding: utf-8 -*-
"""Ordena el arbol de listas de Rekordbox: que carpeta va arriba y en que orden.

"Mejorame el orden de las carpetas, ademas haceme una carpeta sessions en mis
playlist, hace un plan y ejecutalo" (2026-10-26). El arbol estaba en el orden en
que se fueron creando las cosas: casi todas las listas con Seq 0 o NULL, y
Rekordbox las mostraba como caian (148, 149, 150, 151, 152, 155, 156, 153, 157...).

Rekordbox ordena hermanos por djmdPlaylist.Seq; de que carpeta cuelga cada una
vive en la fila (ParentID) Y en masterPlaylists6.xml (ParentId del <NODE>). Mover
una carpeta es cambiar los dos. Cada fila que cambia lleva rb_local_usn nuevo para
que el sync del pen se entere.

Las reglas viven en ORDEN, abajo. Correrlo de nuevo reordena lo que se haya sumado.

Uso:
    python scripts/ordenar_playlists.py --dry
    python scripts/ordenar_playlists.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

# carpeta -> regla. Una lista de nombres fija el orden de esos (prefijo); lo que no
# figura va despues en el orden en que estaba.
ORDEN: dict[str, object] = {
    "root": ["Sessions", "Pro DJ Library", "MI SONIDO", "CUE Analysis Playlist"],
    "Sessions": ["Session 01", "Session 02", "Session 03", "Session 04", "Session 05", "Session 06",
                 "Session 07", "Session 08", "Session 09", "Sunset"],
    "Pro DJ Library": ["Sets Armados", "PEN — Todo", "PEN — Activos", "Por Posicion de Set", "Por Estilo",
                       "Por Género", "Por BPM", "Por Key Camelot", "Curaduria Original"],
    "Sets Armados": "sets",
    "Por Key Camelot": "camelot",
}
MOVER = {"Sessions": ("Sets Armados", "root")}       # carpeta: (de donde, a donde)
BORRAR_SI_VACIA = ["Por Posición de Set"]             # duplicado vacio, con tilde, de "Por Posicion de Set"


# --------------------------------------------------------------- funciones puras


def numero_set(nombre: str) -> int | None:
    m = re.match(r"^\s*(\d+)\.", nombre or "")
    return int(m.group(1)) if m else None


def camelot(nombre: str) -> tuple[int, int]:
    m = re.match(r"^\s*(\d{1,2})([AB])\s*$", nombre or "", re.I)
    return (int(m.group(1)), 0 if m.group(2).upper() == "A" else 1) if m else (99, 9)


def ordenar(hijos: list[tuple[str, str]], regla: object) -> list[str]:
    """IDs de `hijos` [(id, nombre)] en el orden de la regla, estable para lo que no cubre."""
    if regla == "camelot":
        return [i for i, _ in sorted(hijos, key=lambda h: camelot(h[1]))]
    if regla == "sets":
        # "0 Fechas" arriba (el 0 del nombre ya lo pedia), los sets del mas nuevo al
        # mas viejo (el numero mas alto es el mas nuevo), [POOL] al final.
        def clave(h):
            i, n = h
            if n.startswith("0 Fechas"):
                return (0, 0)
            num = numero_set(n)
            if num is not None:
                return (1, -num)
            return (3, 0) if n.startswith("[POOL]") else (2, 0)
        return [i for i, _ in sorted(hijos, key=clave)]
    if isinstance(regla, list):
        def pos(h):
            for k, prefijo in enumerate(regla):
                if h[1] == prefijo or h[1].startswith(prefijo + " ") or h[1].startswith(prefijo + "·"):
                    return k
            return len(regla)
        return [i for i, _ in sorted(hijos, key=pos)]
    return [i for i, _ in hijos]


# ------------------------------------------------------------------ escritura


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    from build_set import db_connect, next_usn, now_str
    from plomo import config
    from plomo.rekordbox_app import esta_abierto

    if not args.dry and esta_abierto():
        raise SystemExit("Rekordbox esta abierto: cerralo y volve a correr.")
    con = db_connect()
    vivas = "COALESCE(rb_local_deleted,0)=0"
    filas = con.execute(f"SELECT ID, Name, ParentID, Attribute, Seq FROM djmdPlaylist WHERE {vivas}").fetchall()
    por_id = {f[0]: f for f in filas}
    carpetas = {}
    for f in filas:
        if f[3] == 1:
            carpetas.setdefault(f[1], []).append(f[0])

    def id_carpeta(nombre: str, padre: str | None = None) -> str | None:
        ids = [i for i in carpetas.get(nombre, []) if padre is None or por_id[i][2] == padre]
        return ids[0] if len(ids) == 1 else None

    ts = now_str()
    xml = Path(config.REKORDBOX_XML_PATH)
    xml_txt = xml.read_text(encoding="utf-8") if xml.exists() else ""
    cambios = 0

    # 1. mover
    for nombre, (de, a) in MOVER.items():
        de_id = id_carpeta(de)
        pid = id_carpeta(nombre, de_id) if de_id else None
        if not pid:
            print(f"  mover {nombre}: no esta en {de} (ya movida?)")
            continue
        destino = "root" if a == "root" else id_carpeta(a)
        print(f"  mover {nombre}: {de} -> {a}")
        if not args.dry:
            con.execute("UPDATE djmdPlaylist SET ParentID=?, rb_local_synced=0, rb_local_usn=?, updated_at=? WHERE ID=?",
                        (destino, next_usn(con), ts, pid))
            viejo = f'Id="{int(pid):X}" ParentId="{int(de_id):X}"'
            nuevo = f'Id="{int(pid):X}" ParentId="{0 if destino == "root" else format(int(destino), "X")}"'
            if viejo not in xml_txt:
                raise SystemExit(f"no encuentro el nodo de {nombre} en {xml}: no muevo nada a medias")
            xml_txt = xml_txt.replace(viejo, nuevo)
            por_id[pid] = (pid, nombre, destino, 1, por_id[pid][4])
            cambios += 1

    # 2. borrar carpetas vacias duplicadas
    for nombre in BORRAR_SI_VACIA:
        for pid in carpetas.get(nombre, []):
            adentro = con.execute(f"SELECT COUNT(*) FROM djmdPlaylist WHERE ParentID=? AND {vivas}", (pid,)).fetchone()[0]
            if adentro:
                print(f"  {nombre}: no esta vacia ({adentro}), no se toca")
                continue
            print(f"  borrar carpeta vacia: {nombre}")
            if not args.dry:
                con.execute("UPDATE djmdPlaylist SET rb_local_deleted=1, rb_local_synced=0, rb_local_usn=?, updated_at=? "
                            "WHERE ID=?", (next_usn(con), ts, pid))
                xml_txt = re.sub(rf'\s*<NODE Id="{int(pid):X}" [^>]*/>', "", xml_txt)
                por_id.pop(pid, None)
                cambios += 1

    # 3. ordenar
    for carpeta, regla in ORDEN.items():
        padre = "root" if carpeta == "root" else id_carpeta(carpeta)
        if padre is None:
            print(f"  {carpeta}: no la encuentro (o hay dos con ese nombre), no se ordena")
            continue
        hijos = sorted(((f[0], f[1]) for f in por_id.values() if f[2] == padre),
                       key=lambda h: (por_id[h[0]][4] or 0))
        orden = ordenar(hijos, regla)
        nombres = [por_id[i][1] for i in orden]
        print(f"  {carpeta}: " + " | ".join(n[:28] for n in nombres[:8]) + (" | ..." if len(nombres) > 8 else ""))
        for seq, i in enumerate(orden, 1):
            if por_id[i][4] != seq and not args.dry:
                con.execute("UPDATE djmdPlaylist SET Seq=?, rb_local_synced=0, rb_local_usn=?, updated_at=? WHERE ID=?",
                            (seq, next_usn(con), ts, i))
                cambios += 1

    if args.dry:
        print("--dry: no se escribio nada")
        con.close()
        return
    con.commit()
    if xml_txt:
        xml.write_text(xml_txt, encoding="utf-8")
    print(f"  {cambios} filas cambiadas | integridad: {con.execute('PRAGMA quick_check').fetchone()[0]}")
    con.close()


if __name__ == "__main__":
    main()
