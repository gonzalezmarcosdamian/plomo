# Aprendizajes

Lo que sirve después, sin la anécdota. Cada uno con **qué pasó**, **por qué** y
**cómo se aplica**.

Se corrigen cuando se demuestra que estaban mal: un aprendizaje equivocado es
peor que ninguno, porque se aplica con confianza.

---

## "Colorido" era un nombre, no un numero — y el set entero estaba en menor

**Que paso.** El DJ escucho el set de 1 a 3 y dijo: "un par medios oscuros para
ser el colorido". Buscando esos dos temas aparecio algo mas grande: los SIETE
sets del cumple tenian **0% de temas en tonalidad mayor**. No un par de temas
oscuros: el set entero en modo menor, de punta a punta.

Los numeros, sobre 15 setlists de referencia con key:

| | mayor | cambios de modo entre temas |
|---|---|---|
| los pros | 11% (p25 8%, p75 20%) | **25%** |
| Ezequiel Arias, que el DJ sigue | 25% | |
| nuestros sets | **0%** | **0%** |

Nada lo prohibia. Pasar de 8A a 8B es distancia 1 en Camelot y estaba
permitido con `max_camelot_dist` en 2. Lo que no habia era algo que lo
premiara, y como el 84% de la biblioteca esta en menor, el solver nunca tenia
motivo para cruzar. Una preferencia que no se escribe en el costo no existe.

Los dos temas oscuros que el DJ escucho eran, efectivamente, los dos primeros:
Imentet (percentil 33 de brillo) y Open Sea (43). Son la apertura que el eligio
para el 139 y ahi estan bien; la variante colorida los heredaba del config base
y abria oscura por herencia, no por decision.

**Por que importa.** "Colorido" venia implementado como una lista de preferidos
por brillo aplicada por AFUERA del costo. Empujaba, pero no impedia nada: el
set podia arrancar con lo mas oscuro que tuviera y seguir llamandose colorido.
Un adjetivo que no es un numero no se puede cumplir ni verificar.

**Como se aplica.** Cuando el DJ pide un caracter ("colorido", "oscuro",
"organico"), traducirlo a rasgos medibles ANTES de armar, calibrarlos contra la
referencia, y meterlos en el costo. Colorido son dos numeros: `modo_mayor_
objetivo` 0.25 (donde esta Ezequiel Arias) y `color_peso` sobre el brillo. Y el
control que lo hubiera cachado antes: mirar el reparto del rasgo en el set
terminado, no solo si los temas "suenan" al pedido.

---

## Una cuota sobre algo binario hay que cobrarla de los dos lados

**Que paso.** La cuota de tonalidad mayor, recien puesta, movio el set colorido
de 0% a 6% cuando el objetivo era 25%. El codigo copiaba la cuota de genero:

    c += (mayores_hasta_aca / (i + 1) - objetivo) * peso

Con generos funciona porque el contador es del genero del candidato: un tema de
House mueve el contador de House. Con una variable binaria no: el contador solo
sube con los mayores, asi que un tema MENOR dejaba el cociente abajo del
objetivo y el termino le daba un DESCUENTO, justo cuando faltaban mayores. La
cuota empujaba para el lado contrario al que decia.

**Por que importa.** El bug no rompe nada, no tira ningun error y deja el set
armado: solo hace lo opuesto de lo que se le pidio, un poco. Del 0% subio a 6%
—por el otro termino, el de brillo— y eso alcanzaba para parecer que andaba.

**Como se aplica.** Una cuota sobre algo binario se cobra en las dos caras: el
mayor contra su objetivo, el menor contra el complemento. Y siempre verificar
una cuota nueva barriendo su peso: si el rasgo no se mueve al subirlo, el
termino esta mal escrito. Aca el barrido lo mostro de una: 2.0 daba 12%, 5.0
daba 24%, y de 5.0 a 9.0 no se movia mas.

---

## La jerarquia estaba escrita en la doc y al reves en el codigo

**Que paso.** El DJ escucho los sets del cumple y saco tres cosas: un tema de
afro house, Meduza - Friends y "nada afro" como categoria. Despues dijo donde
estaba el problema de fondo: "quiero que domine la energia y groove constante,
luego lo progresivo y luego recien la cuota de genero; artistas le gana,
productores le gana a cuota de genero".

Medido en el codigo, la escala real era:

| termino | peso |
|---|---|
| cuota de genero (`peso_mezcla`) | **8.0** |
| desvio del arco de energia | 3.0 |
| groove | no existia |
| de que escena viene el tema | no existia |

La cuota de genero pesaba 2.7 veces mas que la energia, y los cuatro temas que
el DJ rechazo entraron todos por ahi: pedir "20% de House" obliga al solver a
meter el House que haya, y lo que habia era Meduza, David Guetta y Kiko Navarro.
Peor: los seis configs del cumple traian `"peso_mezcla": 8.0` escrito adentro,
asi que bajar la regla no hubiera cambiado nada. Dos capas de la misma decision,
y la de abajo ganando en silencio.

**El eje que faltaba no era el que yo pensaba.** Primero probe medir "mi sonido"
por la FORMA del audio (donde cae el breakdown, balance espectral, rango
dinamico), que es lo que ya teniamos indexado. No los distingue: los cuatro
rechazados quedaban a 2.6-3.7 de sus favoritos contra una mediana de 2.40 de la
biblioteca entera. Un umbral que los cortara se comia media coleccion.

Lo que si los separa es la PROCEDENCIA. Cruzando artista y sello contra
`djmdHistory` —lo que el DJ efectivamente toco, que no lo escribio el solver—:
los cuatro rechazados eran los cuatro unicos temas de esos sets con artista Y
sello ajenos a su historial. Y el set 140, el unico que elogio entero, tiene
cero ajenos en 17 temas.

**Por que importa.** El solver optimizaba key, energia, BPM y cuota de genero.
Para el, dos temas en 9A a 124 BPM con E7.2 son intercambiables aunque uno sea
Cendryma y el otro David Guetta. Le faltaba la pregunta que un DJ se hace
primero: de que mundo viene esto.

**Como se aplica.** La jerarquia vive en `rules/curaduria.json` 1.6.0 y el orden
lo fija el DJ, no el optimizador. Un veto es por CATEGORIA (genero, artista), no
por track: sacar un tema de afro house y que vuelva otro del mismo palo es no
haber entendido el veto. Y antes de agregar un eje nuevo, medir si el que ya
existe lo ve: la forma del audio no veia nada, y me hubiera ahorrado el termino.

---

## Cuando el loop se clava, sospechar del techo — y despues creerle al loop

**Que paso.** Con la jerarquia puesta, el DJ pidio "un loop de entrenamiento de
tus criterios mirando los pro que me gustan". `scripts/entrenar_criterio.py`
hace descenso por coordenadas: mueve un peso por vez, arma los sets, los mide
con la misma vara que a los 40 setlists de referencia, y se queda con el que
acorta la distancia.

La primera corrida bajo la perdida de 3.40 a 2.55 y ahi se clavo, con una
diferencia sistematica que ningun peso movia:

| rasgo | nuestro | pro |
|---|---|---|
| paso de energia entre temas | 0.55 | **1.00** |
| paso de BPM | 1.00 | **2.00** |
| corr(posicion, energia) | +0.35 | +0.11 |

Nuestros sets se mueven MENOS que los de los pros, no mas. La hipotesis obvia
era el techo: `energia.max_escalon` estaba en 1.3 y el p90 de los pros es 2.50,
o sea que el solver tenia prohibido el paso que ellos dan. Entraron al loop
`max_escalon` y `max_bpm_jump` como coordenadas propias.

**El loop refuto la hipotesis.** Aflojar el techo a 1.8, 2.3 o 2.8 da 3.107 de
perdida contra 2.467 con el techo en 1.3, y las tres dan exactamente lo mismo:
pasos mayores a 1.8 no aparecen ni cuando se permiten. El freno no era el limite
duro, era el costo. Lo que si mejoro fue subir energia (6.0 -> 8.0) y groove
(4.0 -> 6.0), que dejaron la perdida en 2.467.

