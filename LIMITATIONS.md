# Limitations

- **Strings only.** No filesystem access. `CONTAINED_LEXICALLY` does not mean
  "safe to extract": an earlier entry may create a symlink that a later entry
  writes through, and the destination may already contain links. Link entries
  are always `UNKNOWN`.
- **Two profiles, not every platform.** macOS case-insensitivity and Unicode
  normalisation, Windows 8.3 short names, NTFS case sensitivity flags,
  and file-system-specific rules are not modelled.
- **Windows behaviour depends on the API.** Trailing dots/spaces, reserved
  names, `:` and control characters are `UNKNOWN`, not `REJECT`, because the
  outcome varies by API and file system.
- **No decoding by design.** If an application percent-decodes or otherwise
  transforms names before using them, validate the transformed string.
- **zipfile NUL truncation (visible limitation).** `list` reads zip names
  through Python's `zipfile`, which truncates a name at the first NUL byte
  (`_sanitize_filename`). A zip entry such as `ok.txt\x00../../x` is listed as
  `ok.txt` and classified on that truncated string. The `NUL_BYTE` rule only
  fires for names given directly (`check`) or exposed in full by the parser.
- **Not an extraction safety guarantee.** Nothing in this repository should
  be read as "safe to extract".
- **Encoding.** Input is text. Raw bytes that are not valid in the archive's
  declared encoding are not handled; `list` uses the standard library's
  decoding and inherits its NUL truncation for zip names.
- **Conservative `..`.** Any walk above the root is rejected even when the
  joined path would come back inside.
- **`contain` uses POSIX destinations** only.
- **Corpus counts** describe this corpus, not real-world prevalence.
- CI is defined but has only been run locally (Python 3.13.5 and 3.10).
