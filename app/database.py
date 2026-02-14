from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from app.models import Signal, SnapshotRow


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        conn = self._conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    sport TEXT,
                    market TEXT,
                    bookmaker TEXT,
                    odds_raw REAL,
                    implied_p REAL,
                    fair_p REAL,
                    timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    market TEXT,
                    signal_type TEXT,
                    odds REAL,
                    fair_probability REAL,
                    ev REAL,
                    timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS clv_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    market TEXT,
                    entry_odds REAL,
                    closing_odds REAL,
                    clv REAL,
                    timestamp TEXT
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def insert_snapshots(self, rows: Iterable[SnapshotRow]) -> None:
        data = [
            (
                row.event_id,
                row.sport,
                row.market,
                row.bookmaker,
                row.odds_raw,
                row.implied_p,
                row.fair_p,
                row.ts.isoformat(),
            )
            for row in rows
        ]
        if not data:
            return
        conn = self._conn()
        try:
            conn.executemany(
                """
                INSERT INTO snapshots (event_id, sport, market, bookmaker, odds_raw, implied_p, fair_p, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                data,
            )
            conn.commit()
        finally:
            conn.close()

    def recent_market_snapshots(self, event_id: str, market: str, minutes: int) -> List[tuple]:
        conn = self._conn()
        try:
            cutoff = datetime.utcnow().timestamp() - minutes * 60
            rows = conn.execute(
                """
                SELECT bookmaker, implied_p, fair_p, odds_raw, timestamp
                FROM snapshots
                WHERE event_id = ? AND market = ?
                """,
                (event_id, market),
            ).fetchall()
            return [r for r in rows if datetime.fromisoformat(r[4]).timestamp() >= cutoff]
        finally:
            conn.close()

    def last_market_odds(self, event_id: str, market: str) -> float | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT odds_raw FROM snapshots
                WHERE event_id = ? AND market = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (event_id, market),
            ).fetchone()
            return float(row[0]) if row else None
        finally:
            conn.close()

    def insert_alert(self, signal: Signal) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO alerts (event_id, market, signal_type, odds, fair_probability, ev, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.event_id,
                    signal.market,
                    signal.signal_type,
                    signal.odds,
                    signal.fair_probability,
                    signal.ev,
                    signal.ts.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def has_recent_alert(self, event_id: str, market: str, cooldown_minutes: int) -> bool:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT timestamp FROM alerts
                WHERE event_id = ? AND market = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (event_id, market),
            ).fetchone()
            if not row:
                return False
            return (datetime.utcnow() - datetime.fromisoformat(row[0])).total_seconds() < cooldown_minutes * 60
        finally:
            conn.close()

    def store_clv(self, event_id: str, market: str, entry_odds: float, closing_odds: float) -> None:
        clv = closing_odds - entry_odds
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO clv_results (event_id, market, entry_odds, closing_odds, clv, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, market, entry_odds, closing_odds, clv, datetime.utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()
