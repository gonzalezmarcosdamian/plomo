# Arquetipo de proyecto

Esqueleto para arrancar un proyecto nuevo con la forma de trabajo que este
—plomo— fue encontrando a los golpes. No es una estructura de carpetas: las
carpetas son lo de menos. Lo que se copia es el **método**, y las carpetas
existen para sostenerlo.

```bash
python arquetipo/nuevo_proyecto.py ~/Documents/mi-proyecto --nombre "Mi Proyecto"
```

---

## El método, en cinco reglas

### 1. Las reglas son dato, no código

Todo criterio vive en `rules/criterio.json`, y cada regla lleva tres campos:
**valor**, **porque** y **evidencia**. Una regla sin evidencia se marca
`PENDIENTE` y se sabe que está sin medir. El código las lee; nadie las
hardcodea.

Por qué: una constante adentro de una función es una opinión disfrazada de
implementación. Cuando está en un JSON con su porqué al lado, se puede discutir,
medir y refutar.

### 2. Medir contra un grupo de control, o no medís nada

El error más caro que cometió este proyecto fue medir sus propios resultados y
creer que eso probaba algo. Si el solver impone la regla, medir la regla contra
lo que produjo el solver siempre la confirma. Eso es circular y no es evidencia.

La forma correcta tiene tres corpus:

- **PROPIO** — lo que produjo el sistema. No prueba nada.
- **USADO** — lo que la persona efectivamente eligió usar. Sirve.
- **CONTROL** — lo mismo, pero que la persona **no** eligió. Es el que convierte
  una descripción del dominio en una preferencia.

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

### 5. La bitácora guarda lo que pasó; los aprendizajes, lo que sirve después

Son dos archivos distintos y confundirlos los arruina a los dos.

- `docs/BITACORA.md` — qué se hizo, con fecha. Se agrega arriba, no se edita.
- `docs/APRENDIZAJES.md` — la lección durable, sin la anécdota. Cada una con
  **qué pasó**, **por qué** y **cómo se aplica**. Se corrige cuando se demuestra
  que estaba mal.

Regla para saber en cuál va: si dentro de seis meses, en otro proyecto, la
seguirías aplicando, es aprendizaje. Si solo explica una fecha, es bitácora.

---

## La estructura

```
CLAUDE.md              reglas del proyecto para el agente — corto y sin relleno
docs/
  ARCHITECTURE.md      dónde vive cada cosa y por qué
  BITACORA.md          qué pasó, por fecha, lo nuevo arriba
  APRENDIZAJES.md      lo que sirve después, sin la anécdota
rules/
  criterio.json        las reglas como dato: valor, porque, evidencia
src/<paquete>/         módulos que se importan y se testean
scripts/               lo que se corre desde la línea de comandos
  archive/             one-offs ya ejecutados, no se borran
data/                  datos generados y medidos (en .gitignore salvo los chicos)
tests/
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
