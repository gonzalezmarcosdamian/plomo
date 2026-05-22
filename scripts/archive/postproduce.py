"""
Post-production pipeline:
1. Master audio (normalize, compress, limit)
2. Generate YouTube clip (16:9, full fragment)
3. Generate Reels/Shorts clips (9:16 crop, best energy segments)
"""
import sys
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import librosa
from pedalboard import Pedalboard, Compressor, Limiter, Gain, HighpassFilter
from pedalboard.io import AudioFile

FFMPEG = r"C:\Users\gonza\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
VIDEO_IN = r"C:\Users\gonza\Documents\plomo\IMG_8372.MOV"
AUDIO_WAV = r"C:\Users\gonza\Documents\plomo\set_audio.wav"
OUT_DIR = Path(r"C:\Users\gonza\Documents\plomo\postproduction")

# ── 1. MASTER AUDIO ──────────────────────────────────────────────────────────
print("=== MASTERIZANDO AUDIO ===")

with AudioFile(AUDIO_WAV) as f:
    audio = f.read(f.frames)
    sr = f.samplerate

print(f"Audio cargado: {audio.shape}, sr={sr}")

board = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80),      # Sacar ruido sub-grave del cel
    Compressor(threshold_db=-18, ratio=3.0,      # Compresor suave
               attack_ms=10, release_ms=150),
    Gain(gain_db=12),                             # +12 dB para llevar a nivel DJ
    Limiter(threshold_db=-1.0, release_ms=100),   # Limitar a -1 dBFS
])

print("Aplicando cadena de masterización...")
mastered = board(audio, sr)

master_path = OUT_DIR / "audio" / "set_masterizado.wav"
with AudioFile(str(master_path), "w", sr, mastered.shape[0]) as f:
    f.write(mastered)
print(f"Audio masterizado guardado: {master_path}")

# Verificar loudness resultado
rms = float(np.sqrt(np.mean(mastered**2)))
lufs = 20 * np.log10(rms + 1e-9) - 3
peak = float(np.max(np.abs(mastered)))
print(f"Loudness resultado: {lufs:.1f} dBFS | Pico: {20*np.log10(peak+1e-9):.1f} dBFS")

# ── 2. YOUTUBE CLIP (16:9, video completo con audio masterizado) ──────────────
print("\n=== GENERANDO CLIP YOUTUBE (16:9) ===")

youtube_path = OUT_DIR / "clips" / "youtube" / "set_youtube.mp4"
cmd = [
    FFMPEG, "-y",
    "-i", VIDEO_IN,
    "-i", str(master_path),
    "-map", "0:v:0",       # Video del MOV
    "-map", "1:a:0",       # Audio masterizado
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "20",
    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(youtube_path)
]
print(f"Exportando {youtube_path.name}...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print(f"OK: {youtube_path}")
else:
    print(f"Error: {result.stderr[-500:]}")

# ── 3. REELS CLIPS (9:16, segmentos de mayor energia, 60s) ───────────────────
print("\n=== GENERANDO CLIPS REELS/SHORTS (9:16) ===")

# Detectar segmento de mayor energia (60s)
y_mono, _ = librosa.load(AUDIO_WAV, sr=22050, mono=True)
segment_sr = 22050
window = 60 * segment_sr  # 60 segundos
best_start = 0
best_energy = 0
for i in range(0, len(y_mono) - window, segment_sr * 5):
    seg = y_mono[i:i+window]
    e = float(np.sqrt(np.mean(seg**2)))
    if e > best_energy:
        best_energy = e
        best_start = i

best_start_s = best_start / segment_sr
print(f"Mejor segmento (60s): empieza en {best_start_s:.0f}s ({best_start_s/60:.1f} min)")

reel_path = OUT_DIR / "clips" / "reels" / "set_reel_60s.mp4"
cmd_reel = [
    FFMPEG, "-y",
    "-ss", str(best_start_s),
    "-i", VIDEO_IN,
    "-ss", str(best_start_s),
    "-i", str(master_path),
    "-t", "60",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "20",
    # Crop centro para 9:16 (portrait)
    "-vf", "crop=ih*9/16:ih,scale=1080:1920",
    "-c:a", "aac",
    "-b:a", "192k",
    str(reel_path)
]
print(f"Exportando reel 60s...")
result = subprocess.run(cmd_reel, capture_output=True, text=True)
if result.returncode == 0:
    print(f"OK: {reel_path}")
else:
    print(f"Error: {result.stderr[-500:]}")

# También generar un reel de 30s (el pico más alto)
reel_30_path = OUT_DIR / "clips" / "reels" / "set_reel_30s.mp4"
cmd_reel_30 = [
    FFMPEG, "-y",
    "-ss", str(best_start_s),
    "-i", VIDEO_IN,
    "-ss", str(best_start_s),
    "-i", str(master_path),
    "-t", "30",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "20",
    "-vf", "crop=ih*9/16:ih,scale=1080:1920",
    "-c:a", "aac",
    "-b:a", "192k",
    str(reel_30_path)
]
print(f"Exportando reel 30s...")
result = subprocess.run(cmd_reel_30, capture_output=True, text=True)
if result.returncode == 0:
    print(f"OK: {reel_30_path}")
else:
    print(f"Error: {result.stderr[-500:]}")

print("\n=== RESUMEN ===")
for f in OUT_DIR.rglob("*"):
    if f.is_file():
        size = f.stat().st_size / 1024 / 1024
        print(f"  {f.relative_to(OUT_DIR)} ({size:.1f} MB)")
