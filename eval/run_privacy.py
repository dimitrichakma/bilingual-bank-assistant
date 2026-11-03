"""Check the privacy yes/no question on eval/privacy_questions.csv with the model in NB_MODEL."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.gate import GATE_MODEL, asks_about_other_person  # noqa: E402

rows = list(csv.DictReader(open(ROOT / "eval" / "privacy_questions.csv", encoding="utf-8-sig")))
wrong = [r for r in rows if int(asks_about_other_person(r["question"])) != int(r["other_person"])]
print(f"{GATE_MODEL}: {len(rows) - len(wrong)}/{len(rows)} right")
for r in wrong:
    print("WRONG", r["id"], r["other_person"], r["question"])
