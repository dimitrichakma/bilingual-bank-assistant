from src.check import invented_numbers, numbers_in
from src.gate import gate

FAQ7 = "Transfers to Nirbhor Bank accounts: up to BDT 10 lakh per day. BEFTN: up to BDT 5 lakh."


def test_numbers_normalise_bangla_digits_commas_and_decimals():
    assert numbers_in("৫০০ টাকা, BDT 1,000 and 7.50%") == {"500", "1000", "7.5"}


def test_invented_number_is_found_and_real_one_is_not():
    assert invented_numbers("Limit is 10 lakh", FAQ7) == set()
    assert invented_numbers("Limit is 20 lakh", FAQ7) == {"20"}


def test_gate_privacy_beats_a_high_score():
    assert gate(0.9, other_person=True).reason == "privacy"
    assert gate(0.4, other_person=False).reason == "low_score"
    assert gate(0.5, other_person=False).passed
