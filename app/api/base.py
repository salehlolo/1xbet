from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Protocol


@dataclass
class Event:
    id: str
    sport: str
    league: str
    start_time: datetime
    home: str
    away: str
    status: str
    match_url: str | None = None


@dataclass
class Outcome:
    name: str
    price: float


@dataclass
class Market:
    name: str
    group: str
    line: float | None
    side: str | None
    outcomes: List[Outcome]
    raw_name: str | None = None


@dataclass
class OddsSnapshot:
    event_id: str
    ts: datetime
    markets: List[Market]


@dataclass
class Result:
    event_id: str
    home_score: int
    away_score: int
    final_total: int
    winner: str


class Adapter(Protocol):
    def list_events(self, sport: str, date_range: Iterable[str]) -> List[Event]:
        ...

    def get_event_odds(self, event_id: str) -> OddsSnapshot:
        ...

    def get_results(self, date_range: Iterable[str]) -> List[Result]:
        ...
