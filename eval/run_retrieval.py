"""Step 3 experiment: retrieval hit rate by language, and the banglish rewrite options."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.lang import detect_language  # noqa: E402
from src.retrieve import Retriever, rewrite_query  # noqa: E402

rows = list(csv.DictReader(open(ROOT / "eval" / "expected.csv", encoding="utf-8-sig")))
r = Retriever()

# 1) Language detection check on all 40.
wrong = [(x["id"], x["language"], detect_language(x["question"])) for x in rows
         if detect_language(x["question"]) != x["language"]]
print(f"Language detection: {40 - len(wrong)}/40 correct. Wrong: {wrong}\n")

# 2) Retrieval. Variants: 'none' for all; 'english' and 'bangla' rewrites for banglish only.
out = []
for x in rows:
    q, lang = x["question"], x["language"]
    variants = {"none": q}
    if lang == "banglish":
        variants["english"] = rewrite_query(q, "english")
        variants["bangla"] = rewrite_query(q, "bangla")
    for name, text in variants.items():
        hits = r.search(text, 3)
        out.append({"id": x["id"], "lang": lang, "expected": x["expected_faq_id"],
                    "variant": name, "query": text,
                    "top1": hits[0].faq_id, "top1_score": round(hits[0].score, 3),
                    "top3": " ".join(str(h.faq_id) for h in hits)})

with open(ROOT / "outputs" / "retrieval_experiment.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

# 3) Hit rates on the 30 covered questions only.
stats = defaultdict(lambda: [0, 0, 0])  # (lang, variant) -> [n, top1, top3]
for o in out:
    if o["expected"] == "NONE":
        continue
    s = stats[(o["lang"], o["variant"])]
    s[0] += 1
    s[1] += str(o["top1"]) == o["expected"]
    s[2] += o["expected"] in o["top3"].split()
print(f"{'language':10} {'variant':8} {'n':>3} {'top1':>8} {'top3':>8}")
for (lang, variant), (n, t1, t3) in sorted(stats.items()):
    print(f"{lang:10} {variant:8} {n:>3} {t1:>3}/{n} {t1/n:4.0%} {t3:>3}/{n} {t3/n:4.0%}")
print("\nMisses (top1 wrong, covered questions):")
for o in out:
    if o["expected"] != "NONE" and str(o["top1"]) != o["expected"]:
        print(f"  Q{o['id']} {o['lang']}/{o['variant']}: expected {o['expected']}, top3 {o['top3']}, query: {o['query'][:70]}")
