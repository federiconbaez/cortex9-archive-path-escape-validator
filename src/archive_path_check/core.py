"""Lexical classification of archive entry names under explicit profiles.

Verdicts:
  CONTAINED_LEXICALLY  the string, read under the profile, cannot leave the
                       destination by itself. This says nothing about links
                       created by other entries or already on disk.
  REJECT               the string is absolute, drive-qualified, UNC/device,
                       contains NUL, is empty, or walks above the root.
  UNKNOWN              the outcome depends on things a string cannot show
                       (links, Windows name normalisation, streams, devices).

No percent-decoding or other decoding is applied: archive formats store names
as given, so "%2e%2e" is a literal component.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

PROFILES = ("posix", "windows")

_DRIVE = re.compile(r"^[A-Za-z]:")
_RESERVED = re.compile(
    r"^(CON|PRN|AUX|NUL|COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3])(\..*)?$",
    re.IGNORECASE,
)


@dataclass
class Result:
    name: str
    profile: str
    entry_type: str
    verdict: str
    reason: str
    components: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def row(self) -> dict:
        d = asdict(self)
        d["components"] = "/".join(self.components)
        d["flags"] = ";".join(self.flags)
        return d


def _split(name: str, profile: str) -> list[str]:
    if profile == "windows":
        return re.split(r"[\\/]", name)
    return name.split("/")


def _walk(parts: list[str]) -> tuple[list[str] | None, list[str]]:
    """Lexically resolve '.', '..' and empty parts. None means it went above root."""
    out: list[str] = []
    flags: list[str] = []
    for p in parts:
        if p == "":
            flags.append("EMPTY_COMPONENT")
            continue
        if p == ".":
            flags.append("DOT_COMPONENT")
            continue
        if p == "..":
            if not out:
                return None, flags
            flags.append("DOTDOT_INSIDE")
            out.pop()
            continue
        out.append(p)
    return out, sorted(set(flags))


def classify(name: str, profile: str, entry_type: str = "file") -> Result:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    r = Result(name=name, profile=profile, entry_type=entry_type, verdict="", reason="")

    def done(verdict: str, reason: str) -> Result:
        r.verdict, r.reason = verdict, reason
        return r

    if name == "":
        return done("REJECT", "EMPTY")
    if "\x00" in name:
        return done("REJECT", "NUL_BYTE")

    if profile == "posix":
        if name.startswith("/"):
            return done("REJECT", "ABSOLUTE")
        if "\\" in name:
            r.flags.append("BACKSLASH_LITERAL")  # a normal byte on POSIX
    else:
        if name.startswith(("\\\\?\\", "\\\\.\\", "//?/", "//./", "\\\\?/", "\\\\./")):
            return done("REJECT", "DEVICE_OR_VERBATIM_PREFIX")
        if re.match(r"^[\\/]{2}", name):
            return done("REJECT", "UNC")
        if re.match(r"^[\\/]", name):
            return done("REJECT", "ROOT_RELATIVE")
        if _DRIVE.match(name):
            if re.match(r"^[A-Za-z]:[\\/]", name):
                return done("REJECT", "DRIVE_ABSOLUTE")
            return done("REJECT", "DRIVE_RELATIVE")

    if "%" in name and re.search(r"%[0-9A-Fa-f]{2}", name):
        r.flags.append("PERCENT_LITERAL")

    parts = _split(name, profile)
    walked, wflags = _walk(parts)
    r.flags.extend(wflags)
    if walked is None:
        return done("REJECT", "DOTDOT_ESCAPE")
    r.components = walked

    if profile == "windows":
        for c in walked:
            if c.endswith((".", " ")):
                return done("UNKNOWN", "WIN_TRAILING_DOT_OR_SPACE")
            if ":" in c:
                return done("UNKNOWN", "WIN_COLON_IN_COMPONENT")
            if any(ord(ch) < 32 for ch in c):
                return done("UNKNOWN", "WIN_CONTROL_CHAR")
            if _RESERVED.match(c):
                return done("UNKNOWN", "WIN_RESERVED_NAME")

    if entry_type in ("symlink", "hardlink"):
        return done("UNKNOWN", "LINK_NOT_EVALUATED")
    if entry_type not in ("file", "dir"):
        return done("UNKNOWN", "SPECIAL_ENTRY_TYPE")
    if not walked:
        r.flags.append("RESOLVES_TO_DESTINATION")
    return done("CONTAINED_LEXICALLY", "OK")


def classify_both(name: str, entry_type: str = "file") -> dict:
    res = {p: classify(name, p, entry_type) for p in PROFILES}
    vs = {x.verdict for x in res.values()}
    combined = "REJECT" if "REJECT" in vs else "UNKNOWN" if "UNKNOWN" in vs else "CONTAINED_LEXICALLY"
    return {"combined": combined, **res}


# --- containment checks on joined paths (string level, POSIX destination) ---

def _norm_posix(path: str) -> list[str]:
    out: list[str] = []
    for p in path.split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if out:
                out.pop()
            continue
        out.append(p)
    return out


def within_components(dest: str, name: str) -> bool:
    """Component-wise check that normpath(dest/name) is dest or below it."""
    if not dest.startswith("/"):
        raise ValueError("dest must be an absolute POSIX path")
    joined = name if name.startswith("/") else dest.rstrip("/") + "/" + name
    d, j = _norm_posix(dest), _norm_posix(joined)
    return j[: len(d)] == d


def naive_prefix(dest: str, name: str) -> bool:
    """The flawed check: string prefix of the normalised join (no separator)."""
    joined = name if name.startswith("/") else dest.rstrip("/") + "/" + name
    return ("/" + "/".join(_norm_posix(joined))).startswith("/" + "/".join(_norm_posix(dest)))


def containment(dest: str, name: str) -> dict:
    w, n = within_components(dest, name), naive_prefix(dest, name)
    return {"dest": dest, "name": name, "within_components": w, "naive_prefix": n,
            "sibling_prefix_confusion": n and not w}
