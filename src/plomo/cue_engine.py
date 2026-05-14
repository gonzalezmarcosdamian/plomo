"""Cue Engine v8 - Algoritmo de cues automático con feedback DJ aplicado.

Layout v8 (11 markers):
- Cue 1 / M1 — Mix-IN First Beat: primer onset absoluto
- Cue 2 / M2 — Bass IN: primer kick sustained
- Cue 3 / M3 — Breakdown: longest kick-absent stretch
- Cue 4 / M4 — DROP: kick re-entry post-breakdown
- Cue 5 — Mix-OUT (no Memory): 16 bars antes del último kick
- Loop Intro 16-bar: ActiveLoop=0 (naranja)
- Loop Outro 16-bar: ActiveLoop=1 (rojo) ← AUTO-LOOP cuando llega
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
from pyrekordbox.db6 import DjmdContent, DjmdCue, ContentCue


@dataclass
class CueAnalysis:
    """Resultado del análisis de un track."""
    first_beat: float       # seconds - Cue 1 / M1
    bass_in: float          # seconds - Cue 2 / M2
    breakdown: Optional[float] = None  # Cue 3 / M3
    drop: Optional[float] = None       # Cue 4 / M4
    outro: float = 0.0      # Cue 5 - Mix-OUT
    loop_intro_end: float = 0.0
    loop_outro_start: float = 0.0


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
        loop_intro_end=(bass_in_bar + 16) * bar_duration,
        loop_outro_start=(outro_bar - 16) * bar_duration,
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

    # Loops: intro INACTIVE, outro ACTIVE (v8 key change)
    for ls, le, name, active in [
        (cues.bass_in, cues.loop_intro_end, 'Loop Intro 16b', 0),
        (cues.loop_outro_start, cues.outro, 'Loop Outro 16b ACTIVE', 1),
    ]:
        loop = DjmdCue(
            ID=str(random.randint(100000000, 999999999)),
            ContentID=canonical.ID,
            InMsec=int(ls * 1000), InFrame=int(ls * 1000 * 0.150),
            InMpegFrame=0, InMpegAbs=0,
            OutMsec=int(le * 1000), OutFrame=int(le * 1000 * 0.150),
            OutMpegFrame=0, OutMpegAbs=0,
            Kind=0, Color=-1, ColorTableIndex=None, ActiveLoop=active,
            Comment=name, BeatLoopSize=16,
            ContentUUID=canonical.UUID, UUID=str(uuid_lib.uuid4()),
            rb_data_status=0, rb_local_data_status=0,
            rb_local_deleted=0, rb_local_synced=0,
            usn=None, rb_local_usn=None,
            created_at=now, updated_at=now,
        )
        db.session.add(loop)
        new_objs.append(loop)

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
