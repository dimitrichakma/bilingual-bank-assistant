import time
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.check import check_reply
from src.gate import asks_about_other_person, gate
from src.generate import CANNOT, GEN_MODEL, HANDOFF, generate
from src.lang import detect_language
from src.retrieve import Retriever


@dataclass
class Result:
    reply: str
    lang: str
    status: str            # 'answered' or 'handoff'
    reason: str            # why: ok, privacy, low_score, cannot_answer, check_numbers, ...
    faq_id: int | None
    score: float | None
    raw_reply: str | None  # what the model wrote, kept for debugging failed checks
    seconds: float
    retried: bool = False


class ReplyState(TypedDict, total=False):
    """State of the small write, check, retry graph."""
    question: str
    entry: Any        # the retrieved FaqEntry
    lang: str
    model: str
    think: bool
    raw: str          # what the model wrote
    retried: bool
    status: str       # 'answered' or 'handoff'
    reason: str


class PipelineState(TypedDict, total=False):
    """State of the main graph. A node returns only the keys it adds or changes."""
    question: str
    lang: str
    other: bool       # privacy check: asks about another person
    hit: Any          # best retrieval hit
    gate: Any         # GateResult
    status: str
    reason: str
    raw: str
    reply: str
    retried: bool


# ---- Write, check, retry (steps 4 and 5) -----------------------------------------------------

def _write(s: ReplyState) -> dict:
    raw = generate(s["question"], s["entry"], s["lang"], retry=s.get("retried", False),
                   model=s["model"], think=s["think"])
    return {"raw": raw}


def _check(s: ReplyState) -> dict:
    raw = s["raw"]
    if not raw or CANNOT in raw.upper():
        return {"status": "handoff", "reason": "cannot_answer"}
    bad = check_reply(raw, s["entry"].answer, s["lang"])
    if bad:
        return {"status": "handoff", "reason": bad}
    return {"status": "answered", "reason": "ok"}


def _after_check(s: ReplyState) -> str:
    # A model sometimes answers a banglish question in English. One stricter retry is cheap.
    # A number failure is never retried: that is a possible invented fact.
    if s["reason"] == "check_language" and not s.get("retried"):
        return "retry"
    return END


def build_reply_graph():
    g = StateGraph(ReplyState)
    g.add_node("write", _write)
    g.add_node("check", _check)
    g.add_node("mark_retry", lambda s: {"retried": True})
    g.add_edge(START, "write")
    g.add_edge("write", "check")
    g.add_conditional_edges("check", _after_check, {"retry": "mark_retry", END: END})
    g.add_edge("mark_retry", "write")  # the loop: write again, then check again
    return g.compile()


class Assistant:
    def __init__(self):
        self.retriever = Retriever()
        self.faq = {e.id: e for e in self.retriever.faq}
        self.reply_graph = build_reply_graph()
        self.graph = self._build_graph()

    # ---- Main pipeline (steps 1 to 5) --------------------------------------------------------

    def _build_graph(self):
        def detect(s: PipelineState) -> dict:
            lang = detect_language(s["question"])
            if lang == "unknown":
                # Cannot pick a reply language, so hand off in English rather than guess.
                return {"lang": "en", "status": "handoff", "reason": "unknown_language"}
            return {"lang": lang}

        def privacy(s: PipelineState) -> dict:
            return {"other": asks_about_other_person(s["question"])}

        def retrieve(s: PipelineState) -> dict:
            return {"hit": self.retriever.retrieve(s["question"], s["lang"]).hits[0]}

        def confidence_gate(s: PipelineState) -> dict:
            g = gate(s["hit"].score, s["other"])
            if not g.passed:
                return {"gate": g, "status": "handoff", "reason": g.reason}
            return {"gate": g}

        def answer(s: PipelineState) -> dict:
            entry = self.faq[s["hit"].faq_id]
            status, reason, raw, retried = self.reply_for(s["question"], entry, s["lang"])
            return {"status": status, "reason": reason, "raw": raw, "retried": retried,
                    "reply": raw if status == "answered" else ""}

        def stop_if_handed_off(next_node):
            # Any node that set a status has decided to hand off, so skip the remaining steps.
            return lambda s: END if s.get("status") == "handoff" else next_node

        g = StateGraph(PipelineState)
        for name, fn in [("detect", detect), ("privacy", privacy), ("retrieve", retrieve),
                         ("gate", confidence_gate), ("answer", answer)]:
            g.add_node(name, fn)
        g.add_edge(START, "detect")
        g.add_conditional_edges("detect", stop_if_handed_off("privacy"), ["privacy", END])
        g.add_edge("privacy", "retrieve")  # run one after another: one model in memory at a time
        g.add_edge("retrieve", "gate")
        g.add_conditional_edges("gate", stop_if_handed_off("answer"), ["answer", END])
        g.add_edge("answer", END)
        return g.compile()

    def diagram(self) -> str:
        """Mermaid text of the main graph, for the README and the Loom."""
        return self.graph.get_graph().draw_mermaid()

    def ask(self, question: str) -> Result:
        t0 = time.time()
        o = self.graph.invoke({"question": question})
        lang, hit = o["lang"], o.get("hit")
        return Result(o.get("reply") or HANDOFF[lang if lang in HANDOFF else "en"], lang, o["status"],
                      o["reason"], hit.faq_id if hit else None, round(hit.score, 3) if hit else None,
                      o.get("raw"), round(time.time() - t0, 2), o.get("retried", False))

    def reply_for(self, question, entry, lang, model: str = GEN_MODEL, think: bool = False):
        """Write, check, and retry once for a wrong language. Returns (status, reason, raw, retried).
        Split out so eval/run_models.py and eval/run_online.py can swap the model."""
        o = self.reply_graph.invoke({"question": question, "entry": entry, "lang": lang,
                                     "model": model, "think": think, "retried": False})
        return o["status"], o["reason"], o["raw"], o["retried"]
