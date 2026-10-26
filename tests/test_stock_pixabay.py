# -*- coding: utf-8 -*-
"""Buscar en Pixabay: una busqueda vacia no tira abajo las otras ni pierde lo ya buscado."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import stock_pixabay  # noqa: E402


def _hit(i: int) -> dict:
    v = {"url": f"https://x/{i}.mp4", "width": 3840, "height": 2160, "thumbnail": f"https://x/{i}.jpg"}
    return {"id": i, "tags": "sky", "duration": 40, "pageURL": f"https://p/{i}", "user": "u", "views": 1,
            "videos": {"large": v, "medium": v, "small": v, "tiny": v}}


class _Respuesta:
    def __init__(self, hits):
        self._hits = hits

    def raise_for_status(self):
        pass

    def json(self):
        return {"hits": self._hits}


class _Cliente:
    def __init__(self, por_busqueda):
        self.por_busqueda = por_busqueda

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        return _Respuesta(self.por_busqueda[params["q"]])


@pytest.mark.unit
def test_busqueda_vacia_no_corta_y_se_guarda_lo_buscado(tmp_path, monkeypatch):
    por_busqueda = {"heathland": [], "blue hour sky": [_hit(1), _hit(2)]}
    hojas = []
    monkeypatch.setattr(stock_pixabay, "DEST", tmp_path)
    monkeypatch.setattr(stock_pixabay, "CANDIDATOS", tmp_path / "candidatos.json")
    monkeypatch.setattr(stock_pixabay, "PAUSA_S", 0)
    monkeypatch.setattr(stock_pixabay, "clave", lambda: "k")
    monkeypatch.setattr(stock_pixabay.httpx, "Client", lambda **kw: _Cliente(por_busqueda))
    monkeypatch.setattr(stock_pixabay, "hoja", lambda cli, items, salida: hojas.append(len(items)))

    stock_pixabay.buscar(["heathland", "blue hour sky"])

    assert hojas == [2]
    guardados = json.loads((tmp_path / "candidatos.json").read_text(encoding="utf-8"))
    assert sorted(guardados) == ["1", "2"]
