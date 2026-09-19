# Plugins e instrumentos de afuera

Que se bajo, por que, y que problema medido resuelve cada uno. Todo es gratis y
de descarga directa del sitio del fabricante; nada de esto necesita cuenta.

Los `.vst3` estan en `C:\Users\gonza\Documents\VST3` y NO en
`C:\Program Files\Common Files\VST3`, que es donde Live mira por defecto:
esa carpeta necesita permisos de administrador y la sesion no los tiene. Para
que Live los vea hay que apuntarle una sola vez:

    Options > Preferences > Plug-Ins
      Use VST3 Plug-In System Folders   -> On
      VST3 Plug-In Custom Folder        -> C:\Users\gonza\Documents\VST3
      Rescan

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

## Lo bajado que falta instalar

Son instaladores y piden permisos; el doble clic lo tiene que hacer una persona.

- `postproduction/descargas/Install_Xfer_OTT.exe` — **OTT**, el compresor
  multibanda de Xfer. Es el que mas se acerca al "suena producido": la cresta
  de bateria propia da 12-18 dB contra 9-11 de las referencias.
- `postproduction/descargas/Sitala-Setup.msi` — **Sitala**, sampler de bateria
  de 16 pads. Alternativa al Drum Rack con mapeo fijo y conocido.

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
