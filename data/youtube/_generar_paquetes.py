"""Genera los paquetes de publicacion de la serie "Sonido Argentino".

Lee el orden real de la playlist en Rekordbox (solo lectura), las duraciones de
`data/pool.json`, los cues DROP de `djmdCue`, y el texto editorial de
`_editorial.json`. Escribe un `set_NN.md` por video y un `README.md` de indice.

No escribe en master.db: abre la conexion con `mode=ro`.

Uso:
    python data/youtube/_generar_paquetes.py             # 80-89
    python data/youtube/_generar_paquetes.py 96          # el video 11 cuando exista
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

OUT_DIR = ROOT / "data" / "youtube"
BLEND_SEG = 180          # blend fijo de 3:00 entre track y track
BARRA_PRE = 8            # compases antes del drop que entran al short
BARRA_POST = 16          # compases despues del drop
TRACKS_ESPERADOS = 18
N_SHORTS = 6
MAX_TAGS_CHARS = 480     # el campo de YouTube corta en 500

# Correcciones de metadata que no se pueden arreglar en la DB desde aca.
ARTISTA_FIX = {"Mike rish": "Mike Rish"}
SELLO_FIX = {"meanwhile": "Meanwhile", "Anjunadeep Anjunadeep": "Anjunadeep"}
# Sello que la biblioteca no tiene y se verifico afuera (no inventado).
SELLO_EXTERNO = {"191133539": ("COMET Records", "Beatport 18487764 / Comet Records")}
# Titulos que parecen typos de origen: se reportan, no se tocan.
TITULOS_SOSPECHOSOS = {"Goldes Eyes", "Wakefeld", "Cinimatic"}


def mmss(seg: float) -> str:
    seg = int(round(seg))
    return f"{seg // 60}:{seg % 60:02d}"


def hmmss(seg: float) -> str:
    seg = int(round(seg))
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def norm(s: str | None) -> str:
    """Colapsa espacios dobles y saca los de los bordes."""
    return re.sub(r"\s+", " ", s or "").strip()


def celda(s: str) -> str:
    """Escapa el pipe para que no rompa la tabla markdown."""
    return str(s).replace("|", "\\|")


def norm_titulo(s: str | None) -> str:
    t = norm(s)
    t = re.sub(r"\s+-\s+(Original|Extended|Club|Radio)\s+(Mix|Edit)$", r" (\1 \2)", t)
    return t


def abrir_db():
    uri = "file:///" + quote(str(config.REKORDBOX_DB_PATH).replace("\\", "/")) + "?mode=ro"
    con = sqlcipher3.connect(uri, uri=True)
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def leer_playlist(con, num: int):
    fila = con.execute(
        "SELECT ID, Name FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0"
        " AND Name LIKE ?", (f"{num}.%",)).fetchall()
    if len(fila) != 1:
        return None, None, f"la playlist '{num}.%' aparece {len(fila)} veces en Rekordbox"
    pid, nombre = fila[0]
    filas = con.execute(
        """SELECT c.ID, a.Name, c.Title, l.Name, c.Length, c.BPM, k.ScaleName
           FROM djmdSongPlaylist sp
           JOIN djmdContent c ON c.ID = sp.ContentID
           LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
           LEFT JOIN djmdLabel  l ON l.ID = c.LabelID
           LEFT JOIN djmdKey    k ON k.ID = c.KeyID
           WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0
           ORDER BY sp.TrackNo""", (pid,)).fetchall()
    return nombre, filas, None


def leer_drops(con, ids: list[str]) -> dict[str, int]:
    marcas = ",".join("?" * len(ids))
    return {
        str(cid): msec
        for cid, msec in con.execute(
            f"SELECT ContentID, InMsec FROM djmdCue"
            f" WHERE rb_local_deleted=0 AND Kind=4 AND ContentID IN ({marcas})", ids)
    }


def armar_tracks(filas, pool, drops):
    """Cruza playlist + pool + cues y devuelve la lista de tracks del set."""
    tracks, avisos = [], []
    for i, (cid, artista, titulo, sello, largo, bpm_db, key) in enumerate(filas):
        cid = str(cid)
        p = pool.get(cid, {})
        art_raw, tit_raw = artista or "", titulo or ""
        art, tit = norm(art_raw), norm_titulo(tit_raw)
        art = ARTISTA_FIX.get(art, art)
        if art != art_raw.strip() or art_raw != art_raw.strip() or "  " in art_raw:
            avisos.append(f"artista normalizado: {art_raw!r} -> {art!r}")
        if tit != tit_raw.strip() or "  " in tit_raw or tit_raw != tit_raw.strip():
            avisos.append(f"titulo normalizado: {tit_raw!r} -> {tit!r}")

        sel = SELLO_FIX.get(norm(sello), norm(sello))
        fuente_sello = "Rekordbox"
        if not sel and cid in SELLO_EXTERNO:
            sel, fuente_sello = SELLO_EXTERNO[cid]
            avisos.append(f"sello de {art} - {tit}: vacio en la biblioteca, "
                          f"tomado de {SELLO_EXTERNO[cid][1]}")
        elif norm(sello) != sel:
            avisos.append(f"sello normalizado: {norm(sello)!r} -> {sel!r}")

        dur = p.get("dur_seg") or largo
        if p.get("dur_seg") and largo and abs(p["dur_seg"] - largo) > 2:
            avisos.append(f"duracion distinta entre pool y DB en {tit}: "
                          f"{p['dur_seg']}s vs {largo}s (se usa la de la DB)")
            dur = largo
        for sospechoso in TITULOS_SOSPECHOSOS:
            if sospechoso in tit:
                avisos.append(f"posible typo de origen en el titulo: {tit!r} "
                              f"(revisar antes de publicar)")

        tracks.append({
            "n": i + 1, "id": cid, "artista": art, "titulo": tit, "sello": sel,
            "fuente_sello": fuente_sello, "dur": dur,
            "bpm": p.get("bpm") or (bpm_db / 100 if bpm_db else 0),
            "key": p.get("key") or key or "", "energia": p.get("energy"),
            "drop": drops.get(cid, None),
        })
    return tracks, avisos


def calcular_tiempos(tracks):
    t = 0
    for tr in tracks:
        tr["inicio"] = t
        tr["fin"] = t + tr["dur"]
        t += tr["dur"] - BLEND_SEG
    return tracks[-1]["fin"]


def elegir_shorts(tracks):
    """Seis marcas: la mejor de cada sexto del set, por energia, sobre el DROP."""
    elegidos, notas = [], []
    bloques = [tracks[i:i + 3] for i in range(0, len(tracks), 3)][:N_SHORTS]
    usados = set()

    def candidatos(bloque, estricto=True):
        salida = []
        for tr in bloque:
            if tr["n"] in usados or tr["drop"] is None:
                continue
            off = tr["drop"] / 1000
            compas = 4 * 60 / (tr["bpm"] or 122)
            pre, post = BARRA_PRE * compas, BARRA_POST * compas
            if off - pre < 0 or off + post > tr["dur"]:
                continue
            if estricto and off + post > tr["dur"] - BLEND_SEG:
                continue      # el drop cae dentro del blend de salida
            salida.append((tr, off, pre, post))
        return salida

    for bloque in bloques:
        opciones = candidatos(bloque) or candidatos(bloque, estricto=False)
        if not opciones:
            notas.append(f"sin drop utilizable entre los tracks "
                         f"{bloque[0]['n']}-{bloque[-1]['n']}")
            continue
        tr, off, pre, post = max(opciones, key=lambda o: o[0]["energia"] or 0)
        usados.add(tr["n"])
        elegidos.append({
            "track": tr, "drop_rel": off, "pre": pre, "post": post,
            "drop_abs": tr["inicio"] + off,
            "in_abs": tr["inicio"] + off - pre,
            "out_abs": tr["inicio"] + off + post,
        })

    if len(elegidos) < N_SHORTS:
        resto = [c for bloque in bloques for c in candidatos(bloque, estricto=False)]
        resto.sort(key=lambda o: o[0]["energia"] or 0, reverse=True)
        for tr, off, pre, post in resto:
            if len(elegidos) >= N_SHORTS:
                break
            usados.add(tr["n"])
            elegidos.append({
                "track": tr, "drop_rel": off, "pre": pre, "post": post,
                "drop_abs": tr["inicio"] + off,
                "in_abs": tr["inicio"] + off - pre,
                "out_abs": tr["inicio"] + off + post,
            })
        elegidos.sort(key=lambda s: s["drop_abs"])
    return elegidos, notas


def armar_tags(tracks, nicho):
    nombres = []
    for tr in tracks:
        for parte in re.split(r",| & | x | feat\. ", tr["artista"]):
            # El sufijo de pais es de Beatport, no del nombre que se busca.
            parte = norm(re.sub(r"\((AR|BR|CL|COL|MX|PL|UK|US|UY)\)", "", parte))
            if parte and parte not in nombres:
                nombres.append(parte)
    sellos = [s for s, _ in Counter(tr["sello"] for tr in tracks).most_common()]
    tags, largo = [], 0
    for tag in list(nicho) + nombres + sellos:
        extra = len(tag) + (2 if tags else 0)
        if largo + extra > MAX_TAGS_CHARS:
            continue
        tags.append(tag)
        largo += extra
    return tags, largo


def verificar(num, tracks, total, shorts, orden_json, orden_rb):
    fallos = []
    if len(tracks) != TRACKS_ESPERADOS:
        fallos.append(f"{len(tracks)} tracks en la playlist, se esperaban {TRACKS_ESPERADOS}")
    if orden_json is None:
        fallos.append(f"no existe data/set_targets/set_{num}.json")
    elif orden_json != orden_rb:
        fallos.append("el orden de la playlist de Rekordbox no coincide con el del JSON")
    sin_sello = [f"#{t['n']} {t['artista']} - {t['titulo']}" for t in tracks if not t["sello"]]
    if sin_sello:
        fallos.append("tracks sin sello: " + "; ".join(sin_sello))
    prev = -1
    for tr in tracks:
        if not (0 <= tr["inicio"] < total) or tr["inicio"] <= prev and tr["n"] > 1:
            fallos.append(f"timestamp fuera de rango o desordenado en #{tr['n']} {tr['titulo']}")
        if tr["fin"] > total + 1:
            fallos.append(f"#{tr['n']} {tr['titulo']} termina despues del final del mix")
        prev = tr["inicio"]
    for s in shorts:
        tr = s["track"]
        if not (tr["inicio"] <= s["in_abs"] and s["out_abs"] <= tr["fin"]):
            fallos.append(f"short sobre #{tr['n']} {tr['titulo']} cae fuera del track")
        if not (0 <= s["in_abs"] and s["out_abs"] <= total):
            fallos.append(f"short sobre #{tr['n']} {tr['titulo']} cae fuera del mix")
    if len(shorts) != N_SHORTS:
        fallos.append(f"solo {len(shorts)} momentos para shorts (se necesitan {N_SHORTS})")
    return fallos


def render(num, ed, nombre_pl, tracks, total, shorts, tags, tags_len, avisos, notas_shorts):
    L = []
    A = L.append
    A(f"# Video {ed['n_video']} — set {num}")
    A("")
    A(f"**Estado:** listo para grabar. No grabado.  ")
    A(f"**Playlist Rekordbox:** `{nombre_pl}` (carpeta SERIE YOUTUBE — Sonido Argentino)  ")
    A(f"**Duracion proyectada:** {hmmss(total)} — {len(tracks)} tracks, blend de {mmss(BLEND_SEG)}  ")
    energias = [t["energia"] for t in tracks if t["energia"] is not None]
    bpms = [t["bpm"] for t in tracks if t["bpm"]]
    if energias:
        A(f"**Arco:** energia {min(energias):.1f} → {max(energias):.1f}, "
          f"BPM {min(bpms):.0f}-{max(bpms):.0f}, key {tracks[0]['key']} → {tracks[-1]['key']}")
    A("")
    A("---")
    A("")
    A("## Titulo")
    A("")
    A("```")
    A(ed["titulo"])
    A("```")
    A("")
    A(f"Formato corto para playlist y miniatura: `{ed['titulo_corto']}`")
    A("")
    A("## Descripcion")
    A("")
    A("```")
    for parrafo in ed["descripcion"]:
        A(parrafo)
        A("")
    A("TRACKLIST")
    A("")
    for tr in tracks:
        A(f"{hmmss(tr['inicio'])} {tr['artista']} - {tr['titulo']} [{tr['sello']}]")
    A("")
    sellos = [s for s, _ in Counter(t["sello"] for t in tracks).most_common()]
    A("Sellos: " + ", ".join(sellos) + ".")
    A("")
    A("Todos los tracks son de sus autores y sellos. Este set existe para mostrarlos,")
    A("no para reemplazarlos: si algo te gusta, compralo en el sello.")
    A("```")
    A("")
    A("## Tracklist con timestamps")
    A("")
    A(f"Calculados desde las duraciones reales de `data/pool.json` con blend fijo de "
      f"{mmss(BLEND_SEG)}. El timestamp marca **la entrada del track a la mezcla**, no el "
      f"punto donde queda solo. Son proyecciones: hay que verificarlos contra el audio "
      f"despues de grabar.")
    A("")
    A("| # | Entra | Artista | Titulo | Sello | Dur | BPM | Key | E |")
    A("|---|-------|---------|--------|-------|-----|-----|-----|---|")
    for tr in tracks:
        e = f"{tr['energia']:.1f}" if tr["energia"] is not None else "—"
        A(f"| {tr['n']} | {hmmss(tr['inicio'])} | {celda(tr['artista'])} | {celda(tr['titulo'])} | "
          f"{celda(tr['sello'])} | {mmss(tr['dur'])} | {tr['bpm']:.0f} | {tr['key']} | {e} |")
    A("")
    A(f"Final del mix: **{hmmss(total)}**.")
    A("")
    A("## Tags")
    A("")
    A("```")
    A(", ".join(tags))
    A("```")
    A("")
    A(f"{len(tags)} tags, {tags_len} caracteres (el campo de YouTube corta en 500).")
    A("")
    A("## Portada")
    A("")
    A(f"Color de la serie: **{ed['color']}**.")
    A("")
    A(ed["portada"])
    A("")
    A("## Momentos para shorts")
    A("")
    A(f"Seis marcas sacadas del cue DROP de cada track, una por cada sexto del set, "
      f"eligiendo el track de mas energia del bloque. El clip entra {BARRA_PRE} compases "
      f"antes del drop y sale {BARRA_POST} despues: el drop cae en el primer tercio del "
      f"short, que es donde tiene que caer.")
    A("")
    A("| # | In | Drop | Out | Dur | Track |")
    A("|---|----|------|-----|-----|-------|")
    for i, s in enumerate(shorts, 1):
        tr = s["track"]
        A(f"| {i} | {hmmss(s['in_abs'])} | {hmmss(s['drop_abs'])} | {hmmss(s['out_abs'])} | "
          f"{int(round(s['out_abs'] - s['in_abs']))}s | #{tr['n']} {celda(tr['artista'])} - "
          f"{celda(tr['titulo'])} |")
    A("")
    for nota in notas_shorts:
        A(f"- {nota}")
    if notas_shorts:
        A("")
    A("## Verificacion")
    A("")
    A(f"- 18 tracks en la playlist de Rekordbox: **si**")
    A(f"- Orden de Rekordbox igual al de `data/set_targets/set_{num}.json`: **si**")
    A(f"- Todos los tracks con sello: **si**")
    A(f"- Timestamps dentro del track que nombran: **si**")
    sin_drop = [t for t in tracks if t["drop"] is None]
    if sin_drop:
        A(f"- Tracks sin cue DROP (no se usan para shorts): "
          + "; ".join(f"#{t['n']} {t['artista']} - {t['titulo']}" for t in sin_drop))
    if avisos:
        A("")
        A("Correcciones y avisos:")
        for aviso in dict.fromkeys(avisos):
            A(f"- {aviso}")
    A("")
    A("---")
    A("")
    A("Generado por `data/youtube/_generar_paquetes.py`. No publicar sin que Gonzalo lo decida.")
    A("")
    return "\n".join(L)


def procesar(con, num, pool, editorial):
    ed = editorial.get(str(num))
    if ed is None:
        return None, [f"no hay texto editorial para el set {num} en _editorial.json"], None
    nombre_pl, filas, error = leer_playlist(con, num)
    if error:
        return None, [error], None
    ids = [str(f[0]) for f in filas]
    if not ids:
        return None, [f"la playlist {num} esta vacia"], None
    drops = leer_drops(con, ids)
    tracks, avisos = armar_tracks(filas, pool, drops)
    total = calcular_tiempos(tracks)
    shorts, notas_shorts = elegir_shorts(tracks)

    destino_json = ROOT / "data" / "set_targets" / f"set_{num}.json"
    orden_json = None
    if destino_json.exists():
        orden_json = [t["content_id"] for t in
                      json.loads(destino_json.read_text(encoding="utf-8"))["tracks"]]
    fallos = verificar(num, tracks, total, shorts, orden_json, ids)
    if fallos:
        return None, fallos, total
    texto = render(num, ed, nombre_pl, tracks, total, shorts, *armar_tags(tracks, ed["nicho"]),
                   avisos, notas_shorts)
    (OUT_DIR / f"set_{num}.md").write_text(texto, encoding="utf-8")
    return {"num": num, "ed": ed, "total": total, "tracks": len(tracks),
            "avisos": len(set(avisos))}, [], total


def main() -> None:
    numeros = [int(a) for a in sys.argv[1:]] or list(range(80, 90))
    editorial = json.loads((OUT_DIR / "_editorial.json").read_text(encoding="utf-8"))
    pool = {t["id"]: t for t in
            json.loads((ROOT / "data" / "pool.json").read_text(encoding="utf-8"))}
    con = abrir_db()
    ok, fallados = [], []
    for num in numeros:
        res, fallos, total = procesar(con, num, pool, editorial)
        if res:
            ok.append(res)
            print(f"  set {num}: OK — {hmmss(total)}")
        else:
            fallados.append((num, fallos))
            print(f"  set {num}: FALLA — " + " | ".join(fallos))
    if ok:
        escribir_indice(ok, fallados, editorial)
    print(f"\n{len(ok)} paquetes, {len(fallados)} fallados")


def escribir_indice(ok, fallados, editorial):
    por_num = {r["num"]: r for r in ok}
    L = []
    A = L.append
    A("# Paquetes de publicacion — serie \"Sonido Argentino\"")
    A("")
    A("Un archivo por video con titulo, descripcion, tracklist con timestamps, tags,")
    A("concepto de portada y seis momentos para shorts. Nada de esto esta publicado:")
    A("los sets todavia no se grabaron y subir lo decide Gonzalo.")
    A("")
    A(f"Timestamps calculados con blend fijo de {mmss(BLEND_SEG)} sobre las duraciones")
    A("reales de `data/pool.json`. Hay que verificarlos contra el audio despues de grabar.")
    A("")
    A("| # | Set | Titulo | Duracion proyectada | Tracks | Estado | Archivo |")
    A("|---|-----|--------|---------------------|--------|--------|---------|")
    filas = []
    for num_str, ed in sorted(editorial.items(), key=lambda kv: kv[1]["n_video"]):
        num = int(num_str)
        r = por_num.get(num)
        fallo = dict(fallados).get(num)
        if r:
            estado, dur, tracks = "listo para grabar", hmmss(r["total"]), str(r["tracks"])
            archivo = f"[set_{num}.md](set_{num}.md)"
        elif fallo:
            estado = "FALLA VERIFICACION: " + fallo[0]
            dur, tracks, archivo = "—", "—", "—"
        else:
            estado = "pendiente — el set todavia no existe"
            dur, tracks, archivo = "—", "—", "—"
        filas.append(f"| {ed['n_video']} | {num} | {celda(ed['titulo_corto'])} | {dur} | {tracks} "
                     f"| {estado} | {archivo} |")
    L.extend(filas)
    A("")
    if por_num:
        totales = sorted(r["total"] for r in por_num.values())
        A(f"Rango de duraciones: **{hmmss(totales[0])} a {hmmss(totales[-1])}**, "
          f"promedio {hmmss(sum(totales) / len(totales))}.")
        A("")
    A("## Como se regenera")
    A("")
    A("```")
    A("python data/youtube/_generar_paquetes.py        # los diez")
    A("python data/youtube/_generar_paquetes.py 96     # el video 11, cuando el set exista")
    A("```")
    A("")
    A("El texto editorial (titulo, descripcion, portada, nicho) vive en `_editorial.json`;")
    A("todo lo demas sale de Rekordbox y de `data/pool.json` y no se escribe a mano.")
    A("El script abre master.db en modo solo lectura.")
    A("")
    A("## Orden de publicacion")
    A("")
    A("Un video cada dos semanas, un short por semana entre medio. El 01 y el 10 son los")
    A("dos extremos de la serie: el primero define el tono, el ultimo da adonde ir despues.")
    A("")
    (OUT_DIR / "README.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
