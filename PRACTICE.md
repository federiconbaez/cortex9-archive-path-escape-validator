# Guía práctica / Practice guide

Ejercicios **offline y locales** de validación defensiva. No se extrae nada,
no se escribe fuera de un directorio temporal de tests y no se interactúa con
ningún host ni laboratorio. *English summary at the end.*

## Objetivos

1. Clasificar nombres de entradas bajo POSIX y Windows y explicar por qué
   difieren.
2. Entender el error clásico de Zip Slip: concatenar `destino + nombre` sin
   validar (ejemplo Java del README de Snyk).
3. Distinguir la validación por entrada de la comprobación de contención del
   camino unido, y el error de prefijo de cadena.
4. Saber qué **no** puede afirmar una validación de cadenas (enlaces).

## Prerrequisitos

Python ≥ 3.10. Lectura: README de Snyk y la página de Microsoft sobre nombres
de archivo (ver [SOURCES.md](SOURCES.md)).

## Comandos locales

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m archive_path_check check --jsonl fixtures/corpus.jsonl --profile both
PYTHONPATH=src python3 -m archive_path_check contain --dest /srv/out ../outx ../out/x
```

## Ejercicios graduados

**Nivel 1 — leer el corpus.** Recorre `fixtures/corpus.jsonl` y predice
`VERDICT:REASON` por perfil antes de mirar `fixtures/expected.json`.

**Nivel 2 — mismo nombre, dos sistemas.** `C:x.txt` es un nombre normal en
POSIX y `DRIVE_RELATIVE` en Windows. Busca la frase de Microsoft que lo
justifica. Haz lo mismo con `..\..\x` y `\\server\share\x`.

**Nivel 3 — el error de prefijo.** Con destino `/srv/out`, `../outx` pasa
`naive_prefix` pero no `within_components`. Escribe la versión correcta en
otro lenguaje que conozcas y un test equivalente.

**Nivel 4 — normalización de Windows.** ¿Por qué `.. /x.txt` es `UNKNOWN`
en Windows y no `REJECT`? Argumenta con la regla de punto/espacio final.

**Nivel 5 — enlaces (código).** Implementa un validador **con estado** que
recorra la lista de entradas en orden, recuerde qué rutas son enlaces y
marque `REJECT` cualquier entrada posterior que pase por un enlace. Sigue sin
seguir enlaces en disco: solo la lista.

**Nivel 6 — comparar con la biblioteca estándar.** En Python ≥ 3.12,
`tarfile` tiene filtros de extracción (`filter="data"`). Lee la
documentación y escribe una tabla de qué casos del corpus rechazaría ese
filtro y cuáles no, sin extraer nada fuera de un directorio temporal.

**Nivel 7 — integración defensiva.** Usa `archive-path-check list` en un
pre-commit local o en CI para rechazar archivos con entradas `REJECT` antes
de que alguien los descomprima.

Los niveles 2–4 están verificados en `tests/test_practice.py`.

## Vínculo con los CVE

| Caso real (README de Snyk) | En el código |
|---|---|
| `new File(destinationDir, e.getName())` sin validar | lo que `classify` evita: decidir antes de unir |
| nombres `../../evil.sh` | `DOTDOT_ESCAPE` |
| comprobaciones `startsWith(dest)` mal hechas | `naive_prefix` frente a `within_components` |
| adm-zip (CVE-2018-1002204), plexus-archiver (CVE-2018-1002200), tarfile (CVE-2007-4559) | contexto; este repo no contiene ni ejecuta esas bibliotecas |

---

## English summary

Offline defensive exercises; nothing is extracted. Levels: (1) predict the
corpus verdicts; (2) one name under two profiles, justified from the
Microsoft page; (3) the string-prefix bug and a correct component check;
(4) why Windows trailing dot/space is `UNKNOWN`; (5) a stateful,
list-only link-aware validator; (6) compare with `tarfile` extraction
filters inside a temp dir; (7) use `list` as a local pre-commit gate.
Levels 2–4 are checked by `tests/test_practice.py`.
