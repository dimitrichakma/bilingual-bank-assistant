"""Step 6: compare generator models on the 40 test questions.
Only the reply-writing model changes. Language detection, the privacy check, rewrite and retrieval stay
on qwen3.5:9b-mlx, so the comparison isolates who writes the reply.
Usage: uv run python eval/run_models.py qwen9_off qwen9_think ...   |   uv run python eval/run_models.py --summary"""
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.assistant import Assistant  # noqa: E402
from src.gate import asks_about_other_person, gate  # noqa: E402
from src.lang import detect_language  # noqa: E402

OUT = ROOT / "outputs" / "models"
CANDIDATES = {  # tag: (ollama model, thinking)
    "qwen9_off": ("qwen3.5:9b-mlx", False),
    "qwen9_think": ("qwen3.5:9b-mlx", True),
    "qwen4_off": ("qwen3.5:4b", False),
    "qwen4mlx_off": ("qwen3.5:4b-mlx", False),
    "gemma4b_off": ("gemma3:4b", False),
    "gemma4mlx_off": ("gemma4:e4b-mlx", False),
    "gemma12b_off": ("gemma3:12b", False),
}
rows = list(csv.DictReader(open(ROOT / "eval" / "expected.csv", encoding="utf-8-sig")))


def gate_cache(bot):
    """Language, retrieval and gate decision do not depend on the generator, so compute them once."""
    path = OUT / "_gate.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    cache = {}
    for x in rows:
        lang = detect_language(x["question"])
        hit = bot.retriever.retrieve(x["question"], lang).hits[0]
        g = gate(hit.score, asks_about_other_person(x["question"]))
        cache[x["id"]] = {"lang": lang, "faq_id": hit.faq_id, "score": hit.score,
                          "passed": g.passed, "reason": g.reason}
    path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def run(tag):
    model, think = CANDIDATES[tag]
    bot = Assistant()
    cache = gate_cache(bot)
    if tag.startswith("gemma"):
        # qwen 9B and Gemma do not fit in 16 GB together. The model checks its own reply language in this run.
        import src.lang as lang
        lang.LANG_MODEL = model
    bot.reply_for("warm up", bot.faq[1], "en", model=model, think=think)  # load the model first
    out = []
    for x in rows:
        c = cache[x["id"]]
        if not c["passed"]:
            out.append({"id": x["id"], "status": "handoff", "reason": c["reason"], "raw": "", "reply": "",
                        "retried": 0, "gen_seconds": 0})
            continue
        t = time.time()
        status, reason, raw, retried = bot.reply_for(x["question"], bot.faq[c["faq_id"]], c["lang"],
                                                     model=model, think=think)
        out.append({"id": x["id"], "status": status, "reason": reason, "raw": raw, "retried": int(retried),
                    "reply": raw if status == "answered" else "", "gen_seconds": round(time.time() - t, 2)})
        print(f"{tag} Q{x['id']:>2} {status:8} {reason:15} {out[-1]['gen_seconds']:5.1f}s", flush=True)
    with open(OUT / f"{tag}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)


def summary():
    cache = json.loads((OUT / "_gate.json").read_text(encoding="utf-8"))
    print(f"{'model':13} {'answered/right':>14} {'false HO':>9} {'NONE HO':>8} {'lang-fail':>9} {'retried':>7} {'avg s':>6} {'max s':>6}")
    for tag in CANDIDATES:
        p = OUT / f"{tag}.csv"
        if not p.exists():
            continue
        res = {r["id"]: r for r in csv.DictReader(open(p, encoding="utf-8-sig"))}
        cov = [x for x in rows if x["expected_faq_id"] != "NONE"]
        none = [x for x in rows if x["expected_faq_id"] == "NONE"]
        right = sum(res[x["id"]]["status"] == "answered" and str(cache[x["id"]]["faq_id"]) == x["expected_faq_id"] for x in cov)
        fho = sum(res[x["id"]]["status"] == "handoff" for x in cov)
        nho = sum(res[x["id"]]["status"] == "handoff" for x in none)
        lf = sum(r["reason"] == "check_language" for r in res.values())
        secs = [float(r["gen_seconds"]) for r in res.values() if float(r["gen_seconds"]) > 0]
        print(f"{tag:13} {right:>10}/{len(cov)} {fho:>9} {nho:>5}/{len(none)} {lf:>9} {sum(int(r['retried']) for r in res.values()):>7} "
              f"{sum(secs)/len(secs):>6.1f} {max(secs):>6.1f}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--summary"]:
        summary()
    else:
        for tag in sys.argv[1:]:
            run(tag)
