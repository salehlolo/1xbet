from __future__ import annotations

import sqlite3
from pathlib import Path


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                sport TEXT,
                league TEXT,
                start_time TEXT,
                home TEXT,
                away TEXT,
                status TEXT,
                match_url TEXT
            );

            CREATE TABLE IF NOT EXISTS odds_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                ts TEXT,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS markets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                group_name TEXT,
                name TEXT,
                line REAL,
                side TEXT,
                FOREIGN KEY(snapshot_id) REFERENCES odds_snapshots(id)
            );

            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id INTEGER,
                outcome_name TEXT,
                price REAL,
                FOREIGN KEY(market_id) REFERENCES markets(id)
            );

            CREATE TABLE IF NOT EXISTS results (
                event_id TEXT PRIMARY KEY,
                home_score INTEGER,
                away_score INTEGER,
                final_total INTEGER,
                winner TEXT
            );
            """
        )
        columns = [row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()]
        if "match_url" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN match_url TEXT")
        conn.commit()
    finally:
        conn.close()
