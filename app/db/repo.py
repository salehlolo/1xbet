from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Iterable, List

from app.api.base import Event, OddsSnapshot, Result


class Repository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def upsert_events(self, events: Iterable[Event]) -> None:
        conn = self._connect()
        try:
            conn.executemany(
                """
                INSERT INTO events (id, sport, league, start_time, home, away, status, match_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sport=excluded.sport,
                    league=excluded.league,
                    start_time=excluded.start_time,
                    home=excluded.home,
                    away=excluded.away,
                    status=excluded.status,
                    match_url=excluded.match_url
                """,
                [
                    (
                        event.id,
                        event.sport,
                        event.league,
                        event.start_time.isoformat(),
                        event.home,
                        event.away,
                        event.status,
                        event.match_url,
                    )
                    for event in events
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def insert_snapshot(self, snapshot: OddsSnapshot) -> int:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO odds_snapshots (event_id, ts) VALUES (?, ?)",
                (snapshot.event_id, snapshot.ts.isoformat()),
            )
            snapshot_id = cursor.lastrowid
            for market in snapshot.markets:
                cursor = conn.execute(
                    """
                    INSERT INTO markets (snapshot_id, group_name, name, line, side)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (snapshot_id, market.group, market.name, market.line, market.side),
                )
                market_id = cursor.lastrowid
                conn.executemany(
                    "INSERT INTO outcomes (market_id, outcome_name, price) VALUES (?, ?, ?)",
                    [(market_id, outcome.name, outcome.price) for outcome in market.outcomes],
                )
            conn.commit()
            return int(snapshot_id)
        finally:
            conn.close()

    def upsert_results(self, results: Iterable[Result]) -> None:
        conn = self._connect()
        try:
            conn.executemany(
                """
                INSERT INTO results (event_id, home_score, away_score, final_total, winner)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    home_score=excluded.home_score,
                    away_score=excluded.away_score,
                    final_total=excluded.final_total,
                    winner=excluded.winner
                """,
                [
                    (
                        result.event_id,
                        result.home_score,
                        result.away_score,
                        result.final_total,
                        result.winner,
                    )
                    for result in results
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def load_events(self, sport: str) -> List[Event]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, sport, league, start_time, home, away, status, match_url FROM events WHERE sport = ?",
                (sport,),
            ).fetchall()
            return [
                Event(
                    id=row[0],
                    sport=row[1],
                    league=row[2],
                    start_time=datetime.fromisoformat(row[3]),
                    home=row[4],
                    away=row[5],
                    status=row[6],
                    match_url=row[7],
                )
                for row in rows
            ]
        finally:
            conn.close()
