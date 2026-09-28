# Arquitectura de {{NOMBRE}}

Dónde vive cada cosa y por qué. Si una carpeta nueva aparece, entra acá en el
mismo commit; si un script deja de usarse, sale de la tabla y va a `archive/`.

## Carpetas

| Carpeta | Qué va | Qué NO va |
|---|---|---|
| `src/{{PAQUETE}}/` | módulos que se importan y se testean | scripts, one-offs |
| `scripts/` | lo que se corre más de una vez | pruebas, one-offs |
| `scripts/archive/` | one-offs ya ejecutados (memoria, no se borran) | lo activo |
| `rules/` | criterios como dato: valor, porque, evidencia | datos medidos |
| `data/` | datos medidos y chicos que el código lee | scratch, caches, pesados |
| `docs/` | esta arquitectura, bitácora, aprendizajes, método | código, datos |
| Raíz | config: `pyproject.toml`, `.gitignore`, `.env.example`, `CLAUDE.md` | todo lo demás |

Qué no va al repo lo dice `.gitignore`, y solo ahí: una copia de la lista en este
archivo queda vieja el primer día que alguien agrega una línea al otro.

## Scripts activos

| Script | Cuándo | Qué hace |
|---|---|---|

## Flujo principal

<!-- Los comandos, en orden, del trabajo que más se repite. -->
