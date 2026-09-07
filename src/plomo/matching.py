"""Clave de matcheo de tracks entre fuentes distintas.

Los ContentID de Rekordbox cambian cuando se reconstruye la biblioteca, asi que
cruzar `set_targets`, setlists externos y `pool.json` por ID descarta la mayoria
de los tracks. El cruce tiene que ser por nombre — pero por un nombre normalizado
con cuidado.

El cuidado es el remixer: si la clave descarta todo lo que esta entre parentesis,
"Everlong (Original Mix)" y "Everlong (Ruben Karapetyan Remix)" colapsan en la
misma clave y el cruce asigna la key y el BPM del track equivocado. Sobre la
biblioteca actual eso afectaba al 7.6% de los tracks.

Entonces: se descartan los calificativos genericos de version y se conserva el
nombre propio del remixer.
"""
from __future__ import annotations

import re
import unicodedata

# Palabras que describen la version pero no dicen de quien es.
GENERICOS = {
    "original", "extended", "mix", "remix", "edit", "version", "club", "radio",
    "vocal", "instrumental", "dub", "long", "short", "reshape", "re", "shape",
    "rework", "reinterpretation", "feat", "ft", "featuring", "remaster",
    "remastered", "bootleg", "vip", "intro", "outro", "pt", "part",
}
_PARENTESIS = re.compile(r"[(\[]([^)\]]*)[)\]]")
_NO_ALNUM = re.compile(r"[^a-z0-9]")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def clave(artista: str, titulo: str) -> str:
    """Clave estable para el mismo track entre fuentes distintas.

    'Emi Galvan - Everlong (Original Mix)'        -> emigalvaneverlong
    'Emi Galvan - Everlong (Ruben Karapetyan Remix)' -> emigalvaneverlongrubenkarapetyan
    """
    titulo = titulo or ""
    # lo que queda entre parentesis y no es generico es el nombre del remixer
    manos = []
    for tramo in _PARENTESIS.findall(titulo):
        palabras = [p for p in _NO_ALNUM.sub(" ", _ascii(tramo).lower()).split()
                    if p and p not in GENERICOS]
        manos.extend(palabras)
    base = _PARENTESIS.sub("", titulo)
    return _NO_ALNUM.sub("", _ascii(f"{artista} {base}").lower()) + "".join(sorted(set(manos)))
