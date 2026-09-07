# Arquitectura de agentes de Plomo

Como esta organizado el trabajo con Claude Code en este proyecto: quien hace
que, con que herramientas, y que cosas el sistema no deja hacer.

---

## El arquetipo

Plomo no es un proyecto de software con una tarea. Son cinco dominios que se
tocan entre si:

```
                            master
                (decide quien, en que orden, y consolida)
                                |
   +------------+------------+--+---------+------------+------------+
   |            |            |            |            |            |
 curador     analista     research     tecnico     archivista    productor
 (criterio    (mide y      (trae       (pipeline    (carpetas     (ingenieria
  de DJ)      discute)     material)    y DB)        y vistas)     inversa)
                                |
                          +-----+-----+
                          |           |
                        video       redes
                      (YouTube)   (IG/TikTok,
                                   identidad)
```

Cada uno vive en `.claude/agents/<nombre>.md`. No son roles decorativos: cada
archivo lleva el conocimiento especifico del dominio — los comandos, las trampas
que ya costaron caro, y lo que tiene prohibido hacer.

| Agente | Dominio | Lo que no hace |
|---|---|---|
| `master` | orquestacion | ejecutar el trabajo de otro sin delegarlo |
| `curador` | armado de sets, criterio | armar sin conocer el contexto del set |
| `analista` | medicion, backtest, reglas | cambiar una regla sin evidencia |
| `research` | descubrir musica y setlists | proponer sin decir por que entra |
| `tecnico` | pipeline, Rekordbox, DB | tocar la DB con Rekordbox abierto |
| `archivista` | carpetas, deposito, vistas | mover un archivo sin relink |
| `productor` | analisis de produccion | opinar de oido en vez de medir |
| `video` | YouTube | publicar por su cuenta |
| `redes` | IG/TikTok, marca, metricas | publicar por su cuenta |

---

## Las skills: los flujos que se invocan por nombre

| Skill | Que hace |
|---|---|
| `/sesion` | arranque: estado real + preguntar el foco antes de tocar nada |
| `/set` | armar un set de punta a punta |
| `/reglas` | desafiar el criterio con el backtest |
| `/vistas` | regenerar el arbol de carpetas navegable |
| `/receta` | ingenieria inversa de un track de referencia |
| `/boceto` | esqueleto de track para Ableton: clips MIDI + plano de arreglo |

Viven en `.claude/skills/<nombre>/SKILL.md`.

---

## Las tres capas de conocimiento

Lo que separa este setup de un prompt largo es que el conocimiento esta separado
por su naturaleza y cada capa se actualiza por su cuenta.

**Doctrina** — `docs/MI_SONIDO.md`, `docs/REGLAS.md`, `docs/YOUTUBE_SERIE.md`.
Que sonido se persigue, que se aprendio tocando, que apuesta se hizo con el
canal. Cambia despacio y la cambia una persona.

**Reglas operativas** — `rules/curaduria.json`. Los numeros que el solver usa,
cada uno con su valor, su porque y su evidencia. Cambia con datos y deja
historial versionado.

**Estado** — la DB de Rekordbox, `data/pool.json`, `data/set_targets/`,
`data/setlists/`. Cambia todo el tiempo y se consulta, nunca se memoriza.

Un agente que necesita saber "cuanto es el escalon maximo de energia" lee
`rules/curaduria.json`, no su propio prompt. Por eso la regla se puede discutir.

---

## Las reglas dejaron de ser constantes

Antes los numeros del criterio estaban hardcodeados en `scripts/select_set.py`:
`MAX_E_STEP = 1.3`, `if d > 1`, `- 0.6`. Un numero en el codigo no se puede
discutir — no tiene autor, no tiene fecha y no tiene evidencia.

Ahora viven en `rules/curaduria.json`:

```json
"max_escalon": {
  "valor": 1.3,
  "duro": true,
  "porque": "Un escalon mayor lo nota el publico como corte.",
  "evidencia": "PENDIENTE"
}
```

`src/plomo/rules.py` los sirve (`R.get("energia.max_escalon")`) y ademas expone
lo que el proyecto prefiere no ver: `R.conflictos()` lista donde lo escrito no
coincide con lo que corre, y `R.sin_evidencia()` lista las reglas duras que
nadie midio nunca.

`scripts/backtest_rules.py` cierra el circuito: mide cada regla como tasa de
violacion sobre dos corpus y emite un veredicto.

**La trampa que el sistema evita a proposito:** medir las reglas contra los sets
propios es circular — el solver las impone, siempre da 100% de cumplimiento. Por
eso hay tres corpus y no uno:

| corpus | de donde | que puede decir |
|---|---|---|
| PROPIO | `data/set_targets/` | nada: lo produjo el solver |
| TOCADO | `data/tocados/`, de `djmdHistory` via `ingest_history.py` | si la regla describe la practica propia |
| REFERENCIA | `data/setlists/` via `ingest_setlist.py` | si la regla es una ley del genero. El unico que refuta |

El corpus TOCADO sale del historial de Rekordbox: que se puso, en que orden y a
que hora, con key y BPM de la misma DB. Cobertura 100%, sin matcheo por nombre,
y no lo produjo el solver — es donde uno se desvia del plan arriba del escenario.
Hoy son 18 tandas, 299 tracks, 281 transiciones.

