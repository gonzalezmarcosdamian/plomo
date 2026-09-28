---
name: sesion
description: Arranque de sesion de {{NOMBRE}}. Muestra el estado real y pregunta el foco antes de tocar nada. Usar al empezar a trabajar.
---

# Arranque de sesion

No propongas nada antes de terminar los dos pasos.

## 1. Estado (ejecutar, no adivinar)

```bash
git log --oneline -5
git status --short
python -m pytest -q
python -c "from {{PAQUETE}}.criterio import R; print(R.version, R.sin_evidencia(), R.sin_lector())"
```

Y la entrada de arriba de `docs/BITACORA.md`: en que quedo la sesion anterior.

Reportar en cinco lineas como maximo: que cambio, que esta roto, que reglas
estan sin medir o sin lector, que quedo pendiente.

## 2. Preguntar el foco antes de actuar

Si el pedido inicial ya lo trae, saltear la pregunta y decirlo.

## 3. Recien ahi, delegar

Al agente del dominio que corresponde (`.claude/agents/`).
