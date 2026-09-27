"""Mide un set grabado: energia por segmento, BPM, transiciones y loudness.

El archivo se pasa por argumento. Estaba clavado en `set_audio.wav` de la raiz
del repo con la ruta absoluta de esta maquina, o sea que el script servia para UN
archivo y solo en esta computadora. Las grabaciones viven en `grabaciones/`.

    python scripts/analyze_set.py grabaciones/2026-09-23_set_consola_REC001.wav
    python scripts/analyze_set.py          # la grabacion mas nueva que haya
"""
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import librosa
import librosa.display

if len(sys.argv) > 1:
    AUDIO_PATH = Path(sys.argv[1])
else:
    grabs = sorted((Path(__file__).resolve().parent.parent / "grabaciones").glob("*.wav"),
                   key=lambda f: f.stat().st_mtime)
    if not grabs:
        sys.exit("no hay grabaciones en grabaciones/: pasa el archivo por argumento")
    AUDIO_PATH = grabs[-1]
    print(f"(sin argumento: uso la mas nueva, {AUDIO_PATH.name})")
if not AUDIO_PATH.exists():
    sys.exit(f"no existe {AUDIO_PATH}")

print("Cargando audio...")
y, sr = librosa.load(AUDIO_PATH, sr=22050, mono=True)
duration = len(y) / sr
print(f"Duracion: {duration/60:.1f} minutos ({duration:.0f}s)")

# BPM global
print("\nAnalizando BPM...")
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
tempo_val = float(np.atleast_1d(tempo)[0])
print(f"BPM global: {tempo_val:.1f}")

# Loudness por segmentos de 30s
print("\nAnalisis de energia por segmento (30s):")
segment_len = 30 * sr
n_segments = int(len(y) / segment_len)
energies = []
for i in range(n_segments):
    seg = y[i*segment_len:(i+1)*segment_len]
    rms = float(np.sqrt(np.mean(seg**2)))
    energies.append(rms)
    mins = (i * 30) // 60
    secs = (i * 30) % 60
    bar = "█" * int(rms * 500)
    print(f"  {mins:02d}:{secs:02d} | {bar:<20} {rms:.4f}")

# Detectar transiciones (caidas de energia)
print("\nPosibles transiciones (caidas de energia >20%):")
for i in range(1, len(energies)):
    if energies[i-1] > 0 and (energies[i-1] - energies[i]) / energies[i-1] > 0.20:
        mins = (i * 30) // 60
        secs = (i * 30) % 60
        print(f"  ~{mins:02d}:{secs:02d} — caida {((energies[i-1]-energies[i])/energies[i-1]*100):.0f}%")

# Loudness LUFS aproximado
rms_total = float(np.sqrt(np.mean(y**2)))
lufs_approx = 20 * np.log10(rms_total + 1e-9) - 3
print(f"\nLoudness aproximado: {lufs_approx:.1f} dBFS")
print(f"Referencia streaming: -14 LUFS | DJ sets: -9 LUFS")
if lufs_approx < -14:
    diff = -14 - lufs_approx
    print(f"  -> Necesita +{diff:.1f} dB de ganancia para streaming")
elif lufs_approx < -9:
    diff = -9 - lufs_approx
    print(f"  -> Necesita +{diff:.1f} dB para nivel DJ set")
else:
    print(f"  -> Nivel OK para DJ set")

# Clipping check
peak = float(np.max(np.abs(y)))
print(f"\nPico maximo: {peak:.4f} ({20*np.log10(peak+1e-9):.1f} dBFS)")
if peak > 0.99:
    print("  ⚠️  CLIPPING detectado")
else:
    print("  OK — sin clipping")
