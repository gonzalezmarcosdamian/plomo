"""Lo que el motor de mezcla necesita saber de cada tema: audio, grilla, cues y estructura medida.

POR QUE MEDIR LA ESTRUCTURA Y NO USAR LOS CUES
----------------------------------------------
"Los cues no son 100% precisos" (el DJ, 2026-10-01). Los cues los puso
`cue_engine.py` con heuristicas sobre la envolvente; una transicion que entra en
el compas equivocado se escucha enseguida. Aca la estructura se mide compas por
compas SOBRE LA GRILLA DE REKORDBOX (que el DJ usa y corrige en el CDJ): en cada
compas, si hay bombo en los cuatro tiempos y si hay bajo sostenido entre ellos.
De eso salen la entrada del bajo, el breakdown y el ultimo bombo, y se comparan
con los cues: donde no coinciden, manda lo medido y la diferencia se reporta.

Solo lectura: la DB se abre con `mode=ro` y los ANLZ se parsean, no se escriben.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import librosa
import numpy as np
import sqlcipher3
from scipy.signal import butter, sosfilt

from plomo import config

SR_ANALISIS = 22050
COMPASES_FRASE = 8            # los cambios caen en multiplos de 8 compases
UMBRAL_BOMBO = 0.55           # fraccion del p90 del golpe de grave en el tiempo
UMBRAL_BAJO = 0.35            # fraccion del p90 del grave entre tiempos
KIND_CUE = {1: "mix_in", 2: "bass_in", 3: "breakdown", 4: "drop", 5: "mix_out", 6: "mix_out"}


@dataclass(frozen=True)
class Tema:
    content_id: str
    artista: str
    titulo: str
    archivo: Path
    bpm: float
    key: str
    duracion: float
    beats: np.ndarray           # tiempo de cada beat (s)
    numero: np.ndarray          # 1..4 dentro del compas
    cues: dict[str, float] = field(default_factory=dict)   # nombre -> segundos

    @property
    def compases(self) -> np.ndarray:
        """Tiempo de cada primer tiempo de compas."""
        return self.beats[self.numero == 1]


def _abrir_db():
    uri = "file:///" + quote(str(config.REKORDBOX_DB_PATH).replace("\\", "/")) + "?mode=ro"
    con = sqlcipher3.connect(uri, uri=True, timeout=5)
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def _grilla(analysis_path: str) -> tuple[np.ndarray, np.ndarray]:
    from pyrekordbox.anlz import AnlzFile
    ruta = Path(os.environ["APPDATA"]) / "Pioneer" / "rekordbox" / "share" / analysis_path.lstrip("/")
    tag = AnlzFile.parse_file(str(ruta)).get_tag("PQTZ")
    return tag.get_times().astype(float), tag.get_beats().astype(int)


TARGETS = Path(__file__).resolve().parents[2] / "data" / "set_targets"


def leer_set(prefijo: str) -> list[Tema]:
    """Los temas del set `prefijo`, en orden: la playlist `prefijo.` de Rekordbox si existe, y si
    no el target que arma el selector (data/set_targets/set_NNN.json).

    El target existe para poder mezclar un set propuesto antes de escribirlo en Rekordbox: el
    2026-10-19 la Session 03 estaba lista para mezclar y otra sesion tenia la base tomada."""
    con = _abrir_db()
    fila = con.execute("select ID from djmdPlaylist where Name like ? and rb_local_deleted = 0",
                       (f"{prefijo}.%",)).fetchone()
    if fila:
        ids = [cid for (cid,) in con.execute("select ContentID from djmdSongPlaylist where PlaylistID = ? "
                                              "and rb_local_deleted = 0 order by TrackNo", (fila[0],))]
    else:
        objetivo = TARGETS / f"set_{prefijo}.json"
        if not objetivo.exists():
            raise SystemExit(f"no hay playlist {prefijo}. ni {objetivo.name}")
        ids = [t["content_id"] for t in json.loads(objetivo.read_text(encoding="utf-8"))["tracks"]]
    return [_tema(con, cid) for cid in ids]


def _tema(con: sqlcipher3.Connection, cid: str) -> Tema:
    fila = con.execute("""select c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Length, c.FolderPath, c.AnalysisDataPath
                          from djmdContent c left join djmdArtist a on a.ID = c.ArtistID
                          left join djmdKey k on k.ID = c.KeyID
                          where c.ID = ? and c.rb_local_deleted = 0""", (cid,)).fetchone()
    if not fila:
        raise SystemExit(f"el tema {cid} no esta en la biblioteca")
    cid, art, tit, bpm, key, ln, fp, anlz = fila
    beats, numero = _grilla(anlz)
    cues = {}
    for kind, ms in con.execute("select Kind, InMsec from djmdCue where ContentID = ? and rb_local_deleted = 0 "
                                "and Kind > 0", (cid,)):
        if kind in KIND_CUE:
            cues[KIND_CUE[kind]] = ms / 1000
    return Tema(str(cid), (art or "").strip(), (tit or "").strip(), Path(fp), bpm / 100, key or "",
                float(ln), beats, numero, cues)


@dataclass(frozen=True)
class Estructura:
    bombo: np.ndarray           # por compas, fraccion de tiempos con golpe de grave
    bajo: np.ndarray            # por compas, grave sostenido entre tiempos (0..1)
    bass_in: int                # primer compas con bombo y bajo llenos (en frase)
    fin_bombo: int              # compas donde termina la frase del ultimo bombo (exclusivo)
    breakdown: tuple[int, int] | None   # el tramo sin bombo mas largo en el medio (en frase)
    drop: int | None            # vuelta del bombo despues del breakdown (en frase)
    crudo: dict[str, int] = field(default_factory=dict)   # lo medido antes de llevarlo a frase

    def mix_out(self) -> int:
        """16 compases antes de que termine el bombo: donde empieza el ultimo tramo con bombo."""
        return max(self.bass_in, self.fin_bombo - 16)


def _frase_cercana(compas: int) -> int:
    return int(round(compas / COMPASES_FRASE)) * COMPASES_FRASE


def _a_frase(compas: int, hacia_abajo: bool = True) -> int:
    resto = compas % COMPASES_FRASE
    if resto == 0:
        return compas
    return compas - resto if hacia_abajo else compas + COMPASES_FRASE - resto


def medir(tema: Tema, audio: np.ndarray | None = None) -> Estructura:
    """Bombo y bajo por compas sobre la grilla de Rekordbox."""
    y = audio if audio is not None else librosa.load(str(tema.archivo), sr=SR_ANALISIS, mono=True)[0]
    grave = sosfilt(butter(4, [35, 130], "bandpass", fs=SR_ANALISIS, output="sos"), y)
    env = np.abs(grave)
    beats = tema.beats[tema.beats < len(y) / SR_ANALISIS - 0.6]
    numero = tema.numero[:len(beats)]
    # golpe: pico de grave en los 60 ms siguientes al tiempo; bajo: grave medio en el
    # tramo entre 35% y 85% del intervalo, donde el bombo ya se apago
    paso = np.median(np.diff(beats))
    golpe, entre = [], []
    for t in beats:
        i = int(t * SR_ANALISIS)
        golpe.append(env[i: i + int(0.06 * SR_ANALISIS)].max(initial=0))
        a, b = int((t + 0.35 * paso) * SR_ANALISIS), int((t + 0.85 * paso) * SR_ANALISIS)
        entre.append(np.sqrt(np.mean(grave[a:b] ** 2)) if b > a else 0)
    golpe, entre = np.array(golpe), np.array(entre)
    hay_golpe = golpe > UMBRAL_BOMBO * np.percentile(golpe, 90)
    nivel_bajo = np.clip(entre / (np.percentile(entre, 90) + 1e-9), 0, 1)
    inicios = np.where(numero == 1)[0]
    bombo = np.array([hay_golpe[i:i + 4].mean() for i in inicios])
    bajo = np.array([nivel_bajo[i:i + 4].mean() for i in inicios])
    lleno = (bombo >= 0.75) & (bajo >= UMBRAL_BAJO)
    llenos = np.where(lleno)[0]
    if len(llenos) == 0:
        raise ValueError(f"{tema.titulo}: no se encontro ningun compas con bombo y bajo")
    bass_in = _a_frase(int(llenos[0]), hacia_abajo=False)
    ultimo = int(np.where(bombo >= 0.75)[0][-1])
    # breakdown: el tramo mas largo sin bombo entre la entrada del bajo y el final
    sin = (bombo < 0.5).astype(int)
    mejor, inicio, corrida = None, None, 0
    for c in range(bass_in, ultimo):
        if sin[c]:
            inicio = c if corrida == 0 else inicio
            corrida += 1
            if corrida >= 8 and (mejor is None or corrida > mejor[1] - mejor[0]):
                mejor = (inicio, c + 1)
        else:
            corrida = 0
    crudo = {"bass_in": int(llenos[0]), "ultimo_bombo": ultimo}
    if mejor:
        crudo.update(breakdown=mejor[0], drop=mejor[1])
        mejor = (_frase_cercana(mejor[0]), _frase_cercana(mejor[1]))
    fin = min(_a_frase(ultimo + 1, hacia_abajo=False), len(bombo))
    return Estructura(bombo, bajo, bass_in, fin, mejor, mejor[1] if mejor else None, crudo)


def en_compases(tema: Tema, segundos: float) -> float:
    """Posicion en compases (fraccionaria) de un tiempo del tema."""
    c = tema.compases
    return float(np.interp(segundos, c, np.arange(len(c))))
