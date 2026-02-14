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
                    bookmaker=row.bookmaker,
                    odds=row.odds_raw,
                    fair_probability=row.fair_p,
                    ev=ev,
                    note="EV above threshold",
                    ts=datetime.utcnow(),
                )
            )
    return signals


def detect_outlier(event: EventModel, rows: Iterable[SnapshotRow], settings: Settings) -> List[Signal]:
    grouped: dict[str, list[SnapshotRow]] = defaultdict(list)
    for row in rows:
        grouped[row.market].append(row)

    signals: List[Signal] = []
    for market, market_rows in grouped.items():
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
                        bookmaker=row.bookmaker,
                        odds=row.odds_raw,
                        fair_probability=row.fair_p,
                        ev=calculate_ev(row.odds_raw, row.fair_p),
                        note=f"Odds {diff_ratio:.2%} above median",
                        ts=datetime.utcnow(),
                    )
                )
    return signals


def detect_steam(
    event: EventModel,
    current_rows: Iterable[SnapshotRow],
    historical_rows: Iterable[tuple],
    settings: Settings,
) -> List[Signal]:
    by_book_market: dict[tuple[str, str], float] = {}
    for bookmaker, implied_p, _fair_p, _odds_raw, _ts in historical_rows:
        by_book_market[(bookmaker, _ts)] = implied_p

    moved_books = 0
    signals: List[Signal] = []
    for row in current_rows:
        # compare against most recent implied_p for same bookmaker (best effort)
        recent_candidates = [v for (book, _), v in by_book_market.items() if book == row.bookmaker]
        if not recent_candidates:
            continue
        prev = recent_candidates[-1]
        delta = row.implied_p - prev
        if abs(delta) >= settings.steam_prob_delta:
            moved_books += 1
            signals.append(
                Signal(
                    signal_type="steam",
                    event_id=event.event_id,
                    sport=event.sport,
                    league=event.league,
                    teams=f"{event.home} vs {event.away}",
                    market=row.market,
                    bookmaker=row.bookmaker,
                    odds=row.odds_raw,
                    fair_probability=row.fair_p,
                    ev=calculate_ev(row.odds_raw, row.fair_p),
                    note=f"Implied probability shift {delta:+.3f}",
                    ts=datetime.utcnow(),
                )
            )

    if moved_books < settings.steam_min_books:
        return []
    return signals


def calculate_clv(entry_odds: float, closing_odds: float) -> float:
    return closing_odds - entry_odds
