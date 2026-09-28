# Arquetipo de proyecto

Esqueleto para arrancar un proyecto nuevo con la forma de trabajo que este
—plomo— fue encontrando a los golpes. No es una estructura de carpetas: las
carpetas son lo de menos. Lo que se copia es el **método**, y las carpetas
existen para sostenerlo.

```bash
python arquetipo/nuevo_proyecto.py ~/Documents/mi-proyecto --nombre "Mi Proyecto"       # muestra qué haría
python arquetipo/nuevo_proyecto.py ~/Documents/mi-proyecto --nombre "Mi Proyecto" --si  # lo hace
```

La versión vive en `VERSION` y los cambios en `CHANGELOG.md`. El proyecto nuevo
se lleva este método como `docs/METODO.md`, con la versión de la que salió.

---

## El método, en ocho reglas

### 1. Las reglas son dato, no código

Todo criterio vive en `rules/criterio.json`, y cada regla lleva tres campos:
**valor**, **porque** y **evidencia**. Una regla sin evidencia se marca
`PENDIENTE` y se sabe que está sin medir. El código las lee; nadie las
hardcodea.

Por qué: una constante adentro de una función es una opinión disfrazada de
implementación. Cuando está en un JSON con su porqué al lado, se puede discutir,
medir y refutar.

Dos cosas que la hacen valer. Una regla que ningún código lee —o que se lee con
el número escrito a mano al lado— es peor que no tenerla, porque parece que
manda y no manda: `R.sin_lector()` las lista. Y un cambio de regla va entero en
un commit: valor, evidencia, historial, versión y tag juntos. Una regla cambiada
a medias deja un número que nadie sabe de dónde salió.

### 2. Medir contra un grupo de control, o no medís nada

El error más caro que cometió este proyecto fue medir sus propios resultados y
creer que eso probaba algo. Si el solver impone la regla, medir la regla contra
lo que produjo el solver siempre la confirma. Eso es circular y no es evidencia.

La forma correcta tiene tres corpus:

- **PROPIO** — lo que produjo el sistema. No prueba nada.
- **USADO** — lo que la persona efectivamente eligió usar. Sirve.
- **CONTROL** — lo mismo, pero que la persona **no** eligió. Es el que convierte
  una descripción del dominio en una preferencia.
- **REFERENCIA** — lo que hacen otros que saben. Es el único que **refuta**: si
  la referencia viola la regla seguido y funciona igual, la regla es
  autoimpuesta, no una ley del dominio. USADO matiza; REFERENCIA refuta.

Una regla que la persona eligió por gusto se marca como decisión humana, y la
referencia no la refuta: es una preferencia, no una hipótesis.

Sin el control, todo número describe el género y no el gusto. En plomo, LUFS,
rango dinámico y balance espectral daban idénticos entre lo tocado y lo nunca
tocado: creer que eran el criterio hubiera costado meses persiguiendo lo que ya
venía gratis.

### 3. Una métrica que separa dos cosas no es necesariamente *la* métrica

Pasó dos veces. El tilt espectral parecía distinguir registros musicales y en
realidad medía qué sintetizador se usó. Un ±1.4 contra la referencia parecía
significativo y era coincidencia: dos bocetos de registros opuestos medían
igual.

Antes de creerle a un número, preguntar **qué otra cosa podría estar midiendo**,
y buscar el caso que lo refutaría. Si no existe un resultado que te haría
cambiar de opinión, no estás midiendo.

### 4. Verificar antes de entregar

Toda herramienta que produzca algo para que una persona lo evalúe tiene que
chequearse a sí misma primero y reportar el chequeo. En plomo, una transcripción
se hacía escuchar sin saber que el detector había devuelto 43 golpes irregulares
donde había 32 parejos.

El costo de la verificación es minutos. El costo de no tenerla es que la persona
gasta su atención —que es el recurso escaso— evaluando basura.

Y el chequeo se reporta **también cuando sale bien**. Un número al lado del otro
muestra en un segundo lo que dos iteraciones de escuchar no encontraron.

Un chequeo puede dar verde sin haber mirado nada. Para que valga, tiene que
cumplir tres cosas:

