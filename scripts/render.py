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


def _clips(live: Live) -> list[tuple[float, float]]:
    ini = live.preguntar("/live/track/get/arrangement_clips/start_time", PISTA_RENDER)[1:]
    lar = live.preguntar("/live/track/get/arrangement_clips/length", PISTA_RENDER)[1:]
    return [(float(a), float(b)) for a, b in zip(ini, lar)]


def _tiene_borrado(live: Live) -> bool:
    """Si el handler propio /live/arrangement/delete_clip esta cargado.

    Se prueba con un timeout corto: preguntarle a un handler que no existe
    espera el timeout entero (45 s) y eso paso adentro del render sin que nada
    lo dijera.
    """
    viejo = live.timeout
    live.timeout = 3.0
    try:
        live.preguntar("/live/arrangement/delete_clip", PISTA_RENDER, 9999)
        return True
    except Exception:
        return False
    finally:
        live.timeout = viejo


def _vaciar_region(live: Live, a: float, b: float, recien_grabado: bool = False) -> None:
    """Saca de la pista de render todo clip que toque [a, b) pulsos.

    Dos politicas segun el momento. ANTES de grabar, un clip viejo se borra
    por indice (handler propio), que es determinista. DESPUES de grabar, la
    toma se DESHACE: borrarla la deja viva en el historial de undo y Live
    mantiene el WAV abierto —"no solto el archivo en 25 s"—; deshacerla la
    desengancha y el archivo se libera en un segundo.
    """
    borrar = _tiene_borrado(live) and not recien_grabado
    for _ in range(8):
        toca = [i for i, (ini, lar) in enumerate(_clips(live)) if ini < b and ini + lar > a]
        if not toca:
            return
        if borrar:
            live.preguntar("/live/arrangement/delete_clip", PISTA_RENDER, toca[-1])
        else:
            live.enviar("/live/song/undo")
        time.sleep(0.8)
    quedan = [c for c in _clips(live) if c[0] < b and c[0] + c[1] > a]
    if quedan:
        sys.exit(f"  la pista de render tiene clips en la region y no los pude sacar: "
                 f"{quedan}. Recargar el Control Surface (handler de borrado) o "
                 f"borrarlos a mano.")


def grabar(live: Live, desde: int, compases: int,
           solo: list[int] | None = None, sesion: bool = False) -> tuple[Path, float]:
    antes = _wavs()
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
    # El loop de la cancion se apaga durante la toma. Las tomas que se fugaban
    # terminaban TODAS en el pulso 960 —el compas 240, el fin del loop— sin
    # importar cuando se mandara el stop. Con el loop apagado la toma termina
    # donde se la para. Se restaura despues, porque montar.py lo deja puesto
    # para que el cabezal no se vaya mas alla del final.
    loop_habia = bool(live.preguntar("/live/song/get/loop")[-1])
    live.enviar("/live/song/set/loop", 0); time.sleep(0.2)
    # La region de la toma tiene que estar VACIA en la pista de render. Si hay
    # un clip viejo ahi, grabar encima lo parte en dos y despues no se sabe
    # cual es la toma: se leia el largo del viejo (398 pulsos) como si fuera la
    # nueva, y el undo sacaba lo que no era. Se limpia con el handler propio
    # de borrado si esta cargado, y si no con undo hasta que la region quede
    # libre. Si no se puede, se aborta con un mensaje claro y no con una toma
    # que parece buena y no lo es.
    _vaciar_region(live, (desde - 1) * 4.0, (desde + compases + 2) * 4.0)
    # Volver al arreglo antes de tocar. Cualquier accion de sesion —disparar
    # o parar un clip, incluso borrar uno de un slot— saca a esa pista del
    # arreglo, y entonces sus clips del arreglo no suenan aunque esten ahi:
    # una pista entera midio -240 dBFS con 251 notas cargadas. Es un estado de
    # Live, no un error del MIDI, y se apaga con back_to_arranger.
    # ...salvo cuando la toma es de un clip de sesion disparado a proposito
    # (sondas de pads): Back to Arrangement PARA los clips de sesion, y todas
    # las sondas del 808 y del AG Techno Kit dieron silencio por esto.
    if not sesion:
        live.enviar("/live/song/set/back_to_arranger", 0); time.sleep(0.2)
    # Desarmar TODAS las demas pistas. Live arma sola la ultima pista creada,
    # y con la grabacion prendida graba en todas las armadas: esa pista entra
    # en grabacion, reproduce su entrada (nada) en vez de sus clips, y encima
    # los pisa. La pista Hats midio -240 dBFS con 251 notas cargadas por eso.
    for t in range(live.n_pistas()):
        if t != PISTA_RENDER:
            try:
                if live.preguntar("/live/track/get/can_be_armed", t)[-1]:
                    live.enviar("/live/track/set/arm", t, 0)
            except Exception:
                pass
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

    # Verificar que el transporte AVANZA antes de punchear. Una toma salio con
    # catorce compases de silencio digital y audio recien al final: Live estaba
    # todavia ocupado despues de montar cien clips, el start_playing se aplico
    # tarde, y la grabacion registro silencio mientras tanto. Preguntar dos
    # veces la posicion y exigir que suba es lo unico que distingue "andando"
    # de "todavia no".
    p1 = live.preguntar("/live/song/get/current_song_time")[0]
    time.sleep(1.0)
    p2 = live.preguntar("/live/song/get/current_song_time")[0]
    if p2 <= p1 + 0.5:
        live.enviar("/live/song/start_playing"); time.sleep(1.5)
        p3 = live.preguntar("/live/song/get/current_song_time")[0]
        if p3 <= p2 + 0.5:
            live.enviar("/live/song/stop_playing")
            sys.exit("  el transporte no avanza: Live esta ocupado o el set no suena")
    live.enviar("/live/song/set/record_mode", 1)
    # un compas de mas: lo que se pierde al recortar al compas pedido
    time.sleep((compases + 2) * 4 * 60.0 / BPM + 0.3)   # dos de margen: la toma arranca hasta un compas tarde
    # Parar y VERIFICAR que paro. Las tomas salian de 58, 69 y 150 segundos
    # para pedidos de 10 a 33: Live seguia grabando despues del stop, y el undo
    # de una grabacion en curso no la deshace, asi que el archivo quedaba
    # trabado. No se supone que paro: se pregunta hasta que diga que si.
    for _ in range(20):
        live.enviar("/live/song/set/record_mode", 0)
        live.enviar("/live/song/stop_playing")
        time.sleep(0.5)
        if not live.preguntar("/live/song/get/is_playing")[-1]:
            break
    live.enviar("/live/track/set/arm", PISTA_RENDER, 0)
    if solo:
        for t in range(4, live.n_pistas()):
            live.enviar("/live/track/set/solo", t, 0)

    largos = [float(x) for x in
              live.preguntar("/live/track/get/arrangement_clips/length", PISTA_RENDER)[1:]]
    a, b = (desde - 1) * 4.0, (desde + compases + 2) * 4.0
    en_region = [c for c in _clips(live) if c[0] < b and c[0] + c[1] > a]
    if len(en_region) != 1:
        sys.exit(f"  esperaba UN clip nuevo en la region y hay {len(en_region)}: {en_region}")
    inicio, largo_toma = en_region[0]
    largos = [largo_toma]
    # El undo saca el clip y Live suelta el archivo; el WAV queda en disco.
    # Tambien verificado: se cuenta los clips antes y despues, y se reintenta
    # porque el primer undo a veces deshace otra cosa (el arm, el nombre).
    # Primero se intenta borrar el clip nuevo por indice (handler propio del
    # Remote Script); si ese handler no esta cargado, se cae al undo. En los dos
    # casos se verifica contra el conteo de ANTES de armar, no contra el de
    # despues de grabar: el undo a veces deshace otra cosa primero.
    _vaciar_region(live, (desde - 1) * 4.0, (desde + compases + 2) * 4.0, recien_grabado=True)
    if loop_habia:
        live.enviar("/live/song/set/loop", 1)
    wav = _wav_nuevo(antes)
    if wav is None:
        sys.exit("  Live no escribio ningun WAV")
    # El largo que reporta Live para un clip recien grabado es el del sample
    # pre-asignado (unos 400 pulsos), no el de lo grabado: no se muestra como
    # si fuera la duracion de la toma.
    print(f"  toma desde el pulso {inicio:.2f} · {wav.name}")
    return wav, inicio


