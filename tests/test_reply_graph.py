"""Tests for the write, check, retry graph. The model and the language check are faked,
so these run without Ollama."""
import src.assistant as A
from src.faq import FaqEntry

ENTRY = FaqEntry(1, "Fees", "What is the fee?", "The fee is BDT 100.")


def run(monkeypatch, replies, language_ok=("check_language", None)):
    """replies: what the fake model writes on each call. language_ok: results of the language check."""
    calls, checks = [], list(language_ok)
    monkeypatch.setattr(A, "generate", lambda q, e, l, retry=False, model="m", think=False:
                        (calls.append(retry), replies[len(calls) - 1])[1])
    monkeypatch.setattr(A, "check_reply", lambda raw, ans, lang: checks.pop(0) if checks else None)
    graph = A.build_reply_graph()
    o = graph.invoke({"question": "q", "entry": ENTRY, "lang": "banglish", "model": "m", "think": False,
                      "retried": False})
    return o, calls


def test_wrong_language_is_retried_once_with_the_stricter_prompt(monkeypatch):
    o, calls = run(monkeypatch, ["English reply", "Fee 100 taka"])
    assert calls == [False, True]
    assert (o["status"], o["reason"], o["retried"]) == ("answered", "ok", True)


def test_wrong_language_twice_hands_off_and_does_not_loop_again(monkeypatch):
    o, calls = run(monkeypatch, ["English", "English again"], language_ok=("check_language", "check_language"))
    assert calls == [False, True]
    assert (o["status"], o["reason"]) == ("handoff", "check_language")


def test_cannot_answer_hands_off_without_retry(monkeypatch):
    o, calls = run(monkeypatch, ["CANNOT_ANSWER"])
    assert calls == [False]
    assert (o["status"], o["reason"], o["retried"]) == ("handoff", "cannot_answer", False)


def test_invented_number_is_never_retried(monkeypatch):
    o, calls = run(monkeypatch, ["Fee 999"], language_ok=("check_numbers",))
    assert calls == [False]
    assert (o["status"], o["reason"]) == ("handoff", "check_numbers")
