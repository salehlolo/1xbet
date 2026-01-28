from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta

from app.api.generic_adapter import GenericJSONAdapter
from app.api.http_client import HttpClient
from app.config import get_settings
from app.db.repo import Repository
from app.db.schema import init_db
from app.logging import setup_logging
from app.markets.filters import QualityConfig, filter_quality
from app.markets.mapper import map_markets
from app.markets.overround import overround
from app.strategies.totals_baseline import TotalsBaselineConfig, TotalsBaselineStrategy
from app.backtest.engine import BacktestConfig, BacktestEngine
from app.alerts.notifier import Alert, Notifier, TelegramNotifier

SPORTS = ["soccer", "basketball", "tennis", "hockey", "baseball"]


def _date_range(days: int) -> list[str]:
    today = datetime.utcnow().date()
    return [(today + timedelta(days=offset)).isoformat() for offset in range(days)]


def _apply_match_url_template(events, template: str) -> None:
    if not template:
        return
    for event in events:
        if not event.match_url:
            event.match_url = template.format(event_id=event.id)


def command_fetch(args: argparse.Namespace) -> None:
    settings = get_settings()
    init_db(settings.db_path)
    repo = Repository(settings.db_path)
    client = HttpClient(
        settings.api_base_url,
        settings.api_key,
        settings.rate_limit_per_day,
    )
    adapter = GenericJSONAdapter(client, settings.api_mapping(), mock_mode=settings.mock_mode)

    events = adapter.list_events(args.sport, _date_range(args.days))
    _apply_match_url_template(events, settings.match_url_template)
    repo.upsert_events(events)
    for event in events:
        snapshot = adapter.get_event_odds(event.id)
        repo.insert_snapshot(snapshot)
    print(f"Fetched {len(events)} events for {args.sport}.")


def command_map_markets(args: argparse.Namespace) -> None:
    settings = get_settings()
    init_db(settings.db_path)
    repo = Repository(settings.db_path)
    events = repo.load_events(args.sport)
    if not events:
        print("No events available. Run fetch first.")
        return

    client = HttpClient(
        settings.api_base_url,
        settings.api_key,
        settings.rate_limit_per_day,
    )
    adapter = GenericJSONAdapter(client, settings.api_mapping(), mock_mode=settings.mock_mode)
    snapshot = adapter.get_event_odds(events[0].id)
    mapped = map_markets(snapshot.markets)
    quality_config = QualityConfig(
        max_overround=settings.overround_max,
        common_lines=settings.common_total_lines + settings.common_asian_lines,
        include_groups=("total", "asian_total", "asian_handicap", "btts", "team_total"),
    )
    filtered = filter_quality(mapped, quality_config)
    for market in filtered:
        print(f"{market.name} -> group={market.group} line={market.line} overround={overround(market):.3f}")


def command_backtest(args: argparse.Namespace) -> None:
    settings = get_settings()
    init_db(settings.db_path)
    repo = Repository(settings.db_path)
    client = HttpClient(
        settings.api_base_url,
        settings.api_key,
        settings.rate_limit_per_day,
    )
    adapter = GenericJSONAdapter(client, settings.api_mapping(), mock_mode=settings.mock_mode)
    events = adapter.list_events(args.sport, [args.from_date, args.to_date])
    _apply_match_url_template(events, settings.match_url_template)
    markets_by_event = {}
    for event in events:
        snapshot = adapter.get_event_odds(event.id)
        markets_by_event[event.id] = map_markets(snapshot.markets)
    results = {result.event_id: result for result in adapter.get_results([args.from_date, args.to_date])}

    strategy = TotalsBaselineStrategy(TotalsBaselineConfig(edge_threshold=settings.edge_threshold))
    engine = BacktestEngine(strategy, BacktestConfig())
    metrics = engine.run(events, markets_by_event, results)
    print("Backtest metrics:")
    print(metrics)


def command_alerts(args: argparse.Namespace) -> None:
    settings = get_settings()
    notifier = Notifier(settings.alerts_path, settings.telegram_webhook)
    message = f"Alert check for {args.sport} at {datetime.utcnow().isoformat()}"
    notifier.send(Alert(message=message, created_at=datetime.utcnow()))
    if settings.telegram_enabled:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logging.warning("Telegram enabled but missing bot token or chat id.")
        else:
            telegram = TelegramNotifier(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                parse_mode=settings.telegram_parse_mode,
                disable_web_preview=settings.telegram_disable_web_preview,
                rate_limit_seconds=settings.telegram_rate_limit_seconds,
                max_message_len=settings.telegram_max_message_len,
            )
            telegram.send_message(f"🔔 تنبيه: {message}")
    else:
        logging.warning("Telegram is disabled. Set TELEGRAM_ENABLED=1 to enable.")
    print("Alert sent")


