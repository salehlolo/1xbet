from __future__ import annotations

from datetime import datetime
from typing import List

from app.models import EventModel, SnapshotRow


def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1:
        raise ValueError("Odds must be greater than 1")
    return 1 / decimal_odds


def remove_vig(implied_probs: list[float]) -> list[float]:
    total = sum(implied_probs)
    if total <= 0:
        raise ValueError("Invalid probabilities")
    return [p / total for p in implied_probs]


def calculate_ev(book_odds: float, fair_p: float) -> float:
    return (book_odds * fair_p) - 1


def normalize_odds(event: EventModel) -> List[SnapshotRow]:
    rows: List[SnapshotRow] = []
    now = datetime.utcnow()
    for market in event.markets:
        implieds = [implied_probability(outcome.odds) for outcome in market.outcomes]
        fairs = remove_vig(implieds)
        for outcome, implied, fair in zip(market.outcomes, implieds, fairs):
            rows.append(
                SnapshotRow(
                    event_id=event.event_id,
                    sport=event.sport,
                    market=f"{market.market_name}:{outcome.name}",
                    bookmaker=outcome.bookmaker,
                    odds_raw=outcome.odds,
                    implied_p=implied,
                    fair_p=fair,
                    ts=now,
                )
            )
    return rows
