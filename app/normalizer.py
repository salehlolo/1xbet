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


def market_group(market_name: str) -> str:
    text = market_name.lower()
    if "total" in text or "over" in text or "under" in text:
        return "totals"
    if "handicap" in text or "spread" in text:
        return "handicap"
    if "1x2" in text or "moneyline" in text or "winner" in text:
        return "1x2"
    return "other"


def normalize_odds(event: EventModel, allowed_groups: list[str], max_overround: float) -> List[SnapshotRow]:
    rows: List[SnapshotRow] = []
    now = datetime.utcnow()

    for market in event.markets:
        group = market_group(market.market_name)
        if group not in allowed_groups:
            continue

        implieds = [implied_probability(outcome.odds) for outcome in market.outcomes]
        raw_sum = sum(implieds)
        if raw_sum > max_overround:
            continue

        fairs = remove_vig(implieds)
        for outcome, implied, fair in zip(market.outcomes, implieds, fairs):
            rows.append(
                SnapshotRow(
                    event_id=event.event_id,
                    sport=event.sport,
                    market=market.market_name,
                    outcome=outcome.name,
                    bookmaker=outcome.bookmaker,
                    odds_raw=outcome.odds,
                    implied_p=implied,
                    fair_p=fair,
                    timestamp=now,
                )
            )
    return rows
