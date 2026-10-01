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


def leer_set(prefijo: str) -> list[Tema]:
    """Los temas de la playlist `prefijo.` en el orden de Rekordbox, sin filas borradas."""
    con = _abrir_db()
    fila = con.execute("select ID from djmdPlaylist where Name like ? and rb_local_deleted = 0",
                       (f"{prefijo}.%",)).fetchone()
    if not fila:
        raise SystemExit(f"no hay playlist {prefijo}.")
    temas = []
    for cid, art, tit, bpm, key, ln, fp, anlz in con.execute(
            """select c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Length, c.FolderPath, c.AnalysisDataPath
               from djmdSongPlaylist sp join djmdContent c on c.ID = sp.ContentID
               left join djmdArtist a on a.ID = c.ArtistID left join djmdKey k on k.ID = c.KeyID
               where sp.PlaylistID = ? and sp.rb_local_deleted = 0 order by sp.TrackNo""", (fila[0],)):
        beats, numero = _grilla(anlz)
        cues = {}
        for kind, ms in con.execute("select Kind, InMsec from djmdCue where ContentID = ? and rb_local_deleted = 0 "
                                    "and Kind > 0", (cid,)):
            if kind in KIND_CUE:
                cues[KIND_CUE[kind]] = ms / 1000
        temas.append(Tema(str(cid), (art or "").strip(), (tit or "").strip(), Path(fp), bpm / 100, key or "",
                          float(ln), beats, numero, cues))
    return temas


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
