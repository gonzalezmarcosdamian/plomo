"""Reescala los rangos de energia de los set_configs de la formula v1 a la v2.

Al sacarle el BPM al score de energia, el promedio de la biblioteca casi no se
movio (5.56 -> 5.54) pero los tracks SI se movieron de lugar: un tema lento con
un breakdown largo subio y un tema rapido y plano bajo. Los `e_lo`/`e_hi` de los
configs estaban calibrados contra la vieja distribucion, asi que despues del
cambio el solver ya no encontraba material donde el arco lo pedia — en el set 97
el pico se corrio del 83% al 33% del set.

La traduccion correcta no es sumar un delta: es por PERCENTIL. "E5.4" no queria
decir 5.4, queria decir "el track que esta en el percentil 42 de la biblioteca".
Se busca ese mismo percentil en la distribucion nueva.

El valor viejo queda guardado al lado con el sufijo `_v1` para poder auditar la
traduccion.

Uso:
    python scripts/migrar_configs_energia.py --dry
    python scripts/migrar_configs_energia.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from bisect import bisect_left
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

CAMPOS = ("e_lo", "e_hi")
E_RE = re.compile(r"^E:\s*([\d.]+).*?\bv1:([\d.]+)")


def distribuciones() -> tuple[list[float], list[float]]:
    """(energias v1 ordenadas, energias v2 ordenadas) de toda la biblioteca."""
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    v1, v2 = [], []
    for (com,) in con.execute(
            "SELECT Commnt FROM djmdContent WHERE rb_local_deleted=0 AND Commnt IS NOT NULL"):
        m = E_RE.match((com or "").strip())
        if m:
            v2.append(float(m.group(1)))
            v1.append(float(m.group(2)))
    return sorted(v1), sorted(v2)


def traducir(valor: float, v1: list[float], v2: list[float]) -> float:
    """El valor de la escala vieja, al mismo percentil de la escala nueva."""
    if not v1 or not v2:
        return valor
    pct = bisect_left(v1, valor) / len(v1)
    idx = min(len(v2) - 1, max(0, int(round(pct * (len(v2) - 1)))))
    return round(v2[idx], 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    v1, v2 = distribuciones()
    print(f"muestra: {len(v1)} tracks con v1 y v2\n")
    if len(v1) < 500:
        sys.exit("muy pocos tracks con v1 guardado — corre recalcular_energia.py primero")

    for f in sorted((RAIZ / "data" / "set_configs").glob("*.json")):
        cfg = json.loads(f.read_text(encoding="utf-8"))
        tocado = False
        print(f"{f.name}")
        for spec in cfg.get("sets", []):
            cambios = []
            for campo in CAMPOS:
                if campo not in spec or f"{campo}_v1" in spec:
                    continue
                viejo = spec[campo]
                nuevo = traducir(viejo, v1, v2)
                spec[f"{campo}_v1"] = viejo
                spec[campo] = nuevo
                cambios.append(f"{campo} {viejo} -> {nuevo}")
                tocado = True
            if "e_pool" in spec and "e_pool_v1" not in spec:
                spec["e_pool_v1"] = list(spec["e_pool"])
                spec["e_pool"] = [traducir(spec["e_pool"][0], v1, v2),
                                  traducir(spec["e_pool"][1], v1, v2)]
                cambios.append(f"e_pool {spec['e_pool_v1']} -> {spec['e_pool']}")
                tocado = True
            if cambios:
                print(f"   {spec.get('num','?')}. {'; '.join(cambios)}")
        if tocado and not args.dry:
            cfg["_migracion_energia"] = (
                "Los rangos se tradujeron de la formula v1 (con BPM) a la v2 (sin BPM) "
                "por percentil de la biblioteca, no por delta. Los valores viejos quedan "
                "en los campos *_v1. Ver scripts/migrar_configs_energia.py.")
            f.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.dry:
        print("\n[dry] no se escribio nada")


if __name__ == "__main__":
    main()
