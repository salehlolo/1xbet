from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

from app.models import Signal, SnapshotRow
from app.signals import calculate_clv


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
                    outcome TEXT,
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
                    outcome TEXT,
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
                    outcome TEXT,
                    entry_odds REAL,
                    closing_odds REAL,
                    clv REAL,
                    timestamp TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_snapshots_event_market_time
                    ON snapshots(event_id, market, timestamp);
                CREATE INDEX IF NOT EXISTS idx_snapshots_event_market_outcome_time
                    ON snapshots(event_id, market, outcome, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_event_market_outcome_time
                    ON alerts(event_id, market, outcome, timestamp);
                """
            )
            cols = [row[1] for row in conn.execute("PRAGMA table_info(snapshots)")]
            if "outcome" not in cols:
                conn.execute("ALTER TABLE snapshots ADD COLUMN outcome TEXT DEFAULT ''")
            alert_cols = [row[1] for row in conn.execute("PRAGMA table_info(alerts)")]
            if "outcome" not in alert_cols:
                conn.execute("ALTER TABLE alerts ADD COLUMN outcome TEXT DEFAULT ''")
            clv_cols = [row[1] for row in conn.execute("PRAGMA table_info(clv_results)")]
            if "outcome" not in clv_cols:
                conn.execute("ALTER TABLE clv_results ADD COLUMN outcome TEXT DEFAULT ''")
            conn.commit()
        finally:
            conn.close()

    def insert_snapshots(self, rows: Iterable[SnapshotRow]) -> None:
        data = [
            (
                row.event_id,
                row.sport,
                row.market,
                row.outcome,
                row.bookmaker,
                row.odds_raw,
                row.implied_p,
                row.fair_p,
                row.timestamp.isoformat(),
            )
            for row in rows
        ]
        if not data:
            return
        conn = self._conn()
        try:
            conn.executemany(
                """
                INSERT INTO snapshots (event_id, sport, market, outcome, bookmaker, odds_raw, implied_p, fair_p, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                data,
            )
            conn.commit()
        finally:
            conn.close()

    def recent_market_snapshots(self, event_id: str, market: str, minutes: int) -> List[tuple]:
        conn = self._conn()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            return conn.execute(
                """
                SELECT bookmaker, outcome, implied_p, fair_p, odds_raw, timestamp
                FROM snapshots
                WHERE event_id = ? AND market = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (event_id, market, cutoff.isoformat()),
            ).fetchall()
        finally:
            conn.close()

    def last_market_odds(self, event_id: str, market: str, outcome: str) -> float | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT odds_raw FROM snapshots
                WHERE event_id = ? AND market = ? AND outcome = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (event_id, market, outcome),
            ).fetchone()
            return float(row[0]) if row else None
        finally:
            conn.close()

    def insert_alert(self, signal: Signal) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO alerts (event_id, market, outcome, signal_type, odds, fair_probability, ev, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.event_id,
                    signal.market,
                    signal.outcome,
                    signal.signal_type,
                    signal.odds,
                    signal.fair_probability,
                    signal.ev,
                    signal.timestamp.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def has_recent_alert(self, event_id: str, market: str, outcome: str, cooldown_minutes: int) -> bool:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT timestamp FROM alerts
                WHERE event_id = ? AND market = ? AND outcome = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (event_id, market, outcome),
            ).fetchone()
            if not row:
                return False
            return (datetime.utcnow() - datetime.fromisoformat(row[0])).total_seconds() < cooldown_minutes * 60
        finally:
            conn.close()

    def alerts_sent_today(self) -> int:
        conn = self._conn()
        try:
            today = datetime.utcnow().date().isoformat()
            row = conn.execute(
                "SELECT COUNT(1) FROM alerts WHERE substr(timestamp,1,10)=?",
                (today,),
            ).fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()

    def store_clv(self, event_id: str, market: str, outcome: str, entry_odds: float, closing_odds: float) -> None:
        clv = calculate_clv(entry_odds, closing_odds)
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO clv_results (event_id, market, outcome, entry_odds, closing_odds, clv, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, market, outcome, entry_odds, closing_odds, clv, datetime.utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def report_performance(self, days: int = 7) -> list[tuple]:
        conn = self._conn()
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            return conn.execute(
                """
                SELECT market, COUNT(1) AS n, AVG(clv) AS avg_clv
                FROM clv_results
                WHERE timestamp >= ?
                GROUP BY market
                ORDER BY n DESC
                """,
                (cutoff,),
            ).fetchall()
        finally:
            conn.close()