- **Mirar la salida, no el número que la describe.** El cuadro, el audio, la
  página ya renderizada: lo mismo que va a recibir la persona. En plomo, tres
  errores de un mismo día —un ritmo medido a 30 cuadros por segundo que marcaba
  un golpe sí y uno no, una paleta toda de un color, un nombre repetido en la
  misma pantalla— tenían los números bien y aparecieron recién mirando un cuadro.
- **Comparar contra la fuente, no contra un paso propio.** Un validador que
  compara contra lo que guardó el paso anterior prueba que el proceso es
  coherente consigo mismo, nada más: un error dicho con seguridad valida
  perfecto. No falla, tranquiliza, y eso es peor.
- **Decir lo que no aplicó.** Una instrucción ignorada en silencio —una palabra
  que el filtro no reconoció, algo pedido que no estaba, un cruce que cubrió el
  30%— deja un resultado idéntico a uno bueno. Lo que no se cumplió se avisa, y
  con poca cobertura no se da veredicto.

### 5. La bitácora guarda lo que pasó; los aprendizajes, lo que sirve después

Son dos archivos distintos y confundirlos los arruina a los dos.

- `docs/BITACORA.md` — qué se hizo, con fecha. Se agrega arriba, no se edita.
- `docs/APRENDIZAJES.md` — la lección durable, sin la anécdota. Cada una con
  **qué pasó**, **por qué** y **cómo se aplica**. Se corrige cuando se demuestra
  que estaba mal.

Regla para saber en cuál va: si dentro de seis meses, en otro proyecto, la
seguirías aplicando, es aprendizaje. Si solo explica una fecha, es bitácora.

### 6. "No se puede" es una conclusión, no una observación

Es la conclusión más barata de sacar y la más cara de pagar. Un error por
optimismo se descubre usando la cosa; uno por pesimismo no, porque nadie vuelve
a probar lo que está escrito que es imposible. Queda en el repo, se cita a sí
mismo y cierra el camino para siempre.

Antes de decirlo:

1. **Separar el síntoma de la explicación.** "403" es el síntoma. "La plataforma
   bloquea las apps nuevas" es una historia, y que sea coherente y tenga
   documentación que la respalde no la hace cierta.
2. **Probar la versión nueva y el camino de al lado.** Un error puede estar mal
   etiquetado, y una función bloqueada suele tener otra que produce lo mismo.
3. **Probar la operación mínima, aislada.** Cada prueba que pasa o falla recorta
   el espacio.
4. **Recién ahí decirlo —y escribirlo—, con qué se probó y qué devolvió cada
   cosa**, para que el próximo lo pueda refutar.

Una restricción que documenta otro también es una hipótesis, y probarla suele
costar una llamada. Es el "preguntarle al sistema" de más abajo, aplicado a lo
que uno concluye.

En plomo, un 403 sin cuerpo era un endpoint deprecado y no un permiso: lo que se
había declarado imposible salió diez minutos después. Y cuando la persona vuelve
sobre algo que se dio por cerrado, es señal de que la conclusión estaba floja, no
de que no entendió.

### 7. Lo que dice la persona es dato; lo que sale a su nombre es suyo

La persona para la que se trabaja es la verdad de base sobre su criterio, y lo
que dijo se guarda como lo dijo. Lo que no dijo no se completa: queda vacío, o se
pregunta. "Cambiá esto" no es "esto está mal", "tiene algo" no es "me gusta", y
"ya lo usé mucho" no es un veto.

Por qué: todo lo que se calcula después sale de ahí. Una entrada inferida lo
desvía todo, y ya no hay forma de separar lo que dijo de lo que se supuso. Por
eso se anota la frase textual al lado del campo.

Hacia afuera vale lo mismo, al revés. Lo que se publica a su nombre va en su voz
—como lo habría escrito, no como un informe sobre ella—, sin hechos que no dijo,
y lo técnico va a `docs/`. La prueba es si lo firmaría tal cual. En plomo, la
primera descripción de un video explicaba cómo estaba hecha la imagen y hablaba
del autor en tercera persona; él la dejó en el tracklist y un "Gracias por
escuchar".

Y lo que sale hacia afuera lo decide la persona. Un video, un mensaje, un cambio
en su cuenta: se deja listo en privado o en borrador, y pasa a público con su OK.
Publicar no se deshace.

### 8. La fuente se lee en el momento; lo que uno recuerda es una copia

