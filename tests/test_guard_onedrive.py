"""El guardarrail de OneDrive corta escrituras y deja pasar lecturas."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "scripts" / "hooks" / "guard_onedrive.py"


def correr(herramienta: str, entrada: dict) -> int:
    evento = json.dumps({"tool_name": herramienta, "tool_input": entrada})
    return subprocess.run([sys.executable, str(HOOK)], input=evento,
                          capture_output=True, text=True).returncode


@pytest.mark.parametrize("herramienta,entrada", [
    ("Write", {"file_path": r"C:\Users\gonza\OneDrive\Documentos\nota.md"}),
    ("Edit", {"file_path": "C:/Users/gonza/OneDrive/Escritorio/x.txt"}),
    ("PowerShell", {"command": r"Copy-Item a.mp3 'C:\Users\gonza\OneDrive\Documentos\Music'"}),
    ("PowerShell", {"command": r"'x' | Out-File $env:OneDrive\x.txt"}),
    ("Bash", {"command": "mv render.mp4 /c/Users/gonza/OneDrive/plomo_shorts/"}),
    ("Bash", {"command": "echo hola > ~/OneDrive/x.txt"}),
])
def test_bloquea_escrituras(herramienta, entrada):
    assert correr(herramienta, entrada) == 2


@pytest.mark.parametrize("herramienta,entrada", [
    ("Write", {"file_path": r"C:\Users\gonza\Documents\Music\nota.md"}),
    ("PowerShell", {"command": r"Get-ChildItem 'C:\Users\gonza\OneDrive\Documentos\Mi Sonido del 20'"}),
    ("Bash", {"command": "ls /c/Users/gonza/OneDrive 2>/dev/null | wc -l"}),
    ("Bash", {"command": "cp a.mp3 /c/Users/gonza/Documents/Music/"}),
    ("Bash", {"command": "git commit -m 'saca todo de OneDrive'"}),
])
def test_deja_pasar_lo_demas(herramienta, entrada):
    assert correr(herramienta, entrada) == 0
