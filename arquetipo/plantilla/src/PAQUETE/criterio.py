"""Los criterios del proyecto, leidos de `rules/criterio.json`.

Viven en un archivo de datos y no como constantes para que se puedan medir,
discutir y versionar. Si hay un `R.get(...)` con un numero equivalente escrito a
mano al lado, la regla se lee y no se usa: eso es peor que no tenerla.

Uso:
    from {{PAQUETE}}.criterio import R
    R.get("ejemplo.umbral_algo")       -> 0.75
    R.porque("ejemplo.umbral_algo")    -> "Por debajo de esto..."
    R.sin_evidencia()                  -> reglas duras que nadie midio
    R.sin_lector()                     -> reglas que ningun .py pide
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "rules" / "criterio.json"


class Criterio:
    def __init__(self, path: Path = RUTA) -> None:
        self.path = path
        self._data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    def _nodo(self, ruta: str) -> Any:
        nodo: Any = self._data
        for parte in ruta.split("."):
            if not isinstance(nodo, dict) or parte not in nodo:
                raise KeyError(f"regla inexistente: {ruta}")
            nodo = nodo[parte]
        return nodo

    def get(self, ruta: str) -> Any:
        """Sin default a proposito: una regla que no existe es un error, no un 0."""
        nodo = self._nodo(ruta)
        return nodo["valor"] if isinstance(nodo, dict) and "valor" in nodo else nodo

    def porque(self, ruta: str) -> str:
        return str(self._nodo(ruta).get("porque", ""))

    def es_dura(self, ruta: str) -> bool:
        return bool(self._nodo(ruta).get("duro", False))

    def es_decision_humana(self, ruta: str) -> bool:
        """La puso una persona por gusto: la referencia externa no la refuta."""
        return bool(self._nodo(ruta).get("decision_humana", False))

    @property
    def version(self) -> str:
        return self._data["_meta"]["version"]

    def todas(self) -> dict[str, dict]:
        return dict(self._recorrer(self._data, ""))

    def _recorrer(self, nodo: dict, prefijo: str) -> Iterator[tuple[str, dict]]:
        for k, v in nodo.items():
            if k.startswith("_") or k == "historial" or not isinstance(v, dict):
                continue
            ruta = f"{prefijo}.{k}" if prefijo else k
            if "valor" in v:
                yield ruta, v
            else:
                yield from self._recorrer(v, ruta)

    def sin_evidencia(self) -> list[str]:
        """Reglas duras sin medir. Sin campo `evidencia` tambien cuenta."""
        def sin_medir(n: dict) -> bool:
            ev = str(n.get("evidencia", "")).strip()
            return not ev or ev.upper().startswith("PENDIENTE")
        return [r for r, n in self.todas().items() if n.get("duro") and sin_medir(n)]

    def sin_lector(self, carpetas: tuple[str, ...] = ("src", "scripts")) -> list[str]:
        """Reglas cuyo nombre no aparece en ningun .py: existen y nadie las lee."""
        codigo = "\n".join(
            p.read_text(encoding="utf-8", errors="replace")
            for c in carpetas for p in (RAIZ / c).rglob("*.py")
            if p.resolve() != Path(__file__).resolve()
        )
        return [r for r in self.todas() if f'"{r}"' not in codigo and f"'{r}'" not in codigo]

    def proponer(self, ruta: str, valor_nuevo: Any, evidencia: str, autor: str = "?") -> dict:
        """Devuelve el parche. NO escribe: lo aprueba una persona mirando el numero."""
        return {"ruta": ruta, "valor_actual": self.get(ruta), "valor_propuesto": valor_nuevo,
                "evidencia": evidencia, "autor": autor}

    def aplicar(self, parche: dict, nota: str = "") -> str:
        """Aplica un parche aprobado: valor, evidencia, version menor e historial."""
        nodo = self._nodo(parche["ruta"])
        anterior = nodo.get("valor")
        nodo["valor"] = parche["valor_propuesto"]
        nodo["evidencia"] = parche["evidencia"]
        mayor, menor, _ = self.version.split(".")
        self._data["_meta"]["version"] = f"{mayor}.{int(menor) + 1}.0"
        # del mas viejo al mas nuevo: la ultima entrada es la version vigente
        self._data["historial"].append({
            "version": self.version, "ruta": parche["ruta"], "de": anterior,
            "a": parche["valor_propuesto"], "evidencia": parche["evidencia"],
            "autor": parche.get("autor", "?"), "nota": nota,
        })
        # indent=1 y LF, como esta escrito: si no, cambiar un numero reformatea todo
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8", newline="\n")
        return self.version


R = Criterio()
