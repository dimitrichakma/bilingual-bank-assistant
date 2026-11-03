import re
from decimal import Decimal, InvalidOperation

from src.lang import detect_language

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> set[str]:
    """All numbers in a text, in one form: Bangla digits to 0-9, commas removed, 7.50 == 7.5."""
    out = set()
    for m in NUMBER.findall(text.translate(BN_DIGITS)):
        try:
            out.add(format(Decimal(m.replace(",", "")).normalize(), "f"))
        except InvalidOperation:
            continue
    return out


def invented_numbers(reply: str, faq_answer: str) -> set[str]:
    return numbers_in(reply) - numbers_in(faq_answer)


def check_reply(reply: str, faq_answer: str, lang: str) -> str | None:
    """Return None if the reply passes, else the reason to hand off."""
    # Numbers first: a made up fee or phone number is the worst mistake a bank bot can make.
    if invented_numbers(reply, faq_answer):
        return "check_numbers"
    if detect_language(reply) != lang:
        return "check_language"
    return None
