"""Crea un proyecto nuevo con la estructura y el metodo del arquetipo.

Copia `arquetipo/plantilla/` al destino, reemplaza los marcadores y deja la
bitacora abierta con la primera entrada. No instala dependencias ni inicializa
git: eso se decide por proyecto.

Uso:
    python arquetipo/nuevo_proyecto.py ~/Documents/mi-proyecto --nombre "Mi Proyecto"
    python arquetipo/nuevo_proyecto.py ./x --nombre X --paquete equis --si
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLANTILLA = Path(__file__).resolve().parent / "plantilla"
# Extensiones donde se reemplazan los marcadores. En binarios no se toca nada.
TEXTO = {".md", ".json", ".py", ".txt", ".toml", ".cfg", ".yml", ".yaml"}


def _sustituir(texto: str, reemplazos: dict[str, str]) -> str:
    for clave, valor in reemplazos.items():
        texto = texto.replace("{{" + clave + "}}", valor)
    return texto


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("destino", type=Path)
    ap.add_argument("--nombre", required=True, help="nombre legible del proyecto")
    ap.add_argument("--paquete", help="nombre del paquete python (default: del nombre)")
    ap.add_argument("--descripcion", default="", help="una linea: que es esto")
    ap.add_argument("--si", action="store_true",
                    help="escribir de verdad; sin esto solo muestra que haria")
    args = ap.parse_args()

    paquete = args.paquete or re.sub(r"[^a-z0-9_]", "", args.nombre.lower().replace(" ", "_"))
    if not paquete or not paquete[0].isalpha():
        sys.exit(f"  '{paquete}' no sirve como nombre de paquete: pasá --paquete")

    destino = args.destino.expanduser().resolve()
    # No se pisa un proyecto existente ni por accidente ni con --si: si hay algo
    # adentro, el que decide que hacer es una persona.
    if destino.exists() and any(destino.iterdir()):
        sys.exit(f"  {destino} ya existe y no esta vacio")

    reemplazos = {
        "NOMBRE": args.nombre,
        "PAQUETE": paquete,
        "DESCRIPCION": args.descripcion or "(sin descripción todavía)",
        "FECHA": date.today().isoformat(),
    }

    archivos = [p for p in PLANTILLA.rglob("*") if p.is_file()]
    print(f"  {args.nombre}  ->  {destino}")
    print(f"  paquete: {paquete}\n")

    for origen in archivos:
        relativo = origen.relative_to(PLANTILLA)
        # la carpeta del paquete se llama como el paquete, no "PAQUETE"
        partes = [paquete if p == "PAQUETE" else p for p in relativo.parts]
        final = destino.joinpath(*partes)
        print(f"    {final.relative_to(destino)}")
        if not args.si:
            continue
        final.parent.mkdir(parents=True, exist_ok=True)
        if origen.suffix in TEXTO:
            final.write_text(_sustituir(origen.read_text(encoding="utf-8"), reemplazos),
                             encoding="utf-8")
        else:
            shutil.copy2(origen, final)

    # las carpetas vacias no viajan en un rglob de archivos, y son parte de la
    # estructura: sin ellas el arquetipo llega a medias
    vacias = [p.relative_to(PLANTILLA) for p in PLANTILLA.rglob("*")
              if p.is_dir() and not any(p.iterdir())]
    for v in vacias:
        partes = [paquete if p == "PAQUETE" else p for p in v.parts]
        print(f"    {Path(*partes)}/")
        if args.si:
            destino.joinpath(*partes).mkdir(parents=True, exist_ok=True)
            destino.joinpath(*partes, ".gitkeep").touch()

    if not args.si:
        print(f"\n  {len(archivos)} archivos y {len(vacias)} carpetas. "
              "Nada escrito: agregá --si para hacerlo.")
        return

    bitacora = destino / "docs" / "BITACORA.md"
    if bitacora.exists():
        texto = bitacora.read_text(encoding="utf-8")
        texto = texto.replace("## AAAA-MM-DD — título de la sesión",
                              f"## {reemplazos['FECHA']} — arranque\n\n"
                              f"Proyecto creado desde el arquetipo.\n\n"
                              "## AAAA-MM-DD — título de la sesión")
        bitacora.write_text(texto, encoding="utf-8")

    print(f"\n  Listo. Empezá por {destino / 'CLAUDE.md'}:")
    print("    - qué es esto")
    print("    - qué NO se hace, y por qué")
    print("  Y leé arquetipo/README.md si es la primera vez.")


if __name__ == "__main__":
    main()
