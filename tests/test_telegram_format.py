from datetime import datetime

from app.alerts.notifier import chunk_text, format_matches_ar
from app.api.base import Event


def test_format_matches_non_empty():
    event = Event(
        id="evt1",
        sport="soccer",
        league="League A",
        start_time=datetime(2025, 1, 1, 12, 0),
        home="Team A",
        away="Team B",
        status="scheduled",
    )
    message = format_matches_ar([event], sport_name_ar="كرة القدم")
    assert message


def test_chunking_respects_limit():
    text = "\n\n".join(["x" * 50 for _ in range(10)])
    chunks = chunk_text(text, max_len=120)
    assert all(len(chunk) <= 120 for chunk in chunks)
