import asyncio
from datetime import datetime

from app.brain.analyst import Analyst
from app.database import Database
from app.models import SnapshotRow


def test_analyst_evaluate_snapshot(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    row = SnapshotRow(
        event_id="e1",
        sport="soccer",
        market="totals",
        outcome="over",
        bookmaker="b1",
        odds_raw=2.1,
        implied_p=0.48,
        fair_p=0.52,
        timestamp=datetime.utcnow(),
    )
    db.insert_snapshots([row])
    analyst = Analyst(db)
    opp = asyncio.run(analyst.evaluate_snapshot(row))
    assert opp.overall_score != 0
    assert 0 <= opp.confidence <= 1
