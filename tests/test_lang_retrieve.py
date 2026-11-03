from src.lang import detect_language
from src.retrieve import Hit, merge_best


def test_bangla_script_is_bn_without_model():
    assert detect_language("আমার কার্ড হারিয়ে গেছে") == "bn"
    assert detect_language("আমার card এর PIN কিভাবে reset করব?") == "bn"


def test_merge_best_keeps_best_score_per_entry_and_sorts():
    a = [Hit(1, 0.5), Hit(2, 0.4)]
    b = [Hit(2, 0.7), Hit(3, 0.6)]
    assert [(h.faq_id, h.score) for h in merge_best(a, b)] == [(2, 0.7), (3, 0.6), (1, 0.5)]
