"""Higiene de metadata de la biblioteca: espacios, sellos y artistas repetidos.

Esto NO es pipeline. Es limpieza de datos que ya estan en la DB y que ensucian
tres cosas concretas:

1. **Espacios sobrantes en el titulo.** 370 de 1816 tracks (20%) tienen espacio
   final o doble espacio. Vienen asi del tag ID3 de origen — 369 de los 370 lo
   tienen tambien en el archivo, o sea que no los genero el proyecto. Rompen
   cualquier match por titulo y se ven en la pantalla del CDJ.
2. **Sellos partidos por capitalizacion.** `Meanwhile` y `meanwhile` son dos
   filas distintas en `djmdLabel`, asi que el mismo sello aparece dos veces en
   la vista de Rekordbox y cualquier conteo por sello miente.
3. **Artistas partidos por capitalizacion.** `Guy J` y `GUY J` son dos filas en
   `djmdArtist`. `select_set.py` normaliza a minusculas al contar, asi que el
   tope por artista no se rompe — pero la lista de artistas de Rekordbox si.

Lo que NO toca, y es a proposito:

- **Typos del release** (`Goldes Eyes`, `Wakefeld`, `Cinimatic`). Si el sello lo
  publico asi, ese es el titulo. Corregirlo desincroniza con Beatport, con Muzpa
  y con cualquier setlist que ya lo tenga escrito.
- **Los tags ID3 del archivo.** Limpiar solo la DB no toca el audio y se
  revierte con un backup. Si algun dia Rekordbox hace "Reload Tag" el espacio
  vuelve; ahi la solucion es limpiar en `import_all.py`, no aca.
- **Nombres de archivo.** 121 archivos tienen el espacio en el nombre. Renombrar
  obliga a mover el archivo y actualizar `FolderPath` en el mismo latido; un
  corte a la mitad deja el track roto. Es otra operacion, no esta.
- **Sellos y generos vacios.** 66 tracks sin sello, y ninguno tiene el `[Sello]`
  en el nombre de archivo para recuperarlo. Inventar no es limpiar.
- **Separadores de artista** (`GMJ, Matter` vs `GMJ & Matter`) y **acentos**
  (`Ben Bohmer` vs `Ben Bohmer` con dieresis). Son la misma gente, pero eso es
  como el sello acredito el track. `select_set.py` ya parte por `,` y por `&`,
  asi que el tope por artista los cuenta igual. Cambiarlo es reescribir el
  credito, no arreglar un error.
- **djmdAlbum.** Rekordbox crea una fila de album por cada (nombre, artista del
  album): "Theia" duplicado no es un error de datos sino como funciona la tabla.

Uso:
    python scripts/limpiar_metadata.py --censo     # todas las categorias, no escribe
    python scripts/limpiar_metadata.py             # dry-run del plan de arreglo
    python scripts/limpiar_metadata.py --si        # ejecuta
    python scripts/limpiar_metadata.py --si --solo espacios
    python scripts/limpiar_metadata.py --excluir MESH --si
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import psutil  # noqa: E402
import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

# Tablas de entidad fusionables: op -> (tabla, columna en djmdContent, columna nombre)
ENTIDADES = {
    "sellos": ("djmdLabel", "LabelID", "Name"),
    "artistas": ("djmdArtist", "ArtistID", "Name"),
    "generos": ("djmdGenre", "GenreID", "Name"),
}
# djmdArtist se referencia desde cuatro columnas distintas de djmdContent. Si se
# repunta solo ArtistID, la fila perdedora sigue viva colgada de un remixer.
COLUMNAS_EXTRA = {"djmdArtist": ["RemixerID", "OrgArtistID", "ComposerID"]}

OPERACIONES = ("espacios", "sellos", "artistas", "generos")

VIVOS = "rb_local_deleted=0"

# Categorias que el censo reporta pero el script no arregla.
CENSO_SOLO_LECTURA = [
    ("tracks sin sello",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} "
     "AND NOT EXISTS (SELECT 1 FROM djmdLabel l WHERE l.ID=c.LabelID)"),
    ("tracks sin genero",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} "
     "AND NOT EXISTS (SELECT 1 FROM djmdGenre g WHERE g.ID=c.GenreID)"),
    ("tracks sin artista",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} "
     "AND NOT EXISTS (SELECT 1 FROM djmdArtist a WHERE a.ID=c.ArtistID)"),
    ("tracks sin key",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} "
     "AND NOT EXISTS (SELECT 1 FROM djmdKey k WHERE k.ID=c.KeyID)"),
    ("tracks con BPM 0",
     f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS} AND (BPM IS NULL OR BPM=0)"),
    ("tracks sin ningun cue",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} AND NOT EXISTS "
     f"(SELECT 1 FROM djmdCue u WHERE u.ContentID=c.ID AND u.{VIVOS})"),
    ("tracks sin energia (E: en Commnt)",
     f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS} "
     "AND (Commnt IS NULL OR Commnt NOT LIKE 'E:%')"),
    ("archivos fuera de Music/Biblioteca",
     f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS} "
     "AND FolderPath NOT LIKE '%/Music/Biblioteca/%'"),
    ("nombres de archivo con espacio",
     f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS} "
     "AND (FileNameL<>trim(FileNameL) OR FileNameL LIKE '%  %')"),
    ("titulos con parentesis desbalanceado",
     f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS} AND Title IS NOT NULL "
     "AND (length(Title)-length(replace(Title,'(',''))) "
     "<> (length(Title)-length(replace(Title,')','')))"),
    ("filas de contentFile de tracks borrados",
     "SELECT COUNT(*) FROM contentFile f JOIN djmdContent c ON c.ID=f.ContentID "
     "WHERE c.rb_local_deleted<>0"),
    ("tracks vivos sin fila en contentFile",
     f"SELECT COUNT(*) FROM djmdContent c WHERE c.{VIVOS} "
     "AND NOT EXISTS (SELECT 1 FROM contentFile f WHERE f.ContentID=c.ID)"),
]


def rekordbox_corriendo() -> bool:
    return any(p.info["name"] and "rekordbox" in p.info["name"].lower()
               for p in psutil.process_iter(["name"]))


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def limpiar(texto: str) -> str:
    """Colapsa espacios internos y recorta puntas. No toca nada mas."""
    return re.sub(r"[\s ]+", " ", texto).strip()


def sucio(texto: str | None) -> bool:
    return bool(texto) and texto != limpiar(texto)


def clave(texto: str) -> str:
    """Clave de fusion: sin mayusculas y sin espacios de mas. Los acentos SI
    distinguen — `Ben Bohmer` y su forma acentuada quedan separados a proposito."""
    return limpiar(texto).casefold()


def _acentos(texto: str) -> int:
    return sum(1 for c in unicodedata.normalize("NFD", texto)
               if unicodedata.category(c) == "Mn")


def canonica(variantes: list[tuple[str, str, int]]) -> tuple[str, str, int]:
    """Elige que fila sobrevive de un grupo de (id, nombre, tracks vivos).

    Manda el uso: la forma que ya esta en mas tracks es la que el ojo reconoce
    en Rekordbox. Los desempates evitan quedarse con un grito (`GUY J`) o con un
    murmullo (`meanwhile`) cuando existe la forma normal.

    El segundo criterio es "estar limpio", y no es cosmetico: con el uso
    empatado, `'Techno (Raw  Deep  Hypnotic)'` le ganaba por ser mas corta a
    `'Techno (Raw / Deep / Hypnotic)'`, que es la forma real de Beatport. El
    desempate por largo tiene que ir despues de este, nunca antes.
    """
    def puntaje(v: tuple[str, str, int]) -> tuple:
        _, nombre, uso = v
        letras = [c for c in nombre if c.isalpha()]
        grito = bool(letras) and all(c.isupper() for c in letras)
        murmullo = bool(letras) and all(c.islower() for c in letras)
        return (uso, not sucio(nombre), not grito, not murmullo,
                _acentos(nombre), -len(nombre), nombre)

    return max(variantes, key=puntaje)


def uso_por_entidad(con, tabla: str, columna: str) -> dict[str, int]:
    """Cuantos tracks vivos apunta cada fila de entidad, sumando todas las FKs."""
    cuenta: dict[str, int] = defaultdict(int)
    for col in [columna] + COLUMNAS_EXTRA.get(tabla, []):
        for eid, n in con.execute(
            f"SELECT {col}, COUNT(*) FROM djmdContent "
            f"WHERE {VIVOS} AND {col} IS NOT NULL GROUP BY 1"
        ):
            cuenta[str(eid)] += n
    return cuenta


# ---------------------------------------------------------------- planificacion

def plan_espacios(con) -> list[tuple[str, str, str]]:
    """Titulos de track con espacio sobrante. (content_id, viejo, nuevo)."""
    filas = con.execute(
        f"SELECT ID, Title FROM djmdContent WHERE {VIVOS} AND Title IS NOT NULL"
    ).fetchall()
    return [(str(cid), t, limpiar(t)) for cid, t in filas if sucio(t)]


def _reubicar_barras_perdidas(grupos: dict[str, list]) -> None:
    """Reasigna los nombres cuyo doble espacio es una barra que se perdio.

    `'Organic House  Downtempo'` no es un doble espacio al azar: la biblioteca
    ya tiene `'Organic House / Downtempo'` con 40 tracks. Colapsar el espacio a
    secas produce `'Organic House Downtempo'`, que es una TERCERA variante y
    deja el genero peor que antes. Solo se reubica cuando la forma con barra
    coincide con un nombre que ya existe — es evidencia, no adivinanza.
    """
    for llave in list(grupos):
        # La llave ya viene colapsada por clave(), asi que el doble espacio hay
        # que buscarlo en el nombre crudo de cada variante.
        quedan, mudan = [], defaultdict(list)
        for variante in grupos[llave]:
            crudo = variante[1]
            alterna = clave(re.sub(r"\s{2,}", " / ", crudo)) if re.search(r"\s{2,}", crudo) else None
            if alterna and alterna != llave and alterna in grupos:
                mudan[alterna].append(variante)
            else:
                quedan.append(variante)
        if not mudan:
            continue
        for destino, variantes in mudan.items():
            grupos[destino].extend(variantes)
        if quedan:
            grupos[llave] = quedan
        else:
            del grupos[llave]


def plan_entidad(con, tabla: str, columna: str, namecol: str,
                 excluidos: set[str]) -> tuple[list, list, list]:
    """Devuelve (fusiones, renombres, vacias) para una tabla de entidad.

    fusion   = (id_ganador, nombre_final, [(id_perdedor, nombre, tracks)])
    renombre = (id, viejo, nuevo)  — solo espacios, sin fusion
    vacia    = (id, nombre)        — fila duplicada que no sostiene ningun track

    Las dos primeras se planifican juntas porque limpiar el espacio de
    `'All Day I Dream '` lo convierte en un duplicado exacto de
    `'All Day I Dream'`: el trim tiene que resolverse como fusion, no como
    renombre, o quedan dos filas identicas.

    Una fusion cuyos perdedores ya no tienen tracks y cuyo ganador ya esta
    limpio no se lista: no haria nada. Sin ese filtro el script se propone a si
    mismo el mismo trabajo en cada corrida, porque la fila perdedora sigue viva
    aunque este vacia. Esas filas salen por `vacias`, que es lo que se lleva
    `--huerfanos`.
    """
    uso = uso_por_entidad(con, tabla, columna)
    filas = con.execute(
        f"SELECT ID, {namecol} FROM {tabla} WHERE {VIVOS} AND {namecol} IS NOT NULL"
    ).fetchall()

    grupos: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for eid, nombre in filas:
        grupos[clave(nombre)].append((str(eid), nombre, uso.get(str(eid), 0)))
    _reubicar_barras_perdidas(grupos)

    fusiones, renombres, vacias = [], [], []
    for variantes in grupos.values():
        if any(v[1] in excluidos or limpiar(v[1]) in excluidos for v in variantes):
            continue
        ganador = canonica(variantes)
        final = limpiar(ganador[1])
        perdedores = [v for v in variantes if v[0] != ganador[0]]
        if not perdedores:
            if ganador[1] != final:
                renombres.append((ganador[0], ganador[1], final))
            continue
        vacias.extend((eid, nombre) for eid, nombre, _ in perdedores)
        hay_tracks = any(uso > 0 for _, _, uso in perdedores)
        if hay_tracks or ganador[1] != final:
            fusiones.append((ganador[0], final, perdedores))
    return fusiones, renombres, vacias


# ------------------------------------------------------------------- ejecucion

def escribir_espacios(con, plan, ahora: str) -> tuple[int, int]:
    """Un UPDATE y un commit por track. Un fallo no arrastra a los demas."""
    usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdContent").fetchone()[0] or 0
    ok = fallos = 0
    for cid, viejo, nuevo in plan:
        try:
            usn += 1
            con.execute(
                "UPDATE djmdContent SET Title=?, rb_local_usn=?, updated_at=? WHERE ID=?",
                (nuevo, usn, ahora, cid),
            )
            con.commit()
            ok += 1
        except Exception as e:  # noqa: BLE001 — un fallo no aborta la tanda
            con.rollback()
            fallos += 1
            print(f"    [ERROR] titulo {cid} {viejo!r}: {e}")
    return ok, fallos


def escribir_entidad(con, tabla: str, columna: str, namecol: str,
                     fusiones: list, renombres: list, ahora: str) -> tuple[int, int]:
    """Repunta los tracks del perdedor al ganador y renombra al ganador.

    La fila perdedora queda viva pero sin tracks. Es a proposito: borrarla es
    una operacion de sync que Rekordbox tiene que decidir, y una fila de sello
    sin uso no molesta a nadie.
    """
    usn_tabla = con.execute(f"SELECT MAX(rb_local_usn) FROM {tabla}").fetchone()[0] or 0
    usn_content = con.execute("SELECT MAX(rb_local_usn) FROM djmdContent").fetchone()[0] or 0
    columnas = [columna] + COLUMNAS_EXTRA.get(tabla, [])
    ok = fallos = 0

    for ganador, final, perdedores in fusiones:
        try:
            for perdedor, _, _ in perdedores:
                for col in columnas:
                    afectados = con.execute(
                        f"SELECT ID FROM djmdContent WHERE {col}=? AND {VIVOS}",
                        (perdedor,),
                    ).fetchall()
                    for (cid,) in afectados:
                        usn_content += 1
                        con.execute(
                            f"UPDATE djmdContent SET {col}=?, rb_local_usn=?, "
                            f"updated_at=? WHERE ID=?",
                            (ganador, usn_content, ahora, cid),
                        )
            usn_tabla += 1
            con.execute(
                f"UPDATE {tabla} SET {namecol}=?, rb_local_usn=?, updated_at=? WHERE ID=?",
                (final, usn_tabla, ahora, ganador),
            )
            con.commit()          # commit por grupo fusionado
            ok += 1
        except Exception as e:  # noqa: BLE001
            con.rollback()
            fallos += 1
            print(f"    [ERROR] fusion {tabla} -> {final!r}: {e}")

    for eid, viejo, nuevo in renombres:
        try:
            usn_tabla += 1
            con.execute(
                f"UPDATE {tabla} SET {namecol}=?, rb_local_usn=?, updated_at=? WHERE ID=?",
                (nuevo, usn_tabla, ahora, eid),
            )
            con.commit()
            ok += 1
        except Exception as e:  # noqa: BLE001
            con.rollback()
            fallos += 1
            print(f"    [ERROR] renombre {tabla} {viejo!r}: {e}")
    return ok, fallos


def borrar_vacias(con, tabla: str, columna: str, vacias: list,
                  ahora: str) -> tuple[int, int]:
    """Marca como borradas las filas duplicadas que ya no sostienen ningun track.

    Es un borrado logico (`rb_local_deleted=1`), el mismo que usa Rekordbox: la
    fila sigue en la tabla para que el sync sepa que desaparecio. Antes de tocar
    cada fila se vuelve a contar el uso — si alguien quedo colgado, se saltea.
    """
    usn_tabla = con.execute(f"SELECT MAX(rb_local_usn) FROM {tabla}").fetchone()[0] or 0
    columnas = [columna] + COLUMNAS_EXTRA.get(tabla, [])
    ok = saltadas = 0
    for eid, nombre in vacias:
        usada = any(
            con.execute(
                f"SELECT 1 FROM djmdContent WHERE {col}=? AND {VIVOS} LIMIT 1", (eid,)
            ).fetchone()
            for col in columnas
        )
        if usada:
            saltadas += 1
            print(f"    [SALTEADA] {tabla} {nombre!r} todavia tiene tracks")
            continue
        try:
            usn_tabla += 1
            con.execute(
                f"UPDATE {tabla} SET rb_local_deleted=1, rb_local_usn=?, updated_at=? "
                f"WHERE ID=?", (usn_tabla, ahora, eid))
            con.commit()
            ok += 1
        except Exception as e:  # noqa: BLE001
            con.rollback()
            saltadas += 1
            print(f"    [ERROR] borrado {tabla} {nombre!r}: {e}")
    return ok, saltadas


# ----------------------------------------------------------------------- censo

def censo(con) -> None:
    """Todas las categorias, incluidas las que este script no arregla."""
    total = con.execute(f"SELECT COUNT(*) FROM djmdContent WHERE {VIVOS}").fetchone()[0]
    print(f"\n  CENSO — {total} tracks vivos\n")
    print("  -- se arregla (seguro) --")
    print(f"    {'titulos con espacio sobrante':38} {len(plan_espacios(con)):5}")
    for op in ("sellos", "artistas", "generos"):
        tabla, columna, namecol = ENTIDADES[op]
        fusiones, renombres, vacias = plan_entidad(con, tabla, columna, namecol, set())
        repuntados = sum(v[2] for _, _, ps in fusiones for v in ps)
        print(f"    {op + ' a fusionar':38} {len(fusiones):5} grupos "
              f"({repuntados} tracks repuntados, {len(renombres)} renombres, "
              f"{len(vacias)} filas duplicadas vacias)")

    print("\n  -- se reporta, no se toca --")
    for etiqueta, sql in CENSO_SOLO_LECTURA:
        print(f"    {etiqueta:38} {con.execute(sql).fetchone()[0]:5}")

    # uso_por_entidad solo devuelve las filas que SI se usan, asi que los
    # huerfanos son las que no aparecen en el dict — no las que valen 0.
    usadas = {k for k, v in uso_por_entidad(con, "djmdArtist", "ArtistID").items() if v}
    todas = {str(r[0]) for r in con.execute(f"SELECT ID FROM djmdArtist WHERE {VIVOS}")}
    print(f"    {'artistas sin ningun track vivo':38} {len(todas - usadas):5} de {len(todas)}")
    print("\n    Los typos de origen (Goldes Eyes / Wakefeld / Cinimatic) no se")
    print("    cuentan ni se corrigen: si el sello lo publico asi, es el titulo.\n")


# ------------------------------------------------------------------------ main

def imprimir_plan(titulos: list, entidades: dict, huerfanos: bool) -> int:
    print(f"\n  titulos con espacio sobrante: {len(titulos)}")
    for _, viejo, nuevo in titulos[:15]:
        print(f"    {viejo!r}  ->  {nuevo!r}")
    if len(titulos) > 15:
        print(f"    ... y {len(titulos) - 15} mas")

    total = 0
    for op, (fusiones, renombres, vacias) in entidades.items():
        print(f"\n  {op}: {len(fusiones)} fusiones, {len(renombres)} renombres"
              + (f", {len(vacias)} filas vacias a borrar" if huerfanos else ""))
        for _, final, perdedores in fusiones:
            pierde = ", ".join(f"{n!r}({u} tracks)" for _, n, u in perdedores)
            print(f"    queda {final!r}   <- absorbe {pierde}")
        for _, viejo, nuevo in renombres:
            print(f"    renombra {viejo!r} -> {nuevo!r}")
        total += len(fusiones) + len(renombres)
        if huerfanos:
            for _, nombre in vacias:
                print(f"    borra fila vacia {nombre!r}")
            total += len(vacias)
        elif vacias:
            print(f"    ({len(vacias)} filas duplicadas quedan vacias pero vivas; "
                  f"--huerfanos las borra)")
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--si", action="store_true", help="ejecuta (por defecto dry-run)")
    ap.add_argument("--censo", action="store_true", help="solo el censo, no escribe")
    ap.add_argument("--solo", choices=OPERACIONES, action="append",
                    help="limitar a una operacion (repetible)")
    ap.add_argument("--excluir", action="append", default=[],
                    help="nombre exacto de entidad a dejar en paz (repetible)")
    ap.add_argument("--huerfanos", action="store_true",
                    help="ademas borra (logico) las filas duplicadas que quedan vacias")
    args = ap.parse_args()

    # El preflight corre siempre, no solo con --si: si Rekordbox esta abierto
    # tiene la DB en memoria y hasta el censo puede estar leyendo algo viejo.
    if rekordbox_corriendo():
        print("  Rekordbox esta abierto. Cerralo desde la bandeja (Quit) — con la X")
        print("  sigue vivo y pisa cualquier cambio externo al salir.")
        sys.exit(1)

    con = db_connect()
    if args.censo:
        censo(con)
        con.close()
        return

    operaciones = args.solo or list(OPERACIONES)
    excluidos = set(args.excluir)

    titulos = plan_espacios(con) if "espacios" in operaciones else []
    entidades = {}
    for op in ("sellos", "artistas", "generos"):
        if op in operaciones:
            tabla, columna, namecol = ENTIDADES[op]
            entidades[op] = plan_entidad(con, tabla, columna, namecol, excluidos)

    total_entidades = imprimir_plan(titulos, entidades, args.huerfanos)
    if not titulos and not total_entidades:
        print("\n  Nada que limpiar.")
        con.close()
        return

    if not args.si:
        print("\n  Dry-run. Agregar --si para ejecutar.")
        con.close()
        return

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = config.BACKUP_FOLDER / f"master_pre_limpieza_{ts}.db"
    shutil.copy2(config.REKORDBOX_DB_PATH, backup)
    print(f"\n  backup -> {backup}")
    if config.REKORDBOX_XML_PATH.exists():
        xml = config.BACKUP_FOLDER / f"masterPlaylists6_pre_limpieza_{ts}.xml"
        shutil.copy2(config.REKORDBOX_XML_PATH, xml)
        print(f"  backup -> {xml}")

    ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = fallos = 0

    if titulos:
        a, b = escribir_espacios(con, titulos, ahora)
        print(f"  titulos limpiados: {a}   fallos: {b}")
        ok, fallos = ok + a, fallos + b

    for op, (fusiones, renombres, vacias) in entidades.items():
        tabla, columna, namecol = ENTIDADES[op]
        a, b = escribir_entidad(con, tabla, columna, namecol, fusiones, renombres, ahora)
        print(f"  {op}: {a} aplicados   fallos: {b}")
        ok, fallos = ok + a, fallos + b
        if args.huerfanos and vacias:
            # Va despues de las fusiones: recien ahi las filas quedan sin tracks.
            a, b = borrar_vacias(con, tabla, columna, vacias, ahora)
            print(f"  {op}: {a} filas vacias borradas   salteadas: {b}")
            ok, fallos = ok + a, fallos + b

    integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    print(f"\n  total aplicado: {ok}   fallos: {fallos}")
    print(f"  integrity_check: {integridad}")
    if integridad != "ok":
        print(f"  INTEGRIDAD ROTA — restaurar {backup}")


if __name__ == "__main__":
    main()
