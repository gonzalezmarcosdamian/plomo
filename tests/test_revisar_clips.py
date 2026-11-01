"""Tests de scripts/revisar_clips.py: funciones puras, sin ffmpeg ni clips."""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import revisar_clips as rc  # noqa: E402


def cielo(h=540, w=960, base=150):
    rng = np.random.default_rng(0)
    img = np.full((h, w), base, np.float32) + rng.normal(0, 0.8, (h, w))
    return np.clip(img, 0, 255).astype(np.uint8)


def test_estela_se_marca_en_cielo_liso():
    g = cielo()
    cv2.line(g, (100, 60), (800, 130), 175, 3)
    punt, segs = rc.detectar_estelas(g)
    assert segs and punt > 0


def test_cielo_liso_no_marca_estela():
    punt, segs = rc.detectar_estelas(cielo())
    assert segs == [] and punt == 0.0


def test_sol_en_el_horizonte_marca_y_sol_alto_no():
    g = np.full((540, 960), 60, np.uint8)
    g[300:] = 20  # horizonte en fila 300
    alto = g.copy()
    cv2.circle(alto, (480, 100), 25, 255, -1)
    assert rc.detectar_sol(alto)[1] is None
    bajo = g.copy()
    cv2.circle(bajo, (480, 295), 25, 255, -1)
    punt, pos = rc.detectar_sol(bajo)
    assert pos is not None and punt > 0


def test_angulo_recto():
    assert rc.hay_angulo_recto([(0, 0, 100, 0), (0, 0, 0, 100)])
    assert not rc.hay_angulo_recto([(0, 0, 100, 0), (0, 0, 100, 40)])


def test_segmentos_largos_filtra_cortos():
    out = rc.segmentos_largos([(0, 0, 10, 0), (0, 0, 500, 0)], 960, 0.28)
    assert out == [(0, 0, 500, 0)]


def test_blockiness_detecta_bloques():
    rng = np.random.default_rng(1)
    bloques = rng.integers(100, 108, (68, 120)).astype(np.uint8)
    g = np.kron(bloques, np.ones((8, 8), np.uint8))
    liso = np.full_like(g, 120)
    assert rc.blockiness(g, 8) > rc.COMPRESION_RATIO
    assert rc.blockiness(liso, 8) <= 1.0 + 1e-6


def test_fase_del_dia():
    assert rc.fase_del_dia(20, 0, 0) == "G"
    assert rc.fase_del_dia(70, 0, 0) == "F"
    assert rc.fase_del_dia(120, 20, 0) == "D"
    assert rc.fase_del_dia(120, 10, 20) == "E"
    assert rc.fase_del_dia(180, 50, 0) == "C"
    assert rc.fase_del_dia(210, 20, 0) == "B"
    assert rc.fase_del_dia(210, 0, 0) == "A"


def test_largo():
    assert rc.evaluar_largo(90, 30)["alcance"] == "tal_cual"
    assert rc.evaluar_largo(45, 30)["alcance"] == "rife_x2"
    assert rc.evaluar_largo(20, 30)["alcance"] == "corto"


def test_extraer_ids_tolera_sin_nuevos():
    d = {"etapas": [{"n": 1, "candidatos": [{"id": 1}, {"id": 2}]},
                    {"n": 2, "candidatos": [{"id": 3}], "nuevos": [{"id": 3}, {"id": 4}]}]}
    assert rc.extraer_ids(d) == [(1, [1, 2]), (2, [3, 4])]


def test_recorte_tamano_fijo():
    cu = np.zeros((540, 960, 3), np.uint8)
    assert rc.recorte(cu, (5, 5)).shape[:2] == (rc.RECORTE, rc.RECORTE)


def test_recortes_solo_de_lo_marcado_y_pocos_por_motivo():
    marcas = {"estelas": {"marca": True}, "sol": {"marca": False},
              "hombre": {"marca": False}, "compresion": {"marca": False}}
    recortes = [(t, "estela", None) for t in (0, 2, 4)] + [(6, "sol", None)]
    salida = rc.recortes_marcados(recortes, marcas)
    assert [m for _, m, _ in salida] == ["estela"] * rc.RECORTES_POR_MOTIVO


def test_una_estela_gruesa_es_una_sola_recta():
    g = cielo()
    cv2.line(g, (100, 60), (800, 130), 175, 3)
    _, segs = rc.detectar_estelas(g)
    assert rc.rectas_distintas(segs) == 1


def test_estela_dudosa_va_a_la_hoja_con_signo_de_pregunta():
    marcas = {"estelas": {"marca": False, "duda": True}, "sol": {"marca": False},
              "hombre": {"marca": False}, "compresion": {"marca": False}}
    salida = rc.recortes_marcados([(0, "estela", None)], marcas)
    assert [m for _, m, _ in salida] == ["estela?"]


def test_rotulo_resume_largo_fase_y_marcas():
    reg = {"id": 119784, "fase": {"letra": "B"}, "largo": {"duracion_s": 77.3, "alcance": "rife_x2"},
           "marcas": {"estelas": {"marca": False, "duda": True}, "sol": {"marca": True},
                      "hombre": {"marca": False}, "compresion": {"marca": False}}}
    assert rc.rotulo(reg) == "119784 77s B SE?"
