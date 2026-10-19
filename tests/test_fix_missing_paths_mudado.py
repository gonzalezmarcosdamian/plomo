"""mudado() encuentra el mismo archivo bajo la raiz nueva y nada mas."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fix_missing_paths.py"


def cargar(monkeypatch, raiz: Path, vieja: Path):
    spec = importlib.util.spec_from_file_location("fix_missing_paths", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "RAIZ", raiz)
    monkeypatch.setattr(modulo, "RAICES_VIEJAS", (vieja,))
    return modulo


def test_misma_ruta_relativa_bajo_la_raiz_nueva(tmp_path, monkeypatch):
    raiz, vieja = tmp_path / "Documents" / "Music", tmp_path / "OneDrive" / "Music"
    destino = raiz / "Biblioteca" / "2026-06" / "Tema (Original Mix).mp3"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"x")
    fmp = cargar(monkeypatch, raiz, vieja)

    ruta_db = (vieja / "Biblioteca" / "2026-06" / "Tema (Original Mix).mp3").as_posix()
    assert fmp.mudado(ruta_db) == destino


def test_no_inventa_si_el_archivo_no_esta(tmp_path, monkeypatch):
    raiz, vieja = tmp_path / "Documents" / "Music", tmp_path / "OneDrive" / "Music"
    raiz.mkdir(parents=True)
    fmp = cargar(monkeypatch, raiz, vieja)

    assert fmp.mudado((vieja / "Biblioteca" / "falta.mp3").as_posix()) is None


def test_ignora_rutas_fuera_de_la_raiz_vieja(tmp_path, monkeypatch):
    raiz, vieja = tmp_path / "Documents" / "Music", tmp_path / "OneDrive" / "Music"
    (raiz / "x.mp3").parent.mkdir(parents=True)
    (raiz / "x.mp3").write_bytes(b"x")
    fmp = cargar(monkeypatch, raiz, vieja)

    assert fmp.mudado((tmp_path / "Otro" / "x.mp3").as_posix()) is None
