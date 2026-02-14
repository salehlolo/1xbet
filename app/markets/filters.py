from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from app.api.base import Market
from app.markets.overround import overround


@dataclass
class QualityConfig:
    max_overround: float
    common_lines: Iterable[float]
    include_groups: tuple[str, ...]


def filter_quality(markets: Iterable[Market], config: QualityConfig) -> List[Market]:
    filtered: List[Market] = []
    common_lines_set = {round(line, 2) for line in config.common_lines}
    for market in markets:
        if market.group == "excluded" or market.group not in config.include_groups:
            continue
        if market.line is not None and round(market.line, 2) not in common_lines_set:
            continue
        if overround(market) > config.max_overround:
            continue
        filtered.append(market)
    return filtered
