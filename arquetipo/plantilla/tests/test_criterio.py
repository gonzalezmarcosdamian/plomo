"""El archivo de criterios se chequea solo: cada regla con sus tres campos."""
import json
import shutil

from {{PAQUETE}}.criterio import RUTA, Criterio, R


def test_cada_regla_tiene_valor_porque_y_evidencia():
    incompletas = [r for r, n in R.todas().items()
                   if not all(str(n.get(c, "")).strip() for c in ("valor", "porque", "evidencia"))]
    assert incompletas == []


def test_aplicar_sube_version_y_deja_historial(tmp_path):
    copia = tmp_path / "criterio.json"
    shutil.copy(RUTA, copia)
    c = Criterio(copia)
    ruta = next(iter(c.todas()))
    antes = c.version

    nueva = c.aplicar(c.proponer(ruta, 123, "medido en el test"), "prueba")

    data = json.loads(copia.read_text(encoding="utf-8"))
    assert nueva != antes
    assert data["historial"][-1]["version"] == nueva
    assert data["historial"][-1]["a"] == 123
    assert b"\r\n" not in copia.read_bytes()
