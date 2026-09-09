# Aprendizajes

Lo que sirve después, sin la anécdota. Cada uno con **qué pasó**, **por qué** y
**cómo se aplica**.

Se corrigen cuando se demuestra que estaban mal: un aprendizaje equivocado es
peor que ninguno, porque se aplica con confianza.

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

**Cómo se aplica.** Antes de agregar, sacar. Y donde algo tenga que sentirse
grande, dejar que lo anterior sea chico. Vale para un arreglo musical y para un
set: la forma se hace con lo que no está.

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
