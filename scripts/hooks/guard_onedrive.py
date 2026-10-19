"""Hook PreToolUse: corta toda escritura adentro de OneDrive.

OneDrive no se usa desde el 2026-10-19 (ver CLAUDE.md). La cuota se lleno el
2026-09-21 y desde ahi todo lo que caia en la carpeta quedaba como placeholder
que nunca subia: 62 GB que parecian respaldados y no lo estaban, la biblioteca
de Rekordbox incluida. Se saco todo y se dejo de usar. Este hook frena lo que
vuelva a meter algo adentro antes de que pase.

Bloquea:
- Write / Edit / NotebookEdit sobre un archivo bajo la carpeta de OneDrive.
- Bash / PowerShell que nombran la carpeta de OneDrive y ademas escriben:
  redirigen hacia ella, o mueven, copian, crean, renombran o borran.

Leer o listar OneDrive NO se bloquea: un guardarrail que corta operaciones
inofensivas se termina desactivando, como explica guard_rekordbox.py.

Se instala en `.claude/settings.json` como hook PreToolUse. Salir con codigo 2
bloquea la llamada y le muestra el mensaje al modelo.
"""
from __future__ import annotations

import json
import re
import sys

# La carpeta de OneDrive escrita de cualquiera de las formas en que aparece en
# un comando: ruta absoluta con / o \, home con ~, o las variables de entorno.
ONEDRIVE = re.compile(
    r"(?:users[\\/]+gonza[\\/]+onedrive"
    r"|~[\\/]+onedrive"
    r"|\$env:onedrive"
    r"|%onedrive%"
    r"|\$onedrive\b"
    r"|home\(\)\s*/\s*[\"']onedrive)",
    re.IGNORECASE)

# Verbos que escriben. Con `\b` para que "mv" no matchee adentro de otra palabra.
# Sin los alias cortos de PowerShell (mi, ni, del, md): son palabras comunes en
# los nombres de la coleccion ("Mi Sonido", "Cumple del 20") y bloquearian un
# simple listado.
ESCRIBE = re.compile(
    r"\b(?:move-item|copy-item|new-item|set-content|add-content|out-file|"
    r"remove-item|rename-item|robocopy|xcopy|mklink|mv|cp|mkdir|rm|rmdir|"
    r"tee|touch)\b",
    re.IGNORECASE)
# Redireccion cuyo destino es OneDrive: `> C:\Users\gonza\OneDrive\...`
REDIRIGE = re.compile(r">>?\s*[\"']?[^\s\"'|;&]*onedrive", re.IGNORECASE)

ARCHIVO = ("Write", "Edit", "NotebookEdit")
SHELL = ("Bash", "PowerShell")

MENSAJE = (
    "BLOQUEADO: {que} escribe adentro de OneDrive.\n"
    "OneDrive no se usa (regla del 2026-10-19 en CLAUDE.md): la cuota estaba "
    "llena y lo que caia ahi quedaba sin respaldo aunque pareciera subido.\n"
    "Usar las carpetas locales: C:\\Users\\gonza\\Documents, Desktop, Pictures, "
    "Videos o Music. Si de verdad hay que tocar OneDrive, lo hace el DJ a mano.")


def escribe_en_onedrive(herramienta: str, entrada: dict) -> bool:
    if herramienta in ARCHIVO:
        ruta = entrada.get("file_path") or entrada.get("notebook_path") or ""
        return bool(ONEDRIVE.search(ruta))
    if herramienta in SHELL:
        cmd = entrada.get("command") or ""
        if not ONEDRIVE.search(cmd):
            return False
        return bool(ESCRIBE.search(cmd) or REDIRIGE.search(cmd))
    return False


def main() -> None:
    try:
        evento = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # sin evento parseable, no es asunto del hook

    herramienta = evento.get("tool_name") or ""
    entrada = evento.get("tool_input") or {}
    if escribe_en_onedrive(herramienta, entrada):
        print(MENSAJE.format(que=herramienta), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
