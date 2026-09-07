---
name: sesion
description: Arranque de sesion de Plomo. Muestra el estado real de la biblioteca, las reglas y los pendientes, y pregunta el foco antes de tocar nada. Usar al empezar a trabajar.
---

# Arranque de sesion

No propongas nada antes de terminar los dos pasos.

## 1. Estado (ejecutar, no adivinar)

```bash
./.venv/Scripts/python.exe scripts/backtest_rules.py --solo-propio
./.venv/Scripts/python.exe scripts/check_inbox.py
git -C . log --oneline -5
```

Reportar en cinco lineas como maximo:

- tracks en la biblioteca y cuantos sin energia (invisibles para el selector)
- cuantos sets hay y cual es el numero mas alto
- conflictos de reglas abiertos
- que hay sin importar en el Inbox
- en que quedo la sesion anterior

## 2. Preguntar el foco antes de buscar o armar

Gonzalo dejo dicho explicitamente que no arranques a buscar musica ni a armar
sets sin esto. Preguntar:

- **Que estilo / vibe** — no "progressive" a secas: apertura organica, meseta
  hipnotica, colorido, peak oscuro.
- **Artistas de referencia** para esta sesion.
- **Contexto del set** si hay uno: donde, a que hora, cuanto dura, que publico.
- **Foco de la sesion**: descubrir musica, armar sets, ordenar la biblioteca,
  contenido, o desafiar el criterio.

Si el pedido inicial ya trae todo eso, saltear la pregunta y decirlo.

## 3. Recien ahi, delegar

Segun el foco, al agente que corresponde: `research`, `curador`, `tecnico`,
`archivista`, `analista`, `productor`, `video`, `redes`.
