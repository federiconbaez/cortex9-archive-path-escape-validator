"""CLI.

  archive-path-check check [--profile posix|windows|both] NAME...
  archive-path-check check --jsonl FILE   (objects with name, type)
  archive-path-check list ARCHIVE [--profile ...]   (reads names only)
  archive-path-check contain --dest /abs/dir NAME...

Exit codes: 0 all CONTAINED_LEXICALLY; 1 any REJECT; 3 UNKNOWN only; 2 usage.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import PROFILES, classify, containment
from .listing import list_entries


def _results(entries, profile):
    rows = []
    profs = PROFILES if profile == "both" else (profile,)
    for e in entries:
        for p in profs:
            rows.append(classify(e["name"], p, e.get("type", "file")).row())
    return rows


def _code(rows) -> int:
    vs = {r["verdict"] for r in rows}
    return 1 if "REJECT" in vs else 3 if "UNKNOWN" in vs else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="archive-path-check")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--profile", choices=["posix", "windows", "both"], default="both")
    c.add_argument("--jsonl")
    c.add_argument("names", nargs="*")
    li = sub.add_parser("list")
    li.add_argument("archive")
    li.add_argument("--profile", choices=["posix", "windows", "both"], default="both")
    ct = sub.add_parser("contain")
    ct.add_argument("--dest", required=True)
    ct.add_argument("names", nargs="+")
    a = ap.parse_args(argv)

    if a.cmd == "contain":
        out = [containment(a.dest, n) for n in a.names]
        json.dump(out, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if any(not o["within_components"] for o in out) else 0
    if a.cmd == "check":
        entries = [{"name": n, "type": "file"} for n in a.names]
        if a.jsonl:
            with open(a.jsonl, encoding="utf-8") as fh:
                entries += [json.loads(l) for l in fh if l.strip()]
        if not entries:
            ap.error("no names given")
    else:
        entries = list_entries(a.archive)
    rows = _results(entries, a.profile)
    json.dump(rows, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")
    return _code(rows)


if __name__ == "__main__":
    raise SystemExit(main())
