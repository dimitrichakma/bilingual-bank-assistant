from src.faq import load_faq


def test_faq_loads_30_entries_with_ids_1_to_30():
    faq = load_faq()
    assert [e.id for e in faq] == list(range(1, 31))
    assert all(e.question and e.answer for e in faq)
