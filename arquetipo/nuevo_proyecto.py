"""Crea un proyecto nuevo con la estructura y el metodo del arquetipo.

Copia `arquetipo/plantilla/` al destino, reemplaza los marcadores, deja el metodo
en `docs/METODO.md` con la version del arquetipo, y verifica su propia salida.
No instala dependencias ni inicializa git: eso se decide por proyecto.

Uso:
    python arquetipo/nuevo_proyecto.py ~/Documents/mi-proyecto --nombre "Mi Proyecto"
    python arquetipo/nuevo_proyecto.py ./x --nombre X --paquete equis --si
"""
from __future__ import annotations

import argparse
import keyword
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / "plantilla"
VERSION = (AQUI / "VERSION").read_text(encoding="utf-8").strip()
# Extensiones donde se reemplazan los marcadores. En binarios no se toca nada.
TEXTO = {".md", ".json", ".py", ".txt", ".toml", ".cfg", ".yml", ".yaml"}
MARCADOR = re.compile(r"\{\{[A-Z_]+\}\}")


def _paquete_desde(nombre: str) -> str:
    # "Ñandú" -> "nandu", no "and": se le saca el acento a la letra, no la letra
    ascii_ = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9_]", "", re.sub(r"[\s-]+", "_", ascii_.lower()))


def _error_de_paquete(p: str) -> str | None:
    if not (p.isascii() and p.isidentifier()):
        return "no es un identificador python"
    if keyword.iskeyword(p):
        return "es una palabra reservada"
    if p in sys.stdlib_module_names:
        return "tapa un modulo de la biblioteca estandar"
    return None


def _origen() -> str:
    """Version y commit de donde sale, para que el proyecto sepa que le toco."""
    try:
        commit = subprocess.run(["git", "-C", str(AQUI), "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        sucio = subprocess.run(["git", "-C", str(AQUI), "status", "--porcelain", "."],
                               capture_output=True, text=True, check=True).stdout.strip()
        return f"v{VERSION} (plomo {commit}{', con cambios sin commitear' if sucio else ''})"
    except (OSError, subprocess.CalledProcessError):
        return f"v{VERSION}"


def _sustituir(texto: str, reemplazos: dict[str, str]) -> str:
    for clave, valor in reemplazos.items():
        texto = texto.replace("{{" + clave + "}}", valor)
    return texto


def _escribir(origen: Path, final: Path, reemplazos: dict[str, str]) -> None:
    final.parent.mkdir(parents=True, exist_ok=True)
    if origen.suffix in TEXTO:
        # newline="\n": en Windows write_text escribe CRLF y la plantilla es LF
        final.write_text(_sustituir(origen.read_text(encoding="utf-8"), reemplazos),
                         encoding="utf-8", newline="\n")
    else:
        shutil.copy2(origen, final)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("destino", type=Path)
    ap.add_argument("--nombre", required=True, help="nombre legible del proyecto")
    ap.add_argument("--paquete", help="nombre del paquete python (default: del nombre)")
    ap.add_argument("--descripcion", default="", help="una linea: que es esto")
    ap.add_argument("--si", action="store_true",
                    help="escribir de verdad; sin esto solo muestra que haria")
    args = ap.parse_args()

    paquete = args.paquete or _paquete_desde(args.nombre)
    if problema := _error_de_paquete(paquete):
        sys.exit(f"  '{paquete}' {problema}: pasá --paquete")

    destino = args.destino.expanduser().resolve()
    # No se pisa nada existente ni por accidente ni con --si: decide una persona.
    if destino.exists() and (not destino.is_dir() or any(destino.iterdir())):
        sys.exit(f"  {destino} ya existe y no es una carpeta vacia")

    reemplazos = {
        "NOMBRE": args.nombre,
        "PAQUETE": paquete,
        "DESCRIPCION": args.descripcion or "(sin descripción todavía)",
        "FECHA": date.today().isoformat(),
        "ARQUETIPO": _origen(),
    }
    # (origen, destino relativo): la plantilla, mas el metodo como docs/METODO.md
    plan = [(p, Path(*[paquete if s == "PAQUETE" else s for s in p.relative_to(PLANTILLA).parts]))
            for p in sorted(PLANTILLA.rglob("*")) if p.is_file()]
    plan.append((AQUI / "README.md", Path("docs", "METODO.md")))

    print(f"  {args.nombre}  ->  {destino}")
    print(f"  paquete: {paquete}   arquetipo {reemplazos['ARQUETIPO']}\n")
    for _, relativo in plan:
        print(f"    {relativo}")
    if not args.si:
        print(f"\n  {len(plan)} archivos. Nada escrito: agregá --si para hacerlo.")
        return

    for origen, relativo in plan:
        _escribir(origen, destino / relativo, reemplazos)
    metodo = destino / "docs" / "METODO.md"
    metodo.write_text(f"<!-- arquetipo {reemplazos['ARQUETIPO']}, copiado el "
                      f"{reemplazos['FECHA']}. Se actualiza a mano. -->\n\n"
                      + metodo.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    # verificar la propia salida antes de decir "listo"
    sobras = [f"{p.relative_to(destino)}: {m}" for p in destino.rglob("*")
              if p.is_file() and p.suffix in TEXTO
              for m in MARCADOR.findall(p.read_text(encoding="utf-8"))]
    print(f"\n  {len(plan)} archivos escritos, {len(sobras)} marcadores sin reemplazar")
    if sobras:
        sys.exit("  " + "\n  ".join(sobras))
    print(f"\n  Siguiente, en {destino}:")
    print("    git init   (el .gitignore tiene que entrar en el PRIMER commit)")
    print("    python -m venv .venv  y  pip install -e . pytest")
    print("    completar CLAUDE.md: qué es esto y qué NO se hace, y por qué")


if __name__ == "__main__":
    main()
