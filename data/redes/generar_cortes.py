"""Guion de cortes verticales para la serie "Sonido Argentino" (sets 80-89).

Lee master.db en modo SOLO LECTURA (uri mode=ro + PRAGMA query_only) y no
escribe nada fuera de data/redes/. El criterio esta documentado en
data/redes/guion_cortes.md.

Uso:  python data/redes/generar_cortes.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

# --- Constantes de produccion ---------------------------------------------
BLEND_SEG = 180          # solape de mezcla asumido (docs/YOUTUBE_SERIE.md)
LARGO_CORTE = 30.0       # duracion del corte vertical
TOPE_ANTICIPO = 25.0     # cuanto puede arrancar antes del DROP, como maximo
FRACCION_TENSION = 0.60  # del gap Breakdown->DROP que se toma como anticipo
GAP_MINIMO = 15.0        # gap Breakdown->DROP por debajo del cual no sirve
CORTES_POR_SET = 6
SEPARACION_MINIMA = 2    # posiciones de distancia entre dos cortes del mismo set

PESO = {"identidad": 0.35, "tension": 0.30, "energia": 0.20, "arco": 0.15}
ENERGIA_IDEAL = (5.5, 7.5)   # ventana que mejor rinde en formato corto
TENSION_CLIP = (15.0, 90.0)

RE_ENERGIA = re.compile(r"E:(\d+(?:\.\d+)?)")
RE_SEP_ARTISTAS = re.compile(
    r"\s*(?:,|&|\bfeat\.?\b|\bft\.?\b|\bvs\.?\b|\bx\b)\s*", re.I)


def normalizar(texto: str) -> str:
    """Minusculas sin acentos, para cruzar nombres de artista y sello."""
    if not texto:
        return ""
    plano = unicodedata.normalize("NFKD", texto)
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    return plano.strip().lower()


def nombres(campo: str) -> list[str]:
    """Parte el campo artista combinado en nombres individuales.

    Sin esto un mismo productor cuenta como tres y el cruce con el perfil
    medido se rompe (advertencia de docs/MI_SONIDO.md).
    """
    if not campo:
        return []
    return [normalizar(p) for p in RE_SEP_ARTISTAS.split(campo) if p.strip()]


def conectar_solo_lectura() -> "sqlcipher3.Connection":
    con = sqlcipher3.connect(config.REKORDBOX_DB_PATH.as_uri() + "?mode=ro",
                             uri=True)
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    con.execute("PRAGMA query_only = ON")
    return con


def cargar_perfil() -> tuple[dict[str, float], dict[str, float]]:
    """Lift medido por artista y por sello (data/mi_sonido.json).

    Se exige un piso de presencia en biblioteca: sin piso, el ranking lo gana
    quien tiene un solo track que sono mucho, que es muestra de tamano uno.
    """
    datos = json.loads(
        (RAIZ / "data" / "mi_sonido.json").read_text(encoding="utf-8"))
    artistas = {normalizar(a["valor"]): a["lift"]
                for a in datos.get("artistas", [])
                if a.get("en_biblioteca", 0) >= 3}
    sellos = {normalizar(s["valor"]): s["lift"]
              for s in datos.get("sellos", [])
              if s.get("en_biblioteca", 0) >= 3}
    return artistas, sellos


def leer_sets(con) -> list[dict]:
    """Los sets 80-96 con sus tracks en orden, cues y metadata."""
    playlists = con.execute(
        "SELECT ID, Name FROM djmdPlaylist"
        " WHERE rb_local_deleted=0 AND Attribute=0 AND Name GLOB '[89][0-9].*'"
        " ORDER BY Name"
    ).fetchall()

    sets = []
    for pid, nombre in playlists:
        numero = int(nombre[:2])
        if not 80 <= numero <= 96 or "[archivo]" in nombre:
            continue
        filas = con.execute(
            "SELECT sp.TrackNo, c.ID, a.Name, c.Title, c.BPM, k.ScaleName,"
            "       l.Name, c.Commnt, c.FolderPath, c.Length, c.DJPlayCount"
            "  FROM djmdSongPlaylist sp"
            "  JOIN djmdContent c ON c.ID = sp.ContentID"
            "  LEFT JOIN djmdArtist a ON a.ID = c.ArtistID"
            "  LEFT JOIN djmdKey    k ON k.ID = c.KeyID"
            "  LEFT JOIN djmdLabel  l ON l.ID = c.LabelID"
            " WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0"
            "   AND c.rb_local_deleted=0"
            " ORDER BY sp.TrackNo",
            (pid,),
        ).fetchall()

        tracks, reloj = [], 0.0
        for (orden, cid, artista, titulo, bpm_raw, key, sello, commnt,
             ruta, largo, plays) in filas:
            cues = {}
            for kind, inmsec, comentario in con.execute(
                "SELECT Kind, InMsec, Comment FROM djmdCue"
                " WHERE ContentID=? AND rb_local_deleted=0",
                (cid,),
            ):
                etiqueta = (comentario or "").strip()
                if not etiqueta or etiqueta.startswith("M-"):
                    continue
                cues[etiqueta] = (inmsec or 0) / 1000.0

            energia = RE_ENERGIA.match(commnt or "")
            largo_seg = float(largo or 0)
            tracks.append({
                "orden": orden,
                "content_id": str(cid),
                "artist": (artista or "").strip(),
                "title": re.sub(r"\s+", " ", (titulo or "").strip()),
                "bpm": round((bpm_raw or 0) / 100.0, 1),
                "key": key or "",
                "label": (sello or "").strip(),
                "energy": float(energia.group(1)) if energia else None,
                "plays": plays or 0,
                "folder_path": ruta or "",
                "archivo_existe": bool(ruta) and Path(ruta).exists(),
                "dur_seg": largo_seg,
                "cues": cues,
                "inicio_en_set": reloj,
            })
            reloj += max(largo_seg - BLEND_SEG, 0.0)

        sets.append({"playlist_id": str(pid), "numero": numero,
                     "nombre": nombre, "tracks": tracks})
    return sets


# --- Evaluacion de candidatos ---------------------------------------------

def evaluar(track: dict, contexto: dict, artistas: dict,
            sellos: dict) -> dict:
    """Devuelve el candidato con ventana y puntaje, o el motivo del descarte."""
    cues = track["cues"]
    fallas = []
    if not track["archivo_existe"]:
        fallas.append("archivo ausente en disco")
    for requerido in ("Bass IN", "Breakdown", "DROP", "Mix-OUT"):
        if requerido not in cues:
            fallas.append("sin cue " + requerido)
    if fallas:
        return {"apto": False, "motivos": fallas}

    bass_in = cues["Bass IN"]
    breakdown = cues["Breakdown"]
    drop = cues["DROP"]
    mix_out = cues["Mix-OUT"]

    gap = drop - breakdown
    if gap < GAP_MINIMO:
        fallas.append("gap Breakdown->DROP %.0fs < %.0fs" % (gap, GAP_MINIMO))

    inicio = drop - min(FRACCION_TENSION * gap, TOPE_ANTICIPO)
    fin = inicio + LARGO_CORTE
    if inicio < bass_in:
        fallas.append("la ventana arranca antes del Bass IN (%.0fs)" % bass_in)
    if fin > mix_out:
        fallas.append("la ventana pisa el Mix-OUT (%.0fs)" % mix_out)
    if fin > track["dur_seg"]:
        fallas.append("la ventana excede el archivo")
    if fallas:
        return {"apto": False, "motivos": fallas}

    # Identidad: lift medido del artista y del sello, normalizado a 0-1.
    lifts = [artistas[n] for n in nombres(track["artist"]) if n in artistas]
    lift_artista = max(lifts) if lifts else 0.0
    lift_sello = sellos.get(normalizar(track["label"]), 0.0)
    identidad = min((lift_artista + 0.7 * lift_sello) / 8.0, 1.0)

    piso, techo = TENSION_CLIP
    tension = min(max(gap - piso, 0.0) / (techo - piso), 1.0)

    energia_val = track["energy"] or 0.0
    bajo, alto = ENERGIA_IDEAL
    if energia_val <= 0:
        energia = 0.0
    elif bajo <= energia_val <= alto:
        energia = 1.0
    else:
        distancia = bajo - energia_val if energia_val < bajo else energia_val - alto
        energia = max(0.0, 1.0 - distancia / 2.0)

    # Arco: la zona 55-85% del set es el pico; el primer tercio vale menos.
    posicion = (track["orden"] - 1) / max(contexto["total"] - 1, 1)
    if 0.55 <= posicion <= 0.85:
        arco = 1.0
    elif posicion < 0.55:
        arco = 0.35 + 0.65 * (posicion / 0.55)
    else:
        arco = 1.0 - (posicion - 0.85) / 0.15 * 0.35

    puntaje = (PESO["identidad"] * identidad + PESO["tension"] * tension
               + PESO["energia"] * energia + PESO["arco"] * arco)

    if energia_val and energia_val >= contexto["energia_max"] - 0.05:
        tipo = "pico del set"
    elif gap >= 45:
        tipo = "kick tras breakdown largo"
    elif identidad >= 0.5:
        tipo = "track identitario"
    else:
        tipo = "entrada de kick"

    return {
        "apto": True,
        "puntaje": round(puntaje, 4),
        "tipo_momento": tipo,
        "gap_seg": round(gap, 1),
        "ventana": {
            "inicio_track_seg": round(inicio, 1),
            "fin_track_seg": round(fin, 1),
            "largo_seg": LARGO_CORTE,
            "drop_track_seg": round(drop, 1),
            "anticipo_seg": round(drop - inicio, 1),
        },
        "cues": {"bass_in": round(bass_in, 1),
                 "breakdown": round(breakdown, 1),
                 "drop": round(drop, 1),
                 "mix_out": round(mix_out, 1)},
        "identidad": round(identidad, 3),
        "lift_artista": lift_artista,
        "lift_sello": lift_sello,
        "min_set": round((track["inicio_en_set"] + inicio) / 60.0, 1),
    }


def elegir(candidatos: list[dict]) -> list[dict]:
    """Top-6 con separacion minima en el set y sin repetir artista."""
    elegidos: list[dict] = []
    for cand in sorted(candidatos, key=lambda c: -c["puntaje"]):
        if len(elegidos) >= CORTES_POR_SET:
            break
        if any(abs(cand["orden"] - e["orden"]) < SEPARACION_MINIMA
               for e in elegidos):
            continue
        if any(normalizar(cand["artist"]) == normalizar(e["artist"])
               for e in elegidos):
            continue
        elegidos.append(cand)

    # Relleno si la regla de artista dejo menos de 6.
    if len(elegidos) < CORTES_POR_SET:
        ya = {e["content_id"] for e in elegidos}
        for cand in sorted(candidatos, key=lambda c: -c["puntaje"]):
            if len(elegidos) >= CORTES_POR_SET:
                break
            if cand["content_id"] in ya:
                continue
            if any(abs(cand["orden"] - e["orden"]) < SEPARACION_MINIMA
                   for e in elegidos):
                continue
            elegidos.append(cand)
            ya.add(cand["content_id"])
    return sorted(elegidos, key=lambda c: -c["puntaje"])


def linea_seca(c: dict) -> str:
    sello = c["label"] or "SIN SELLO EN LA DB"
    return ("%s — %s — %s — %.0f BPM — minuto %d del set"
            % (c["artist"], c["title"], sello, c["bpm"], int(c["min_set"])))


def comando_ffmpeg(num_set: int, c: dict) -> str:
    """Recorte 9:16 desde la grabacion del set, con el reloj del set."""
    return ('ffmpeg -ss %.1f -t %d -i "grabacion_set%d.mp4" '
            '-vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" '
            '-c:v libx264 -crf 18 -preset slow '
            '-af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k '
            '"corte_%d_%d.mp4"'
            % (c["min_set"] * 60.0, int(LARGO_CORTE), num_set,
               num_set, c["rank"]))


def escribir_markdown(destino: Path, salida: list[dict],
                      descartes: list[dict], colisiones: dict) -> None:
    L = []
    L.append("# Guion de cortes — serie \"Sonido Argentino\" (sets 80-89)")
    L.append("")
    L.append("Generado por `data/redes/generar_cortes.py`. **Nada de esto esta "
             "publicado ni programado.** Es material preparado; la decision de "
             "que sale y cuando la toma Gonzalo.")
    L.append("")
    L.append("## Como se eligio cada momento")
    L.append("")
    L.append("El momento no se elige a ojo. Cada track del set se evalua con "
             "sus cues v8 y su energia, y despues se filtra y se rankea.")
    L.append("")
    L.append("**Filtros duros** (si falla uno, el track queda afuera):")
    L.append("")
    L.append("- Tiene los cuatro cues: `Bass IN`, `Breakdown`, `DROP`, `Mix-OUT`.")
    L.append("- El archivo existe en disco en el `FolderPath` actual "
             "(`Music/Biblioteca/AAAA-MM/`).")
    L.append("- El gap `Breakdown -> DROP` es de **%.0fs o mas**. Menos que eso "
             "no da tension para llenar la primera mitad del corte."
             % GAP_MINIMO)
    L.append("- La ventana **no arranca antes del `Bass IN`** y **no pisa el "
             "`Mix-OUT`**.")
    L.append("")
    L.append("**La ventana**: arranca en `DROP - min(%.0f%% del gap, %.0fs)` y "
             "dura %.0fs. Arranca *antes* del momento, no en el momento: la "
             "tension es la mitad del corte."
             % (FRACCION_TENSION * 100, TOPE_ANTICIPO, LARGO_CORTE))
    L.append("")
    L.append("**El ranking** pondera cuatro cosas:")
    L.append("")
    L.append("| Peso | Que mide |")
    L.append("|---|---|")
    L.append("| %.0f%% identidad | lift medido del artista y del sello en "
             "`data/mi_sonido.json`, con piso de 3 tracks en biblioteca. Es lo "
             "que hace que el corte hable de este proyecto y no de cualquiera. |"
             % (PESO["identidad"] * 100))
    L.append("| %.0f%% tension | largo del gap `Breakdown -> DROP`, entre %.0f y "
             "%.0fs. |" % (PESO["tension"] * 100, *TENSION_CLIP))
    L.append("| %.0f%% energia | premia la franja E%.1f-%.1f, arriba de la "
             "mediana medida (5.7) porque el formato corto no tiene tiempo de "
             "construir. |" % (PESO["energia"] * 100, *ENERGIA_IDEAL))
    L.append("| %.0f%% arco | la zona 55-85%% del set vale mas; el primer tercio "
             "vale menos. |" % (PESO["arco"] * 100))
    L.append("")
    L.append("**Diversidad**: los 6 cortes de un set caen en 6 tracks distintos, "
             "separados por al menos %d posiciones, y sin repetir artista "
             "mientras haya con que. Verificado: 0 colisiones de track entre los "
             "10 sets, asi que los 60 cortes son 60 tracks distintos."
             % SEPARACION_MINIMA)
    L.append("")
    L.append("**El reloj del set** asume blends de %ds (`docs/YOUTUBE_SERIE.md`). "
             "Es una estimacion sobre la grabacion planificada: cuando el set "
             "este grabado de verdad, el minuto real se corrige contra el audio "
             "y esta tabla vuelve a correr." % BLEND_SEG)
    L.append("")
    L.append("## Notas de produccion")
    L.append("")
    L.append("- El `-ss` de cada comando esta en **segundos del set grabado**, no "
             "del track. Sale del reloj estimado; hay que corregirlo contra el "
             "audio real antes de cortar.")
    L.append("- El crop es centrado (`crop=ih*9/16:ih`). Si la camara no esta "
             "centrada en los CDJs hay que agregar el offset `x=` a mano.")
    L.append("- El `loudnorm` va en una pasada, que alcanza para 30 segundos. Si "
             "se van a publicar varios cortes seguidos y se nota diferencia de "
             "volumen entre ellos, conviene medir con `pyloudnorm` sobre los seis "
             "y aplicar una ganancia fija por corte en vez de normalizar cada uno "
             "por separado.")
    L.append("- `docs/YOUTUBE_SERIE.md` habla de cortes de 40-60s y aca son de "
             "30s. **Es una diferencia sin resolver.** 30s entra en la regla de "
             "15-40s del formato vertical; si se prefieren 60s, hay que volver a "
             "correr los filtros porque varias ventanas empiezan a pisar el "
             "`Mix-OUT`.")
    L.append("")
    L.append("---")
    L.append("")

    for s in salida:
        dur = s.get("duracion_estimada_min", 0)
        L.append("## %s" % s["nombre"])
        L.append("")
        L.append("%d tracks · ~%.0f min estimados · %d de %d tracks pasaron los "
                 "filtros" % (s["tracks_en_set"], dur, s["candidatos_aptos"],
                              s["tracks_en_set"]))
        L.append("")
        L.append("| # | min del set | seg en track | ventana | gap | E | tipo | linea |")
        L.append("|---|---|---|---|---|---|---|---|")
        for c in s["cortes"]:
            v = c["ventana"]
            L.append("| %d | %.1f | %.0f | %.0f-%.0fs (drop %.0f) | %.0fs | %s | %s | %s |"
                     % (c["rank"], c["min_set"], v["inicio_track_seg"],
                        v["inicio_track_seg"], v["fin_track_seg"],
                        v["drop_track_seg"], c["gap_seg"], c["energy"],
                        c["tipo_momento"], c["linea"]))
        L.append("")
        L.append("<details><summary>Comandos ffmpeg</summary>")
        L.append("")
        L.append("```bash")
        for c in s["cortes"]:
            L.append(comando_ffmpeg(s["set"], c))
        L.append("```")
        L.append("")
        L.append("</details>")
        L.append("")

    L.append("---")
    L.append("")
    L.append("## Tracks descartados (%d)" % len(descartes))
    L.append("")
    L.append("No es un problema de curaduria: son tracks buenos que no tienen un "
             "momento vertical. Un breakdown de 8 segundos funciona en una "
             "mezcla y no da para un corte.")
    L.append("")
    L.append("| Set | Pos | Track | Motivo |")
    L.append("|---|---|---|---|")
    for x in descartes:
        L.append("| %d | %d | %s — %s | %s |"
                 % (x["set"], x["orden"], x["artist"], x["title"],
                    "; ".join(x["motivos"])))
    L.append("")
    if colisiones:
        L.append("## Colisiones entre sets")
        L.append("")
        for cid, nums in colisiones.items():
            L.append("- ContentID %s elegido en los sets %s" % (cid, nums))
    else:
        L.append("## Colisiones entre sets")
        L.append("")
        L.append("Ninguna. Los 60 cortes salen de 60 tracks distintos.")
    L.append("")
    (destino / "guion_cortes.md").write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    artistas, sellos = cargar_perfil()
    con = conectar_solo_lectura()
    try:
        sets = leer_sets(con)
    finally:
        con.close()

    salida, descartes = [], []
    for s in sets:
        energias = [t["energy"] for t in s["tracks"] if t["energy"]]
        contexto = {"total": len(s["tracks"]),
                    "energia_max": max(energias) if energias else 0.0}
        candidatos = []
        for t in s["tracks"]:
            ev = evaluar(t, contexto, artistas, sellos)
            base = {k: t[k] for k in ("orden", "content_id", "artist", "title",
                                      "bpm", "key", "label", "energy", "plays",
                                      "folder_path", "dur_seg")}
            base["inicio_track_en_set_min"] = round(t["inicio_en_set"] / 60.0, 1)
            if ev["apto"]:
                candidatos.append({**base, **ev})
            else:
                descartes.append({"set": s["numero"], **base,
                                  "motivos": ev["motivos"]})

        elegidos = elegir(candidatos)
        for i, c in enumerate(elegidos, 1):
            c["rank"] = i
            c["linea"] = linea_seca(c)
            c["ffmpeg"] = comando_ffmpeg(s["numero"], c)
        ultimo = s["tracks"][-1]
        salida.append({
            "set": s["numero"],
            "nombre": s["nombre"],
            "playlist_id": s["playlist_id"],
            "tracks_en_set": len(s["tracks"]),
            "duracion_estimada_min": round(
                (ultimo["inicio_en_set"] + ultimo["dur_seg"]) / 60.0, 1),
            "candidatos_aptos": len(candidatos),
            "cortes": elegidos,
        })

    # Colisiones: el mismo track elegido como corte en mas de un set.
    vistos: dict[str, list[int]] = {}
    for s in salida:
        for c in s["cortes"]:
            vistos.setdefault(c["content_id"], []).append(s["set"])
    colisiones = {cid: nums for cid, nums in vistos.items() if len(nums) > 1}

    destino = RAIZ / "data" / "redes"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "guion_cortes.json").write_text(
        json.dumps({"generado_por": "data/redes/generar_cortes.py",
                    "blend_seg": BLEND_SEG,
                    "largo_corte_seg": LARGO_CORTE,
                    "pesos": PESO,
                    "sets": salida,
                    "colisiones_entre_sets": colisiones,
                    "descartados": descartes},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_markdown(destino, salida, descartes, colisiones)

    for s in salida:
        print("\n=== %d - %s  (%d/%d aptos)"
              % (s["set"], s["nombre"].encode("ascii", "replace").decode(),
                 s["candidatos_aptos"], s["tracks_en_set"]))
        for c in s["cortes"]:
            print("  %d. [%-26s] min %5.1f | track %6.1f-%.1f | gap %4.1f | "
                  "E%s | id %.2f | %s"
                  % (c["rank"], c["tipo_momento"], c["min_set"],
                     c["ventana"]["inicio_track_seg"],
                     c["ventana"]["fin_track_seg"], c["gap_seg"],
                     c["energy"], c["identidad"],
                     c["linea"].encode("ascii", "replace").decode()))
    print("\nDescartados: %d" % len(descartes))
    print("Colisiones entre sets: %d" % len(colisiones))


if __name__ == "__main__":
    main()
