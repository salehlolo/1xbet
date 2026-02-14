from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(default=None, default_factory=None, **_kwargs):
        if default_factory is not None:
            return default_factory()
        return default


class OutcomeModel(BaseModel):
    name: str
    odds: float = Field(gt=1.0)
    bookmaker: str = "1xbet"


class MarketModel(BaseModel):
    market_name: str
    outcomes: List[OutcomeModel]


class EventModel(BaseModel):
    event_id: str
    sport_id: int
    sport: str = "unknown"
    league: str = "unknown"
    home: str = "Home"
    away: str = "Away"
    markets: List[MarketModel] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    inplay: bool = False


class BetsAPIResponse(BaseModel):
    success: int | None = None
    results: Any = None


class SnapshotRow(BaseModel):
    event_id: str
    sport: str
    market: str
    outcome: str
    bookmaker: str
    odds_raw: float
    implied_p: float
    fair_p: float
    timestamp: datetime


class Signal(BaseModel):
    signal_type: str
    event_id: str
    sport: str
    league: str
    teams: str
    market: str
    outcome: str
    bookmaker: str
    odds: float
    fair_probability: float
    ev: float
    note: str = ""
    timestamp: datetime


@dataclass
class Opportunity:
    snapshot: SnapshotRow
    edge_score: float
    performance_score: float | None
    schedule_score: float | None
    steam_score: float | None
    outlier_score: float | None
    overall_score: float
    confidence: float
    risk_flags: list[str]
