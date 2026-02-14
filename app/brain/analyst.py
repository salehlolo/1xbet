from __future__ import annotations

from typing import Optional

from app.database import Database
from app.models import Opportunity, SnapshotRow
from app.normalizer import calculate_ev


class Analyst:
    def __init__(self, db: Database, external_data_client: Optional[object] = None):
        self.db = db
        self.external_data_client = external_data_client

    async def evaluate_snapshot(self, snapshot: SnapshotRow) -> Opportunity:
        edge = calculate_ev(snapshot.odds_raw, snapshot.fair_p)
        perf_score = await self._compute_performance_score(snapshot)
        sched_score = await self._compute_schedule_score(snapshot)
        steam_score, outlier_score = await self._compute_market_scores(snapshot)

        overall = (
            0.4 * edge
            + 0.2 * (perf_score or 0.0)
            + 0.2 * (sched_score or 0.0)
            + 0.1 * (steam_score or 0.0)
            + 0.1 * (outlier_score or 0.0)
        )
        confidence = self._estimate_confidence(overall, snapshot)
        flags: list[str] = []
        if snapshot.fair_p < 0.05:
            flags.append("very_low_probability")
        return Opportunity(
            snapshot=snapshot,
            edge_score=edge,
            performance_score=perf_score,
            schedule_score=sched_score,
            steam_score=steam_score,
            outlier_score=outlier_score,
            overall_score=overall,
            confidence=confidence,
            risk_flags=flags,
        )

    async def _compute_performance_score(self, snapshot: SnapshotRow) -> Optional[float]:
        return None

    async def _compute_schedule_score(self, snapshot: SnapshotRow) -> Optional[float]:
        return None

    async def _compute_market_scores(self, snapshot: SnapshotRow) -> tuple[Optional[float], Optional[float]]:
        history = self.db.recent_market_snapshots(snapshot.event_id, snapshot.market, minutes=30)
        if not history:
            return None, None
        prev = history[-1]
        steam = abs(snapshot.implied_p - float(prev[2]))
        outlier = max(0.0, snapshot.odds_raw - float(prev[4])) / max(float(prev[4]), 1e-9)
        return steam, outlier

    def _estimate_confidence(self, overall: float, snapshot: SnapshotRow) -> float:
        _ = snapshot
        return max(0.0, min(1.0, overall + 0.5))
