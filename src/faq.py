import csv
from dataclasses import dataclass
from pathlib import Path

FAQ_PATH = Path(__file__).resolve().parent.parent / "data" / "bank-faq.csv"


@dataclass(frozen=True)
class FaqEntry:
    id: int
    topic: str
    question: str
    answer: str


def load_faq(path: Path = FAQ_PATH) -> list[FaqEntry]:
    # utf-8-sig because the sample CSV starts with a BOM, which would corrupt the "id" header.
    with open(path, encoding="utf-8-sig", newline="") as f:
        entries = [
            FaqEntry(int(r["id"]), r["topic"], r["question"], r["answer"])
            for r in csv.DictReader(f)
        ]
    # Fail loudly: a duplicate id would silently point answers at the wrong entry.
    if len({e.id for e in entries}) != len(entries):
        raise ValueError(f"Duplicate FAQ ids in {path}")
    return entries
