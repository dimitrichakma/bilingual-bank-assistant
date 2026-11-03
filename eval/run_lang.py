"""Compare language detection: word list vs local model, on fresh questions plus dev and test sets."""
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.lang import detect_language, detect_language_wordlist  # noqa: E402

def load(name, tag):
    rows = list(csv.DictReader(open(ROOT / "eval" / name, encoding="utf-8-sig")))
    return [{**r, "set": tag} for r in rows]

rows = load("lang_questions.csv", "fresh") + load("dev_questions.csv", "dev") + load("expected.csv", "test")
# Dimitri's own messages. Rows with an empty question are the unfilled template, so skip them.
rows += [r for r in load("lang_questions_dimitri.csv", "dimitri") if r["question"].strip()]
detect_language("warm up")  # keep model load time out of the timings
res, secs = [], []
for x in rows:
    t = time.time()
    llm = detect_language(x["question"])
    secs.append(time.time() - t)
    res.append({**x, "wordlist": detect_language_wordlist(x["question"]), "llm": llm})

with open(ROOT / "outputs" / "lang_comparison.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["set", "id", "question", "language", "wordlist", "llm"],
                       extrasaction="ignore")
    w.writeheader(); w.writerows(res)

print(f"{'set':6} {'n':>3} {'wordlist':>10} {'qwen':>10}")
for s in ("fresh", "dimitri", "dev", "test", None):
    sel = [r for r in res if s is None or r["set"] == s]
    n = len(sel)
    if n == 0:
        continue
    a = sum(r["wordlist"] == r["language"] for r in sel)
    b = sum(r["llm"] == r["language"] for r in sel)
    print(f"{s or 'ALL':6} {n:>3} {a:>4}/{n} {a/n:4.0%} {b:>4}/{n} {b/n:4.0%}")
lat = [s for s, r in zip(secs, res) if r["language"] != "bn"]
print(f"\nqwen time per Latin text question: avg {sum(lat)/len(lat):.2f}s, slowest {max(lat):.2f}s")
for key in ("wordlist", "llm"):
    print(f"\n{key} errors:")
    for r in res:
        if r[key] != r["language"]:
            print(f"  {r['set']} {r['id']} said {r[key]}, label {r['language']}: {r['question']}")
