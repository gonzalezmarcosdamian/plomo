"""Cue Engine v8 - Algoritmo de cues automático con feedback DJ aplicado.

Layout v8 (9 markers):
- Cue 1 / M1 — Mix-IN First Beat: primer onset absoluto
- Cue 2 / M2 — Bass IN: primer kick sustained
- Cue 3 / M3 — Breakdown: longest kick-absent stretch
- Cue 4 / M4 — DROP: kick re-entry post-breakdown
- Cue 5 — Mix-OUT (no Memory): 16 bars antes del último kick

Sin loops: el engine no escribe ningun cue con OutMsec/BeatLoopSize.
El loop se arma a mano en el CDJ cuando hace falta.
"""
import json
import random
import uuid as uuid_lib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
from scipy.signal import butter, filtfilt

try:
    from pyrekordbox.db6 import DjmdContent, DjmdCue, ContentCue
except ImportError:
    DjmdContent = DjmdCue = ContentCue = None


@dataclass
class CueAnalysis:
    """Resultado del análisis de un track."""
    first_beat: float       # seconds - Cue 1 / M1
    bass_in: float          # seconds - Cue 2 / M2
    breakdown: Optional[float] = None  # Cue 3 / M3
    drop: Optional[float] = None       # Cue 4 / M4
    outro: float = 0.0      # Cue 5 - Mix-OUT


def analyze_track(path: str, known_bpm: float = 122.0) -> Optional[CueAnalysis]:
    """Analyze audio file and detect all cue points (v8 algorithm).

    Args:
        path: Absolute path to audio file
        known_bpm: BPM from ID3 tag or Rekordbox

    Returns:
        CueAnalysis or None if track too short
    """
    if known_bpm <= 0:
        known_bpm = 122.0

    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = len(y) / sr
    bar_duration = 60 / known_bpm * 4
    n_bars = int(duration / bar_duration)
    if n_bars < 8:
        return None

    # === First beat: librosa onset detection ===
    onset_times = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=True)
    first_beat = float(onset_times[0]) if len(onset_times) > 0 else 0.0

    # === Bandpass filters: kick (60-200Hz) + mid (500-3000Hz) ===
    nyq = sr / 2
    b_kick, a_kick = butter(4, [60/nyq, 200/nyq], btype='band')
    b_mid, a_mid = butter(4, [500/nyq, 3000/nyq], btype='band')
    kick = filtfilt(b_kick, a_kick, y)
    mid = filtfilt(b_mid, a_mid, y)

    # Per-bar RMS energy
    bk_raw = np.zeros(n_bars)
    bm_raw = np.zeros(n_bars)
    for i in range(n_bars):
        s = int(i * bar_duration * sr)
        e = min(int((i + 1) * bar_duration * sr), len(y))
        if e > s + 100:
            bk_raw[i] = np.sqrt(np.mean(kick[s:e] ** 2))
            bm_raw[i] = np.sqrt(np.mean(mid[s:e] ** 2))

    def normalize(arr: np.ndarray) -> np.ndarray:
        nz = arr[arr > 0]
        if len(nz) == 0:
            return np.zeros_like(arr)
        return np.nan_to_num(arr / (np.percentile(nz, 95) + 1e-9))

    bk = normalize(bk_raw)
    bm = normalize(bm_raw)

    # === Bass IN: primer bar con kick sustained ===
    bass_in_bar = 0
    for i in range(0, n_bars - 4):
        if all(bk[i:i + 4] > 0.5):
            bass_in_bar = i
            break

    # === Outro: 16 bars antes del último kick ===
    last_kick_bar = n_bars - 1
    for i in range(n_bars - 1, bass_in_bar + 16, -1):
        if bk[i] > 0.5:
            last_kick_bar = i
            break
    outro_bar = max(bass_in_bar + 32, last_kick_bar - 16)

    # === Breakdown + Drop ===
    breakdowns = []
    in_break = False
    bs_idx = 0
    for i in range(bass_in_bar + 16, last_kick_bar - 16):
        if not (bk[i] > 0.5) and not in_break:
            in_break = True
            bs_idx = i
        elif (bk[i] > 0.5) and in_break:
            in_break = False
            if i - bs_idx >= 4:
                breakdowns.append({
                    'start': bs_idx,
                    'end': i,
                    'dur': i - bs_idx,
                    'mid': float(np.mean(bm[bs_idx:i]))
                })
    main_bd = max(breakdowns, key=lambda b: b['dur'] + 5 * b['mid']) if breakdowns else None

    return CueAnalysis(
        first_beat=first_beat,
        bass_in=bass_in_bar * bar_duration,
        breakdown=main_bd['start'] * bar_duration if main_bd else None,
        drop=main_bd['end'] * bar_duration if main_bd else None,
        outro=outro_bar * bar_duration,
    )