**Por que importa.** Un optimizador siempre devuelve un optimo, y el optimo
adentro de una caja chica parece un buen resultado, asi que sospechar del techo
cuando el loop se clava es el reflejo correcto. Lo que no es correcto es
quedarse con la sospecha: yo ya habia escrito el aprendizaje con el techo como
culpable antes de que terminara la corrida que lo desmintio.

**Como se aplica.** Cuando un rasgo no cierra, probar el limite duro COMO UNA
COORDENADA MAS y dejar que el numero decida. Y no escribir la conclusion antes
del resultado, por mas que la hipotesis parezca obvia. Los tres rasgos siguen
cortos: es lo proximo a entender, y todavia no se por que.

---


## Un set sin tracklist igual se puede medir: el arco esta en el audio

**Que paso.** El DJ mando un set que le volo la cabeza (Maze 28 en La Biblioteca,
29/08/2026, tres horas) y pidio aprender de el. No tiene tracklist publicado: en
los comentarios hay cuatro personas pidiendolo y nadie contesta. Con el metodo de
siempre —nombres de temas, cruzarlos contra la biblioteca, sacar energia y key—
el set era inservible. Bajando el audio y midiendolo por bloques de un minuto
(`scripts/arco_de_audio.py`) salieron tres horas de dato de un DJ que el DJ
admire, tocando en el club que le importa.

**Por que.** La evidencia de referencia del proyecto eran setlists: texto. Eso
deja afuera la mayoria de los sets buenos, y ademas la energia que les
atribuimos sale de NUESTRO calculo sobre NUESTRA copia del track, no de lo que
sono esa noche. El audio del set no tiene ninguno de los dos problemas: es el
set entero, en orden, con las mezclas y el EQ reales. Se pierde la identidad de
los temas y se gana el arco, que es justamente lo que el solver decide.

Dos trampas que costaron tiempo:

- **El RMS de un set de YouTube no es energia.** La plataforma normaliza y el
  sistema del club comprime: 10 dB de rango en tres horas, plano. Lo que
  sobrevive es el brillo (banda de aire), la densidad de onsets y el tempo.
- **Un estimador de tempo devuelve valores de una grilla.** Los 178 bloques
  dieron 117.5 exacto y eso parecia un bug. Tres metodos independientes
  (`tempo()`, `beat_track`, tempograma con interpolacion parabolica) en cinco
  momentos distintos dieron 117.45-117.83: era real. Un numero sospechosamente
  redondo se confirma con otro metodo antes de tirarlo Y antes de creerlo.

**Como se aplica.** Cuando un set de referencia no tiene tracklist, medirle el
arco igual: `python scripts/arco_de_audio.py <audio.wav> --nombre <slug>`, y
comparar contra los nuestros con la MISMA vara (para los nuestros, aire y
densidad de `data/recetas/lib/` puestos minuto a minuto). Nunca comparar la
curva del audio contra la escala E1-E10 de la biblioteca: son unidades
distintas.

---

## Lo que el pro no hace tambien es dato: meseta, no rampa

**Que paso.** Medido el set de Maze contra nuestra noche del cumple (140 + 139 +
141, 381 min), con la misma vara:

| | corr(posicion, energia) | pico | meseta (+-0.3 z) | BPM |
|---|---|---|---|---|
| Maze, 3 h | **-0.05** | 36% | **74% del set** | 117.5 plano |
| nuestra noche | +0.19 | 83% | 60% | rampa por set |
| 140 warm | **+0.71** | 92% | 50% | 118 -> 122 |
| 139 pico | +0.25 | 43% | 53% | |
| 141 cierre | +0.32 | 48% | 46% | |

El set del pro **no sube**. Entra abajo, sube en los primeros 40 minutos, y hace
meseta dos horas dentro de una banda angosta hasta un corte brutal en los
ultimos cinco minutos (-2.2 z; el nuestro cierra en -0.4). Y lo hace **sin tocar
el tempo**: 117.5 BPM durante tres horas.

**Por que importa.** Nuestro modelo de arco tiene forma de campana: un
`pico_en_pct` y una `caida_post_pico_pct`. El pro no tiene un pico, tiene una
meseta, y la variedad la mete DENTRO de la meseta, no subiendo. Nuestro warm es
el caso extremo opuesto: correlacion +0.71, o sea una rampa casi limpia que
termina arriba de todo.

**Cuanto vale esta evidencia.** Es UN set contra tres nuestros, medido con un
proxy (brillo + densidad) que no es la escala de energia de la biblioteca, y
contra material puesto punta a punta que no puede capturar lo que el pro hace
con el EQ. Ademas el pro toca la noche entera solo, y una meseta puede ser
consecuencia de eso y no una decision. Por eso NO se cambio ninguna regla: queda
como candidato a medir con mas sets de audio antes de tocar `pico_en_pct`.

**Como se aplica.** Antes de dar por buena una rampa, mirar cuanto del set queda
dentro de una banda angosta. Y sumar sets de audio de referencia: con tres o
cuatro mas, "meseta larga + corte final" pasa de anecdota a regla.

---

## Un filtro que falla en silencio es peor que no tener filtro

**Que paso.** Tres veces en la misma sesion el sistema ignoro una instruccion del
DJ sin decir nada. (1) Los vetos se detectaban buscando palabras en la nota
—"tecnoso", "se cae", "lento"—; el DJ escribio "muy abajo" y "malisimo", y los
dos temas que rechazo volvieron al set. (2) Tres temas anclados para dar onda al
arranque no entraron porque no estaban en el pool: el ancla se ignoraba en
silencio. (3) La version "colorida" de un set salio IDENTICA a la base, porque
heredaba las exclusiones del base y el color solo podia reordenar el mismo
material.

**Por que.** Las tres son la misma forma: una instruccion que no se cumple y un
sistema que sigue adelante sin avisar. El resultado se ve bien —hay 17 temas, 0
transiciones flojas— y solo se descubre leyendo el tracklist tema por tema.

**Como se aplica.**
- El veto es una MARCA (`"veto": true` en `data/energia_percibida.json`), no una
  palabra a adivinar en un texto libre.
- `select_set.py` avisa cuando un ancla, una apertura o un cierre no esta en el
  pool, en vez de ignorarlo.
- Una variante que hereda el pool de otra no es una variante. La colorida arma
  el suyo, ordenado por su propio criterio.
- Al terminar, comparar la variante contra su base: si comparten 17 de 17, algo
  no se aplico.

---

## Fijar un tema no fija sus vecinos; y deduplicar por artista no es deduplicar por cancion

**Que paso.** Armando la noche del cumple de Zorro aparecieron dos errores que
ninguna metrica marcaba. Con `cierre_fijo` = Haunted, el set llegaba a Haunted con
un salto de 5 en la rueda: fijar el ultimo tema le salteaba al solver el control
de key del anteultimo. Y en el warm entraron dos remixes de la misma cancion
(Cry of the Deserts): el solver cuenta artistas, no canciones, y con
`max_per_artist` 2 las dos versiones eran legales. Antes, entre sets, Muse habia
sonado dos veces en la noche en dos remixes distintos.

**Por que.** Cada restriccion nueva que saltea las duras (apertura fija, cierre
fijo) deja sin cubrir las transiciones de su borde. Y la identidad de un tema
para el DJ es la CANCION, no el archivo ni el artista.

**Como se aplica.** Toda posicion fija obliga a su vecino a empalmar con ella
(ya en `select_set.py`). Antes de escribir una noche de varios sets, chequear
canciones repetidas por titulo base —sin versiones ni "feat."— dentro de cada set
y entre todos. Y mirar la transicion de entrada y salida de cada tema fijo.

---

## El oido del DJ es la verdad de base; un patron de una escucha no es una regla

**Que paso.** El DJ escucho el set 139 y corrigio tema por tema. Nuestra energia
calculada estaba invertida en varios pares: Sizer daba 5.2 (el mas bajo del set)
y el DJ lo siente de pico; Low Era daba 7.5 y lo siente oscuro y bajo. Error
medio de la formula contra su oido: **1.3 puntos** sobre 7 temas, con dos de 2.5.

En sus correcciones habia patrones claros: los dos temas que rechazo por "baja
energia" eran los dos con menos medios del set (4.2% y 4.3%), el que "se cae
fortisimo" tenia el breakdown mas profundo (26% de su energia de groove), y el
"tecnoso" era el unico sin aire arriba (1.4%).

