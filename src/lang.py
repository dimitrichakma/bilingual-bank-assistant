import os
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm

LANG_MODEL = os.environ.get("NB_MODEL", "qwen3.5:9b-mlx")  # env override lets eval swap the model
BANGLA_SCRIPT = re.compile(r"[ঀ-৿]")
WORD = re.compile(r"[a-z]+")

# Why the model and not a word list: banglish has no standard spelling, so a list fails on
# new words. Bangla script is still checked in code first because that is always right.
LLM_PROMPT = """Classify the language of a bank customer's message.
Answer with exactly one word:
en = English
banglish = Bangla written in English letters (Roman script). It often mixes in English banking words.

Examples:
Message: How do I apply for a loan?
Answer: en
Message: Loan er jonno ki lagbe amar?
Answer: banglish
Message: Is the ATM open now?
Answer: en
Message: Ekhon kothay giye taka tulbo?
Answer: banglish

Message: {q}
Answer:"""


LANG_PROMPT = ChatPromptTemplate.from_template(LLM_PROMPT)


def detect_language(text: str) -> str:
    """Return 'bn', 'en' or 'banglish'. Returns 'unknown' if the model answers anything else,
    so the caller can hand off instead of guessing the reply language."""
    if BANGLA_SCRIPT.search(text):
        return "bn"
    # LANG_MODEL is read at call time so eval scripts can swap it. A chain: prompt, model, text parser.
    chain = LANG_PROMPT | get_llm(LANG_MODEL, num_predict=6) | StrOutputParser()
    words = WORD.findall(chain.invoke({"q": text}).lower())
    return words[0] if words and words[0] in {"en", "banglish"} else "unknown"


# Old word list method. Not used by the assistant. Kept only so eval/run_lang.py can
# show the comparison honestly in the note.
_BANGLISH_WORDS = {
    "ami", "amar", "amake", "amader", "apni", "apnar", "apnader", "apnake", "tumi", "tomar",
    "ki", "koto", "kothay", "kobe", "kon", "kibhabe", "kivabe", "kemon", "kemne", "keno",
    "kore", "korte", "korbo", "korbe", "korle", "korini", "korechi", "kora", "korun",
    "ache", "achhe", "nai", "nei", "lagbe", "lage", "lagey", "chai", "chaichi", "pabo", "pabe",
    "paro", "pari", "hobe", "hoy", "hoye", "hoyeche", "gele", "gechi", "gelo", "jay", "jabe",
    "janabo", "jani", "bolun", "bolbo", "er", "theke", "ta", "gulo", "ekta",
    "ek", "din", "shomoy", "somoy", "khola", "thake", "bhule", "bochor", "bosor", "por",
    "kinle", "nite", "labh", "boyosh", "bondhu", "bhai", "jonno", "shathe", "sathe", "ar",
    "ebong", "kintu", "ei", "oi", "shob", "sob", "ekhon", "ekhane", "na", "naki",
}


def detect_language_wordlist(text: str) -> str:
    if BANGLA_SCRIPT.search(text):
        return "bn"
    return "banglish" if set(WORD.findall(text.lower())) & _BANGLISH_WORDS else "en"
