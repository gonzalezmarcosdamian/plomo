# El bucle: cómo el productor aprende solo

*2026-09-09. Pedido del DJ: "necesito un plan para que evoluciones", y después:
"todo el esfuerzo en iterar los agentes y la lógica para hacer temas más
parecidos a las referencias".*

## El problema que había

Hasta hoy el ciclo era: yo cambio algo, el DJ escucha, dice una frase, yo busco
el número que la explica. Cada vuelta costaba una escucha humana, y la mitad de
las veces la frase apuntaba a otra cosa ("suena a ringtone" resultó ser mezcla
mono + pump que no llega + pads que no respiran, tres cosas que ningún oído
nombra por separado).

La causa era una sola: **todo lo que medía era MIDI propio o audio ajeno.** Del
audio del propio tema no había nada. Y "suena a ringtone" es una propiedad del
audio.

## Lo que se destrabó hoy

Grabar no es exportar. `scripts/render.py` toma el master por Resampling, Live
lo escribe a disco aunque no pueda guardar el set, y `traducir.py` lo mide con
el mismo instrumento que mide una referencia. `scripts/iterar.py` junta las dos
y devuelve una tabla: dieciocho dimensiones, referencia contra propio, y cuánto
falta.

La primera pasada (v2, drop 2, contra el remix de Kebin Van Reeken):

    dimension             referencia   propio   veredicto
    bombo x compas             4.00     4.00    ok
    clap x compas              6.69     7.44    ok
    percusion x compas         8.69    10.12    ok
    hat x compas               9.19     7.88    ok
    bajo ataques               2.62     2.00    ok
    bajo suena                 76%     100%     propio MAS alto
    melodia ataques            0.81     6.88    propio MAS alto
    melodia suena              77%     100%     propio MAS alto
    sidechain bajo           -14.3 dB  -2.3 dB  propio MAS alto
    sidechain melodico        -8.9 dB  -1.7 dB  propio MAS alto
    ancho bajo medios          0.30     0.01    propio mas bajo
    ancho bat agudos           0.90     0.01    propio mas bajo
    cresta bajo               15.9 dB  13.7 dB  propio mas bajo
    cresta bateria            11.5 dB  17.0 dB  propio MAS alto

Nueve de dieciocho fuera de tolerancia. Todas con nombre. Ninguna la había
dicho nadie en esas palabras.

## Lo que el bucle NO decide

Acercarse a la referencia en todo a la vez no es el objetivo: es una copia. El
DJ elige la referencia y qué dimensiones importan; el bucle solo evita que una
iteración crea que mejoró cuando se alejó. El oído sigue siendo el juez de si
el tema *dice algo*. Esto detecta defectos, no ausencias.

## El plan, en orden

### 0. Destrabar el ancho (bloqueante, y es del DJ)

El master de este Live sale en **mono**: Resampling graba lo que el master
manda a su salida, y si esa salida es un canal, todo se suma antes de grabarse.
Con paneo −0.30 y Haas en la percusión el render dio L y R idénticos.

Es una preferencia de Live y no hay OSC para el master. Se agregó
`/live/master/get/output` al Remote Script para leerlo y fijarlo por código de
acá en adelante (toma efecto al recargar el Control Surface), pero la primera
vez es a mano: **Master › I/O › salida en un par estéreo ("1/2"), y en
Preferences › Audio un dispositivo de salida estéreo.**

Mientras esté en mono, las dos filas de "ancho" de la tabla no significan nada.

### 1. Una dimensión por vuelta

Cada vuelta del bucle cambia UNA cosa, renderiza y mide. Cambiar dos y medir
no dice cuál de las dos hizo qué. Orden por lo que más separa y menos cuesta:

| # | dimensión | qué es | cómo se toca |
|---|---|---|---|
| 1 | melodía suena 100% → 77% | los pads no respiran nunca | MIDI: huecos en acordes y gancho (`idea.py`) |
| 2 | melodía ataques 6.9 → 0.8 | el pump del Auto Pan hace que un pad sostenido cuente 4 ataques por compás | medir con el pump apagado en los pads, o aceptar que es artefacto |
| 3 | sidechain bajo −2 → −14 | el pump existe (el Sub solo mide −31 dB) pero en la mezcla algo rellena el pozo | render por stems propios: `render.py --solo` bajo / subkick / bajo medio |
| 4 | cresta batería 17 → 11.5 | la batería tiene demasiada dinámica: la referencia está más comprimida | Glue Compressor o Drum Buss en la pista de batería |
| 5 | cresta bajo 13.7 → 15.9 | el bajo está más aplastado que la referencia | menos Saturator |
| 6 | ancho | (después del punto 0) | ya está puesto: Utility + Haas; se verifica |

### 2. Stems propios, no Demucs sobre lo propio

Demucs decide a qué stem va cada capa nuestra, y no siempre acierta: el
subkick (un seno sintético) cae en "bass" y rellena el pozo del pump. Con
`render.py --solo` se graban grupos —batería / bajo / melódico— directo de Live
y se comparan con los stems de Demucs de la referencia. Es la comparación
justa, y saca la separación de la ecuación en el lado propio.

### 3. El corpus, no una referencia

Una referencia es un punto; un género es una nube. `estructura.py` y
`traducir.py` corren sobre N referencias y las tolerancias de `iterar.py`
dejan de ser fijas: pasan a ser la dispersión medida entre referencias del
mismo género. Sin esto, acercarse a Van Reeken es acercarse a Van Reeken.

### 4. Automatización

OSC no llega a los envelopes de los clips, así que los filtros están quietos
ocho minutos — y un timbre quieto ocho minutos es en sí un tell de demo.
Pendiente probar `clip.create_automation_envelope()` desde el Remote Script.
Si no se puede: un rol partido en dos pistas con filtros distintos que suenan
en secciones distintas, que es lo mismo por otro camino.

### 5. Recién ahí, la recursión

Cuando las vueltas 1-2 sean estables y el corpus exista, `iterar.py` puede
correr solo: cambia una cosa, renderiza, mide, y se queda con el cambio solo
si acercó SIN alejar otra dimensión. Antes de eso, un bucle automático
optimiza lo medible y se aleja de lo que importa.

## Quién hace qué

- **`productor`** mide referencias y traduce números a frases (ya existe).
- **`mezclador`** (nuevo) corre el bucle: render, tabla, una dimensión por
  vuelta, y documenta cada vuelta en la bitácora con el antes y el después.
- **El DJ** elige la referencia, dice qué dimensión importa, y escucha lo que
  el bucle no ve.

## Los tres comandos

    python scripts/render.py v2 --desde 161 --compases 16
    python scripts/iterar.py v2 --ref "<mp3>" --ref-desde 283 --solo-medir postproduction/render/v2_161-176.wav
    python scripts/iterar.py v2 --ref "<mp3>" --ref-desde 283 --desde 161     # renderiza y mide
