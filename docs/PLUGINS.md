# Plugins e instrumentos de afuera

Que se bajo, por que, y que problema medido resuelve cada uno. Todo es gratis y
de descarga directa del sitio del fabricante; nada de esto necesita cuenta.

Los diez `.vst3` estan instalados en `C:\Program Files\Common Files\VST3`,
que es donde Live mira por defecto. No hace falta configurar ninguna carpeta.

**Falta UN toggle, y lo tiene que hacer una persona.** La base del escaner de
plugins (`%LOCALAPPDATA%\Ableton\Live Database\Live-plugins-1.db`) esta
vacia y el log dice `Scan start` seguido inmediatamente de `Scan end`: el
escaneo corre y no mira las carpetas de sistema porque la opcion esta apagada.

    Options > Preferences > Plug-Ins
      Use VST3 Plug-In System Folders  ->  On
      (si hace falta) Rescan

No se puede hacer por codigo. El flag vive en `Preferences.cfg`, que es un
formato binario serializado donde el valor NO esta pegado a su nombre:
`AreSystemPathsEnabled` aparece seguido del tipo `RemoteableBool` y enseguida
el campo siguiente, sin un byte de valor en el medio. Parchearlo a ciegas es
como se rompe la instalacion de un DAW, y ademas Live reescribe ese archivo al
cerrar, asi que el parche se perderia igual.

## Lo instalado

| plugin | que es | que problema medido resuelve |
|---|---|---|
| **TAL-Filter-2** | filtro modulado y sincronizado al tempo | el movimiento de filtro. El puente OSC no llega a los envelopes de los clips, asi que los filtros del tema estan QUIETOS los ocho minutos — y un centroide que no se mueve es la firma de un boceto. Este modula solo, sincronizado, sin automatizacion. |
| **TAL-Reverb-4** | reverb de placa | la cola de lo melodico: 0.12 s propio contra 0.20 de la referencia |
| **TDR Nova** | EQ dinamico de cuatro bandas | el balance por bandas, que es como se mide la forma del tema |
| **Surge XT** | sintetizador hibrido (+ 30 efectos) | los sonidos. La atmosfera ataca 4.25 veces por compas sin pump: es el LFO del preset de fabrica, y es parte de lo que suena a ringtone |
| **TAL-NoiseMaker** | sintetizador virtual-analogico | lo mismo: pads y bajos que no son presets de fabrica de Live |
| **TAL-Chorus-LX** | chorus del Juno-60 | el ancho. El bajo propio mide 0.02 de ancho en medios contra 0.27 |
| **TAL-Vocoder-2** | vocoder vintage | pendiente: voces sin necesitar samples con licencia |

| **OTT** (Xfer) | compresor multibanda | el "suena producido": la cresta de bateria propia da 12-18 dB contra 9-11 de las referencias |
| **Sitala** | sampler de bateria de 16 pads | alternativa al Drum Rack con mapeo fijo y conocido — los Drum Racks de fabrica no siguen el mapa del 909 y eso ya costo dos capas mudas |

## Lo que hay que bajar a mano (piden mail o cuenta)

- **Valhalla Supermassive** — valhalladsp.com. Reverb/delay gratis, de lo mejor
  que hay para pads y breakdowns. Pide mail en un formulario.
- **Vital** — vital.audio. El mejor sintetizador wavetable gratis. Pide cuenta.
- **Packs oficiales de Ableton** — con la licencia Suite hay ~70 GB en la cuenta
  y la carpeta `Factory Packs` esta VACIA. Se bajan desde Live (`Places > Packs`)
  o desde ableton.com/account. Los que sirven para este genero, por orden:
  Drum Booth y Drum Essentials (baterias), Glitch and Wash y Spectral Textures
  (texturas, que es lo que le falta al tema), Drone Lab, Drive and Glow
  (saturacion analogica), Beat Tools, Chop and Swing.

## Max for Live

Esta instalado (`Resources/Max` existe con la licencia Suite) y todavia no se
uso. Su dispositivo **LFO** puede modular CUALQUIER parametro de cualquier
dispositivo, que es exactamente lo que el puente OSC no puede hacer. Es la via
para que los filtros se muevan a lo largo del tema sin escribir automatizacion.
Pendiente de probar.
