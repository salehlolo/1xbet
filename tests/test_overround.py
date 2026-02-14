from app.api.base import Market, Outcome
from app.markets.overround import de_vig_probs, overround


def test_overround_two_way():
    market = Market(
        name="Totals",
        group="total",
        line=2.5,
        side=None,
        outcomes=[Outcome(name="Over", price=1.9), Outcome(name="Under", price=1.9)],
    )
    result = overround(market)
    assert round(result, 4) == round((1 / 1.9 + 1 / 1.9) - 1, 4)


def test_overround_three_way():
    market = Market(
        name="1X2",
        group="euro_handicap",
        line=None,
        side=None,
        outcomes=[Outcome(name="1", price=2.1), Outcome(name="X", price=3.2), Outcome(name="2", price=3.6)],
    )
    result = overround(market)
    assert result > 0


def test_de_vig_probs_sum_one():
    market = Market(
        name="Totals",
        group="total",
        line=2.5,
        side=None,
        outcomes=[Outcome(name="Over", price=1.8), Outcome(name="Under", price=2.0)],
    )
    probs = de_vig_probs(market)
    assert round(sum(probs), 6) == 1.0
