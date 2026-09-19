"""Mete una transcripcion en el set de Live, para escucharla por la misma cadena.

Por que existe. Cuando un boceto propio suena mal hay dos culpables y
escuchando no se distinguen: puede ser lo que esta ESCRITO —las notas, la
armonia, el groove— o puede ser la CADENA: los instrumentos elegidos, los
efectos, la mezcla. Los dos se escuchan igual de mal.

Esto los separa. Toma la transcripcion de un tema que ya suena bien y la manda
por exactamente el mismo set, los mismos instrumentos y los mismos efectos que
el tema propio. El resultado se lee de una:

    suena bien  -> la cadena esta bien y el problema es lo que escribimos
    suena mal   -> el problema es la cadena, y ninguna nota lo va a arreglar

Es el unico experimento del proyecto que puede refutar la cadena, porque es el
unico donde el material de entrada esta fuera de toda duda.

Lo que NO prueba: que la transcripcion sea fiel. Una transcripcion pobre suena
pobre sin que el tema lo sea. Por eso `copiar_tema.py` verifica antes —bombos
por compas, bombos en grilla, notas adentro de escala— y por eso este script
repite esos numeros al montar.

Uso:
    python scripts/probar_copia.py postproduction/bocetos/copia_tunnel
    python scripts/probar_copia.py <carpeta> --compases 16
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from plomo.live import Live  # noqa: E402
from montar import AG, PISTAS, leer  # noqa: E402

# La transcripcion tiene tres capas y van a las pistas que hacen lo mismo en el
# set propio. Los numeros del nombre del archivo son el orden de la capa, no la
# pista: `01_acordes` no va a la pista 1.
DESTINO = {
    "01_acordes.mid": 5,
    "02_bajo.mid":    6,
    "03_bateria.mid": 7,
}

# Las pistas del set que hay que vaciar para que no suene el tema propio encima.
# Se vacian TODAS y no solo las tres que se usan: si queda una capa del boceto
# sonando debajo, lo que se escucha no es la copia y el experimento no dice nada.
TODAS = sorted(set(PISTAS.values()) | set(DESTINO.values()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("--compases", type=int, default=16)
    args = ap.parse_args()

    if not args.carpeta.exists():
        sys.exit(f"no existe {args.carpeta}")

    with Live(timeout=60.0) as l:
        l.enviar("/live/song/stop_playing")
        time.sleep(0.4)

        print(f"  vaciando {len(TODAS)} pistas del arreglo")
        for t in TODAS:
            l.cargar_midi(t, 0, [], largo_compases=256)
            time.sleep(0.22)
            l.preguntar("/live/arrangement/duplicate", t, 0, 0.0)
            time.sleep(0.22)

        print()
        for nombre, pista in DESTINO.items():
            f = args.carpeta / nombre
            if not f.exists():
                print(f"  ? falta {nombre}")
                continue
            _, _, notas = leer(f)
            # El AG Techno Kit no sigue el mapa del 909. La transcripcion
            # escribe 36/39/42 —bombo, clap, hat— que en el AG son los mismos
            # tres, asi que el remapeo no cambia nada hoy; se aplica igual para
            # que siga valiendo si `copiar_tema.py` empieza a sacar mas piezas.
            if pista == 7:
                notas = [(i, d, AG.get(a, a), v) for i, d, a, v in notas]
            l.cargar_midi(pista, 0, notas, largo_compases=args.compases)
            time.sleep(0.30)
            l.preguntar("/live/arrangement/duplicate", pista, 0, 0.0)
            time.sleep(0.26)
            print(f"  {nombre:<16} -> pista {pista:<3} {len(notas):>3} notas")

        print(f"\n  {args.compases} compases desde el 1")
        print(f"  ahora: python scripts/render.py copia --desde 1 "
              f"--compases {args.compases}")


if __name__ == "__main__":
    main()
