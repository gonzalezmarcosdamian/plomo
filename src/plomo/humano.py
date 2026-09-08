"""Humanizacion por rol: cada instrumento se mueve distinto y para un lado.

Por que existe: la version anterior aplicaba el mismo jitter aleatorio a todo, y
no servia. Un jitter parejo de +-6 ms no es humanizacion — es ruido, y el oido lo
lee como error de cuantizacion, no como alguien tocando.

Lo que hace un productor es otra cosa, y tiene tres partes:

**Direccion.** No es aleatorio hacia los dos lados: cada instrumento se atrasa o
se adelanta de forma consistente. El bombo no se mueve nunca —es el reloj contra
el que se mide todo lo demas—, el clap y el hat van atras, el bajo va adelante
empujando. Esa relacion fija entre capas es lo que se escucha como groove; si
todo se mueve al azar, la relacion no existe.

**Swing.** Las semicorcheas de contratiempo se corren tarde. En house esta entre
54% y 58%; 50% es la grilla dura y 66% ya es shuffle.

**Dinamica con forma.** La velocidad no varia al azar: acentua posiciones fijas
—el uno, el contratiempo— y ademas sube y baja a lo largo de la frase. Ocho
compases con la misma velocidad promedio suenan planos aunque cada nota varie.

La semilla es determinista y sale de blake2b sobre (rol, compas, pulso). No se
usa `hash()` de Python: esta randomizado por proceso, asi que dos corridas del
mismo boceto daban archivos distintos y ninguna comparacion A/B valia.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

# Un pulso a 123 BPM son 488 ms, asi que 0.010 pulsos = 4.9 ms.
MS = 1.0 / 488.0


@dataclass(frozen=True)
class Perfil:
    """Como se mueve un rol.

    corrimiento: adonde vive respecto de la grilla, en pulsos. Negativo = adelante.
    dispersion:  cuanto varia alrededor de eso.
    swing:       cuanto se atrasan las semicorcheas de contratiempo.
    dinamica:    cuanto varia la velocidad.
    arco:        cuanto sube la velocidad a lo largo de la frase de 8 compases.
    """
    corrimiento: float = 0.0
    dispersion: float = 0.0
    swing: float = 0.0
    dinamica: int = 0
    arco: int = 0


# El bombo NO se mueve. Es contra el que se mide todo lo demas: si el reloj
# tiembla, lo que se escucha no es humanidad sino que el tema esta mal grabado.
PERFILES: dict[str, Perfil] = {
    "kick":     Perfil(0.0, 0.0, 0.0, dinamica=2),
    # el clap vive atras del pulso: es lo que lo hace sonar a mano y no a maquina
    "clap":     Perfil(10 * MS, 4 * MS, 0.0, dinamica=7),
    "hat":      Perfil(6 * MS, 5 * MS, swing=0.030, dinamica=9, arco=7),
    "hat_abierto": Perfil(8 * MS, 4 * MS, swing=0.030, dinamica=7),
    "percusion": Perfil(4 * MS, 7 * MS, swing=0.030, dinamica=10, arco=9),
    # el bajo empuja: entra apenas antes y por eso el groove tira hacia adelante
    "bajo":     Perfil(-4 * MS, 3 * MS, 0.0, dinamica=6, arco=6),
    "acordes":  Perfil(12 * MS, 6 * MS, 0.0, dinamica=8, arco=9),
    # el gancho es lo mas expresivo: es la capa que se toca, no la que se programa
    "gancho":   Perfil(8 * MS, 11 * MS, 0.0, dinamica=13, arco=11),
}
POR_DEFECTO = Perfil()
FRASE = 8          # compases sobre los que se dibuja el arco de dinamica


def _azar(semilla: int, rol: str, compas: int, pulso: float) -> float:
    """Un numero en [-1, 1], estable para la misma nota entre corridas."""
    clave = f"{semilla}|{rol}|{compas}|{pulso:.4f}".encode()
    n = int.from_bytes(hashlib.blake2b(clave, digest_size=4).digest(), "big")
    return n / 2147483647.5 - 1.0


class Humano:
    """Mueve una nota segun el perfil de su rol."""

    def __init__(self, semilla: int = 7) -> None:
        self.semilla = semilla

    def pulso(self, rol: str, compas: int, pulso: float) -> float:
        p = PERFILES.get(rol, POR_DEFECTO)
        fuera = pulso + p.corrimiento
        # swing: solo las semicorcheas impares, que son las de contratiempo
        if p.swing and abs((pulso * 4) % 2 - 1) < 1e-6:
            fuera += p.swing
        fuera += p.dispersion * _azar(self.semilla, rol, compas, pulso)
        return max(0.0, fuera)

    def vel(self, rol: str, compas: int, pulso: float, base: int) -> int:
        p = PERFILES.get(rol, POR_DEFECTO)
        v = base + p.dinamica * _azar(self.semilla + 1, rol, compas, pulso)
        if p.arco:
            # Sube hacia el final de la frase de ocho compases: es lo que hace
            # que ocho compases se sientan como una frase y no como ocho
            # compases sueltos.
            #
            # La curva es cuadratica y no una recta. Con la recta el
            # crecimiento se repartia parejo entre los ocho compases, y un
            # crecimiento parejo no se escucha como crecimiento: lo unico que
            # se escuchaba era la caida de golpe al empezar el bloque
            # siguiente. Con la curva casi todo el movimiento vive en los dos
            # ultimos compases, que es donde el oido esta esperando que pase
            # algo, y lo que llega despues llega preparado en vez de aparecer.
            posicion = (compas % FRASE) / (FRASE - 1)
            v += p.arco * (2 * posicion ** 2 - 0.4)
        return max(1, min(127, int(round(v))))
