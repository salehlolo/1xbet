from app.api.base import Market, Outcome
from app.markets.mapper import map_market, is_low_priority


def test_map_totals_arabic():
    market = Market(
        name="مجموع 2.5",
        group="raw",
        line=None,
        side=None,
        outcomes=[Outcome(name="أكثر من 2.5", price=1.9), Outcome(name="أقل من 2.5", price=1.9)],
    )
    mapped = map_market(market)
    assert mapped.group == "total"
    assert mapped.line == 2.5


def test_map_asian_handicap():
    market = Market(
        name="هاندكاب آسيوي -0.75",
        group="raw",
        line=None,
        side=None,
        outcomes=[Outcome(name="فريق 1 -0.75", price=1.9), Outcome(name="فريق 2 +0.75", price=1.9)],
    )
    mapped = map_market(market)
    assert mapped.group == "asian_handicap"
    assert mapped.line == -0.75


def test_low_priority():
    assert is_low_priority("نتيجة صحيحة") is True