**Por que.** La energia calculada sale de DONDE caen los cues (Bass IN, Breakdown,
DROP), no de lo que suena. No ve medios, ni profundidad de breakdown, ni brillo.

Pero antes de convertir los patrones en regla se midieron contra los pros: tocan
temas sin medios a la misma tasa que la biblioteca (10.9% contra 8.2%), y
breakdowns que se desploman tambien (18.6% contra 17.4%). No son reglas del
oficio: son el gusto del DJ para esa noche.

**Como se aplica.**
- Lo que el DJ escucho PISA el calculo en todo el sistema:
  `data/energia_percibida.json`, leido por el solver y por el auditor. Cada
  correccion queda como dato para recalibrar la formula cuando haya suficientes.
- Un patron que sale de una escucha va como filtro DE ESE SET y como preferencia
  documentada. Pasa a regla global solo si los pros tambien lo evitan.
- Dos herramientas quedaron por esto: `inicio_fijo` (los primeros temas en el
  orden del DJ, sin restricciones duras) y `anclas_en` (DONDE tiene que caer un
  ancla, no solo que este).

---

## Cuando cuatro palancas distintas dan el mismo numero, el limite no es la palanca

**Que paso.** Los sets recorrian 1.9 puntos de energia donde una ventana del
mismo largo en un set real recorre 2.9: solo 1 de 18 caia en el rango de los DJ
reales, con probabilidad 4%. Se probaron cuatro cosas distintas para moverlo:
ensanchar las bandas `e_lo`/`e_hi`, ensanchar el `e_pool`, subir el beam de 1200
a 4000, y subir el umbral de paso plano de 0.08 a 0.75 —que efectivamente llevo
el escalon tipico de 0.50 a 0.90, el valor de la referencia—. El rango se planto
en 2.0 en las cuatro.

**Por que.** El pool de cada momento, ya filtrado por genero y BPM, tiene su
p10-p90 en 1.4 puntos de energia. Los temas de los extremos existen pero son
poquisimos, y llegar a ellos choca con las otras restricciones —Camelot, tope por
artista, cuota de generos— todas a la vez. Con pasos mas grandes el solver sube
0.9 y baja 0.9: oscila mas fuerte adentro del mismo span. El techo no estaba en
como elegimos sino en entre que elegimos.

**Como se aplica.** Antes de seguir tuneando, mirar la distribucion del POOL, no
la del resultado. Si el p10-p90 del material disponible es mas angosto que lo que
se quiere producir, ninguna funcion de costo lo va a inventar. La accion correcta
sale del dominio del algoritmo y entra en el de la biblioteca: hay que conseguir
material en los extremos. Y el sintoma que lo delata es justamente este —varias
palancas independientes convergiendo al mismo numero—.

---

## Una regla que se lee y no se usa es peor que no tenerla

**Que paso.** `energia.umbral_paso_plano` vivia en `rules/curaduria.json` con su
valor, su porque y su evidencia. `select_set.py` la leia en la linea 45 y no la
usaba en ningun lado: el umbral real era un `max(0.08, ...)` escrito a mano en la
linea 213. El valor documentado, 0.15, no tuvo efecto nunca.

**Por que.** El proyecto tiene las reglas como dato justamente para que cambiarlas
sea discutir el criterio y no editar codigo. Una regla desconectada rompe eso en
la peor direccion posible: no falla, no avisa, y cualquiera que lea el JSON —o que
corra el backtest— cree que esta midiendo algo que el solver mira. Encima esta
importaba: de ese umbral depende el tamano del escalon tipico del set.

**Como se aplica.** Toda constante leida de las reglas tiene que usarse, y la
forma barata de garantizarlo es que no exista una constante equivalente escrita a
mano al lado. Cuando aparezca un `max(<numero>, ...)` o un default junto a un
`R.get(...)`, sospechar: o el numero deberia salir de la regla, o la regla sobra.

---

## Un objetivo que se persigue punto por punto deja de ser un objetivo

**Que paso.** El solver cobraba `|energia - arco(t)| * 3.0` en cada posicion del
set. El arco es una funcion del reloj, asi que minimizar ese costo es,
literalmente, pedir que la energia sea funcion del reloj. Medido: la correlacion
posicion-energia daba +0.79 en nuestros sets contra +0.11 en los de referencia,
fuera del rango entero del corpus (el maximo observado en un set real era +0.60).
El set subia porque el reloj avanzaba, no porque la pista lo pidiera.

**Por que.** Habia dos cosas distintas confundidas en un mismo termino: la FORMA
de la noche, que si es un objetivo, y la POSICION exacta de cada track dentro de
esa forma, que no lo es. Cobrar el desvio punto por punto impone las dos. Un DJ
real respeta la forma y se mueve libre adentro de ella.

La correccion fue convertir el arco en una BANDA: solo se cobra el desvio que se
SALE de la banda, que vale 0.9 del rango de energia del set. La forma sobrevive
—el pico sigue cayendo donde tiene que caer— y adentro hay lugar para subir y
bajar. Con eso la correlacion paso a +0.18, adentro del IQR de referencia.

**Como se aplica.** Cuando una restriccion blanda se cumple demasiado bien,
sospechar que se convirtio en la unica cosa que el optimizador hace. La prueba es
medir la correlacion entre lo optimizado y su variable independiente: si da mucho
mas alto que en los ejemplos reales, el objetivo esta sobre-especificado. La
respuesta casi nunca es bajarle el peso —eso lo unico que hace es una rampa mas
suave, y de hecho empeoro la metrica— sino darle una zona muerta.

---

## Tres casos no son una muestra: la mitad de lo que medi era ruido

**Que paso.** Barri la tolerancia del arco sobre un banco de 3 sets. `tol=1.00`
salio claramente mejor que todo lo demas: correlacion posicion-energia +0.02,
practicamente el +0.11 de referencia. Antes de aplicarlo a los 18 sets lo repeti
sobre un banco de 6, uno por cada momento de la noche. El mismo `tol=1.00` dio
**+0.37**. El ganador real era `tol=0.90`, que en el banco de 3 no se distinguia.

**Por que.** Cada set es un numero, no una medicion repetida: la mediana de 3
salta con que un solo set caiga distinto. Y los 3 del primer banco eran todos del
mismo caracter (Color), asi que compartian pool, generos y banda de energia — no
eran tres muestras, eran casi la misma muestra tres veces.

**Como se aplica.** El banco de validacion tiene que cubrir los ejes por los que
las configuraciones difieren, no repetir el mas comodo. Para sets: uno por
momento, no tres del mismo tipo. Y cualquier ganador que aparezca en el BORDE de
la grilla barrida es sospechoso por default — o el optimo esta mas afuera, o es
ruido. Las dos cosas se chequean igual: ampliando la grilla o el banco.

---

## Un hueco en un setlist no es una transicion

**Que paso.** Para comparar nuestros sets contra el corpus de referencia habia
que medir la autocorrelacion de los saltos de energia. Los setlists reales tienen
tracks sin identificar: si se toman los tracks con energia y se calculan los
saltos entre consecutivos DE ESA LISTA, se esta midiendo el salto entre el track
12 y el 15 como si fueran vecinos. Esa transicion nunca ocurrio.

**Por que.** Es el mismo error que hizo sonar horrible la reconstruccion del set
de Simon: sacar posiciones fabrica adyacencias. En una medicion el efecto es mas
silencioso —no suena mal, solo da un numero equivocado— y por eso es peor.

**Como se aplica.** Los saltos solo se calculan dentro de tramos de posiciones
CONSECUTIVAS. Con esa correccion el corpus quedo en 15 setlists usables de 40, y
las ventanas de 18 tracks seguidos directamente no existen: la mas larga que el
corpus banca es de 12. Conviene saber eso antes de citar un `n=40`.

---

## Cuidado con la metrica que ya contiene la respuesta

**Que paso.** El DJ pidio sets "de mucha energia sin que los BPM se vayan para
arriba". El solver no podia: el score de energia sumaba el BPM como uno de sus
cinco componentes, el 30% del total. Un tema lento tenia un techo de energia que
no podia superar aunque tuviera el drop mas grande del mundo. De 180 tracks con
energia alta, solo 16 eran de tempo bajo.

