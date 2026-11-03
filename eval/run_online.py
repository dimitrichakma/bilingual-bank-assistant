"""Step 7: run the 40 test questions with an ONLINE model as the reply writer, for comparison only.
The assistant never uses this. Language, retrieval and the gate come from the local pipeline
(cached in outputs/models/_gate.json), and the prompt, number check and language check are the
same as the local run, so the only difference is who writes the reply.
Usage: uv run python eval/run_online.py [model] [--limit=N]      default model: claude-sonnet-5-5"""
import csv
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import src.assistant as assistant_mod  # noqa: E402
from src.assistant import Assistant  # noqa: E402
from src.generate import CANNOT, HANDOFF, LANGUAGE_RULE, PROMPT_TEMPLATE, RETRY_EXTRA  # noqa: E402

DEFAULT_MODEL = "claude-sonnet-5-5"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
LIMIT = int(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--limit=")), 0))
model = args[0] if args else DEFAULT_MODEL
key = os.environ.get("ONLINE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if not key:
    sys.exit("No key found. Put ONLINE_API_KEY (or ANTHROPIC_API_KEY) in .env")
# Same chain shape as the local reply: PROMPT_TEMPLATE, then a chat model, then plain text.
# No temperature: the newest Claude models reject it, so the online run is not forced to be repeatable.
# Thinking off like the local run (this model uses "between_tools" for that).
chain = (PROMPT_TEMPLATE
         | ChatAnthropic(model=model, api_key=key, max_tokens=300, thinking={"type": "between_tools"})
         | StrOutputParser())


def online_generate(question, entry, lang, retry=False, model=model, think=False):
    """Same prompt text as src/generate.py, sent to the online model."""
    return chain.invoke({
        "cannot": CANNOT, "language_rule": LANGUAGE_RULE[lang], "extra": RETRY_EXTRA if retry else "",
        "topic": entry.topic, "faq_question": entry.question, "answer": entry.answer,
        "question": question}).strip()


# reply_for calls generate() by name, so swapping it here reuses the exact same check and retry logic.
assistant_mod.generate = online_generate

rows = list(csv.DictReader(open(ROOT / "eval" / "expected.csv", encoding="utf-8-sig")))
if LIMIT:
    rows = rows[:LIMIT]  # quick smoke test; never overwrites the real results file
cache = json.loads((ROOT / "outputs" / "models" / "_gate.json").read_text(encoding="utf-8"))
bot = Assistant()
out = []
for x in rows:
    c = cache[x["id"]]
    t = time.time()
    if c["passed"]:
        status, reason, raw, retried = bot.reply_for(x["question"], bot.faq[c["faq_id"]], c["lang"], model=model)
    else:
        status, reason, raw, retried = "handoff", c["reason"], "", False
    secs = round(time.time() - t, 2)
    reply = raw if status == "answered" else HANDOFF[c["lang"]]
    out.append({
        "id": x["id"], "question": x["question"], "label_lang": x["language"], "detected_lang": c["lang"],
        "expected_faq": x["expected_faq_id"], "none_type": x["none_type"], "top1_faq": c["faq_id"],
        "score": round(c["score"], 3), "status": status, "reason": reason, "reply": reply,
        "raw_reply": raw, "seconds": secs, "retried": int(retried), "answer_correct": "",
    })
    print(f"{x['id']:>2} {status:8} {reason:14} {secs:5.1f}s", flush=True)

name = "results_online.csv" if model == DEFAULT_MODEL else f"results_online_{model}.csv"
if LIMIT:
    name = "results_online_smoke.csv"
with open(ROOT / "outputs" / name, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)

cov = [o for o in out if o["expected_faq"] != "NONE"]
none = [o for o in out if o["expected_faq"] == "NONE"]
secs = [o["seconds"] for o in out if o["raw_reply"]]
print(f"\n=== {model} ===")
print(f"Answered with the right FAQ entry (covered): "
      f"{sum(o['status'] == 'answered' and str(o['top1_faq']) == o['expected_faq'] for o in cov)}/{len(cov)}")
print(f"False handoff: {sum(o['status'] == 'handoff' for o in cov)}/{len(cov)}")
print(f"Correct 'I don't know' (NONE handed off): {sum(o['status'] == 'handoff' for o in none)}/{len(none)}")
print(f"Speed (reply writing only, incl. checks): average {sum(secs)/len(secs):.1f}s, slowest {max(secs):.1f}s")
print("Wrote", name)