def cue_to_dict(c: DjmdCue) -> dict:
    """Serialize DjmdCue for ContentCue.Cues JSON column."""
    return {
        "ID": c.ID, "ContentID": c.ContentID, "InMsec": c.InMsec,
        "InFrame": c.InFrame or 0, "InMpegFrame": 0, "InMpegAbs": 0,
        "OutMsec": c.OutMsec, "OutFrame": c.OutFrame or 0,
        "OutMpegFrame": 0, "OutMpegAbs": 0, "Kind": c.Kind, "Color": c.Color,
        "ContentUUID": c.ContentUUID, "UUID": c.UUID,
        "BeatLoopSize": c.BeatLoopSize, "ActiveLoop": c.ActiveLoop,
        "Comment": c.Comment,
        "created_at": c.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00",
        "updated_at": c.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00",
    }


def apply_cues_v8(db, content_id: str, cues: CueAnalysis) -> int:
    """Insert v8 cues into the DB for a given track.

    Args:
        db: Active Rekordbox6Database session (within RekordboxDB context)
        content_id: DjmdContent.ID
        cues: Analysis result

    Returns:
        Number of markers inserted
    """
    canonical = db.session.query(DjmdContent).filter_by(ID=content_id).first()
    if not canonical:
        return 0

    # Delete existing cues
    for old in db.session.query(DjmdCue).filter(DjmdCue.ContentID == canonical.ID).all():
        db.session.delete(old)

    now = datetime.now()
    new_objs = []

    # Cue specs: (name, time_msec, kind, color)
    cue_specs = [
        ('Mix-IN First Beat', cues.first_beat * 1000, 1, 1),
        ('M-First Beat', cues.first_beat * 1000, 0, -1),
        ('Bass IN', cues.bass_in * 1000, 2, 4),
        ('M-Bass IN', cues.bass_in * 1000, 0, -1),
    ]
    if cues.breakdown is not None:
        cue_specs.extend([
            ('Breakdown', cues.breakdown * 1000, 3, 5),
            ('M-Breakdown', cues.breakdown * 1000, 0, -1),
        ])
    if cues.drop is not None:
        cue_specs.extend([
            ('DROP', cues.drop * 1000, 4, 8),
            ('M-DROP', cues.drop * 1000, 0, -1),
        ])
    cue_specs.append(('Mix-OUT', cues.outro * 1000, 5, 13))

    for name, in_msec, kind, color in cue_specs:
        cue = DjmdCue(
            ID=str(random.randint(100000000, 999999999)),
            ContentID=canonical.ID, InMsec=int(in_msec),
            InFrame=int(in_msec * 0.150), InMpegFrame=0, InMpegAbs=0,
            OutMsec=-1, OutFrame=0, OutMpegFrame=0, OutMpegAbs=0,
            Kind=kind, Color=color, ColorTableIndex=None, ActiveLoop=None,
            Comment=name, BeatLoopSize=None,
            ContentUUID=canonical.UUID, UUID=str(uuid_lib.uuid4()),
            rb_data_status=0, rb_local_data_status=0,
            rb_local_deleted=0, rb_local_synced=0,
            usn=None, rb_local_usn=None,
            created_at=now, updated_at=now,
        )
        db.session.add(cue)
        new_objs.append(cue)

    # Sin loops: el engine no genera ningun cue con OutMsec/BeatLoopSize.
    # Los loops interferian con el automix de Rekordbox; el usuario loopea a mano
    # en el CDJ cuando lo necesita.

    db.session.flush()

    # Update ContentCue summary row
    cc = db.session.query(ContentCue).filter(ContentCue.ContentID == canonical.ID).first()
    if not cc:
        cc = ContentCue(
            ID=str(random.randint(100000000, 999999999)),
            ContentID=canonical.ID,
            Cues=json.dumps([cue_to_dict(c) for c in new_objs]),
            UUID=str(uuid_lib.uuid4()),
            rb_data_status=0, rb_local_data_status=0,
            rb_local_deleted=0, rb_local_synced=0,
            usn=None, rb_local_usn=None,
            created_at=now, updated_at=now,
        )
        db.session.add(cc)
    else:
        cc.Cues = json.dumps([cue_to_dict(c) for c in new_objs])
        cc.rb_cue_count = len(new_objs)
        cc.updated_at = now

    canonical.CueUpdated = '1'
    canonical.updated_at = now
    db.session.commit()
    return len(new_objs)


