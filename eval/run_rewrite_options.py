"""Compare banglish search options on the dev set and the test set.
A = no rewrite, B = Bangla rewrite only, C = original + Bangla rewrite, best score per FAQ entry."""
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.retrieve import Retriever, merge_best, rewrite_query  # noqa: E402

def load(name, tag):
    rows = list(csv.DictReader(open(ROOT / "eval" / name, encoding="utf-8-sig")))
    return [{**r, "set": tag} for r in rows if r["language"] == "banglish"]

rows = load("dev_questions.csv", "dev") + load("expected.csv", "test")
r = Retriever()
N_ALL = len(r.faq)

out, rewrite_secs = [], []
for x in rows:
    q = x["question"]
    t = time.time()
    rw = rewrite_query(q, "bangla")
    rewrite_secs.append(time.time() - t)
    a = r.search(q, N_ALL)
    b = r.search(rw, N_ALL)
    options = {"A": a, "B": b, "C": merge_best(a, b)}
    for name, hits in options.items():
        out.append({"set": x["set"], "id": x["id"], "expected": x["expected_faq_id"], "option": name,
                    "top1": hits[0].faq_id, "top1_score": round(hits[0].score, 3),
                    "top3": " ".join(str(h.faq_id) for h in hits[:3]), "rewrite": rw})

with open(ROOT / "outputs" / "rewrite_options.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

def table(sets):
    print(f"{'option':7} {'n':>3} {'top1':>10} {'top3':>10}")
    for opt in "ABC":
        sel = [o for o in out if o["option"] == opt and o["set"] in sets and o["expected"] != "NONE"]
        n = len(sel)
        t1 = sum(str(o["top1"]) == o["expected"] for o in sel)
        t3 = sum(o["expected"] in o["top3"].split() for o in sel)
        print(f"{opt:7} {n:>3} {t1:>4}/{n} {t1/n:4.0%} {t3:>4}/{n} {t3/n:4.0%}")

for label, sets in [("DEV banglish", {"dev"}), ("TEST banglish", {"test"}), ("BOTH", {"dev", "test"})]:
    print(f"\n{label}"); table(sets)
print(f"\nBangla rewrite time: avg {sum(rewrite_secs)/len(rewrite_secs):.1f}s, slowest {max(rewrite_secs):.1f}s over {len(rewrite_secs)} questions")
print("\nTop 1 misses (covered):")
for o in out:
    if o["expected"] != "NONE" and str(o["top1"]) != o["expected"]:
        print(f"  {o['set']} {o['id']} option {o['option']}: expected {o['expected']}, top3 {o['top3']}, score {o['top1_score']}")
