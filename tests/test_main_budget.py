import asyncio
from types import SimpleNamespace

from app.main import process_event
from app.models import EventModel, MarketModel, OutcomeModel


class _DB:
    def __init__(self):
        self.inserted = False

    def recent_market_snapshots(self, *_args, **_kwargs):
        return []

    def has_recent_alert(self, *_args, **_kwargs):
        return False

    def insert_alert(self, *_args, **_kwargs):
        return None

    def insert_snapshots(self, *_args, **_kwargs):
        self.inserted = True


class _TG:
    async def send_telegram_alert(self, *_args, **_kwargs):
        return None


class _Analyst:
    async def evaluate_snapshot(self, *_args, **_kwargs):
        return SimpleNamespace(overall_score=1.0)



def test_process_event_respects_remaining_budget():
    event = EventModel(
        event_id="e1",
        sport_id=1,
        sport="soccer",
        league="L",
        home="A",
        away="B",
        markets=[
            MarketModel(
                market_name="1X2",
                outcomes=[
                    OutcomeModel(name="home", odds=2.2, bookmaker="b1"),
                    OutcomeModel(name="away", odds=2.0, bookmaker="b1"),
                ],
            )
        ],
    )

    settings = SimpleNamespace(
        allowed_market_groups=["1x2", "totals", "handicap"],
        max_overround=1.2,
        steam_window_minutes=10,
        cooldown_minutes=30,
        min_score_threshold=0.0,
        ev_threshold=0.0,
        outlier_threshold=0.0,
        steam_prob_delta=999.0,
        steam_min_books=999,
    )

    db = _DB()
    tg = _TG()
    analyst = _Analyst()

    sent, remaining, generated = asyncio.run(process_event(event, db, tg, analyst, settings, remaining_budget=1))
    assert remaining == 0
    assert generated >= 0
    assert sent >= 0
    assert db.inserted is True