def apply_cues_v8_direct(con, content_id: int, cues: CueAnalysis) -> int:
    """Write v8 cues directly via sqlcipher3 — safe, no pyrekordbox writes.

    Args:
        con: Active sqlcipher3 connection (PRAGMA key already set)
        content_id: djmdContent.ID as integer
        cues: Analysis result from analyze_track()

    Returns:
        Number of markers written (0 if track not found)
    """
    row = con.execute(
        "SELECT UUID FROM djmdContent WHERE ID=? AND rb_local_deleted=0",
        (str(content_id),)
    ).fetchone()
    if not row:
        return 0
    content_uuid = row[0]

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

    con.execute(
        "UPDATE djmdCue SET rb_local_deleted=1 WHERE ContentID=? AND rb_local_deleted=0",
        (str(content_id),)
    )

    def new_id() -> str:
        return str(random.randint(100_000_000, 999_999_999))

    inserted = []

    def insert_cue(in_msec, out_msec, kind, color, comment, active_loop=None, beat_loop_size=None):
        cue_id = new_id()
        cue_uuid = str(uuid_lib.uuid4())
        in_frame = int(in_msec * 0.150)
        out_frame = int(out_msec * 0.150) if out_msec >= 0 else 0
        con.execute("""
            INSERT INTO djmdCue (
                ID, ContentID, InMsec, InFrame, InMpegFrame, InMpegAbs,
                OutMsec, OutFrame, OutMpegFrame, OutMpegAbs,
                Kind, Color, ColorTableIndex, ActiveLoop,
                Comment, BeatLoopSize, ContentUUID, UUID,
                rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
                usn, rb_local_usn, created_at, updated_at
            ) VALUES (?,?,?,?,0,0, ?,?,0,0, ?,?,NULL,?, ?,?,?,?, 0,0,0,0, NULL,NULL,?,?)
        """, (
            cue_id, str(content_id), int(in_msec), in_frame,
            int(out_msec), out_frame,
            kind, color, active_loop,
            comment, beat_loop_size, content_uuid, cue_uuid,
            now_str, now_str,
        ))
        inserted.append({
            "ID": cue_id, "ContentID": str(content_id),
            "InMsec": int(in_msec), "InFrame": in_frame,
            "InMpegFrame": 0, "InMpegAbs": 0,
            "OutMsec": int(out_msec), "OutFrame": out_frame,
            "OutMpegFrame": 0, "OutMpegAbs": 0,
            "Kind": kind, "Color": color,
            "ContentUUID": content_uuid, "UUID": cue_uuid,
            "BeatLoopSize": beat_loop_size, "ActiveLoop": active_loop,
            "Comment": comment,
            "created_at": now_iso, "updated_at": now_iso,
        })

    cue_specs = [
        (cues.first_beat * 1000, -1, 1,  1,  'Mix-IN First Beat', None, None),
        (cues.first_beat * 1000, -1, 0, -1,  'M-First Beat',      None, None),
        (cues.bass_in * 1000,    -1, 2,  4,  'Bass IN',           None, None),
        (cues.bass_in * 1000,    -1, 0, -1,  'M-Bass IN',         None, None),
    ]
    if cues.breakdown is not None:
        cue_specs += [
            (cues.breakdown * 1000, -1, 3, 5, 'Breakdown',   None, None),
            (cues.breakdown * 1000, -1, 0,-1, 'M-Breakdown', None, None),
        ]
    if cues.drop is not None:
        cue_specs += [
            (cues.drop * 1000, -1, 4, 8, 'DROP',   None, None),
            (cues.drop * 1000, -1, 0,-1, 'M-DROP', None, None),
        ]
    cue_specs.append((cues.outro * 1000, -1, 5, 13, 'Mix-OUT', None, None))

    for in_ms, out_ms, kind, color, comment, al, bls in cue_specs:
        insert_cue(in_ms, out_ms, kind, color, comment, al, bls)

    # Sin loops: ningun cue lleva OutMsec/BeatLoopSize. Ver apply_cues_v8.

    cue_json = json.dumps(inserted)

    existing_cc = con.execute(
        "SELECT ID FROM ContentCue WHERE ContentID=? AND rb_local_deleted=0",
        (str(content_id),)
    ).fetchone()
    if existing_cc:
        con.execute(
            "UPDATE ContentCue SET Cues=?, updated_at=? WHERE ID=?",
            (cue_json, now_str, existing_cc[0])
        )
    else:
        con.execute("""
            INSERT INTO ContentCue (
                ID, ContentID, Cues, UUID,
                rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
                usn, rb_local_usn, created_at, updated_at
            ) VALUES (?,?,?,?, 0,0,0,0, NULL,NULL,?,?)
        """, (new_id(), str(content_id), cue_json, str(uuid_lib.uuid4()), now_str, now_str))

    con.execute(
        "UPDATE djmdContent SET CueUpdated='1', updated_at=? WHERE ID=?",
        (now_str, str(content_id))
    )

    return len(inserted)