**Por que.** La metrica no estaba midiendo la cosa: estaba midiendo la cosa MAS
una de sus causas. Cualquier pedido de la forma "quiero mas A sin mas B" es
irrealizable si B esta adentro de la definicion de A, y el sintoma es que el
optimizador siempre devuelve lo mismo por mas que se cambien los pesos.

**Como se aplica.** Antes de tocar las reglas de un optimizador que no da lo que
se le pide, abrir la funcion que calcula la variable objetivo y ver de que esta
hecha. Si contiene una de las variables que se quieren controlar por separado,
ese es el bug y no hay peso que lo arregle. Y al sacar el componente, reescalar
los que quedan para que los umbrales viejos sigan queriendo decir lo mismo.

---

## Reordenar y rearmar son dos problemas distintos

**Que paso.** Habia sets curados a mano en sesiones viejas que con la metrica
nueva quedaron con el arco roto. Rearmarlos desde cero perdia la curaduria, asi
que habia que reordenarlos. El primer intento reuso el solver de seleccion
pasandole como pool los tracks del propio set: devolvio "sin solucion" para
todos. Escrito como busqueda que PENALIZA en vez de filtrar, mejoro 37 sets, el
peor de 25 a 8 violaciones.

**Por que.** Elegir y ordenar se parecen pero tienen factibilidad opuesta. Al
elegir, las restricciones duras son baratas: si un candidato no sirve hay
quinientos mas. Al ordenar, el conjunto esta fijo y lo mas probable es que
NINGUNA permutacion cumpla todo — la respuesta correcta no es "no existe" sino
"esta es la menos mala".

**Como se aplica.** Cuando un solver que filtra se usa sobre un dominio cerrado,
convertir las restricciones duras en costos altos. Se pierde la garantia de
cumplimiento y se gana que siempre devuelva algo, mas la medida de cuanto hubo
que ceder — que suele ser la informacion mas util: un set que necesita saltar
media rueda esta diciendo que el problema es la seleccion, no el orden.

---

## Un setlist al que le falta la mitad no es ese setlist

**Que paso.** Se reconstruyo el set de Simon Vuarambon conservando los 32 tracks
que estaban en la biblioteca de las 59 posiciones reales, en el orden original, y
se entrego como set. Sonaba mal. Al medirlo: 29 transiciones flojas de 31, con
saltos de media rueda de Camelot y de 11 BPM. El DJ que lo escucho lo dijo antes
que la herramienta: "el de Simon horrible estaba, y no fue asi".

**Por que.** Conservar el orden no conserva las transiciones. De cada dos tracks
seguidos en la reconstruccion, trece de treinta y uno no eran seguidos en la
noche: entre ellos habia un tema que faltaba, y ese tema era justamente el puente
que hacia funcionar el salto. Sacar los eslabones y dejar las puntas pegadas
produce una secuencia que ningun DJ toco nunca.

**Como se aplica.** Cuando falta una porcion grande de una secuencia, hay dos
productos posibles y ninguno es "la secuencia": o se entrega FIEL —con los huecos
marcados y la advertencia de que no se mezcla, sirve para estudiar el orden— o se
entrega TOCABLE, usando lo que hay como anclas y dejando que el solver ponga los
puentes con el resto de la biblioteca. Lo segundo ya no es el set de ese DJ y el
nombre tiene que decirlo: "Con el material de X", no "X en tal lado".

---

## Lo que valida no sirve si no se corre

**Que paso.** `audit_sets.py` existia, marca cada transicion floja con su motivo,
y se corrio sobre los tres sets nuevos —dieron cero— pero no sobre los cuatro
reconstruidos, que se entregaron sin auditar. Uno tenia 29 transiciones flojas de
31. La herramienta habria mostrado el problema en dos segundos.

**Por que.** El paso de validacion se salteo justo donde el resultado parecia no
necesitarlo: "es el orden real de un DJ profesional, que puede fallar". Esa
confianza era el error, no el codigo.

**Como se aplica.** El validador se corre sobre TODO lo que se entrega, sobre todo
cuando el material viene de una fuente que se presume buena. Y si un generador
produce algo entregable, que imprima el comando de validacion en su propia salida
—`set_desde_setlist.py` ahora termina diciendo "ahora: build_set.py N &&
audit_sets.py N"— para que saltearlo requiera ignorar una instruccion explicita.

---

## Un hueco borrado en un setlist fabrica una transición que nunca existió

**Qué pasó.** El parser de setlists de referencia descartaba las líneas
`ID - ID` por considerarlas ruido. En un set de tres horas eso es la mitad de las
posiciones: dos tracks que estaban a diez minutos uno del otro quedaban
consecutivos en el JSON, y el backtest medía el salto de Camelot entre ellos como
si el DJ los hubiera mezclado.

**Por qué.** Un tracklist no es una lista de tracks, es una secuencia. El valor
está en la adyacencia, y un `ID` no es la ausencia de un dato: es la presencia de
un track cuyo nombre no se sabe. Borrarlo no deja un agujero, junta los bordes.

**Cómo se aplica.** En cualquier corpus donde se mida la relación entre elementos
vecinos, lo desconocido se guarda como hueco explícito que rompe el par, nunca se
omite. Vale igual para transiciones de un set, para huecos en una serie temporal
y para pasos salteados en un log.

---

## Si el dato propio no alcanza para medir, traelo de donde esté

**Qué pasó.** El corpus de setlists de otros DJs existía para refutar las reglas
propias, pero se enriquecía cruzando contra la biblioteca propia: 6-29% de
cobertura contra el 80% que el backtest exige. El corpus estaba cargado y no
medía nada. Muzpa tenía key y BPM de casi todos esos tracks, incluso de los que
no se tienen; con eso la cobertura pasó a 78-80% y el backtest dio su primer
veredicto no circular.

**Por qué.** El solapamiento entre la colección propia y el repertorio de otro es
justo lo que el corpus vino a medir: usarlo también como fuente de datos hace que
solo se pueda medir lo que uno ya tiene, que es la circularidad de nuevo, un piso
más abajo. La fuente de los metadatos tiene que ser independiente de la hipótesis.

**Cómo se aplica.** Antes de dar por inviable una medición por falta de datos,
preguntarse si el dato existe en un catálogo externo. Y al cruzar entre fuentes,
no usar como clave el campo que cada fuente escribe distinto — acá el artista
("D-Shift & Drunken Kong" vs "Drunken Kong, D-SHIFT"): se cruza por título más
remixer, y el artista se usa después como confirmación.

---

## Una restricción es una forma de no estar equivocado, no es una idea

**Qué pasó.** Se midió todo lo medible —densidad de arreglo, colocación del bajo,
color del timbre, continuidad, largo de las secciones— y se compuso satisfaciendo
cada número. El resultado cumplía todas las restricciones del género y su propio
DJ dijo *"la música no me dice nada"*.

**Por qué.** Cada restricción acertada elimina una manera de estar equivocado; no
agrega una manera de estar bien. El promedio de muchos temas buenos no es un tema
bueno: es la ausencia de cualquier idea en particular. Y una mediana de todo el
repertorio no es ningún momento de la noche — es el centro de gravedad entre una
apertura y un peak, que no se parece a ninguno de los dos.

**Cómo se aplica.** Primero la idea, después las restricciones, y solo las que no
la peleen. Las mediciones sirven para descartar familias enteras —eso funciona y
está probado— pero la figura se escribe, no se deriva. Y un artefacto se hace
para un momento concreto, no para la mediana.

Relacionado: [[sin-grupo-de-control-no-medis-preferencia]]

## Vacío y golpeado son el mismo problema

**Qué pasó.** Una intro con bajo, hat y rim se escuchaba percusiva y vacía a la
vez. Parecía contradictorio y no lo era.

**Por qué.** Cuando todo lo que suena ataca y nada sostiene, el oído registra los
golpes **y** el silencio entre ellos. Lo que falta no son eventos: es algo que
dure entre evento y evento.

**Cómo se aplica.** La capa que sostiene no es un elemento del arreglo que
aparece y desaparece: es el piso. Entra primero y no se va. Y si tiene huecos
—aunque sean de 146 ms— reataca al descubierto en cada frontera, y ese ataque
sin nada que lo tape es un golpe más.

