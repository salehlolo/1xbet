from datetime import datetime, timedelta

from app.config import Settings
from app.time_filters import filter_events_by_start
from app.models import EventModel, SnapshotRow
from app.normalizer import calculate_ev, implied_probability, remove_vig
from app.signals import detect_outlier, detect_positive_ev, detect_steam, fractional_kelly


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
        SnapshotRow(event_id="1", sport="soccer", market="totals", outcome="over", bookmaker="b1", odds_raw=2.2, implied_p=0.45, fair_p=0.5, timestamp=datetime.utcnow()),
        SnapshotRow(event_id="1", sport="soccer", market="totals", outcome="over", bookmaker="b2", odds_raw=2.0, implied_p=0.5, fair_p=0.5, timestamp=datetime.utcnow()),
    ]
    assert detect_positive_ev(event, rows, settings)
    assert detect_outlier(event, rows, settings)


def test_detect_steam():
    settings = Settings(bets_api_key="x", steam_prob_delta=0.02, steam_min_books=1)
    event = EventModel(event_id="1", sport_id=1, sport="soccer", league="L", home="A", away="B")
    current = [
        SnapshotRow(event_id="1", sport="soccer", market="ml", outcome="home", bookmaker="b1", odds_raw=1.9, implied_p=0.526, fair_p=0.51, timestamp=datetime.utcnow())
    ]
    historical = [("b1", "home", 0.49, 0.5, 2.04, datetime.utcnow().isoformat())]
    signals = detect_steam(event, current, historical, settings)
    assert signals


def test_filter_events_by_start_and_kelly():
    now = datetime.utcnow()
    e1 = EventModel(event_id="1", sport_id=1, start_time=now + timedelta(minutes=2))
    e2 = EventModel(event_id="2", sport_id=1, start_time=now + timedelta(minutes=20))
    e3 = EventModel(event_id="3", sport_id=1, start_time=now + timedelta(minutes=120))
    e4 = EventModel(event_id="4", sport_id=1, start_time=None)
    filtered = filter_events_by_start([e1, e2, e3, e4], lookahead=60, min_to_kickoff=5)
    assert len(filtered) == 1
    assert filtered[0].event_id == "2"
    assert fractional_kelly(0.55, 2.0) > 0
