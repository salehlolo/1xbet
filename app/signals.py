from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Iterable, List

from app.config import Settings
from app.models import EventModel, Signal, SnapshotRow
from app.normalizer import calculate_ev


def detect_positive_ev(event: EventModel, rows: Iterable[SnapshotRow], settings: Settings) -> List[Signal]:
    signals: List[Signal] = []
    for row in rows:
        ev = calculate_ev(row.odds_raw, row.fair_p)
        if ev >= settings.ev_threshold:
            signals.append(
                Signal(
                    signal_type="positive_ev",
                    event_id=event.event_id,
                    sport=event.sport,
                    league=event.league,
                    teams=f"{event.home} vs {event.away}",
                    market=row.market,
                    outcome=row.outcome,
                    bookmaker=row.bookmaker,
                    odds=row.odds_raw,
                    fair_probability=row.fair_p,
                    ev=ev,
                    note="EV above threshold",
                    timestamp=datetime.utcnow(),
                )
            )
    return signals


def detect_outlier(event: EventModel, rows: Iterable[SnapshotRow], settings: Settings) -> List[Signal]:
    grouped: dict[tuple[str, str], list[SnapshotRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.market, row.outcome)].append(row)

    signals: List[Signal] = []
    for (market, outcome), market_rows in grouped.items():
        if len(market_rows) < 2:
            continue
        med_odds = median([r.odds_raw for r in market_rows])
        for row in market_rows:
            if med_odds <= 0:
                continue
            diff_ratio = (row.odds_raw - med_odds) / med_odds
            if diff_ratio >= settings.outlier_threshold:
                signals.append(
                    Signal(
                        signal_type="outlier",
                        event_id=event.event_id,
                        sport=event.sport,
                        league=event.league,
                        teams=f"{event.home} vs {event.away}",
                        market=market,
                        outcome=outcome,
                        bookmaker=row.bookmaker,
                        odds=row.odds_raw,
                        fair_probability=row.fair_p,
                        ev=calculate_ev(row.odds_raw, row.fair_p),
                        note=f"Odds {diff_ratio:.2%} above median",
                        timestamp=datetime.utcnow(),
                    )
                )
    return signals


def detect_steam(
    event: EventModel,
    current_rows: Iterable[SnapshotRow],
    historical_rows: Iterable[tuple],
    settings: Settings,
) -> List[Signal]:
    prev_map: dict[tuple[str, str], float] = {}
    for bookmaker, outcome, implied_p, _fair_p, _odds_raw, _ts in historical_rows:
        prev_map[(bookmaker, outcome)] = implied_p

    moved_books = set()
    signals: List[Signal] = []
    for row in current_rows:
        key = (row.bookmaker, row.outcome)
        if key not in prev_map:
            continue
        delta = row.implied_p - prev_map[key]
        if abs(delta) >= settings.steam_prob_delta:
            moved_books.add(row.bookmaker)
            signals.append(
                Signal(
                    signal_type="steam",
                    event_id=event.event_id,
                    sport=event.sport,
                    league=event.league,
                    teams=f"{event.home} vs {event.away}",
                    market=row.market,
                    outcome=row.outcome,
                    bookmaker=row.bookmaker,
                    odds=row.odds_raw,
                    fair_probability=row.fair_p,
                    ev=calculate_ev(row.odds_raw, row.fair_p),
                    note=f"Implied probability shift {delta:+.3f}",
                    timestamp=datetime.utcnow(),
                )
            )

    if len(moved_books) < settings.steam_min_books:
        return []
    return signals


def calculate_clv(entry_odds: float, closing_odds: float) -> float:
    return closing_odds - entry_odds


def fractional_kelly(fair_p: float, odds: float, fraction: float = 0.25) -> float:
    b = odds - 1
    q = 1 - fair_p
    if b <= 0:
        return 0.0
    kelly = (b * fair_p - q) / b
    return max(0.0, kelly * fraction)
