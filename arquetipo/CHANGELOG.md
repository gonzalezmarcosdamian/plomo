# Cambios del arquetipo

Lo nuevo arriba. El número vive en `VERSION`; cada versión lleva el tag
`arquetipo-vX.Y.Z` en el mismo commit. MAYOR cambia el método o la forma del
proyecto (lo creado antes queda distinto); MENOR agrega a la plantilla; PARCHE
arregla el generador sin cambiar lo que sale.

Para ver qué le falta a un proyecto viejo: su `docs/BITACORA.md` dice de qué
versión salió, y `git diff arquetipo-vVIEJA arquetipo-vNUEVA -- arquetipo/`.

## 1.0.0 — 2026-09-28 — lo que se prometía, entregado

- La plantilla trae `.gitignore` (secretos por patrón, scratch, pesados, caches)
  y `.env.example`. Antes no traía ninguno y el README decía que `data/` estaba
  en `.gitignore`.
- `rules/criterio.json` pasa al esquema que plomo lee (`_meta.version`, `duro`,
  `historial`) y llega `src/<paquete>/criterio.py` para leerlo. El esquema viejo
  hacía que el lector de plomo diera versión `?`, no viera las reglas duras y
  fallara al aplicar.
- `pyproject.toml` y `__init__.py`: el paquete se instala y se importa desde
  cualquier lado.
- Llegan lo prometido y ausente: `docs/ARCHITECTURE.md` y
  `.claude/skills/sesion/SKILL.md`.
- `docs/METODO.md`: el proyecto nuevo se lleva el método (este README) con su
  versión, en vez de un puntero a una ruta de plomo.
- `tests/`: el criterio y la estructura se chequean solos.
- Método: de cinco a ocho reglas. La 4 (verificar) suma mirar la salida y no el
  número, comparar contra la fuente y decir lo que no aplicó. Nuevas: 6, "no se
  puede" es una conclusión; 7, lo que dice la persona es dato y lo que sale a su
  nombre es suyo; 8, la fuente se lee en el momento. La 2 suma el cuarto corpus
  (REFERENCIA, el único que refuta) y la decisión humana; la 1, reglas sin
  lector y el cambio de regla completo en un commit. La plantilla de CLAUDE.md
  lo lleva en corto, con una sección nueva "Cómo se trabaja".
- `.gitattributes`: LF en cualquier máquina. Con `core.autocrlf` de Windows, git
  convertía a CRLF al primer toque.
- Generador: paquete desde nombres con acentos (`Ñandú` → `nandu`, antes `and`),
  valida `--paquete`, no revienta si el destino es un archivo, escribe LF, y la
  fecha de la bitácora sale del marcador `{{FECHA}}`.
- Sale `redes/short_rapido.py`: era una copia exacta de
  `scripts/short_rapido.py` que el generador nunca copiaba.

## 0.2.1 — 2026-09-27 — `cc6a31f`

- Seis `.gitkeep`: después de un clone el proyecto nuevo nacía sin
  `scripts/archive`, `data`, `tests` ni el paquete.

## 0.2.0 — 2026-09-23 — `d4d5207`

- `redes/short_rapido.py`.

## 0.1.0 — 2026-09-08 — `8d07054`

- Primera versión: README con las cinco reglas, plantilla y generador.
