from __future__ import annotations

import asyncio
import logging

from dotenv import find_dotenv, load_dotenv

# Load .env before importing app modules that depend on environment variables.
load_dotenv(dotenv_path=find_dotenv(".env", usecwd=True), override=True)

from app.brain.analyst import Analyst
from app.config import Settings, get_settings, missing_required_settings, validate_settings
from app.database import Database
from app.fetcher import BetsAPIFetcher
from app.models import EventModel, Signal
from app.normalizer import normalize_odds
from app.signals import detect_outlier, detect_positive_ev, detect_steam
from app.telegram import TelegramClient
from app.time_filters import filter_events_by_start

logger = logging.getLogger(__name__)

SPORT_NAME_MAP = {
    1: "soccer",
    3: "basketball",
    2: "nfl",
}


def healthcheck_summary(settings: Settings) -> dict[str, object]:
    return {
        "bets_api_key_loaded": bool(settings.bets_api_key),
        "telegram_enabled": bool(settings.telegram_enabled),
        "telegram_enabled_raw_present": settings.telegram_enabled_raw_present,
        "telegram_bot_set": bool(settings.telegram_bot_token),
        "telegram_chat_set": bool(settings.telegram_chat_id),
        "upcoming_only": bool(settings.upcoming_only),
        "lookahead_minutes": settings.lookahead_minutes,
        "min_minutes_to_kickoff": settings.min_minutes_to_kickoff,
    }


def log_startup_healthcheck(settings: Settings) -> None:
    missing = missing_required_settings(settings)
    if missing:
        logger.warning("Missing settings detected: %s", ", ".join(missing))
    summary = healthcheck_summary(settings)
    logger.info(
        "Healthcheck: BETS_API_KEY loaded=%s | TELEGRAM_ENABLED raw present=%s | BOT_SET=%s | CHAT_SET=%s | Telegram enabled=%s | UPCOMING_ONLY=%s | LOOKAHEAD=%s | MIN_KICKOFF=%s",
        summary["bets_api_key_loaded"],
        summary["telegram_enabled_raw_present"],
        summary["telegram_bot_set"],
        summary["telegram_chat_set"],
        summary["telegram_enabled"],
        summary["upcoming_only"],
        summary["lookahead_minutes"],
        summary["min_minutes_to_kickoff"],
    )


async def process_mode(
    mode: str,
    fetcher: BetsAPIFetcher,
    db: Database,
    tg: TelegramClient,
    analyst: Analyst,
    settings: Settings,
) -> None:
    alerts_sent_today = db.alerts_sent_today()
    for sport_id in settings.sports_ids:
        if alerts_sent_today >= settings.max_alerts_per_day:
            logger.info("Daily alert limit reached (%s).", settings.max_alerts_per_day)
            return

        try:
            if mode == "upcoming":
                event_ids = await fetcher.fetch_upcoming_event_ids_window(
                    sport_id=sport_id,
                    lookahead_minutes=settings.lookahead_minutes,
                    min_minutes_to_kickoff=settings.min_minutes_to_kickoff,
                )
            else:
                event_ids = await fetcher.fetch_events(mode=mode, sport_id=sport_id)

            events = await fetcher.fetch_event_details(event_ids[: settings.max_events_per_cycle])
            for event in events:
                if not event.sport or event.sport == "unknown":
                    event.sport = SPORT_NAME_MAP.get(sport_id, str(sport_id))

            if mode == "upcoming":
                events = filter_events_by_start(
                    events,
                    lookahead=settings.lookahead_minutes,
                    min_to_kickoff=settings.min_minutes_to_kickoff,
                )

            for event in events:
                sent_now = await process_event(event, db, tg, analyst, settings)
                alerts_sent_today += sent_now
                if alerts_sent_today >= settings.max_alerts_per_day:
                    return
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed processing mode=%s sport=%s: %s", mode, sport_id, exc)


async def process_event(
    event: EventModel,
    db: Database,
    tg: TelegramClient,
    analyst: Analyst,
    settings: Settings,
) -> int:
    rows = normalize_odds(
        event,
        allowed_groups=settings.allowed_market_groups,
        max_overround=settings.max_overround,
    )
    if not rows:
        return 0

    db.insert_snapshots(rows)

    signals = []
    signals.extend(detect_positive_ev(event, rows, settings))
    signals.extend(detect_outlier(event, rows, settings))

    markets = sorted({row.market for row in rows})
    for market in markets:
        market_rows = [row for row in rows if row.market == market]
        history = db.recent_market_snapshots(event.event_id, market, settings.steam_window_minutes)
        signals.extend(detect_steam(event, market_rows, history, settings))

    sent = 0
    if settings.max_analyst_evals_per_cycle and len(signals) > settings.max_analyst_evals_per_cycle:
        def _pre_score(signal: Signal) -> float:
            return (0.7 * float(signal.fair_probability)) + (0.3 * max(0.0, float(signal.ev)))

        signals = sorted(signals, key=_pre_score, reverse=True)[: settings.max_analyst_evals_per_cycle]

    for signal in signals:
        if db.has_recent_alert(signal.event_id, signal.market, signal.outcome, settings.cooldown_minutes):
            continue

        snapshot = next((row for row in rows if row.market == signal.market and row.outcome == signal.outcome), None)
        if snapshot is None:
            continue

        opportunity = await analyst.evaluate_snapshot(snapshot)
        if opportunity.overall_score < settings.min_score_threshold:
            continue

        db.insert_alert(signal)
        await tg.send_telegram_alert(signal)
        sent += 1
    return sent


async def poll_loop() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = validate_settings(get_settings())
    log_startup_healthcheck(settings)

    db = Database(settings.db_path)
    fetcher = BetsAPIFetcher(settings)
    tg = TelegramClient(settings)
    analyst = Analyst(db=db)

    try:
        while True:
            if settings.upcoming_only:
                await process_mode("upcoming", fetcher, db, tg, analyst, settings)
                await asyncio.sleep(max(1, settings.upcoming_interval_seconds))
            else:
                await process_mode("inplay", fetcher, db, tg, analyst, settings)
                await asyncio.sleep(settings.inplay_interval_seconds)
                await process_mode("upcoming", fetcher, db, tg, analyst, settings)
                await asyncio.sleep(max(1, settings.upcoming_interval_seconds - settings.inplay_interval_seconds))
    finally:
        await fetcher.close()


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()
