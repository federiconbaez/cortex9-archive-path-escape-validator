"""Regenerate results/ from the fixture corpus (pure string checks)."""
import collections
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from archive_path_check.core import classify, classify_both, containment  # noqa: E402


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    corpus = [json.loads(l) for l in (ROOT / "fixtures/corpus.jsonl").read_text().splitlines() if l]
    rows = []
    for c in corpus:
        b = classify_both(c["name"], c["type"])
        for p in ("posix", "windows"):
            r = b[p]
            rows.append({"id": c["id"], "name_json": json.dumps(c["name"]), "type": c["type"],
                         "profile": p, "verdict": r.verdict, "reason": r.reason,
                         "flags": ";".join(r.flags), "combined": b["combined"]})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "corpus_results.csv").write_text(buf.getvalue())
    (out / "corpus_results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=True) + "\n")

    cont = [containment(c["dest"], c["name"])
            for c in json.loads((ROOT / "fixtures/containment.json").read_text())]
    (out / "containment.json").write_text(json.dumps(cont, indent=1) + "\n")

    s = io.StringIO()
    sw = csv.writer(s, lineterminator="\n")
    sw.writerow(["profile", "verdict", "reason", "count"])
    for (p, v, r), n in sorted(collections.Counter((x["profile"], x["verdict"], x["reason"]) for x in rows).items()):
        sw.writerow([p, v, r, n])
    (out / "summary.csv").write_text(s.getvalue())

    names = ["corpus_results.csv", "corpus_results.json", "containment.json", "summary.csv"]
    (out / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}\n" for n in names))
    print(f"{len(corpus)} entries x 2 profiles, {len(cont)} containment cases -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results")
