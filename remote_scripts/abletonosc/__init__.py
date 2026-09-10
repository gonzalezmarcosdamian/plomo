import logging
logger = logging.getLogger("abletonosc")

logger.info("Reloading abletonosc...")

from .osc_server import OSCServer
from .application import ApplicationHandler
from .song import SongHandler
from .clip import ClipHandler
from .clip_slot import ClipSlotHandler
from .track import TrackHandler
from .device import DeviceHandler
from .scene import SceneHandler
from .view import ViewHandler
from .midimap import MidiMapHandler
# Agregado por el proyecto plomo: AbletonOSC expone casi todo el Live Object
# Model pero no el browser, asi que faltaba justo el ultimo paso — cargar el
# instrumento en la pista. Ver browser.py.
# Recargar el modulo propio al re-instanciar el script. Reseleccionar el
# Control Surface en Preferences vuelve a crear el Manager, pero Python conserva
# los modulos ya importados: un handler nuevo en browser.py seguia dando
# "Unknown OSC address" hasta reiniciar Live entero (y el set, que no se puede
# guardar, se pierde). Con el reload alcanza con reseleccionar el Control
# Surface. Solo el modulo propio: los de AbletonOSC no cambian.
import importlib
from . import browser as _browser
importlib.reload(_browser)
from .browser import BrowserHandler
from .constants import OSC_LISTEN_PORT, OSC_RESPONSE_PORT
