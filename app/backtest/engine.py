from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from app.api.base import Event, Market, Result
from app.backtest.metrics import BacktestMetrics, compute_drawdown
from app.markets.overround import overround
from app.strategies.base import Signal, Strategy


@dataclass
class BacktestConfig:
    stake_pct: float = 0.005


class BacktestEngine:
    def __init__(self, strategy: Strategy, config: BacktestConfig) -> None:
        self.strategy = strategy
        self.config = config

    def run(
        self,
        events: Iterable[Event],
        markets_by_event: dict[str, List[Market]],
        results: dict[str, Result],
        output_path: str = "output/backtest_report",
    ) -> BacktestMetrics:
        equity = 1.0
        equity_curve = [equity]
        wins = 0
        total_bets = 0
        total_overround = 0.0
        output_dir = Path(output_path)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        rows = []

        for event in events:
            event_markets = markets_by_event.get(event.id, [])
            signals = self.strategy.generate_signals(event, event_markets, {})
            for signal in signals:
                total_bets += 1
                stake = equity * self.config.stake_pct
                outcome = self._settle(signal, results.get(event.id))
                if outcome > 0:
                    wins += 1
                equity += stake * outcome
                equity_curve.append(equity)
                total_overround += sum(overround(market) for market in event_markets) / max(
                    len(event_markets), 1
                )
                rows.append(
                    {
                        "event_id": event.id,
                        "market": signal.market_name,
                        "selection": signal.selection,
                        "price": signal.price,
                        "edge": signal.edge,
                        "outcome": outcome,
                        "equity": equity,
                    }
                )

        roi = (equity - 1.0) if total_bets else 0.0
        hit_rate = wins / total_bets if total_bets else 0.0
        avg_overround = total_overround / total_bets if total_bets else 0.0
        max_dd = compute_drawdown(equity_curve)

        metrics = BacktestMetrics(
            roi=roi,
            hit_rate=hit_rate,
            max_drawdown=max_dd,
            total_bets=total_bets,
            avg_overround=avg_overround,
        )
        self._write_report(output_path, metrics, rows)
        return metrics

    def _settle(self, signal: Signal, result: Result | None) -> float:
        if result is None:
            return 0.0
        if signal.selection in ("نعم", "Yes", "yes"):
            return 1.0 if result.final_total > 0 else -1.0
        return 1.0 if result.winner in ("home", "away") else -1.0

    def _write_report(self, output_path: str, metrics: BacktestMetrics, rows: List[dict]) -> None:
        json_path = f"{output_path}.json"
        csv_path = f"{output_path}.csv"
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "metrics": metrics.__dict__,
                    "rows": rows,
                },
                handle,
                ensure_ascii=False,
                indent=2,
            )
        if rows:
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