def copiar_liberado(origen: Path, destino: Path, espera_s: float = 25.0) -> None:
    """Copia el WAV recien grabado cuando Live ya lo cerro, y VERIFICA la copia.

    Copiar mientras Live todavia tiene el archivo abierto no siempre falla:
    a veces copia un WAV a medias, con la cabecera sin escribir, que despues no
    abre ("System error"). Que la copia exista no prueba nada; que abra si.
    """
    import soundfile as sf
    fin = time.time() + espera_s
    while True:
        try:
            shutil.copy(origen, destino)
            sf.info(destino)
            return
        except Exception:
            if time.time() > fin:
                sys.exit(f"  Live no solto {origen} en {espera_s:.0f}s")
            time.sleep(1.0)


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
    # .crudo.tmp y no .crudo.wav: un glob de *.wav agarraba el intermedio sin
    # recortar, y una tabla entera salio con los compases corridos dos lugares
    crudo = destino.with_suffix(".crudo.tmp")
    copiar_liberado(wav, crudo)
    real = recortar(crudo, destino, inicio, args.desde, args.compases)
    crudo.unlink()
    # Y que el render tenga audio. Un WAV de silencio digital mide como un tema
    # vacio y la tabla del bucle lo compara igual, con cara de dato.
    import soundfile as sf
    y, _ = sf.read(destino, always_2d=True)
    import numpy as np
    rms = 20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-12)
    if rms < -60:
        sys.exit(f"  el render es silencio ({rms:.0f} dBFS): el transporte no andaba o el set esta mudo")
    if real != args.desde:
        nuevo = destino.with_name(destino.name.replace(
            f"{args.desde}-{args.desde + args.compases - 1}",
            f"{real}-{real + args.compases - 1}"))
        # el render mas nuevo de una region pisa al anterior: iterar.py toma el
        # mas reciente por fecha, y guardar diez tomas del mismo tramo no
        # ayuda a nadie
        if nuevo.exists():
            nuevo.unlink()
        destino.rename(nuevo); destino = nuevo
        print(f"  (arranco en el compas {real}, no en el {args.desde})")
    print(f"  {destino.relative_to(RAIZ)} · {destino.stat().st_size / 1e6:.1f} MB")
    print(f"\n  ahora: python scripts/traducir.py \"{destino}\" --desde 0")


if __name__ == "__main__":
    main()