def command_telegram_test(args: argparse.Namespace) -> None:
    settings = get_settings()
    if not settings.telegram_enabled:
        logging.warning("Telegram is disabled. Set TELEGRAM_ENABLED=1 to enable.")
        return
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logging.warning("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return
    telegram = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        parse_mode=settings.telegram_parse_mode,
        disable_web_preview=settings.telegram_disable_web_preview,
        rate_limit_seconds=settings.telegram_rate_limit_seconds,
        max_message_len=settings.telegram_max_message_len,
    )
    telegram.send_message("✅ Telegram is connected")


def command_send_matches(args: argparse.Namespace) -> None:
    settings = get_settings()
    if not settings.telegram_enabled:
        logging.warning("Telegram is disabled. Set TELEGRAM_ENABLED=1 to enable.")
        return
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logging.warning("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return
    init_db(settings.db_path)
    repo = Repository(settings.db_path)
    events = repo.load_events(args.sport)
    if not events:
        client = HttpClient(
            settings.api_base_url,
            settings.api_key,
            settings.rate_limit_per_day,
        )
        adapter = GenericJSONAdapter(client, settings.api_mapping(), mock_mode=settings.mock_mode)
        events = adapter.list_events(args.sport, _date_range(args.days))
        _apply_match_url_template(events, settings.match_url_template)
        repo.upsert_events(events)

    now = datetime.utcnow()
    future_cutoff = now + timedelta(days=args.days)
    filtered = [event for event in events if now <= event.start_time <= future_cutoff]
    filtered.sort(key=lambda event: event.start_time)
    limited = filtered[: args.limit]

    telegram = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        parse_mode=settings.telegram_parse_mode,
        disable_web_preview=settings.telegram_disable_web_preview,
        rate_limit_seconds=settings.telegram_rate_limit_seconds,
        max_message_len=settings.telegram_max_message_len,
    )
    telegram.send_matches(
        limited,
        sport=args.sport,
        include_league=args.league,
        include_link=args.with_links,
        include_event_id=settings.telegram_include_event_id,
        match_url_template=settings.match_url_template,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bet analysis pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch events and odds")
    fetch_parser.add_argument("--sport", choices=SPORTS, required=True)
    fetch_parser.add_argument("--days", type=int, default=1)
    fetch_parser.set_defaults(func=command_fetch)

    map_parser = subparsers.add_parser("map-markets", help="Map markets for first event")
    map_parser.add_argument("--sport", choices=SPORTS, required=True)
    map_parser.set_defaults(func=command_map_markets)

    backtest_parser = subparsers.add_parser("backtest", help="Run backtest")
    backtest_parser.add_argument("--sport", choices=SPORTS, required=True)
    backtest_parser.add_argument("--from", dest="from_date", required=True)
    backtest_parser.add_argument("--to", dest="to_date", required=True)
    backtest_parser.set_defaults(func=command_backtest)

    alert_parser = subparsers.add_parser("alerts", help="Send alerts")
    alert_parser.add_argument("--sport", choices=SPORTS, required=True)
    alert_parser.set_defaults(func=command_alerts)

    telegram_test_parser = subparsers.add_parser("telegram-test", help="Send a Telegram test message")
    telegram_test_parser.set_defaults(func=command_telegram_test)

    send_matches_parser = subparsers.add_parser("send-matches", help="Send upcoming matches to Telegram")
    send_matches_parser.add_argument("--sport", choices=SPORTS, required=True)
    send_matches_parser.add_argument("--days", type=int, default=1)
    send_matches_parser.add_argument("--limit", type=int, default=20)
    send_matches_parser.add_argument("--with-links", dest="with_links", action="store_true", default=True)
    send_matches_parser.add_argument("--no-links", dest="with_links", action="store_false")
    send_matches_parser.add_argument("--league", dest="league", action="store_true", default=True)
    send_matches_parser.add_argument("--no-league", dest="league", action="store_false")
    send_matches_parser.set_defaults(func=command_send_matches)

    return parser


def main() -> None:
    setup_logging(logging.INFO)
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
