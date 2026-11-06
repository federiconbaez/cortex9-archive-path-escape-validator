# Sources

Fetched 2026-11-06. SHA256 values are of the fetched copies (not committed).

## Snyk zip-slip-vulnerability README

- Read raw via `gh api` (read-only) at commit
  b7d57e47f7da846253e2a9098affd2cf1743ddc1:
  https://github.com/snyk/zip-slip-vulnerability/blob/b7d57e47f7da846253e2a9098affd2cf1743ddc1/README.md
- SHA256: 84d6d7e1cdfa8823ebe41c206edbee3133bb0a792812cf8c684e31b933972ce3

> The vulnerability is exploited using a specially crafted archive that holds
> directory traversal filenames (e.g. `../../evil.sh`). The Zip Slip
> vulnerability can affect numerous archive formats, including `tar`, `jar`,
> `war`, `cpio`, `apk`, `rar` and `7z`.

Rows used as context (not reproduced): adm-zip, fixed 0.4.9,
CVE-2018-1002204; codehaus/plexus-archiver, fixed 3.6.0, CVE-2018-1002200;
Python `tarfile`, CVE-2007-4559 (no fixed version listed in that row).

## Microsoft: Naming Files, Paths, and Namespaces

- Published: https://learn.microsoft.com/windows/win32/fileio/naming-a-file
- Source read: https://raw.githubusercontent.com/MicrosoftDocs/win32/docs/desktop-src/FileIO/naming-a-file.md
- SHA256: bf2485c9f36d278b7d96f947869e36247ff8c56eacda6b65124ad0418d7bdcec

Used for the Windows profile:

> A file name is relative to the current directory if it does not begin with
> one of the following: A UNC name of any format, which always start with two
> backslash characters ("\\"). [...] A disk designator with a backslash, for
> example "C:\" or "d:\". A single backslash, for example, "\directory" [...]

> If a file name begins with only a disk designator but not the backslash
> after the colon, it is interpreted as a relative path to the current
> directory on the drive with the specified letter.

> CON, PRN, AUX, NUL, COM1 [...] COM¹, COM², COM³, LPT1 [...] Also avoid these
> names followed immediately by an extension; for example, NUL.txt and
> NUL.tar.gz are both equivalent to NUL.

> Do not end a file or directory name with a space or a period. Although the
> underlying file system may support such names, the Windows shell and user
> interface does not.

Also: the `\\?\` and `\\.\` prefixes, characters 1–31 and the reference to
alternate data streams. Where the page says behaviour depends on the API or
file system, the tool returns `UNKNOWN`.

## Python standard library (local, CPython 3.13.5)

- `zipfile.ZipInfo.__init__`: "Terminate the file name at the first null byte
  and ensure paths always use forward slashes" (`_sanitize_filename`).
- `tarfile.TarInfo.frombuf` docstring: "AREGTYPE headers are transformed to
  DIRTYPE headers if their name ends in '/'".
- Docs: https://docs.python.org/3/library/zipfile.html ,
  https://docs.python.org/3/library/tarfile.html

## CVE identifiers

- https://www.cve.org/CVERecord?id=CVE-2018-1002204
- https://www.cve.org/CVERecord?id=CVE-2018-1002200
- https://www.cve.org/CVERecord?id=CVE-2007-4559
