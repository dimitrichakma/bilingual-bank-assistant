import os
from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm

# Chosen from outputs/gate_scores.csv (Step 4): just above the highest no_match score (0.486).
# The margin is thin (lowest covered score is also 0.486), so say so in the note.
SCORE_THRESHOLD = 0.50
GATE_MODEL = os.environ.get("NB_MODEL", "qwen3.5:9b-mlx")  # env override lets eval swap the model

# Why a model and not a keyword list: people ask about others in many ways and languages.
# This only says WHO the question is about. The score check below stays plain code.
PRIVACY_PROMPT = """A bank customer sent a message. Answer yes ONLY if the message refers to a specific OTHER person \
(a friend, relative, neighbour, colleague or someone else) AND asks for that person's account, balance, \
transactions, loan status or personal data, or asks about an account number that is not the customer's own.
Answer no for everything else. Questions about the customer's own card, PIN, account, loan, fees, limits, \
documents or bank rules are always no. Mentioning a family member without asking for their data is no. \
Words like bhai used to address the bank are no.
Answer with exactly one word: yes or no.

Message: What is my brother's account balance?
Answer: yes
Message: আমার প্রতিবেশীর লোনের কিস্তি কত বাকি?
Answer: yes
Message: Amar chachar account e koto taka ache bolo
Answer: yes
Message: How do I open an account for myself?
Answer: no
Message: Amar card ta lost hoye gese
Answer: no
Message: bhai amar ATM pin bhule gechi
Answer: no
Message: I want to add my wife as a nominee
Answer: no

Message: {q}
Answer:"""


PRIVACY_TEMPLATE = ChatPromptTemplate.from_template(PRIVACY_PROMPT)


def asks_about_other_person(question: str) -> bool:
    chain = PRIVACY_TEMPLATE | get_llm(GATE_MODEL, num_predict=4) | StrOutputParser()
    return chain.invoke({"q": question}).strip().lower().startswith("yes")


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reason: str  # 'ok', 'privacy' or 'low_score'


def gate(top_score: float, other_person: bool, threshold: float = SCORE_THRESHOLD) -> GateResult:
    # Privacy first: a high score must never let another person's data through.
    if other_person:
        return GateResult(False, "privacy")
    if top_score < threshold:
        return GateResult(False, "low_score")
    return GateResult(True, "ok")
