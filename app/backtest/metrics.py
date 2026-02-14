from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class BacktestMetrics:
    roi: float
    hit_rate: float
    max_drawdown: float
    total_bets: int
    avg_overround: float


def compute_drawdown(equity_curve: Iterable[float]) -> float:
    peak = 0.0
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown
