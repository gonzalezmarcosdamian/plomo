"""Carga instrumentos y efectos desde el browser de Live.

Agregado para el proyecto plomo. AbletonOSC expone casi todo el Live Object
Model pero no el browser, asi que se podian crear pistas MIDI y meterles clips
y despues habia que arrastrar el instrumento a mano — justo el ultimo paso.

Direcciones:
    /live/browser/list          categoria            -> nombres disponibles
    /live/browser/load          track_index, categoria, nombre [, slot]
    /live/browser/load_default  track_index, tipo    ("instrumento" | "bateria")
    /live/arrangement/duplicate track_index, slot, compas

`categoria` es una de las ramas del browser: instruments, drums, audio_effects,
midi_effects, sounds, packs, user_library.

El nombre se busca sin distinguir mayusculas y por coincidencia parcial, asi que
"wavetable" encuentra "Wavetable". Si hay mas de uno, gana el mas corto: entre
"Bass" y "Bass Reverb", el que se pidio casi siempre es el primero.
"""
import logging
from typing import Any, Optional, Tuple

import Live

from .handler import AbletonOSCHandler

logger = logging.getLogger("abletonosc")

# Instrumentos que existen en toda instalacion de Live, incluida la Trial: no
# dependen de packs descargados. Son el fallback cuando no se pide nada.
POR_DEFECTO = {
    "instrumento": ["Wavetable", "Analog", "Operator", "Collision"],
    "bateria": ["Drum Rack", "Impulse"],
}


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    def _browser(self):
        return Live.Application.get_application().browser

    def _rama(self, categoria: str):
        rama = getattr(self._browser(), categoria, None)
        if rama is None:
            raise ValueError("categoria desconocida: %s" % categoria)
        return rama

    def _recorrer(self, item, profundidad: int = 0):
        """Aplana el arbol del browser. Se corta a 4 niveles: mas abajo son
        presets de presets y la busqueda se vuelve lenta sin ganar nada."""
        if profundidad > 4:
            return
        for hijo in item.children:
            if hijo.is_loadable:
                yield hijo
            if hijo.children:
                for nieto in self._recorrer(hijo, profundidad + 1):
                    yield nieto

    def _buscar(self, categoria: str, nombre: str):
        objetivo = nombre.lower()
        candidatos = [x for x in self._recorrer(self._rama(categoria))
                      if objetivo in x.name.lower()]
        if not candidatos:
            return None
        # exacto primero; si no, el nombre mas corto que contenga lo pedido
        for c in candidatos:
            if c.name.lower() == objetivo:
                return c
        return min(candidatos, key=lambda x: len(x.name))

    def init_api(self):
        def listar(params: Optional[Tuple[Any]] = ()):
            # Segundo parametro opcional: filtro por subcadena. Sin el, ramas
            # como `drums` devuelven cientos de one-shots antes de llegar a los
            # kits y el corte de 200 deja afuera justo lo que se busca.
            categoria = str(params[0])
            filtro = str(params[1]).lower() if len(params) > 1 else ""
            nombres = [x.name for x in self._recorrer(self._rama(categoria))
                       if filtro in x.name.lower()]
            return (categoria, len(nombres), *nombres[:200])

        def cargar(params: Optional[Tuple[Any]] = ()):
            indice, categoria, nombre = int(params[0]), str(params[1]), str(params[2])
            slot = int(params[3]) if len(params) > 3 else None
            item = self._buscar(categoria, nombre)
            if item is None:
                logger.warning("browser: no se encontro '%s' en %s" % (nombre, categoria))
                return (indice, "no encontrado", nombre)
            # load_item carga sobre la pista seleccionada, asi que primero se
            # selecciona la pista destino. Es la unica forma que da el API.
            self.song.view.selected_track = self.song.tracks[indice]
            # Para un sample no alcanza con la pista: Live lo deja en el slot
            # DESTACADO, que es `highlighted_clip_slot` y no es lo mismo que
            # `selected_clip` del handler de view. Sin esto el load contesta ok
            # y no aparece ningun clip.
            if slot is not None:
                self.song.view.highlighted_clip_slot =                     self.song.tracks[indice].clip_slots[slot]
            self._browser().load_item(item)
            logger.info("browser: cargado '%s' en pista %d" % (item.name, indice))
            return (indice, "ok", item.name)

        def cargar_por_defecto(params: Optional[Tuple[Any]] = ()):
            indice, tipo = int(params[0]), str(params[1])
            categoria = "drums" if tipo == "bateria" else "instruments"
            for nombre in POR_DEFECTO.get(tipo, POR_DEFECTO["instrumento"]):
                item = self._buscar(categoria, nombre)
                if item is not None:
                    self.song.view.selected_track = self.song.tracks[indice]
                    self._browser().load_item(item)
                    return (indice, "ok", item.name)
            return (indice, "no encontrado", tipo)

        def a_arrangement(params: Optional[Tuple[Any]] = ()):
            """Copia un clip de Session al Arrangement, en el compas que se pida.

            AbletonOSC lee el Arrangement pero no escribe: sin esto todo lo que
            se genera por codigo vive en clips de Session, que es donde no se ve
            la forma del tema ni se pueden poner locators — los locators viven
            en el Arrangement y con el Arrangement vacio Live ni siquiera deja
            mover el cursor.

            `duplicate_clip_to_arrangement` esta en el Live Object Model y no
            hace falta ningun permiso especial; simplemente nadie lo habia
            expuesto.
            """
            pista, slot, compas = int(params[0]), int(params[1]), float(params[2])
            track = self.song.tracks[pista]
            clip = track.clip_slots[slot].clip
            if clip is None:
                return (pista, "sin clip", slot)
            track.duplicate_clip_to_arrangement(clip, compas * 4.0)
            return (pista, "ok", compas)

        self.osc_server.add_handler("/live/arrangement/duplicate", a_arrangement)
        self.osc_server.add_handler("/live/browser/list", listar)
        self.osc_server.add_handler("/live/browser/load", cargar)
        self.osc_server.add_handler("/live/browser/load_default", cargar_por_defecto)