## La humanización es por rol y con dirección, no jitter parejo

**Qué pasó.** Aplicar el mismo desplazamiento aleatorio de ±6 ms a todas las
capas no sonó humano. Separarlo por rol y darle dirección sí.

**Por qué.** El groove no está en que las notas se muevan: está en la **relación
fija entre capas**. El bombo clavado porque es el reloj, el bajo 4 ms adelante
empujando, el clap 10 ms atrás. Si todo se mueve al azar hacia los dos lados, esa
relación no existe y lo que queda se escucha como error de cuantización.

**Cómo se aplica.** Un perfil por instrumento: corrimiento, dispersión, swing,
dinámica. Y la dinámica con forma —una curva a lo largo de la frase—, no
variación al azar.

## Una variación con período que divide al de la repetición es invisible

**Qué pasó.** Para romper la repetición se alternó un elemento por compás **par**.
No cambió nada: la célula se repite cada 8 compases y 8 es par, así que la
paridad se conserva y el compás 9 seguía siendo idéntico al 1. Con período 16 la
repetición pasó de 67% a 0%.

**Por qué.** Una variación solo se percibe si su período no divide al período de
lo que se repite.

**Cómo se aplica.** Antes de agregar variación, mirar cada cuánto se repite lo
que se quiere romper y elegir un período que no lo divida. Y medirlo después: la
repetición se cuenta comparando firmas, no se estima.

## Un cambio sin aproximación se escucha como brusco

**Qué pasó.** El bombo entraba entero en un compás, con la suma de velocidades
saltando 97% de un compás al siguiente, y no había **una sola nota** en todo el
loop que preparara un cambio. Se escuchaba como un interruptor, no como una
transición.

**Por qué.** El oído no juzga un evento por su nivel absoluto sino por la
diferencia con lo inmediatamente anterior. Un cambio grande sin rampa se lee como
corte.

**Cómo se aplica.** Preparar con lo que ya está sonando —subir la velocidad de la
percusión existente en los dos compases previos— antes que agregar elementos
nuevos. Y repartir los elementos que entran: dos en un compás y uno más adelante,
no cuatro juntos. Un desarrollo también se parte: primero el registro, después el
cuerpo.

## La duración decide más que la altura

**Qué pasó.** Una melodía "muy atmosférica" y un bajo "cortado" se arreglaron sin
mover una sola nota, solo cambiando cuánto duran.

**Por qué.** A 123 BPM una nota de 0.18 pulsos dura 88 ms: eso es un click, no una
nota. Y al revés, una tríada sostenida cuatro compases con reverb suena a órgano
de iglesia — no es la séptima ni el registro, es la duración.

**Cómo se aplica.** En una línea, la duración sale del hueco hasta la nota
siguiente y no de una constante: al 70% del hueco es una línea, al 30% son golpes
sueltos. Y antes de reescribir notas, medir duraciones.

## Una alarma que avisa mal es peor que ninguna

**Qué pasó.** La herramienta de continuidad marcaba la percusión como "cortada" al
16% de cobertura. Pero es un Drum Rack: el sample se dispara entero y el largo de
la nota no cambia lo que suena. Y sobre un tema completo la cobertura mide el
arreglo, no el corte — una capa que suena en la mitad de las secciones da la
mitad.

**Por qué.** Una alarma con falsos positivos entrena a ignorarla, y entonces
tampoco avisa cuando el problema es real.

**Cómo se aplica.** Cuando una métrica no aplica a un caso, excluirlo
explícitamente en vez de dejar que dispare. Y elegir el indicador que mide la
causa —la duración mediana— y no el que correlaciona con ella.

## Sin grupo de control no medís preferencia, medís el dominio

**Qué pasó.** Se midieron LUFS, rango dinámico, balance espectral y ancho estéreo
sobre los 48 temas más tocados, y también sobre 20 comparables que nunca se
tocaron. Salieron estadísticamente idénticos: LUFS p=0.46, rango dinámico p=0.27,
balance p=0.17. Lo único que separó los dos grupos fue el tiempo — duración
(7.85 vs 7.37 min, p=4.1e-18 sobre 1816 tracks) y largo del breakdown (31 vs 24
compases).

**Por qué.** Toda la biblioteca sale del mismo circuito de sellos y está
masterizada igual. Medir solo lo elegido describe cómo es el género, no qué
prefiere la persona. Sin el control, esos números parecían el criterio.

**Cómo se aplica.** Antes de derivar una regla de una muestra, conseguir la
muestra comparable que **no** se eligió. Si la métrica no separa los dos grupos,
no es criterio: es cómo funciona el dominio, y perseguirla es perseguir lo que ya
viene gratis.

Relacionado: [[el-backtest-contra-lo-propio-es-circular]]

## Una métrica que separa dos cosas no es necesariamente *la* métrica

**Qué pasó.** El tilt espectral parecía distinguir registros musicales; medía qué
sintetizador se usó. Dos bocetos de registros opuestos midieron igual, y el ±1.4
contra la referencia era coincidencia.

**Por qué.** Una correlación en una muestra chica se consigue con muchas
variables, y la que uno nombró no es necesariamente la que actúa.

**Cómo se aplica.** Antes de creerle a un número, preguntarse **qué otra cosa
podría estar midiendo**, y buscar el caso que lo refutaría. Si no existe un
resultado que te haría cambiar de opinión, no estás midiendo.

## Una herramienta que produce algo para escuchar tiene que verificarse sola

**Qué pasó.** Se hizo escuchar una transcripción sin saber que el detector había
devuelto 43 golpes irregulares donde había 32 parejos, 106 "claps" repartidos en
las 16 semicorcheas y 23% de notas fuera de tonalidad. La persona escuchó basura
y dijo "suena mal", lo cual no informaba nada sobre la pregunta real.

**Por qué.** El costo de verificar son minutos. El costo de no verificar es que
la persona gasta su atención —el recurso escaso— evaluando ruido del detector.

**Cómo se aplica.** Toda herramienta que produzca algo para evaluación humana
chequea su propia salida contra lo esperado y **reporta el chequeo, también
cuando sale bien**. `copiar_tema.py` avisa si el bombo no da ~4 por compás;
`make_sketch.py` imprime su densidad al lado de la medida.

## El número al lado del otro encuentra lo que dos iteraciones de escuchar no

**Qué pasó.** Un boceto sonaba "a robot". Se buscó en el timing —swing, jitter—
y el jitter máximo eran 6 ms. El problema era densidad: 44 notas por compás
contra las 17.7 de los temas que se tocan, con un arpegio de semicorcheas sin un
hueco en ocho compases.

**Por qué.** El oído detecta que algo está mal pero nombra mal la causa. "Suena a
robot" apuntaba al timing y era falta de aire.

**Cómo se aplica.** Cuando una queja perceptual no se resuelve en dos intentos,
dejar de ajustar y **medir lo generado contra la referencia, dimensión por
dimensión**. Y dejar esa comparación impresa en la herramienta, para que la
próxima vez esté a la vista.

## Comparar de a uno es lento y además engañoso

**Qué pasó.** Se probaron presets uno por uno durante varias rondas, sin
converger. Cargarlos todos a la vez en pistas paralelas resolvió la comparación
en un click.

**Por qué.** Entre el primero y el cuarto pasan minutos, y el oído no compara
contra un recuerdo: compara contra lo que acaba de escuchar.

**Cómo se aplica.** Cuando haya que elegir entre alternativas perceptuales,
presentarlas simultáneas y alternables, no secuenciales.

## Analizar la mezcla completa no funciona: separar primero

**Qué pasó.** La detección por bandas sobre la mezcla daba bombos irregulares
porque la banda de 30-110 Hz contiene el bajo tanto como el bombo, y pyin seguía
armónicos del pad en vez de la fundamental del bajo. Con stems de Demucs: BPM
exacto, 93% de bombos en grilla, 4% de notas fuera de tonalidad contra 23%.

**Por qué.** Ningún filtro separa instrumentos que comparten registro. Es un
límite del enfoque, no un parámetro mal puesto.

**Cómo se aplica.** Si la señal a medir convive con otras en la misma banda,
separar fuentes antes de medir. Y si eso no es posible, decir que la medición no
es confiable en vez de reportar el número.

