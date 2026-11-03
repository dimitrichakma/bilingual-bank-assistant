"""Step 4: best retrieval score of every labelled question, to choose the gate threshold.
Threshold is picked on dev + dimitri sets and then checked on the test set."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.gate import asks_about_other_person  # noqa: E402
from src.lang import detect_language  # noqa: E402
from src.retrieve import Retriever  # noqa: E402

def load(name, tag):
    rows = list(csv.DictReader(open(ROOT / "eval" / name, encoding="utf-8-sig")))
    return [{**r, "set": tag} for r in rows if r["question"].strip()]

rows = load("dev_questions.csv", "dev") + load("lang_questions_dimitri.csv", "dimitri") \
    + load("expected.csv", "test")
r = Retriever()
out = []
for x in rows:
    q = x["question"]
    lang = detect_language(q)
    res = r.retrieve(q, lang)
    h = res.hits
    exp = x["expected_faq_id"]
    out.append({"set": x["set"], "id": x["id"], "lang": lang, "expected": exp,
                "none_type": x.get("none_type", ""), "top1": h[0].faq_id,
                "score": round(h[0].score, 3), "margin": round(h[0].score - h[1].score, 3),
                "correct": "" if exp == "NONE" else int(str(h[0].faq_id) == exp),
                "privacy": int(asks_about_other_person(q)), "question": q})

with open(ROOT / "outputs" / "gate_scores.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
print(f"wrote {len(out)} rows to outputs/gate_scores.csv")
