import pytest

from news_pipeline import scoring


@pytest.fixture(autouse=True)
def force_heuristic(monkeypatch):
    monkeypatch.setattr(scoring, "AI_AVAILABLE", False)


def test_score_item_empty():
    assert scoring.score_item({}) == 1


def test_score_item_length():
    item = {"title": "A"*500, "summary": "B"*500}
    assert scoring.score_item(item) == 4
