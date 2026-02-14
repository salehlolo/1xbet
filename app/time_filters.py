from __future__ import annotations

from datetime import datetime, timedelta

from app.models import EventModel


def filter_events_by_start(events: list[EventModel], lookahead: int) -> list[EventModel]:
    now = datetime.utcnow()
    max_start = now + timedelta(minutes=lookahead)
    return [e for e in events if e.start_time is None or e.start_time <= max_start]
