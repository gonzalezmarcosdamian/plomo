# -*- coding: utf-8 -*-
"""Cuantas veces y hace cuanto toco el DJ cada tema, desde djmdHistory.

POR QUE EXISTE
El 2026-10-02 le propuse Sinking Sky para el set 150 y contesto "me gusta la
eleccion pero lo he tocado". El dato estaba en la base --2 pasadas-- y la busqueda
no lo miraba: filtraba por el campo `gastado` de energia_percibida, que es lo que
el DJ dijo A MANO, no lo que la DB ya sabia. Proponerle algo que el mismo toco la
semana pasada es gastarle un turno.

ESTO NO FILTRA, INFORMA. Y ESO ESTA MEDIDO
La tentacion era descartar todo lo tocado. Se probo contra el set que el llamo
perfecto y lo refuta: 8 de los 18 temas del 150 ya los habia tocado, Amnesia hace
2 dias y The Silver Lily hace 2 dias --y The Silver Lily la pidio EL por nombre--.
Un filtro duro por "ya lo toco" habria rechazado su propio set.

O sea que "lo he tocado" no es una regla del material, es un juicio que el hace
tema por tema, y cuando el lo nombra pisa cualquier conteo. Lo unico que
corresponde es que el numero este a la vista cuando se propone algo, para poder
decir "ojo, este lo tocaste 2 veces, la ultima hace 9 dias" y que decida el.

El cruce es por NOMBRE, no por ContentID: los ContentID cambian cada vez que
Rekordbox reimporta, y cruzar por ID descartaba el 68% de las coincidencias.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from functools import lru_cache

import sqlcipher3

from . import config


def normalizar(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


@lru_cache(maxsize=1)
def historial() -> dict[str, dict]:
    """{titulo normalizado: {veces, ultima (YYYY-MM-DD), tandas}}.

    Se lee en modo solo lectura: nunca hay que escribir en master.db desde aca,
    y menos con Rekordbox abierto.
    """
    con = sqlcipher3.connect(f"file:{config.REKORDBOX_DB_PATH}?mode=ro", uri=True)
    con.execute(f"PRAGMA key='{config.SQLCIPHER_KEY}'")
    con.execute("PRAGMA cipher_compatibility=4")
    fuera: dict[str, dict] = {}
    filas = con.execute("""
        SELECT c.Title, h.DateCreated, h.Name
          FROM djmdSongHistory sh
          JOIN djmdContent c ON c.ID = sh.ContentID
          JOIN djmdHistory  h ON h.ID = sh.HistoryID
         WHERE sh.rb_local_deleted = 0 AND h.rb_local_deleted = 0
    """).fetchall()
    con.close()
    for titulo, fecha, tanda in filas:
        k = normalizar(titulo)
        if not k:
            continue
        e = fuera.setdefault(k, {"veces": 0, "ultima": "", "tandas": set()})
        e["veces"] += 1
        e["ultima"] = max(e["ultima"], str(fecha)[:10])
        e["tandas"].add(tanda)
    for e in fuera.values():
        e["tandas"] = len(e["tandas"])
    return fuera


def toco(titulo: str, hoy: dt.date | None = None) -> dict | None:
    """Lo que hay que poder decirle al DJ antes de proponerle un tema.

    Devuelve None si nunca lo toco. Si lo toco, trae veces, la fecha de la
    ultima y cuantos dias hace, que es el dato que de verdad cambia la decision:
    dos pasadas hace dos años no es lo mismo que dos la semana pasada.
    """
    e = historial().get(normalizar(titulo))
    if not e:
        return None
    hoy = hoy or dt.date.today()
    y, m, d = (int(x) for x in e["ultima"].split("-"))
    return {"veces": e["veces"], "ultima": e["ultima"],
            "dias": (hoy - dt.date(y, m, d)).days, "tandas": e["tandas"]}


def etiqueta(titulo: str, hoy: dt.date | None = None) -> str:
    """Una linea para pegar al lado de un candidato cuando se lo propone."""
    t = toco(titulo, hoy)
    if not t:
        return "sin tocar"
    return f'{t["veces"]}x, ultima hace {t["dias"]} dias'
