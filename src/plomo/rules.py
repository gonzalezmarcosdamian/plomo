"""Carga las reglas de curaduria desde `rules/curaduria.json`.

Las reglas viven en un archivo de datos y no como constantes en el codigo para
que se puedan medir, discutir y versionar. `select_set.py` y `audit_sets.py`
leen de aca; `scripts/backtest_rules.py` las contrasta contra setlists reales.

Uso:
    from plomo.rules import R
    R.get("energia.max_escalon")        -> 1.3
    R.porque("energia.max_escalon")     -> "Un escalon mayor lo nota..."
    R.conflictos()                      -> reglas cuyo valor escrito no coincide
                                           con el que usa el codigo
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).resolve().parents[2] / "rules" / "curaduria.json"


class Reglas:
    """Acceso por ruta punteada a las reglas, con su justificacion."""

    def __init__(self, path: Path = RULES_PATH) -> None:
        self.path = path
        self._data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    # -- lectura ---------------------------------------------------------
    def _nodo(self, ruta: str) -> Any:
        nodo: Any = self._data
        for parte in ruta.split("."):
            if not isinstance(nodo, dict) or parte not in nodo:
                raise KeyError(f"regla inexistente: {ruta}")
            nodo = nodo[parte]
        return nodo

    def get(self, ruta: str, default: Any = None) -> Any:
        """Valor de la regla. Acepta default para reglas todavia no escritas."""
        try:
            nodo = self._nodo(ruta)
        except KeyError:
            if default is None:
                raise
            return default
        return nodo["valor"] if isinstance(nodo, dict) and "valor" in nodo else nodo

    def porque(self, ruta: str) -> str:
        nodo = self._nodo(ruta)
        return nodo.get("porque", "") if isinstance(nodo, dict) else ""

    def es_dura(self, ruta: str) -> bool:
        nodo = self._nodo(ruta)
        return bool(nodo.get("duro", False)) if isinstance(nodo, dict) else False

    @property
    def version(self) -> str:
        return self._data.get("_meta", {}).get("version", "?")

    # -- introspeccion ---------------------------------------------------
    def _recorrer(self, nodo: Any = None, prefijo: str = ""):
        nodo = self._data if nodo is None else nodo
        for k, v in nodo.items():
            if k.startswith("_") or k == "historial":
                continue
            ruta = f"{prefijo}.{k}" if prefijo else k
            if isinstance(v, dict) and "valor" in v:
                yield ruta, v
            elif isinstance(v, dict):
                yield from self._recorrer(v, ruta)

    def conflictos(self) -> list[tuple[str, str]]:
        """Reglas marcadas con CONFLICTO: lo escrito no coincide con el codigo."""
        return [(r, n["CONFLICTO"]) for r, n in self._recorrer() if "CONFLICTO" in n]

    def sin_evidencia(self) -> list[str]:
        """Reglas duras que todavia nadie midio. Son las candidatas a caerse."""
        # Una regla dura sin campo `evidencia` tambien esta sin medir. El check
        # viejo pedia que el campo dijera "PENDIENTE", asi que las que ni
        # siquiera lo tenian se escapaban — justo las peores.
        def sin_medir(nodo: dict) -> bool:
            ev = str(nodo.get("evidencia", "")).strip()
            return not ev or ev.upper().startswith("PENDIENTE")

        return [r for r, n in self._recorrer() if n.get("duro") and sin_medir(n)]

    def todas(self) -> dict[str, Any]:
        return {r: n for r, n in self._recorrer()}

    # -- escritura -------------------------------------------------------
    def proponer(self, ruta: str, valor_nuevo: Any, evidencia: str, autor: str = "analista") -> dict:
        """Devuelve el parche que habria que aplicar. NO escribe: lo aprueba el humano."""
        nodo = self._nodo(ruta)
        return {
            "ruta": ruta,
            "valor_actual": nodo.get("valor"),
            "valor_propuesto": valor_nuevo,
            "evidencia": evidencia,
            "autor": autor,
        }

    def aplicar(self, parche: dict, nota: str = "") -> None:
        """Aplica un parche aprobado, sube la version menor y deja historial."""
        nodo = self._nodo(parche["ruta"])
        anterior = nodo.get("valor")
        nodo["valor"] = parche["valor_propuesto"]
        nodo["evidencia"] = parche["evidencia"]
        mayor, menor, patch = (self._data["_meta"]["version"].split(".") + ["0", "0"])[:3]
        self._data["_meta"]["version"] = f"{mayor}.{int(menor) + 1}.0"
        self._data.setdefault("historial", []).insert(0, {
            "version": self._data["_meta"]["version"],
            "ruta": parche["ruta"],
            "de": anterior,
            "a": parche["valor_propuesto"],
            "evidencia": parche["evidencia"],
            "autor": parche.get("autor", "?"),
            "nota": nota,
        })
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


R = Reglas()
