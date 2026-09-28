"""El arquetipo se verifica solo: lo que promete existe, y la version es una."""
import re
import subprocess
import sys
from pathlib import Path

ARQ = Path(__file__).resolve().parents[1] / "arquetipo"


def test_version_coincide_con_el_changelog():
    version = (ARQ / "VERSION").read_text(encoding="utf-8").strip()
    primera = re.search(r"^## (\d+\.\d+\.\d+)", (ARQ / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
    assert primera and primera.group(1) == version


def test_genera_lo_que_promete(tmp_path):
    destino = tmp_path / "nuevo"
    r = subprocess.run([sys.executable, str(ARQ / "nuevo_proyecto.py"), str(destino),
                        "--nombre", "Mi Proyecto Ñandú", "--si"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert (destino / "src" / "mi_proyecto_nandu" / "criterio.py").exists()
    # cada ruta del bloque "La estructura" del README tiene que llegar
    bloque = (ARQ / "README.md").read_text(encoding="utf-8").split("## La estructura")[1].split("```")[1]
    padre, prometidas = "", []
    for linea in bloque.splitlines():
        m = re.match(r"^(\s*)(\S+)", linea)
        if not m:
            continue
        nombre = m.group(2).replace("<paquete>", "mi_proyecto_nandu")
        padre = nombre if not m.group(1) else padre
        prometidas.append(nombre if not m.group(1) else padre + nombre)
    faltan = [p for p in prometidas if not (destino / p).exists()]
    assert faltan == []
    # sin CRLF
    assert not [p for p in destino.rglob("*") if p.is_file() and b"\r\n" in p.read_bytes()]