**Y una trampa que el sistema NO evitaba:** el cruce entre `set_targets` y
`pool.json` iba por ContentID, y los ContentID de Rekordbox cambian cuando se
reconstruye la biblioteca. Descartaba el 68% de los tracks, y lo que quedaba
eran justo los sets armados despues de la reconstruccion. El cruce ahora va por
`plomo.matching.clave()` — que conserva el remixer, porque una clave que descarta
los parentesis colapsa "Everlong (Original Mix)" con "Everlong (Karapetyan
Remix)" — y el backtest se niega a dar veredicto debajo del 80% de cobertura.

---

## Las carpetas: deposito y vistas

El disco guarda; no organiza.

**Deposito** — `Music/Biblioteca/AAAA-MM/`, por fecha de ingreso. Un archivo
entra una vez y no se mueve nunca mas. Mientras nada se mueva, ningun path de
Rekordbox se rompe. `scripts/tidy_library.py` hace la mudanza inicial en dos
fases, dry-run por defecto, y relinkea `FolderPath` en la misma operacion en que
mueve — si no puede relinkear, no mueve.

**Vistas** — `C:\Users\gonza\Music\Vistas`, arbol de hardlinks generado por
`scripts/build_views.py`. Por rol de set, energia, genero, key, BPM y sello.
10.123 enlaces sobre 1816 tracks, cero bytes extra: un hardlink apunta al mismo
dato en disco. Se borra y se regenera entero.

Cambiar de opinion sobre como ver la coleccion cuesta una funcion de tres lineas
en `VISTAS` y una corrida. Ese es todo el punto.

---

## Produccion: de un track a un estilo a un boceto

Tres herramientas encadenadas, cada una consumiendo el output de la anterior.

`scripts/reverse_engineer.py` mide **un** track: estructura por compases, curva
de energia, balance espectral, ancho estereo por banda, LUFS, densidad de eventos.

`scripts/derive_template.py` mide **muchos** del mismo autor o registro y devuelve
la mediana del estilo. La forma del arreglo se calcula por votacion posicion a
posicion: cada track se normaliza a 100 posiciones, cada posicion vota que tipo
de seccion es, y gana la mayoria. Promediar "donde arranca" y "cuanto dura" por
separado no sirve — son distribuciones independientes y producen un arreglo con
huecos que no encaja consigo mismo.

`scripts/make_sketch.py` genera el esqueleto: cinco clips MIDI de 8 compases
(acordes, bajo rodante, arpegio, bateria, melodia) en la tonalidad Camelot y el
BPM pedidos, mas un `ARREGLO.md` con los compases reales de la plantilla. El
escritor de MIDI (`src/plomo/midi.py`) es propio y sin dependencias: son ochenta
lineas, no valia sumar `mido` al proyecto por eso.

### El DAW

Ableton Live 12 Trial esta en `C:\ProgramData\Ableton\Live 12 Trial\`. Hoy el
agente no lo controla: entrega `.mid` que se arrastran a Live. Los otros dos
caminos, si alguna vez se decide dar el paso:

- **MCP** — `ahujasid/ableton-mcp`, un Remote Script que abre un socket dentro de
  Live. Se copia en
  `C:\Users\gonza\AppData\Roaming\Ableton\Live 12.4\Preferences\User Remote Scripts\`
  y se agrega `uvx ableton-mcp` a la config de MCP (`uv` ya esta instalado).
- **AbletonOSC + pylive** — expone el Live Object Model por OSC. Mas trabajo,
  pero es una libreria y no un protocolo de chat: encaja con el resto del
  proyecto, donde todo es un script que se corre solo y se testea.

Los dos son codigo de terceros corriendo adentro del DAW: no se instalan sin
pedido explicito.

---

## El guardarrail

`scripts/hooks/guard_rekordbox.py` es un hook PreToolUse sobre Bash. Ve si el
comando invoca un script que escribe en `master.db` y, si `rekordbox.exe` esta
corriendo, corta la llamada antes de que pase nada.

Existe porque el error es silencioso y caro: Rekordbox carga la DB en memoria al
abrir y la vuelca al cerrar, asi que un cambio externo hecho con el programa
abierto se pierde sin dar ningun error. Este proyecto ya perdio una biblioteca
entera por eso.

**Instalado y verificado** el 2026-09-07 en `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Users\\gonza\\Documents\\plomo\\.venv\\Scripts\\python.exe\" \"C:\\Users\\gonza\\Documents\\plomo\\scripts\\hooks\\guard_rekordbox.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

La lista de scripts que escriben esta en la constante `ESCRIBEN` del hook. Todo
script nuevo que toque la DB tiene que sumarse ahi: esa lista es lo unico que
separa un descuido de perder la biblioteca. `db_audit.py` se habia quedado
afuera de esa lista aunque hace soft-delete de tracks y mueve archivos.

---

## Como se usa esto en la practica

```
/sesion                 arranque, estado y foco
/set                    armar un set
/reglas                 discutir el criterio con numeros
/vistas                 regenerar las carpetas
/receta <track>         ingenieria inversa
```

Para lo demas, pedirselo al `master` y que reparta.
