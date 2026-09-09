"""Graba el master de Live a un WAV, sin exportar y sin licencia.

Por que existe. Todo lo que el proyecto media era MIDI propio o audio ajeno: del
audio del PROPIO tema no habia nada, porque Live no exporta por OSC y con la
Trial no exporta ni a mano. Eso dejaba ciego justo lo que el DJ describia
—"suena a ringtone" es timbre, capas, ancho, movimiento: propiedades del audio,
no del MIDI— y hacia imposible cualquier iteracion automatica: un bucle habria
optimizado lo medible y se habria alejado de lo que importa.

Grabar no es exportar. Una pista de audio con entrada "Resampling" recibe el
master, y lo que graba Live lo escribe a disco como WAV aunque el set no se
pueda guardar. Con eso `traducir.py` corre sobre el render propio igual que
corre sobre una referencia, y la comparacion pasa a ser simetrica.

Tres cosas que costaron encontrar y hay que respetar:

**El orden del transporte.** Primero se pone a andar y DESPUES se mueve el
cabezal — al reves queda en el compas 2. Y la grabacion se prende recien cuando
el cabezal ya esta en el lugar: mover el cabezal durante la grabacion corta la
toma. La primera prueba grabo 0.94 pulsos por eso.

**El archivo queda trabado.** Live mantiene abierto el WAV mientras el clip
existe en el arreglo, y ni siquiera una apertura compartida lo lee. Deshacer la
toma (`/live/song/undo`) saca el clip, Live suelta el archivo, y el WAV sigue en
disco. Por eso el render termina con un undo y no con un borrado.

**Donde lo escribe.** En un set sin guardar Live graba en
`Ableton/Live Recordings/<fecha> Temp Project/Samples/Recorded/`. Se busca el
WAV mas nuevo de ahi y se copia a `postproduction/render/`, que esta fuera del
repo porque pesa.

Con `--solo` se graba un subconjunto de pistas: un "stem" propio. Sirve para
comparar bateria contra bateria y bajo contra bajo con los stems de Demucs de la
referencia, sin que la separacion decida a que stem va cada capa nuestra.

Uso:
    python scripts/render.py v2 --desde 161 --compases 16
    python scripts/render.py v2 --desde 161 --solo 7 13 16 --nombre bateria
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.live import Live  # noqa: E402

GRABACIONES = Path.home() / "OneDrive" / "Documentos" / "Ableton" / "Live Recordings"
SALIDA = RAIZ / "postproduction" / "render"
PISTA_RENDER = 2          # "3-Audio": una de las vacias que trae el set nuevo
BPM = 123.0


def _wavs() -> set[Path]:
    return set(GRABACIONES.rglob("Samples/Recorded/*.wav"))


def _wav_nuevo(antes: set[Path]) -> Path | None:
    """El WAV que aparecio desde `antes`. Por diferencia de conjunto, no por fecha.

    La primera version comparaba `mtime` contra la hora de inicio y fallaba una
    de cada tres veces: la carpeta vive en OneDrive y la fecha del archivo se
    mueve mientras Live lo cierra y lo recorta. Que archivo es nuevo no depende
    de ningun reloj. Y se reintenta unos segundos porque Live termina de escribir
    despues de soltar el clip.
    """
    for _ in range(12):
        nuevos = _wavs() - antes
        if nuevos:
            return max(nuevos, key=lambda p: p.stat().st_size)
        time.sleep(1.0)
    return None


def grabar(live: Live, desde: int, compases: int,
           solo: list[int] | None = None) -> tuple[Path, float]:
    antes = _wavs()
    clips_antes = {round(float(x), 3) for x in
                   live.preguntar("/live/track/get/arrangement_clips/start_time", PISTA_RENDER)[1:]}
    tipos = [str(x) for x in
             live.preguntar("/live/track/get/available_input_routing_types", PISTA_RENDER)[1:]]
    if not any("Resampl" in x for x in tipos):
        sys.exit("  la pista de render no ofrece Resampling")
    live.enviar("/live/track/set/input_routing_type", PISTA_RENDER, "Resampling")
    live.enviar("/live/track/set/name", PISTA_RENDER, "Render")
    time.sleep(0.4)

    if solo:
        for t in range(4, live.n_pistas()):
            live.enviar("/live/track/set/solo", t, 1 if t in solo else 0)
        time.sleep(0.3)

    live.enviar("/live/song/stop_playing"); time.sleep(0.5)
    live.enviar("/live/song/set/record_mode", 0)
    live.enviar("/live/track/set/arm", PISTA_RENDER, 1); time.sleep(0.3)
    live.enviar("/live/song/start_playing"); time.sleep(0.5)
    live.enviar("/live/song/set/current_song_time", float((desde - 1) * 4)); time.sleep(0.8)
    pos = live.preguntar("/live/song/get/current_song_time")[0]
    # Tolerancia de tres compases, no de dos: el salto tarda y el transporte
    # sigue andando mientras tanto, asi que el cabezal siempre queda un poco
    # despues de donde se lo mando. No importa donde arranque la toma: la
    # posicion exacta la da Live en `start_time` y el WAV se recorta despues al
    # compas pedido. Lo que si importa es que no haya quedado en el compas 2.
    if abs(pos - (desde - 1) * 4) > 12:
        live.enviar("/live/song/stop_playing")
        sys.exit(f"  el cabezal quedo en el compas {int(pos // 4) + 1}, no en el {desde}")

    live.enviar("/live/song/set/record_mode", 1)
    # un compas de mas: lo que se pierde al recortar al compas pedido
    time.sleep((compases + 1) * 4 * 60.0 / BPM + 0.3)
    live.enviar("/live/song/set/record_mode", 0); time.sleep(0.3)
    live.enviar("/live/song/stop_playing"); time.sleep(0.5)
    live.enviar("/live/track/set/arm", PISTA_RENDER, 0)
    if solo:
        for t in range(4, live.n_pistas()):
            live.enviar("/live/track/set/solo", t, 0)

    largos = [float(x) for x in
              live.preguntar("/live/track/get/arrangement_clips/length", PISTA_RENDER)[1:]]
    inicios = [round(float(x), 3) for x in
               live.preguntar("/live/track/get/arrangement_clips/start_time", PISTA_RENDER)[1:]]
    # La toma nueva es el clip que NO estaba antes — por diferencia, no "el de
    # mayor inicio". Un clip viejo que sobrevivio a los undo (uno en el pulso
    # 832) ganaba siempre, y el recorte salia de otro lugar del tema.
    nuevos = [i for i in inicios if i not in clips_antes]
    inicio = (min(nuevos, key=lambda i: abs(i - (desde - 1) * 4)) if nuevos
              else float((desde - 1) * 4))
    # el undo saca el clip y Live suelta el archivo; el WAV queda en disco
    live.enviar("/live/song/undo"); time.sleep(1.0)
    wav = _wav_nuevo(antes)
    if wav is None:
        sys.exit("  Live no escribio ningun WAV")
    print(f"  toma de {max(largos) if largos else 0:.1f} pulsos desde el pulso "
          f"{inicio:.2f} · {wav.name}")
    return wav, inicio


def recortar(origen: Path, destino: Path, inicio_pulsos: float,
             desde: int, compases: int) -> int:
    """Deja el WAV empezando EXACTO en el compas pedido y con el largo pedido.

    La toma arranca donde estaba el cabezal, que nunca es exactamente el
    compas: Live tarda en saltar y el transporte sigue. Pero Live sabe en que
    pulso empezo el clip, y con eso el corte es sample-exacto. Sin esto dos
    renders del mismo tramo no se pueden comparar entre si ni contra la
    referencia, porque cada uno arranca en otro lado.
    """
    import math
    import soundfile as sf
    y, sr = sf.read(origen, always_2d=True)
    # La toma SIEMPRE arranca despues del compas pedido —Live tarda en saltar y
    # el transporte sigue— asi que el primer compas entero es el siguiente al
    # que empezo la toma, no el que se pidio. Se recorta desde ahi y se devuelve
    # cual es, para que el nombre del archivo diga la verdad.
    primer_compas = math.ceil(inicio_pulsos / 4.0)          # 0-based
    corr = primer_compas * 4.0 - inicio_pulsos              # pulsos que sobran
    a = int(round(corr * 60.0 / BPM * sr))
    b = a + int(round(compases * 4 * 60.0 / BPM * sr))
    if b > len(y):
        sys.exit(f"  la toma tiene {len(y) / sr:.1f}s y hacen falta "
                 f"{b / sr:.1f}s: grabar mas compases")
    sf.write(destino, y[a:b], sr, subtype="PCM_24")
    return primer_compas + 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--desde", type=int, default=161)
    ap.add_argument("--compases", type=int, default=16)
    ap.add_argument("--solo", type=int, nargs="*", help="pistas a grabar solas")
    ap.add_argument("--nombre", help="sufijo del archivo (ej. bateria)")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    suf = f"_{args.nombre}" if args.nombre else ""
    destino = SALIDA / f"{args.version}_{args.desde}-{args.desde + args.compases - 1}{suf}.wav"
    with Live(timeout=45.0) as live:
        wav, inicio = grabar(live, args.desde, args.compases, args.solo)
    crudo = destino.with_suffix(".crudo.wav")
    for _ in range(10):
        try:
            shutil.copy(wav, crudo)
            break
        except PermissionError:
            time.sleep(1.0)
    else:
        sys.exit(f"  Live no solto {wav}")
    real = recortar(crudo, destino, inicio, args.desde, args.compases)
    crudo.unlink()
    if real != args.desde:
        nuevo = destino.with_name(destino.name.replace(
            f"{args.desde}-{args.desde + args.compases - 1}",
            f"{real}-{real + args.compases - 1}"))
        destino.rename(nuevo); destino = nuevo
        print(f"  (arranco en el compas {real}, no en el {args.desde})")
    print(f"  {destino.relative_to(RAIZ)} · {destino.stat().st_size / 1e6:.1f} MB")
    print(f"\n  ahora: python scripts/traducir.py \"{destino}\" --desde 0")


if __name__ == "__main__":
    main()
