from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from dotenv import load_dotenv

from app.config import get_settings, validate_settings
from app.database import Database
from app.fetcher import BetsAPIFetcher
from app.models import EventModel
from app.normalizer import normalize_odds
from app.signals import detect_outlier, detect_positive_ev, detect_steam
from app.telegram import TelegramClient

logger = logging.getLogger(__name__)


async def process_mode(mode: str, fetcher: BetsAPIFetcher, db: Database, tg: TelegramClient, settings) -> None:
    sport_ids = [int(x.strip()) for x in settings.sports_ids.split(",") if x.strip()]
    for sport_id in sport_ids:
        try:
            event_ids = await fetcher.fetch_events(mode=mode, sport_id=sport_id)
            events = await fetcher.fetch_event_details(event_ids)
            for event in events:
                await process_event(event, db, tg, settings)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed processing mode=%s sport=%s: %s", mode, sport_id, exc)


async def process_event(event: EventModel, db: Database, tg: TelegramClient, settings) -> None:
    rows = normalize_odds(event)
    db.insert_snapshots(rows)

    by_market = defaultdict(list)
    for row in rows:
        by_market[row.market].append(row)

    signals = []
    signals.extend(detect_positive_ev(event, rows, settings))
    signals.extend(detect_outlier(event, rows, settings))

    for market, market_rows in by_market.items():
        history = db.recent_market_snapshots(event.event_id, market, settings.steam_window_minutes)
        signals.extend(detect_steam(event, market_rows, history, settings))

    for signal in signals:
        if db.has_recent_alert(signal.event_id, signal.market, settings.cooldown_minutes):
            continue
        db.insert_alert(signal)
        await tg.send_telegram_alert(signal)


async def poll_loop() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    settings = validate_settings(get_settings())
    db = Database(settings.db_path)
    fetcher = BetsAPIFetcher(settings)
    tg = TelegramClient(settings)

    try:
        while True:
            await process_mode("inplay", fetcher, db, tg, settings)
            await asyncio.sleep(settings.inplay_interval_seconds)
            await process_mode("upcoming", fetcher, db, tg, settings)
            await asyncio.sleep(max(1, settings.upcoming_interval_seconds - settings.inplay_interval_seconds))
    finally:
        await fetcher.close()


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()
