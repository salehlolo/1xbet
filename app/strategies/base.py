from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from app.api.base import Event, Market


@dataclass
class Signal:
    event_id: str
    market_name: str
    selection: str
    price: float
    edge: float
    market_group: str | None = None
    line: float | None = None
    side: str | None = None
    market_overround: float | None = None


class Strategy(Protocol):
    def generate_signals(
        self, event: Event, markets: Iterable[Market], context: dict
    ) -> list[Signal]:
        ...
