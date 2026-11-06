import io
import json
import os
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from archive_path_check.cli import main
from archive_path_check.core import classify, classify_both, containment
from archive_path_check.listing import list_entries

ROOT = Path(__file__).resolve().parent.parent
CORPUS = [json.loads(l) for l in (ROOT / "fixtures" / "corpus.jsonl").read_text().splitlines() if l]
EXP = json.loads((ROOT / "fixtures" / "expected.json").read_text())["expected"]
CONT = json.loads((ROOT / "fixtures" / "containment.json").read_text())


class Corpus(unittest.TestCase):
    def test_ids_match(self):
        self.assertEqual({c["id"] for c in CORPUS}, set(EXP))

    def test_every_entry_every_profile(self):
        for c in CORPUS:
            for prof in ("posix", "windows"):
                with self.subTest(id=c["id"], name=c["name"], profile=prof):
                    r = classify(c["name"], prof, c["type"])
                    self.assertEqual(f"{r.verdict}:{r.reason}", EXP[c["id"]][prof])

    def test_both_is_strictest(self):
        rank = {"CONTAINED_LEXICALLY": 0, "UNKNOWN": 1, "REJECT": 2}
        for c in CORPUS:
            b = classify_both(c["name"], c["type"])
            want = max((b["posix"].verdict, b["windows"].verdict), key=rank.get)
            self.assertEqual(b["combined"], want, c["id"])


class Containment(unittest.TestCase):
    def test_fixture(self):
        for c in CONT:
            with self.subTest(**c):
                r = containment(c["dest"], c["name"])
                self.assertEqual(r["within_components"], c["within"])
                self.assertEqual(r["naive_prefix"], c["naive"])

    def test_sibling_prefix_counterfactual(self):
        r = containment("/srv/out", "../out-sibling/x.txt")
        self.assertTrue(r["sibling_prefix_confusion"])
        # The entry-level check rejects it independently of any dest.
        self.assertEqual(classify("../out-sibling/x.txt", "posix").reason, "DOTDOT_ESCAPE")

    def test_entry_check_is_stricter_than_containment(self):
        # Leaves and re-enters: contained after normalisation, rejected per entry.
        self.assertTrue(containment("/srv/out", "../out/x.txt")["within_components"])
        self.assertEqual(classify("../out/x.txt", "posix").verdict, "REJECT")


class NoDecoding(unittest.TestCase):
    def test_percent_is_literal(self):
        r = classify("%2e%2e/%2e%2e/x", "posix")
        self.assertEqual(r.verdict, "CONTAINED_LEXICALLY")
        self.assertIn("PERCENT_LITERAL", r.flags)
        self.assertEqual(r.components, ["%2e%2e", "%2e%2e", "x"])


class ProfilesDiffer(unittest.TestCase):
    def test_backslash(self):
        self.assertEqual(classify("..\\x", "posix").verdict, "CONTAINED_LEXICALLY")
        self.assertIn("BACKSLASH_LITERAL", classify("..\\x", "posix").flags)
        self.assertEqual(classify("..\\x", "windows").reason, "DOTDOT_ESCAPE")

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            classify("x", "macos")


class Listing(unittest.TestCase):
    """Builds small archives in a temp dir, lists them, never extracts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_zip_names_and_nul_truncation(self):
        p = self.d / "t.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("ok/a.txt", b"x")
            z.writestr("../escape.txt", b"x")
            z.writestr(zipfile.ZipInfo("dir/"), b"")
        names = [(e["name"], e["type"]) for e in list_entries(str(p))]
        self.assertEqual(names, [("ok/a.txt", "file"), ("../escape.txt", "file"), ("dir/", "dir")])
        # stdlib behaviour: ZipInfo truncates at NUL, so a NUL name cannot be seen via zipfile.
        self.assertEqual(zipfile.ZipInfo("a\x00b").filename, "a")
        before = sorted(os.listdir(self.d))
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["list", str(p), "--profile", "posix"]), 1)
        self.assertEqual(sorted(os.listdir(self.d)), before, "listing must not write files")

    def test_tar_link_is_unknown(self):
        p = self.d / "t.tar"
        with tarfile.open(p, "w") as t:
            ti = tarfile.TarInfo("ok/a.txt")
            ti.size = 1
            t.addfile(ti, io.BytesIO(b"x"))
            ln = tarfile.TarInfo("ok/link")
            ln.type = tarfile.SYMTYPE
            ln.linkname = "a.txt"
            t.addfile(ln)
        es = list_entries(str(p))
        self.assertEqual([(e["name"], e["type"], e["link_target"]) for e in es],
                         [("ok/a.txt", "file", None), ("ok/link", "symlink", "a.txt")])
        self.assertEqual(classify("ok/link", "posix", "symlink").reason, "LINK_NOT_EVALUATED")


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", "--profile", "posix", "a/b"]), 0)
            self.assertEqual(main(["check", "--profile", "windows", "CON"]), 3)
            self.assertEqual(main(["check", "../x"]), 1)
            self.assertEqual(main(["contain", "--dest", "/srv/out", "../out-sibling/x"]), 1)


if __name__ == "__main__":
    unittest.main()
