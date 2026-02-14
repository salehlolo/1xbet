from __future__ import annotations

from datetime import datetime, timedelta

from app.models import EventModel


def filter_events_by_start(
    events: list[EventModel],
    lookahead: int,
    min_to_kickoff: int = 0,
) -> list[EventModel]:
    now = datetime.utcnow()
    min_start = now + timedelta(minutes=min_to_kickoff)
    max_start = now + timedelta(minutes=lookahead)

    out: list[EventModel] = []
    for event in events:
        if event.start_time is None:
            continue
        if min_start <= event.start_time <= max_start:
            out.append(event)
    return out
