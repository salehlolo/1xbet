from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from app.api.base import Event, Market
from app.markets.overround import de_vig_probs
from app.strategies.base import Signal


@dataclass
class TotalsBaselineConfig:
    edge_threshold: float = 0.02


class TotalsBaselineStrategy:
    def __init__(self, config: TotalsBaselineConfig) -> None:
        self.config = config

    def generate_signals(
        self, event: Event, markets: Iterable[Market], context: dict
    ) -> List[Signal]:
        signals: List[Signal] = []
        for market in markets:
            if market.group not in ("total", "asian_total", "btts"):
                continue
            fair_probs = de_vig_probs(market)
            for outcome, fair_prob in zip(market.outcomes, fair_probs):
                implied = 1.0 / outcome.price
                edge = fair_prob - implied
                if edge >= self.config.edge_threshold:
                    signals.append(
                        Signal(
                            event_id=event.id,
                            market_name=market.name,
                            selection=outcome.name,
                            price=outcome.price,
                            edge=edge,
                            market_group=market.group,
                            line=market.line,
                        )
                    )
        return signals