## Verificar en runtime antes de aceptar una corrección ajena

**Qué pasó.** Un informe acusó a `ajustar_a_hz()` de asumir un rango 0-1 que no
correspondía, con una tabla de rangos sacada de los XML de los presets. Se
preguntó en runtime: el parámetro en cuestión **sí** es 0-1. La tabla era el
rango de mapeo MIDI, no el del `DeviceParameter`. Pero el fondo del planteo era
correcto: otro parámetro del mismo device va de 0 a 9, así que asumir 0-1
tampoco vale.

**Por qué.** Una fuente puede estar equivocada en el caso concreto y en lo
cierto en el principio. Aceptar o descartar en bloque pierde la mitad útil.

**Cómo se aplica.** Cuando una herramienta, un informe o un agente contradiga
algo propio: **preguntarle al sistema**, no discutir. Y separar la acusación
específica del principio general — pueden tener valores de verdad distintos.

## Las operaciones tienen que ser deterministas, no depender de qué había antes

**Qué pasó.** `create_clip` sobre un slot ocupado no reemplaza: devuelve error,
sigue, y las notas se agregan al clip viejo. El resultado dependía de qué hubiera
antes. Zafó por casualidad una vez.

**Por qué.** Una API que falla parcialmente y continúa produce estados que
parecen correctos hasta que no lo son.

**Cómo se aplica.** Borrar antes de crear, y **verificar el resultado contra lo
pedido**, no contra el archivo de origen. Lo mismo con `load_item` de Live, que
inserta en vez de reemplazar y deja dos instrumentos apilados sonando juntos.

## Un archivo generado no se actualiza solo porque el código se arregló

**Qué pasó.** `data/mi_sonido.json` decía 1004 reproducciones y son 510. El fix
del doble conteo estaba en el código desde hacía horas, pero el JSON nunca se
había regenerado porque el script solo escribe con `--json`.

**Por qué.** El artefacto y el código tienen ciclos de vida distintos, y nada
los sincroniza.

**Cómo se aplica.** Al arreglar un bug de cálculo, regenerar los artefactos que
dependían de él **en el mismo movimiento**. Y ante un número sospechoso,
comparar la fecha del dato contra la del código.

## La energía de un arreglo es contraste, no nivel

**Qué pasó.** Para que un drop suene a drop no alcanzó con agregarle capas. Lo
que lo hizo funcionar fueron los compases sin batería que vienen antes.

**Por qué.** La percepción de intensidad es relativa a lo inmediatamente
anterior, no absoluta.

**Cómo se aplica.** Donde algo tenga que sentirse grande, dejar que lo anterior
sea chico. Vale para un arreglo musical y para un set.

**Corrección (2026-09-09).** Este aprendizaje decía además "antes de agregar,
sacar", y esa frase suelta es la que hizo perder una tarde entera. Es verdadera
solo cuando hay algo que sacar. Aplicada sobre un arreglo que ya venía plano
produjo un pozo de una capa antes del drop, un final que soltaba capas hasta
quedar en el 5% del pico, y un gancho que se callaba para dejarle lugar al
arpegio en el momento más grande del tema. El DJ lo resumió mejor que la
medición: *"hacé que explote, que sumen cosas, no restes"*.

