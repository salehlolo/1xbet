from __future__ import annotations

from typing import Iterable, List

from app.api.base import Market


def implied_prob(price: float) -> float:
    if price <= 0:
        raise ValueError("Price must be positive")
    return 1.0 / price


def overround(market: Market) -> float:
    probs = [implied_prob(outcome.price) for outcome in market.outcomes]
    return sum(probs) - 1.0


def de_vig_probs(market: Market) -> List[float]:
    probs = [implied_prob(outcome.price) for outcome in market.outcomes]
    total = sum(probs)
    if total == 0:
        return [0.0 for _ in probs]
    return [p / total for p in probs]


def overround_from_prices(prices: Iterable[float]) -> float:
    return sum(1.0 / price for price in prices) - 1.0
