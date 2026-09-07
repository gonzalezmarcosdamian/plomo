"""Escritor minimo de archivos MIDI, sin dependencias.

Existe para no sumar `mido` ni `pretty_midi` al proyecto por algo que son
ochenta lineas: escribir notas en un archivo que Ableton abra. Formato 1, una
pista por archivo, tempo en la pista.

    m = Pista("Bajo", bpm=124)
    m.nota(compas=0, pulso=0.5, altura=45, duracion=0.5, velocidad=100)
    m.guardar(Path("bajo.mid"))
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

TICKS_POR_NEGRA = 480
PULSOS_POR_COMPAS = 4


def _vlq(n: int) -> bytes:
    """Variable-length quantity: como MIDI codifica los deltas de tiempo."""
    if n == 0:
        return b"\x00"
    partes = []
    while n:
        partes.append(n & 0x7F)
        n >>= 7
    return bytes([p | 0x80 for p in reversed(partes[1:])] + [partes[0]])


@dataclass(order=True)
class _Evento:
    tick: int
    orden: int          # note-off antes que note-on en el mismo tick
    datos: bytes = field(compare=False)


class Pista:
    """Una pista MIDI. Las posiciones se dan en compases y pulsos, no en ticks."""

    def __init__(self, nombre: str, bpm: float, canal: int = 0) -> None:
        self.nombre = nombre
        self.bpm = bpm
        self.canal = canal
        self._eventos: list[_Evento] = []

    def _tick(self, compas: float, pulso: float) -> int:
        return int(round((compas * PULSOS_POR_COMPAS + pulso) * TICKS_POR_NEGRA))

    def nota(self, compas: float, pulso: float, altura: int,
             duracion: float, velocidad: int = 100) -> None:
        """duracion en pulsos (1.0 = negra, 0.25 = semicorchea)."""
        ini = self._tick(compas, pulso)
        fin = ini + max(int(duracion * TICKS_POR_NEGRA), 1)
        altura = max(0, min(127, altura))
        self._eventos.append(_Evento(ini, 1, bytes([0x90 | self.canal, altura, velocidad])))
        self._eventos.append(_Evento(fin, 0, bytes([0x80 | self.canal, altura, 0])))

    def acorde(self, compas: float, pulso: float, alturas: list[int],
               duracion: float, velocidad: int = 90) -> None:
        for a in alturas:
            self.nota(compas, pulso, a, duracion, velocidad)

    def _cuerpo(self) -> bytes:
        meta = b""
        nombre = self.nombre.encode("utf-8")[:127]
        meta += b"\x00\xff\x03" + bytes([len(nombre)]) + nombre
        us = int(round(60_000_000 / self.bpm))
        meta += b"\x00\xff\x51\x03" + us.to_bytes(3, "big")

        cuerpo, anterior = meta, 0
        for ev in sorted(self._eventos):
            cuerpo += _vlq(ev.tick - anterior) + ev.datos
            anterior = ev.tick
        return cuerpo + b"\x00\xff\x2f\x00"

    def guardar(self, destino: Path) -> Path:
        destino.parent.mkdir(parents=True, exist_ok=True)
        cabecera = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_POR_NEGRA)
        cuerpo = self._cuerpo()
        pista = b"MTrk" + struct.pack(">I", len(cuerpo)) + cuerpo
        destino.write_bytes(cabecera + pista)
        return destino


# -- teoria minima ----------------------------------------------------------
# Camelot -> (semitono de la tonica, modo). A = menor, B = mayor.
_CAMELOT_TONICA = {
    1: 8, 2: 3, 3: 10, 4: 5, 5: 0, 6: 7, 7: 2, 8: 9, 9: 4, 10: 11, 11: 6, 12: 1,
}
NOMBRES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MENOR = [0, 2, 3, 5, 7, 8, 10]   # eolica
MAYOR = [0, 2, 4, 5, 7, 9, 11]


def tonica_de_camelot(camelot: str) -> tuple[int, bool]:
    """'8A' -> (9, True) = La, menor. Devuelve (semitono 0-11, es_menor)."""
    num = int("".join(c for c in camelot if c.isdigit()))
    menor = camelot.strip().upper().endswith("A")
    tonica = _CAMELOT_TONICA[num]
    return (tonica if menor else (tonica + 3) % 12), menor


def nombre_tonalidad(camelot: str) -> str:
    tonica, menor = tonica_de_camelot(camelot)
    return f"{NOMBRES[tonica]}{'m' if menor else ''}"


def grado(tonica: int, escala: list[int], g: int, octava: int = 3) -> int:
    """Nota MIDI del grado `g` (0 = tonica) en la octava dada."""
    saltos, indice = divmod(g, len(escala))
    return 12 * (octava + 1) + tonica + escala[indice] + 12 * saltos


def triada(tonica: int, escala: list[int], g: int, octava: int = 3,
           septima: bool = True, novena: bool = False) -> list[int]:
    """Acorde por terceras sobre el grado `g` de la escala."""
    grados = [g, g + 2, g + 4] + ([g + 6] if septima else []) + ([g + 8] if novena else [])
    return [grado(tonica, escala, x, octava) for x in grados]


# -- lectura ----------------------------------------------------------------
def leer(ruta: Path) -> tuple[str, float, list[tuple[float, float, int, int]]]:
    """Devuelve (nombre, bpm, notas) donde cada nota es
    (inicio_en_pulsos, duracion_en_pulsos, altura, velocidad).

    Solo entiende lo que escribe `Pista`: formato 1, una pista, sin running
    status. Alcanza para volver a leer lo que este mismo modulo genero.
    """
    d = ruta.read_bytes()
    if d[:4] != b"MThd":
        raise ValueError(f"{ruta.name}: no es un archivo MIDI")
    _, _, _, division = struct.unpack(">IHHH", d[4:14])
    i = 14
    if d[i:i + 4] != b"MTrk":
        raise ValueError(f"{ruta.name}: falta la pista")
    largo = struct.unpack(">I", d[i + 4:i + 8])[0]
    i += 8
    fin = i + largo

    tick, bpm, nombre = 0, 120.0, ""
    abiertas: dict[int, tuple[int, int]] = {}
    notas: list[tuple[float, float, int, int]] = []
    while i < fin:
        delta = 0
        while True:
            b = d[i]
            i += 1
            delta = (delta << 7) | (b & 0x7F)
            if not b & 0x80:
                break
        tick += delta
        estado = d[i]
        if estado == 0xFF:
            tipo, n = d[i + 1], d[i + 2]
            datos = d[i + 3:i + 3 + n]
            i += 3 + n
            if tipo == 0x51:
                bpm = 60_000_000 / int.from_bytes(datos, "big")
            elif tipo == 0x03:
                nombre = datos.decode("utf-8", "replace")
        elif estado & 0xF0 in (0x80, 0x90):
            altura, velocidad = d[i + 1], d[i + 2]
            i += 3
            if estado & 0xF0 == 0x90 and velocidad:
                abiertas[altura] = (tick, velocidad)
            elif altura in abiertas:
                ini, vel = abiertas.pop(altura)
                notas.append((ini / division, (tick - ini) / division, altura, vel))
        else:
            i += 3
    return nombre, bpm, sorted(notas)
