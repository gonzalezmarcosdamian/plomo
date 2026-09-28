"""Tests del matcher de Spotify, sin tocar la red.

Existen porque este buscador produjo TRES bugs distintos en dos dias, todos del
mismo tipo: elegir un tema que se llama igual pero no es. Un remix por otro, un
corte de compilacion en vez del tema, y un "Confusion" de otro artista. Los tres
se ven en un segundo con una respuesta falsa de la API y no se ven nunca mirando
el codigo.

La respuesta se arma a mano: `buscar()` solo necesita que `get()` devuelva la
forma de Spotify, asi que se le pasa un objeto con esa unica funcion.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from spotify_sync import Spotify  # noqa: E402


def tema(nombre: str, artistas: list[str], seg: float = 420.0) -> dict:
    return {"uri": f"spotify:track:{abs(hash(nombre)) % 10**8}", "name": nombre,
            "artists": [{"name": a} for a in artistas],
            "duration_ms": int(seg * 1000)}


class FalsaAPI(Spotify):
    """Un Spotify que no habla con Spotify: devuelve siempre los mismos temas."""

    def __init__(self, resultados: list[dict]) -> None:   # noqa: D107
        self.h = {}
        self.yo = "test"
        self._res = resultados

    def get(self, ruta, **params):
        if ruta == "/search":
            return {"tracks": {"items": self._res}}
        raise AssertionError(f"el test no deberia pedir {ruta}")


@pytest.mark.unit
class TestElegirVersion:
    def test_el_remixer_manda(self) -> None:
        # El bug del 2026-09-27: la lista quedo con el remix de Roman cuando la
        # biblioteca tiene el de L.GU. Los dos dicen "mix" y los dos son "Muse".
        sp = FalsaAPI([
            tema("Muse - Roman Extended Mix", ["Rezident", "Kate Morgan", "Roman"], 510),
            tema("Muse - L.GU. Extended Mix", ["Rezident", "Kate Morgan", "L.GU."], 399),
        ])
        _, nombre = sp.buscar("Rezident, Kate Morgan",
                              "Muse feat. Kate Morgan (L.GU. Extended Mix)", 399)
        assert "L.GU." in nombre
        assert "Roman" not in nombre

    def test_el_invitado_no_es_el_remixer(self) -> None:
        # "Altitude (Feat. Frameloue Extended Mix)": si "feat" se toma como parte
        # del nombre del remixer, se exige "feat frameloue" en el candidato y el
        # tema correcto queda afuera diciendo "no esta en Spotify".
        sp = FalsaAPI([tema("Altitude - Extended Mix", ["Kostya Outta", "Frameloue"], 444)])
        uri, nombre = sp.buscar("Kostya Outta, Frameloue",
                                "Altitude (Feat. Frameloue Extended Mix)", 444)
        assert uri is not None, "el tema existe y el matcher tiene que encontrarlo"
        assert "Altitude" in nombre

    def test_el_artista_tiene_piso(self) -> None:
        # "Confusion" de Dilby engancho el "Confusion" de Adam Sellouk: titulo
        # identico, artista completamente distinto. Con un titulo generico el
        # titulo no identifica nada.
        sp = FalsaAPI([tema("Confusion", ["Adam Sellouk", "Glowal"], 400)])
        uri, _ = sp.buscar("Dilby, Amine K (Moroko Loko)", "Confusion (Extended Mix)", 444)
        assert uri is None

    def test_el_artista_correcto_entra_aunque_cambie_el_credito(self) -> None:
        # Y el piso no puede llevarse puestos los creditos que Spotify escribe
        # distinto: la biblioteca dice "Rockka" y alla figura "Rockka, Fuenka".
        sp = FalsaAPI([tema("Amnesia - Fuenka Remix", ["Rockka", "Fuenka"], 444)])
        uri, nombre = sp.buscar("Rockka", "Amnesia (Fuenka Remix)", 444)
        assert uri is not None
        assert "Amnesia" in nombre

    def test_original_mix_no_es_un_remix(self) -> None:
        # El regex que evita tratar "(Original Mix)" como remix estuvo roto por
        # un caracter de control durante cuatro dias. Si vuelve a romperse, el
        # matcher exige un "remixer" que no existe y este test se cae.
        sp = FalsaAPI([tema("Sizer", ["Agustin Pietrocola"], 413)])
        uri, nombre = sp.buscar("Agustin Pietrocola", "Sizer (Original Mix)", 413)
        assert uri is not None
        assert nombre.endswith("Sizer")

    def test_prefiere_el_largo_parecido(self) -> None:
        # Entre dos versiones del MISMO mix gana la que dura como el archivo.
        sp = FalsaAPI([
            tema("Portal Six", ["Durante"], 240),
            tema("Portal Six - Extended Mix", ["Durante"], 362),
        ])
        _, nombre = sp.buscar("Durante", "Portal Six (Extended Mix)", 362)
        assert "Extended" in nombre

    def test_sin_resultados_no_inventa(self) -> None:
        sp = FalsaAPI([])
        assert sp.buscar("Nadie", "Nada (Original Mix)", 400) == (None, "")
