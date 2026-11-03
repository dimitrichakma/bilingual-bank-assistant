"""Extra check: run the assistant on the practice (dev) and Dimitri questions, which were not used
to write the prompts' answers. Shows how CANNOT_ANSWER and the checks behave on unseen questions."""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.assistant import Assistant  # noqa: E402

def load(name, tag):
    rows = list(csv.DictReader(open(ROOT / "eval" / name, encoding="utf-8-sig")))
    return [{**r, "set": tag} for r in rows if r["question"].strip()]

rows = load("dev_questions.csv", "dev") + load("lang_questions_dimitri.csv", "dimitri")
bot = Assistant()
bot.ask("warm up")
out = []
for x in rows:
    r = bot.ask(x["question"])
    out.append({"set": x["set"], "id": x["id"], "question": x["question"], "label_lang": x["language"],
                "detected_lang": r.lang, "expected_faq": x["expected_faq_id"], "top1_faq": r.faq_id,
                "score": r.score, "status": r.status, "reason": r.reason, "reply": r.reply,
                "raw_reply": r.raw_reply or "", "seconds": r.seconds})
    print(f"{x['set']:7}{x['id']:>4} {r.status:8} {r.reason:15} {r.seconds:5.1f}s", flush=True)

with open(ROOT / "outputs" / "results_extra.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)

cov = [o for o in out if o["expected_faq"] != "NONE"]
none = [o for o in out if o["expected_faq"] == "NONE"]
print(f"\nCovered: {len(cov)}  right entry on top {sum(str(o['top1_faq']) == o['expected_faq'] for o in cov)}"
      f"  answered with right entry {sum(o['status'] == 'answered' and str(o['top1_faq']) == o['expected_faq'] for o in cov)}"
      f"  false handoff {sum(o['status'] == 'handoff' for o in cov)}")
print(f"NONE: {len(none)}  handed off {sum(o['status'] == 'handoff' for o in none)}")
print("NONE by reason:", dict(Counter(o["reason"] for o in none)))
print("Language detected = label:", sum(o["detected_lang"] == o["label_lang"] for o in out), "/", len(out))