Lo que uno tiene en la cabeza —o en un comentario, en un config, en este mismo
archivo— es una copia de algo que vive en otro lado. Las copias se separan del
original sin avisar, y una copia vieja no falla: da un número plausible con toda
seguridad.

- **Un número, un lugar.** Un criterio vive en `rules/` y en ningún otro lado:
  ni una constante al lado del código que lo lee, ni un config que lo pise, ni
  un doc que lo repita. Donde haga falta, se dice dónde está. Y una perilla nueva
  se prueba moviéndola: si la salida no cambia, no está conectada.
- **Lo que está afuera se lee antes de escribir.** Una base, un canal, un
  documento: la persona los edita en paralelo. Si lo que hay no es lo último que
  escribiste, lo cambió ella, y no se pisa.
- **Y se vuelve a leer después.** Que un sistema acepte un cambio sin dar error
  no quiere decir que lo haya aplicado.

En plomo, un script pisó una descripción que la persona había escrito a mano en
el panel del canal; ahora lee primero y se frena si lo que encuentra no lo
escribió él.

---

## La estructura

```
CLAUDE.md              reglas del proyecto para el agente — corto y sin relleno
.gitignore             secretos por patrón, scratch y pesados, desde el día uno
.gitattributes         finales de línea LF, en cualquier máquina
.env.example           qué variables hacen falta, sin sus valores
pyproject.toml         el paquete se instala: nada de sys.path a mano
docs/
  METODO.md            este método, con la versión del arquetipo de la que salió
  ARCHITECTURE.md      dónde vive cada cosa y por qué
  BITACORA.md          qué pasó, por fecha, lo nuevo arriba
  APRENDIZAJES.md      lo que sirve después, sin la anécdota
rules/
  criterio.json        las reglas como dato: valor, porque, evidencia
src/<paquete>/         módulos que se importan y se testean
  criterio.py          el lector de las reglas
scripts/               lo que se corre desde la línea de comandos
  archive/             one-offs ya ejecutados, no se borran
data/                  datos medidos y chicos; lo pesado lo ataja .gitignore
tests/
  test_criterio.py     las reglas se leen y dicen cuáles no se usan
  test_estructura.py   la raíz tiene solo configuración y nada ignorado quedó adentro
.claude/
  agents/              un agente por dominio, no uno por tarea
  skills/              los flujos invocables con /
```

Dos convenciones que valen más de lo que parecen:

**Módulos chicos, muchos.** 200-400 líneas típico, 800 máximo. Un archivo grande
esconde sus propias contradicciones.

**Los scripts ejecutados no se borran, se archivan.** `scripts/archive/` es
memoria: dentro de un año la pregunta "¿cómo se hizo aquello?" tiene respuesta.

---

## Los agentes

Uno por **dominio**, no uno por tarea. Un agente por tarea es una función con
disfraz; un agente por dominio acumula criterio.

Cada definición tiene que declarar tres cosas, y la tercera es la que casi nunca
está:

1. **Las herramientas** que tiene, con el comando exacto.
2. **Las reglas de operación**, cada una con el error que la originó. "Borrar
   antes de cargar" sin el "porque `load_item` inserta y quedan dos apilados"
   se olvida en dos semanas.
3. **Los límites** — qué NO puede hacer y qué NO prueba lo que mide. Esto se
   repite en cada entrega, no una vez en la documentación.

Un agente cuya definición describe herramientas que ya no existen, o que ignora
la mitad de las que tiene, es peor que no tenerlo: da respuestas confiadas sobre
un mundo que quedó atrás. Revisarlos cuando el código se mueve.

---

## Trabajar con mediciones

El ciclo, cuando el proyecto tiene algo que medir:

```
medir la referencia  ->  derivar un objetivo numérico  ->  producir  ->
medir el resultado  ->  comparar contra el objetivo  ->  repetir
```

El eslabón que siempre falta es el segundo "medir". Si no podés medir lo que
produjiste, no estás iterando: estás adivinando con más pasos.

Y cuando una herramienta externa —o un agente— contradiga algo tuyo:
**verificarlo en runtime antes de aceptarlo o descartarlo**. En este proyecto un
informe acusó a una función de asumir un rango equivocado; la acusación era
falsa para el caso concreto y correcta en el fondo. Las dos cosas se supieron
preguntándole al sistema, no discutiendo.
