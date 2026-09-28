"""Lo que CLAUDE.md afirma de la estructura, chequeado en vez de prometido.

"Raiz: solo config" y "el .gitignore ataja X" son frases; estos tests son el
chequeo. Sin git (proyecto recien creado, antes de `git init`) se saltean.
"""
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RAIZ_PERMITIDA = {".gitignore", ".env.example", "CLAUDE.md", "README.md",
                  "pyproject.toml", "requirements.txt"}


def _git(*args: str) -> list[str]:
    try:
        salida = subprocess.run(["git", "-C", str(RAIZ), *args], check=True,
                                capture_output=True, text=True, encoding="utf-8").stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("sin git todavia")
    return [linea for linea in salida.splitlines() if linea]


def test_nada_versionado_que_el_gitignore_excluya():
    assert _git("ls-files", "-ci", "--exclude-standard") == []


def test_la_raiz_solo_tiene_config():
    en_raiz = {f for f in _git("ls-files") if "/" not in f}
    assert en_raiz <= RAIZ_PERMITIDA, en_raiz - RAIZ_PERMITIDA
