"""Read member names and types from zip/tar archives without extracting.

Names are reported as the Python standard library parses them. Note:
zipfile truncates names at the first NUL byte (`_sanitize_filename`), and
tarfile turns old-style regular entries ending in '/' into directories.
"""
from __future__ import annotations

import tarfile
import zipfile


def _tar_type(m: tarfile.TarInfo) -> str:
    if m.issym():
        return "symlink"
    if m.islnk():
        return "hardlink"
    if m.isdir():
        return "dir"
    if m.isfile():
        return "file"
    return "special"


def list_entries(path: str) -> list[dict]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            return [{"name": i.filename, "type": "dir" if i.is_dir() else "file",
                     "link_target": None, "format": "zip"} for i in z.infolist()]
    with tarfile.open(path) as t:
        return [{"name": m.name, "type": _tar_type(m),
                 "link_target": m.linkname or None, "format": "tar"} for m in t.getmembers()]