El contraste no se hace restando donde no sobra. Se hace acumulando y después
soltando, en ese orden. Está desarrollado en [El contraste no se hace
restando](#el-contraste-no-se-hace-restando).

## Un agente cuya definición quedó vieja es peor que no tenerlo

**Qué pasó.** `.claude/agents/productor.md` decía que el agente "no controla el
DAW" y listaba AbletonOSC como una de tres opciones a evaluar, cuando ya estaba
instalado, con extensión propia y tres scripts usándolo. Describía menos de la
mitad de sus herramientas.

**Por qué.** Un agente responde con confianza sobre el mundo que su definición
describe. Si ese mundo quedó atrás, la confianza es el problema.

**Cómo se aplica.** Cuando el código se mueve, revisar los agentes que lo
mencionan. Y que cada definición declare tres cosas: sus herramientas con el
comando exacto, sus reglas de operación **con el error que las originó**, y sus
límites — qué no puede hacer y qué no prueba lo que mide.

## Guardar el resultado no siempre es guardar el archivo

**Que paso.** Todo el armado del set de Live —trece pistas con instrumentos,
cadenas de efectos, filtros calibrados y niveles— vivia solo en la RAM de Live.
El `.als` en disco tenia cuatro meses. Live no le expone `save` a los Remote
Scripts (probado: no hay handler, y es deliberado), y la licencia Trial tampoco
deja guardar a mano.

**Por que.** El set no es un original: es el RESULTADO de una receta. Trece
pistas, cada una con un instrumento buscado por nombre en el browser, unos
efectos y unos numeros. Eso entra en un JSON de cuatro kilobytes.

**Como se aplica.** Cuando no se puede guardar el artefacto, se guarda lo que lo
produce y se verifica que lo produzca. `data/set_live.json` + `armar_set.py` +
`idea.py` + `montar.py` reconstruyen el tema entero en cinco minutos de maquina.
El script tiene los dos sentidos —`--capturar` lee el set y reescribe la
receta— porque una receta que hay que mantener a mano deja de coincidir con la
realidad en la primera sesion.

Y hay que CORRERLO antes de decir que sirve. Un script de reconstruccion sin
probar es peor que no tenerlo: da por resuelto un riesgo que sigue abierto.

El efecto de costado resulto valer mas que el objetivo: como cada instrumento
lleva su lista de alternativas y la ultima es siempre un motor y no un preset,
cambiar de edicion de Live —donde muchos presets no existen— pasa a ser cambiar
un nombre en un JSON.

## "A destiempo" casi nunca es fuera de grilla: es adelante o atrás

**Qué pasó.** El DJ dijo tres veces "el clap está a destiempo". Se sacaron
golpes que anticipaban, se revisó la humanización, se buscaron flams. Cuando
por fin se midió el render propio contra Lake Of Fire con el mismo detector,
el dato fue simple: el clap propio caía **+13 ms después** del bombo y el de
Vuarambón **−7.6 ms antes**. Veinte milisegundos, todos los golpes en su
lugar de la grilla. Los hats +19 contra −5.5.

**Por qué.** El oído no escucha posiciones, escucha relaciones: un clap que
llega después del bombo "arrastra", uno que llega antes "empuja". Ninguno de
los dos suena fuera de tiempo mirando la grilla, y los dos suenan a destiempo
respecto del estilo que se tiene en la cabeza. Los perfiles de humanización
venían de Moonflare, que toca atrás; el pedido era Vuarambón, que empuja.

Y una trampa de calibración: entre lo que se escribe en el MIDI y lo que mide
el detector hay un arrastre de unos 9 ms —el ataque del sample del clap es
más lento que el del bombo, y un Haas ensancha el ataque—. Para medir −7 hay
que escribir −14. Se calibra en dos pasos, midiendo, no por fórmula.

**Cómo se aplica.** Ante "a destiempo", medir el feel relativo al bombo con el
mismo instrumento en los dos lados antes de tocar la grilla. Y leer los
números **relativos** al bombo: el absoluto depende de dónde el detector
puso el cero.

## En un breakdown los medios SUBEN; el que baja es el grave

**Qué pasó.** Cinco versiones de la misma sección, cada una rechazada:
"larguísimo y muy silencioso", "re brusco", "sigue muy brusco", "mucho
silencio", "se muere el drop". Cada vez se midió, cada vez se corrigió la
pendiente o el largo, y cada vez estuvo mal — porque se estaba midiendo la
variable equivocada.

Al medir Interlocutor compás por compás por **bandas** apareció el dato: en su
breakdown los graves caen 14 dB respecto del drop, y los medios **suben 1.2
dB** (−19.7 contra −20.9 dBFS). El breakdown es la sección con MÁS medios de
todo el tema. En el boceto los medios bajaban 4.4 dB. Esos 5.6 dB de
diferencia eran las cinco quejas.

**Por qué.** Un breakdown no es "lo mismo con menos". Es un cambio de
registro: se va el grave —que es lo que en el drop llena los medios, porque el
bombo tiene cuerpo— y la armonía tiene que ocupar ese lugar. Si no lo ocupa
nadie, el oído registra un agujero, y da igual cuántos compases dure o cuán
suave sea la pendiente.

**Cómo se aplica.** Medir las tres bandas por sección, no el nivel total, y
comparar cada sección contra el DROP del mismo tema (no contra el compás
anterior). En un breakdown: graves −14 dB, medios **+1**, agudos ±1. Y para
que los medios suban hace falta material nuevo que suene el 100% del tiempo —
golpes cortos de acorde cubren el 28% y no alcanzan; una tríada sostenida sí.

## Comparar contra la sección equivocada invalida todas las cifras

**Qué pasó.** Durante dos días los "números de referencia" de Interlocutor
salieron del segundo 283, que es el compás 146. Medida la estructura, el
compás 146 cae en un **groove**, no en el drop — el drop es 137-184 en la
medición por bandas, y 153-192 según el clasificador. Todas las comparaciones
de densidad, sidechain y ancho estaban contra la sección equivocada.

**Por qué.** El fragmento lo elegía `_mejor_momento`, que busca el pico de
energía. En un tema donde el groove está tan fuerte como el drop, ese pico no
distingue. Nadie lo verificó porque el número salía plausible.

**Cómo se aplica.** Antes de usar un fragmento como referencia, mirar en qué
sección cae: `estructura.py` o el mapa por bandas. Y anotar el compás junto al
segundo, que es lo que permite darse cuenta.

## La tensión no es silencio: se retira una sola cosa y el resto pide que vuelva

**Qué pasó.** Cuatro versiones de la misma sección en una tarde. Bajada de 32
compases sin bombo: "es larguísimo y muy silencioso". De 16, con la percusión
entrando después: "es re brusco, es silencio, y viene de una conga linda". De
8, con medios y agudos planos como en las referencias: "sigue muy brusco". Con
el bombo y el bajo desvaneciéndose en cuatro compases, pendiente idéntica a
Estigia: "mucho silencio". Y entonces la definición del DJ, que valía más que
las cuatro mediciones: *"el ambiente no lo sacaría, el groove lo mantendría,
haría tensión, y luego liberaría todo"*.

**Por qué.** Se estaba midiendo bien la forma equivocada. Las referencias de
Vuarambón peak —Stamina, Zenith, Prodiga— no tienen bajada después del drop;
Estigia hace un bajón de tres compases y vuelve. La sección que faltaba no era
una bajada bien hecha: era **tensión**. Y la tensión se hace reteniendo UNA
cosa que el cuerpo espera —el bajo— con todo lo demás sonando. Cuando se van
varias capas el oído no espera nada: no hay a qué volver, y eso se escucha
como silencio aunque los medidores digan que los agudos van planos.

**Cómo se aplica.** Después de un drop, antes de otro, no se vacía: se retira
el grupo de bajo con el bombo puesto, se suma el riser, y el redoble libera.
Medido en el render: total −4 dB (las referencias −5), graves −2.5, medios
−1.5, agudos planos y subiendo. Antes: −11 dB. Y una regla más general: cuando
el DJ describe lo que HARÍA con verbos —"mantendría", "haría", "liberaría"—
eso es la especificación; las mediciones son para verificarla, no para
reemplazarla.

## En la bajada se van los graves, no el tema

**Qué pasó.** "Es re brusco, es silencio, y viene de una conga linda". La
bajada apagaba todo salvo el pad: de doce capas a cuatro en un compás,
−92% de impacto. Medido en cuatro de los temas más tocados con
`transicion.py`: en la entrada a la bajada los **graves caen 20 dB y los
medios y agudos siguen planos a ±1 dB**. Minicube tarda dos compases.

**Por qué.** Lo que junta tensión no es el silencio: es un groove al que le
falta el bombo. Si se va todo, el oído no espera nada — no hay a qué volver.

**Cómo se aplica.** En una bajada se van el bombo y el grupo de bajo. La
percusión, los metales, la textura y la armonía siguen exactamente como en el
drop, sin rampa. Medido después en el render propio: medios −2 dB, agudos
−2.5, graves −9.

## Una pista armada graba, no reproduce

**Qué pasó.** La pista Hats, recién creada, con sus clips en el arreglo y su
cadena sonando cuando se le disparaba una nota desde sesión, daba −240 dBFS
al grabar el master. Se revisó enrutado, dispositivos, "Back to Arrangement",
el contenido de los clips, y se reconstruyó la pista entera: seguía muda. El
dato estaba impreso desde el principio y se pasó por encima: `arm: True`.

**Por qué.** Live arma sola la última pista creada. Y cuando el render prende
la grabación, Live graba en TODAS las pistas armadas: esa pista entra en
grabación, reproduce su entrada (nada) en vez de sus clips, y encima los pisa
—de ahí los clips partidos en 145/147—. No es un error de la pista: es Live
haciendo exactamente lo que se le pidió.

**Cómo se aplica.** Antes de cualquier toma, desarmar todas las pistas menos
la de render; `render.py` lo hace solo. Y una regla más general que ya se
pagó dos veces hoy: cuando un estado se imprime y se lee "irrelevante", volver
a mirarlo antes de reconstruir nada. Reconstruir es caro y no cambia el
estado que causó el problema.

## Un pad vacío no suena flojo: no suena

**Qué pasó.** Durante dos días la batería escribió shaker en la nota 70 y
congas en 63/64 —las del General MIDI— y los kits del proyecto (909 Core Kit,
707 Core Kit) no tienen pad ahí. Sobre ese silencio se razonó horas: el
"filtro de peine entre clap y shaker", la densidad de percusión, el redoble que
"acumula", la capa Repiques entera. Todo eso era MIDI a un pad vacío. Se
descubrió grabando la pista sola y midiendo pico 0.000.

**Por qué.** El MIDI en disco estaba perfecto, y todo lo que se medía era el
MIDI. Una capa muda no da ninguna señal de alarma en ese mundo: tiene sus
notas, su patrón, su humanización. La ausencia solo existe en el audio.

**Cómo se aplica.** Antes de razonar sobre una capa, verificar que suena:
`render.py --solo <pista>` y pico > 0. Y los pads de un kit se leen por
**nombre**, no se suponen: la lista de canales de enrutado de una pista
(`available_input_routing_channels` con la entrada puesta en esa pista) nombra
cada cadena del Drum Rack. El 909 Core Kit trae bombo, hats, clap, toms, rim,
snare, crash y ride; el 707 lo mismo más tamb y cowbell. Ninguno tiene congas
ni shaker.

## Sondar por tiempo es frágil; sondar por nombre o por contenido no

**Qué pasó.** Para saber qué notas responde un kit se grabó un clip con una
nota por corchea y se midió la energía por ranura. Dio mapas contradictorios
tres veces: la toma arranca en un lugar distinto cada vez y el clip de prueba
caía fuera de la ventana recortada o corrido una ranura. Se leyó que el clap
del 909 no sonaba, con el clap sonando.

**Por qué.** Una medición que depende de una alineación que no se controla
hereda todo el error de esa alineación, y lo hereda en silencio: el resultado
tiene la misma forma que uno correcto.

**Cómo se aplica.** Si existe una fuente determinista —un nombre, una lista,
un estado que Live reporta— se usa esa antes que cualquier medición por
tiempo. Y cuando la medición por tiempo es inevitable, poner una ancla
conocida al principio y al final de la prueba para medir el corrimiento
antes de leer el resto.

## Grabar no es exportar: el lazo se cierra sin licencia

**Qué pasó.** Todo lo que el proyecto medía era MIDI propio o audio ajeno. Del
audio del propio tema no había nada: Live no exporta por OSC y con la Trial no
exporta ni a mano. Eso dejaba ciego justo lo que el DJ describía —"suena a
ringtone" es timbre, capas, ancho: propiedades del audio— y hacía imposible
iterar solo: un bucle habría optimizado lo medible y se habría alejado de lo
que importa, con la confianza de estar mejorando.

**Por qué.** La restricción era "no se puede exportar", y se leyó como "no se
puede obtener audio". Son dos cosas distintas. Una pista de audio con entrada
Resampling recibe el master, y lo que Live graba lo escribe a disco como WAV
aunque el set no se pueda guardar. Deshacer la toma saca el clip del set, Live
suelta el archivo, y el WAV queda.

**Cómo se aplica.** Cuando una función está bloqueada, buscar qué otra función
produce el mismo artefacto por otro camino antes de aceptar el bloqueo. Y las
tres cosas que costaron encontrar: el transporte se arranca ANTES de mover el
cabezal, la grabación se prende recién con el cabezal en su lugar (moverlo
durante la toma la corta), y el archivo nuevo se identifica por diferencia de
conjunto y no por fecha, porque OneDrive mueve las fechas mientras Live cierra.

## Lo que se mide de uno mismo tiene que medirse igual que lo ajeno

**Qué pasó.** La primera medición simétrica —render propio y referencia por el
mismo `traducir.py`— encontró en diez segundos lo que tres tardes de escuchar
no habían nombrado: la mezcla era mono (ancho 0.01 contra 0.90 en la
referencia), el pump del bajo no llegaba (-2 dB contra -14) y las capas
melódicas sonaban el 100% del tiempo cuando la referencia respira al 77%.

Y también encontró un error de medición propio: el render de 8 compases se
midió como si fueran 16 y todas las densidades salieron a la mitad — "bombo
1.94 por compás" se leía como un bombo enterrado cuando era un divisor.

**Por qué.** Comparar dos cosas medidas con instrumentos distintos no compara
las cosas: compara los instrumentos. Y una medición sobre uno mismo tiene que
pasar por los MISMOS supuestos (largo, fragmento, separación) que la ajena.

**Cómo se aplica.** Un solo instrumento para los dos lados, siempre. Y cuando
un número propio sale absurdo, primero sospechar del divisor.

## La tensión es una rampa, no un evento

**Qué pasó.** Las dos subidas del tema eran dieciséis compases de los cuales
doce estaban planos: el impacto se quedaba entre 850 y 1000 del compás 65 al 76
y recién en el 77 arrancaba a moverse. La bajada era peor — treinta y dos
compases entre 250 y 470, con las seis capas sonando desde el primero. Escrito
parecía bien: había un redoble, había un breakdown, estaban los elementos.

**Por qué.** Tener el elemento no es tener la función. Un redoble en los últimos
cuatro compases no genera tensión, la *anuncia*: cuando aparece ya no hay tiempo
de que crezca nada, y lo que el oído registra es un susto. La tensión es la
sensación de que algo viene creciendo, y crecer lleva compases.

Y hay un caso peor que el plano, que es el que iba en contra: la segunda subida
empezaba más abajo de donde terminaba la bajada. El compás donde vuelve el bombo
—el momento más prometedor del tema— medía menos que el anterior.

**Cómo se aplica.** Medir cada sección por su primer cuarto contra su último
cuarto, no por su promedio. Toda sección tiene que terminar más fuerte de lo que
empieza, y ninguna puede empezar abajo de donde terminó la anterior salvo que
sea un breakdown declarado.

La herramienta es una rampa de velocidad a lo largo de la sección entera
(`_rampa` en `idea.py`), y es distinta del crescendo de fin de frase que ya
existía: ese se reinicia cada ocho compases, así que hace textura y no arco.

## La rampa no se le aplica al piso

**Qué pasó.** La primera versión de la rampa de la bajada la aplicaba a todas
las capas, incluida la atmósfera. El primer compás del breakdown quedó en el 7%
de la energía del compás anterior. Medido parecía un contraste enorme; lo que se
escucha con esos números no es que bajó, es que se cortó.

**Por qué.** En una sección hay dos clases de capa y hacen trabajos opuestos. Lo
que ENTRA es lo que construye la sensación de que algo crece, y ahí la rampa es
exactamente lo que se quiere. Lo que AGUANTA —el pad, los acordes, el sub— es lo
que sostiene el espacio para que la caída se lea como una caída y no como un
corte de señal. Bajarlo saca el piso justo cuando es lo único que queda.

**Cómo se aplica.** Marcar explícitamente qué capas son piso y eximirlas de
cualquier rampa. Lo que crece es lo que entra, no lo que aguanta. Con la
atmósfera, los acordes y el sub exentos, la misma bajada pasó de -93% a -77%: la
misma forma, y ahora se sostiene.

## Un sample no se estira desde el MIDI

**Qué pasó.** El riser antes del drop se escribió como una nota larga, con la
idea de que durara los cuatro compases que dura la subida. Un sample dura lo que
dura: la nota larga daba dos compases de barrido y después silencio, justo en
los dos compases donde más falta hacía.

**Por qué.** Un sintetizador sostiene mientras la nota esté abierta; un sampler
reproduce un archivo y termina. Son dos cosas distintas que se escriben igual en
MIDI, y por eso el error no se ve leyendo la partitura.

**Cómo se aplica.** Para cualquier elemento de un solo disparo cuya duración no
se controla —risers, barridos, reversas, impactos— se apilan varios disparos
escalonados y crecientes en vez de uno largo. Cuatro disparos arman una escalera
que llega arriba cualquiera sea el largo del archivo, y además funcionan si
mañana se cambia el sample por otro.

## El contraste no se hace restando

**Que paso.** El cierre eran dieciseis compases con una unica pista tocando. Se
probo con guitarra, sono mal; se cambio el instrumento, siguio sonando mal. La
primera correccion fue hacer que el final soltara una capa cada cuatro compases
en vez de todas juntas — y tambien estaba mal, por el mismo motivo de fondo.

Medido el arreglo entero compas por compas aparecio el cuadro real: del 17 al 60
el tema tenia SIEMPRE cuatro capas y un peso entre 1800 y 2500. Cuarenta y
cuatro compases sin que entre ni salga nada. El climax abria en 2328 cuando el
compas 16 ya estaba en 2065, o sea que el drop era 1.7 veces la intro. Y habia
un pozo de 218 en los compases 61-62 —una sola capa— puesto ahi a proposito
"para que el drop pegue".

**Por que.** Tres errores que son el mismo. El pozo antes del drop: vaciar
funciona cuando lo que se vacia estaba lleno, y en una planicie un agujero no se
escucha como tension sino como que se corto la luz. El cambio de capa en el
peak: se callaba el gancho para que entrara el arpegio, y el oido no escucha
"entro algo", escucha "se fue la melodia". Y el final que suelta: dedicar
dieciseis compases a desarmar lo que costo treinta y dos construir.

Un tema no crece porque las capas que ya estan toquen mas fuerte. Crece porque
ENTRA algo que antes no estaba.

**Como se aplica.** Contar capas activas por compas de punta a punta antes de
tocar cualquier otra cosa. La cuenta tiene que subir y no bajar nunca: 3, 5, 6,
6, 9, 9, 10. Si una seccion "nueva" tiene la misma cuenta que la anterior, no es
una seccion. Si algo entra y otra cosa se va en el mismo compas, eso es un
cambio de capa y no una suma, y en el drop es el error mas caro que hay.

Ojo tambien con el peso medido como suma de velocidades: un redoble de veinte
golpes flojos infla el numero sin sonar mas fuerte. Pesar la velocidad al
cuadrado, que castiga el adorno y premia el golpe, ordena distinto y ordena
mejor.

## Una capa sola no es una seccion

**Que paso.** El cierre eran dieciseis compases con una unica pista tocando. Se
probo con guitarra y sono mal, se cambio el instrumento y siguio sonando mal. El
problema nunca fue el timbre: era que despues de tres minutos con seis capas,
sacar cinco de golpe no se escucha como un final sino como que se corto algo. El
mismo error, invertido, estaba en el climax: se callaba el gancho cuando entraba
el arpegio, dejando la capa nueva sola justo en el peak.

**Por que.** Una seccion se define por su DENSIDAD RELATIVA a la anterior, no
por su material. Cambiar el instrumento de una capa solitaria no cambia que este
sola. Y un drop no es una capa nueva: es que este todo.

**Como se aplica.** Antes de cambiar el sonido de algo que no gusta, contar
cuantas capas suenan ahi. Si es una, el sonido no es el problema.

(Corregido: la primera version de esta entrada terminaba diciendo que un final
baja soltando una capa cada cuatro compases. Es falso, y esta desarrollado en
"El contraste no se hace restando", arriba.)
