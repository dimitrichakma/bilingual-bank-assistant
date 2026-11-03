import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.faq import FaqEntry
from src.llm import get_llm

GEN_MODEL = os.environ.get("NB_MODEL", "qwen3.5:9b-mlx")  # env override lets eval swap the model
CANNOT = "CANNOT_ANSWER"

HANDOFF = {
    "en": "I don't know, let me connect you to a person.",
    "bn": "আমি জানি না, আপনাকে একজন প্রতিনিধির সাথে যুক্ত করে দিচ্ছি।",
    "banglish": "Ami jani na, apnake ekjon protinidhir shathe jukto kore dichhi.",
}

LANGUAGE_RULE = {
    "en": "English.",
    "bn": "Bangla script, with simple common words. Write names such as Nirbhor Bank and NB Go "
          "in English letters.",
    "banglish": "Banglish: Bangla written in English letters, the way people text in Bangladesh. "
                "Write the whole reply this way, never as an English sentence, and never use Bangla "
                "script. Keep English banking words such as card, loan, branch, fee. "
                "Example 1. FAQ answer: The annual fee is BDT 200. Question: Fee koto? "
                "Reply: Annual fee 200 taka. "
                "Example 2. FAQ answer: Fees are charged once a year. Question: Fee kokhon kete? "
                "Reply: Fee proti bochor ekbar kete neya hoy.",
}

# Why the FAQ question and topic are included: an answer like "The interest rate is 12%"
# does not say WHICH product it belongs to. Without that the model reused it for other loans.
# Why the CANNOT_ANSWER rule: the score gate cannot stop questions that sound close to an
# FAQ entry but ask for something different (another product, a waiver, a phone number).
PROMPT = """You are a bank assistant. Answer the customer using ONLY the FAQ entry below.
Rules:
1. Use only facts written in the FAQ entry. Add nothing else. Do not guess.
2. The FAQ question tells you what the answer is about. If the customer asks about a different \
product or service, or about something the FAQ answer does not say, reply with exactly: {cannot}
3. If the FAQ answer does answer the customer's question, even in different words, answer it.
4. Reply in {language_rule}
5. Be short and polite: one to three sentences.
6. Copy numbers exactly as in the FAQ answer, written with the digits 0 to 9.
7. Keep the meaning exact. Do not change words like before, after, within, at least, up to, free, or per year.
{extra}
FAQ topic: {topic}
FAQ question: {faq_question}
FAQ answer: {answer}

Customer question: {question}
Reply:"""

RETRY_EXTRA = ("IMPORTANT: your previous reply was in the wrong language. "
               "Follow rule 4 exactly and write the whole reply in that language.\n")


PROMPT_TEMPLATE = ChatPromptTemplate.from_template(PROMPT)


def reply_chain(model: str = GEN_MODEL, think: bool = False):
    """Prompt, then local model, then plain text. The same chain shape is used for every model."""
    # Thinking models spend tokens on their reasoning first, so they need a much larger limit.
    return PROMPT_TEMPLATE | get_llm(model, think=think, num_predict=3000 if think else 300) | StrOutputParser()


def generate(question: str, entry: FaqEntry, lang: str, retry: bool = False,
             model: str = GEN_MODEL, think: bool = False) -> str:
    return reply_chain(model, think).invoke({
        "cannot": CANNOT, "language_rule": LANGUAGE_RULE[lang],
        "extra": RETRY_EXTRA if retry else "", "topic": entry.topic,
        "faq_question": entry.question, "answer": entry.answer, "question": question}).strip()
