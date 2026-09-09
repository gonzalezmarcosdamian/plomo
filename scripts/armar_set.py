"""Reconstruye el set de Live desde cero: pistas, instrumentos, efectos y niveles.

Por que existe: el `.als` no se puede guardar por codigo. Live no le expone
`save` a los Remote Scripts —lo probamos, no hay handler y no es un olvido: es
deliberado— asi que todo el armado del set vive en la RAM de Live y se pierde al
cerrar. Y con la licencia Trial no se puede guardar a mano tampoco.

La salida no es guardar el archivo sino no necesitarlo. El set es el resultado
de una receta, y la receta si se puede versionar:

    data/set_live.json     que pistas hay, con que instrumento y a que nivel
    scripts/armar_set.py   la aplica sobre un set vacio
    scripts/idea.py        escribe el MIDI
    scripts/montar.py      lo pone en el arreglo

Con esas cuatro cosas en el repo, el tema entero se reconstruye con dos
comandos. Perder el set deja de ser perder el trabajo y pasa a ser perder cinco
minutos de maquina.

Tiene ademas un efecto que no era el objetivo y termino siendo lo mas util: hace
que cambiar de edicion de Live sea barato. Si un preset no existe en la edicion
que se compre, se cambia un nombre en el JSON y se vuelve a correr; no hay que
acordarse de que tenia cada pista.

Uso:
    python scripts/armar_set.py              # sobre el set abierto
    python scripts/armar_set.py --capturar   # al reves: lee Live y escribe el JSON
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.live import Live  # noqa: E402

RECETA = RAIZ / "data" / "set_live.json"

# El tempo del tema. Vive aca y no solo en `idea.py --bpm` porque las dos cosas
# tienen que coincidir y no coincidian: el MIDI se escribio a 123 y el set estaba
# en 121. No se rompe nada —la humanizacion esta en pulsos, asi que escala— pero
# los milisegundos medidos contra las referencias dejan de ser los que se
# midieron, y el tema entero dura ocho segundos mas de lo que dice el plan.
BPM = 123.0

# Donde buscar cada instrumento en el browser, y con que reemplazarlo si no esta.
#
# La lista de alternativas no es decoracion: es lo que hace que este script
# sobreviva a un cambio de edicion de Live. Intro trae 5 GB de sonidos contra los
# 71 de Suite, asi que un preset puede no existir — pero el MOTOR si (Drift,
# Instrument Rack, Drum Rack y Simpler estan en las tres ediciones), y lo ultimo
# de cada lista es siempre un motor, no un preset.
CATEGORIA = {
    "909 Core Kit": "drums", "707 Core Kit": "drums",
    "Cymbal 808 Full": "drums", "Cymbal Crash Reverse Gnirob": "drums",
}
ALTERNATIVAS = {
    "Warm Analog Pad": ["Warm Analog Pad", "Thick Chord Pad", "Drift"],
    "Sandman Pad": ["Sandman Pad", "Warm Analog Pad", "Drift"],
    "Deep Bass": ["Deep Bass", "Analog Bass", "Drift"],
    "909 Core Kit": ["909 Core Kit", "808 Core Kit", "Drum Rack"],
    "707 Core Kit": ["707 Core Kit", "909 Core Kit", "Drum Rack"],
    "Deep Pluck": ["Deep Pluck", "Snappy Pluck", "Drift"],
    "Snappy Pluck": ["Snappy Pluck", "Deep Pluck", "Drift"],
    "Tube Lead Pluck": ["Tube Lead Pluck", "Sweet Lead", "Drift"],
    "Cymbal 808 Full": ["Cymbal 808 Full", "Cymbal 808 Hard", "Cymbal Acid House"],
    "Cymbal Crash Reverse Gnirob": ["Cymbal Crash Reverse Gnirob", "FX Reverse",
                                    "Sweep White Noise Fall"],
}


def _hz(texto: str) -> float | None:
    """'2.32 kHz' -> 2320.0. El parametro se guarda como texto a proposito.

    El valor crudo de un DeviceParameter es 0 a 1 y no significa nada solo: 0.68
    son 2.3 kHz en un Auto Filter y otra cosa en cualquier otro dispositivo. Lo
    que se quiere reproducir es la frecuencia, asi que se guarda la frecuencia y
    se busca por biseccion al aplicar.
    """
    t = texto.strip().replace(",", ".")
    try:
        if t.lower().endswith("khz"):
            return float(t[:-3].strip()) * 1000.0
        if t.lower().endswith("hz"):
            return float(t[:-2].strip())
    except ValueError:
        return None
    return None


def capturar(live: Live, destino: Path = RECETA) -> dict:
    """Lee el set abierto y escribe la receta. El camino inverso."""
    fuera: dict = {"tempo": live.tempo(), "pistas": []}
    for t in range(4, live.n_pistas()):
        disp = []
        for d in range(live.n_dispositivos(t)):
            nombre = str(live.preguntar("/live/device/get/name", t, d)[-1])
            clase = str(live.preguntar("/live/device/get/class_name", t, d)[-1])
            par = {}
            if clase == "AutoFilter2":
                par["Frequency"] = live.valor_mostrado(t, d, 1)
            disp.append({"nombre": nombre, "clase": clase, "parametros": par})
        fuera["pistas"].append({
            "indice": t,
            "nombre": str(live.preguntar("/live/track/get/name", t)[-1]),
            "volumen": round(live.volumen(t), 4),
            "dispositivos": disp,
        })
    destino.write_text(json.dumps(fuera, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    return fuera


def armar(live: Live, receta: dict) -> None:
    live.tempo(BPM)
    hay = live.n_pistas()
    for p in receta["pistas"]:
        t = p["indice"]
        # Las pistas 0 a 3 son las que Live crea al abrir un set vacio. La receta
        # empieza en la 4 y no las toca: borrarlas seria lo prolijo, pero un
        # script que borra pistas en el set que el usuario tiene abierto puede
        # comerse trabajo que no es suyo.
        while live.n_pistas() <= t:
            live.enviar("/live/song/create_midi_track", -1)
            time.sleep(1.2)
        live.enviar("/live/track/set/name", t, p["nombre"])
        time.sleep(0.3)

        if not p["dispositivos"]:
            continue
        inst = p["dispositivos"][0]["nombre"]
        cand = ALTERNATIVAS.get(inst, [inst])
        cargado = live.cambiar_instrumento(t, cand, CATEGORIA.get(inst, "instruments"))
        time.sleep(0.8)
        if not cargado:
            print(f"    ! {p['nombre']}: no encontre ninguno de {cand}")

        for d in p["dispositivos"][1:]:
            live.cargar_instrumento(t, [d["nombre"]], "audio_effects")
            time.sleep(0.6)
            hz = _hz(d["parametros"].get("Frequency", ""))
            if hz is not None:
                real = live.ajustar_a_hz(t, live.n_dispositivos(t) - 1, 1, hz)
                print(f"      filtro {real:.0f} Hz (pedido {hz:.0f})")

        live.volumen(t, p["volumen"])
        print(f"  {t:>2} {p['nombre']:<10} {cargado or '?':<30} "
              f"vol {p['volumen']:.2f}", flush=True)
    if hay > 4:
        print(f"\n  ojo: el set ya tenia {hay} pistas y la receta escribe sobre "
              f"las {receta['pistas'][0]['indice']} en adelante")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capturar", action="store_true",
                    help="al reves: lee el set abierto y reescribe la receta")
    args = ap.parse_args()

    with Live(timeout=45.0) as live:
        if args.capturar:
            d = capturar(live)
            print(f"  {RECETA.relative_to(RAIZ)} · {len(d['pistas'])} pistas")
            return
        if not RECETA.exists():
            sys.exit(f"no existe {RECETA}; corre con --capturar primero")
        receta = json.loads(RECETA.read_text(encoding="utf-8"))
        print(f"  armando {len(receta['pistas'])} pistas a {BPM:.0f} BPM\n")
        armar(live, receta)
        print("\n  ahora: python scripts/montar.py v1")


if __name__ == "__main__":
    main()
