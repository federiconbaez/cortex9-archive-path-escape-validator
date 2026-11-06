# cortex9-archive-path-escape-validator

[English](README.md) · [Guía práctica](PRACTICE.md)

Validación puramente de cadenas de los nombres de entradas de archivos
comprimidos (la clase de fallos "Zip Slip") con dos perfiles explícitos,
**POSIX** y **Windows**. Nunca extrae, crea ni sigue nada en disco.

**Es un validador y herramienta de estudio, no una reproducción de un CVE.**
**`CONTAINED_LEXICALLY` no significa que un archivo sea seguro de extraer.**
`list` hereda de `zipfile` el truncamiento de nombres en el primer NUL: un
nombre zip con NUL no es visible completo.

- `CONTAINED_LEXICALLY`: la cadena sola no sale del destino bajo ese perfil;
  no considera enlaces creados por otras entradas ni existentes en disco.
- `REJECT`: vacío, NUL, absoluto, relativo a raíz, unidad absoluta
  (`C:\`), unidad relativa (`C:x`), UNC, prefijos `\\?\` / `\\.\`, o `..`
  que sube por encima de la raíz en algún punto.
- `UNKNOWN`: enlaces simbólicos o duros (sin afirmaciones de seguridad solo
  por cadena), tipos especiales y, en Windows, punto o espacio final, `:` en
  un componente, caracteres de control y nombres reservados.

Sin decodificación URL: `%2e%2e` es literal. En POSIX la barra invertida es un
carácter normal. `contain --dest` muestra la confusión de prefijo hermano
(`/srv/out` frente a `/srv/out-sibling`).

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/gen_results.py && (cd results && sha256sum -c SHA256SUMS)
```

Resultados sobre el corpus de 42 entradas: POSIX 29/10/3, Windows 12/19/11
(contenidos/rechazados/desconocidos). Ver [README.md](README.md),
[SOURCES.md](SOURCES.md) y [LIMITATIONS.md](LIMITATIONS.md). Licencia
Apache-2.0.
