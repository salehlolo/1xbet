from datetime import datetime

from app.config import Settings
from app.models import EventModel, MarketModel, OutcomeModel, SnapshotRow
from app.normalizer import calculate_ev, implied_probability, remove_vig
from app.signals import detect_outlier, detect_positive_ev, detect_steam


def test_implied_probability():
    assert round(implied_probability(2.0), 3) == 0.5


def test_remove_vig_sum_to_one():
    fair = remove_vig([0.55, 0.55])
    assert round(sum(fair), 6) == 1.0


def test_calculate_ev():
    ev = calculate_ev(2.1, 0.52)
    assert ev > 0


def test_detect_positive_ev_and_outlier():
    settings = Settings(bets_api_key="x", ev_threshold=0.01, outlier_threshold=0.02)
    event = EventModel(event_id="1", sport_id=1, sport="soccer", league="L", home="A", away="B")
    rows = [
        SnapshotRow(event_id="1", sport="soccer", market="totals:over", bookmaker="b1", odds_raw=2.2, implied_p=0.45, fair_p=0.5, ts=datetime.utcnow()),
        SnapshotRow(event_id="1", sport="soccer", market="totals:over", bookmaker="b2", odds_raw=2.0, implied_p=0.5, fair_p=0.5, ts=datetime.utcnow()),
    ]
    assert detect_positive_ev(event, rows, settings)
    assert detect_outlier(event, rows, settings)


def test_detect_steam():
    settings = Settings(bets_api_key="x", steam_prob_delta=0.02, steam_min_books=1)
    event = EventModel(event_id="1", sport_id=1, sport="soccer", league="L", home="A", away="B")
    current = [
        SnapshotRow(event_id="1", sport="soccer", market="ml:home", bookmaker="b1", odds_raw=1.9, implied_p=0.526, fair_p=0.51, ts=datetime.utcnow())
    ]
    historical = [("b1", 0.49, 0.5, 2.04, datetime.utcnow().isoformat())]
    signals = detect_steam(event, current, historical, settings)
    assert signals
