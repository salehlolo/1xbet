from datetime import datetime

from app.alerts.notifier import chunk_text, format_matches_ar
from app.api.base import Event


def test_format_matches_ar_contains_title_and_teams():
    event = Event(
        id="evt_ar",
        sport="soccer",
        league="Mock League",
        start_time=datetime(2025, 1, 1, 18, 30),
        home="الأهلي",
        away="الهلال",
        status="scheduled",
        match_url="https://example.com/match/evt_ar",
    )
    message = format_matches_ar(
        [event],
        sport_name_ar="كرة القدم",
        include_link=True,
        include_event_id=True,
        include_league=True,
    )
    assert "مباريات قادمة" in message
    assert "الأهلي" in message
    assert "الهلال" in message
    assert "[افتح المباراة]" in message


def test_chunking_does_not_exceed_limit():
    text = "\n\n".join(["⚽ فريق أ ضد فريق ب" for _ in range(200)])
    chunks = chunk_text(text, max_len=200)
    assert all(len(chunk) <= 200 for chunk in chunks)
