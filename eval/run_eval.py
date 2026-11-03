"""Run the 40 test questions through the local assistant and write outputs/results_local.csv.
Automatic numbers are proxies. 'answer_correct' is left empty for Dimitri to mark by hand."""
import csv
import platform
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.assistant import Assistant  # noqa: E402
from src.generate import GEN_MODEL  # noqa: E402

rows = list(csv.DictReader(open(ROOT / "eval" / "expected.csv", encoding="utf-8-sig")))
bot = Assistant()
bot.ask("warm up")  # keep first model load out of the timings
out = []
for x in rows:
    r = bot.ask(x["question"])
    out.append({
        "id": x["id"], "question": x["question"], "label_lang": x["language"],
        "detected_lang": r.lang, "expected_faq": x["expected_faq_id"], "none_type": x["none_type"],
        "top1_faq": r.faq_id, "score": r.score, "status": r.status, "reason": r.reason,
        "reply": r.reply, "raw_reply": r.raw_reply or "", "seconds": r.seconds, "retried": int(r.retried),
        "answer_correct": "",
    })
    print(f"{x['id']:>2} {r.status:8} {r.reason:14} {r.seconds:5.1f}s", flush=True)

with open(ROOT / "outputs" / "results_local.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)

cov = [o for o in out if o["expected_faq"] != "NONE"]
none = [o for o in out if o["expected_faq"] == "NONE"]
print("\n=== SUMMARY (automatic) ===")
print(f"Retrieval top1 right (covered): {sum(str(o['top1_faq']) == o['expected_faq'] for o in cov)}/{len(cov)}")
print(f"Answered with the right FAQ entry (covered): "
      f"{sum(o['status'] == 'answered' and str(o['top1_faq']) == o['expected_faq'] for o in cov)}/{len(cov)}  (facts still need your hand check)")
print(f"False handoff (covered but handed off): {sum(o['status'] == 'handoff' for o in cov)}/{len(cov)}")
print(f"Correct 'I don't know' (NONE handed off): {sum(o['status'] == 'handoff' for o in none)}/{len(none)}")
by = defaultdict(lambda: [0, 0])
for o in none:
    by[o["none_type"]][0] += 1
    by[o["none_type"]][1] += o["status"] == "handoff"
for k, (n, ok) in sorted(by.items()):
    print(f"   {k}: {ok}/{n}")
print("Language detected = label:")
for lang in ("en", "bn", "banglish"):
    sel = [o for o in out if o["label_lang"] == lang]
    print(f"   {lang}: {sum(o['detected_lang'] == lang for o in sel)}/{len(sel)}")
secs = [o["seconds"] for o in out]
print(f"Speed: average {sum(secs)/len(secs):.1f}s, slowest {max(secs):.1f}s per reply on {platform.machine()} {platform.system()}, {GEN_MODEL}, thinking off")
print("Handoff reasons:", dict(sorted(__import__('collections').Counter(o['reason'] for o in out).items())))
