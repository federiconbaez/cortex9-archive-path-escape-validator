# cortex9-archive-path-escape-validator

[Español](README.es.md) · [Practice guide](PRACTICE.md) · [CI](https://github.com/federiconbaez/cortex9-archive-path-escape-validator/actions/workflows/ci.yml)

Pure string validation of archive entry names (the "Zip Slip" class of
path-traversal bugs) under two explicit profiles, **POSIX** and **Windows**.
It never extracts, creates or follows anything on disk.

**This is a validator and teaching tool, not a reproduction of any CVE.**
**A `CONTAINED_LEXICALLY` result does not mean an archive is safe to
extract.** Links, existing files and the extractor's own parsing are outside
what a string check can see. See [LIMITATIONS.md](LIMITATIONS.md).

## Verdicts

| Verdict | Meaning |
|---|---|
| `CONTAINED_LEXICALLY` | Read under this profile, the string alone cannot leave the destination. It does **not** account for symlinks created by other entries or already on disk. |
| `REJECT` | `EMPTY`, `NUL_BYTE`, `ABSOLUTE` (POSIX `/…`), `ROOT_RELATIVE` (Windows `\…` or `/…`), `DRIVE_ABSOLUTE` (`C:\…`, `C:/…`), `DRIVE_RELATIVE` (`C:x`), `UNC` (`\\server\share`, `//server/share`), `DEVICE_OR_VERBATIM_PREFIX` (`\\?\`, `\\.\`), `DOTDOT_ESCAPE` (walks above the root at any point). |
| `UNKNOWN` | `LINK_NOT_EVALUATED` (symlink/hardlink entries: no string-only safety claim), `SPECIAL_ENTRY_TYPE`, and on Windows `WIN_TRAILING_DOT_OR_SPACE`, `WIN_COLON_IN_COMPONENT`, `WIN_CONTROL_CHAR`, `WIN_RESERVED_NAME`. |

Rules that are deliberate:

- **Separators.** POSIX splits on `/` only; a backslash is an ordinary
  character (flag `BACKSLASH_LITERAL`). Windows splits on `/` and `\`.
- **No decoding.** `%2e%2e` stays a literal component (flag
  `PERCENT_LITERAL`); fullwidth dots `．．` are literal too.
- **`..` is rejected if it ever goes above the root,** even if the path
  comes back (`../out/x`). This is stricter than a containment check on the
  joined path.
- **Sibling-prefix confusion.** `contain --dest` compares the normalised join
  with the destination component by component and also reports the flawed
  string-prefix check, so `/srv/out` vs `/srv/out-sibling/x` shows
  `naive_prefix: true`, `within_components: false`.
- **`both` profile** returns the strictest of the two.

## Usage

```sh
PYTHONPATH=src python3 -m archive_path_check check --profile both '../x' 'C:x' 'a/b'
PYTHONPATH=src python3 -m archive_path_check check --jsonl fixtures/corpus.jsonl --profile windows
PYTHONPATH=src python3 -m archive_path_check list some.zip      # reads names only
PYTHONPATH=src python3 -m archive_path_check contain --dest /srv/out ../out-sibling/x
```

Exit codes: `0` all contained; `1` any `REJECT` (or, for `contain`, any
entry outside); `3` only `UNKNOWN`; `2` usage.

`list` uses Python's `zipfile`/`tarfile` to read names and types without
extracting. It inherits their parsing: `zipfile` truncates a name at the first
NUL byte, so NUL names inside zip files are not visible through `list`.

## Tests and results

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/gen_results.py && (cd results && sha256sum -c SHA256SUMS)
```

- `fixtures/corpus.jsonl`: 42 entries. `fixtures/expected.json`:
  hand-written `VERDICT:REASON` for each entry and profile (84 checks).
  `fixtures/containment.json`: 9 destination/name cases.
- Tests also build small zip/tar files in a temporary directory, list them,
  and assert that nothing was written.
- `results/summary.csv`: POSIX 29 contained / 10 reject / 3 unknown;
  Windows 12 contained / 19 reject / 11 unknown. With `both`: 12 / 19 / 11.
  These are counts over this corpus only.

Tested locally with Python 3.13.5 and 3.10; standard library only.

Files to read first: `src/archive_path_check/core.py`, `tests/test_corpus.py`,
`fixtures/corpus.jsonl`.

See [SOURCES.md](SOURCES.md), [LIMITATIONS.md](LIMITATIONS.md).
License: Apache-2.0.
