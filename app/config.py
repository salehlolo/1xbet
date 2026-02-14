from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    bets_api_base_url: str = "https://api.betsapi.com"
    bets_api_key: str = ""

    inplay_endpoint: str = "/v1/1xbet/inplay"
    upcoming_endpoint: str = "/v1/1xbet/upcoming"
    event_endpoint: str = "/v1/1xbet/event"
    result_endpoint: str = "/v1/1xbet/result"

    db_path: str = "data/app.db"
    sports_ids_raw: str = "1,3,2"
    allowed_market_groups_raw: str = "1X2,totals,handicap"

    lookahead_minutes: int = 60
    min_minutes_to_kickoff: int = 5
    max_alerts_per_day: int = 10
    min_score_threshold: float = 0.03
    max_events_per_cycle: int = 200
    max_analyst_evals_per_cycle: int = 30

    inplay_interval_seconds: int = 60
    upcoming_interval_seconds: int = 600
    upcoming_only: bool = True

    steam_window_minutes: int = 10
    steam_prob_delta: float = 0.03
    steam_min_books: int = 2
    outlier_threshold: float = 0.05
    ev_threshold: float = 0.03
    cooldown_minutes: int = 30
    max_overround: float = 1.06

    request_timeout: float = 20.0
    concurrency_limit: int = 5

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_parse_mode: str = "Markdown"

    # legacy compatibility for existing CLI modules
    api_base_url: str = "https://api.betsapi.com"
    api_key: str = ""
    api_events_endpoint: str = "/events"
    api_odds_endpoint: str = "/odds"
    api_results_endpoint: str = "/results"
    mock_mode: bool = False
    rate_limit_per_day: int = 1800
    overround_max: float = 0.08
    edge_threshold: float = 0.02
    common_total_lines: tuple[float, ...] = (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
    common_asian_lines: tuple[float, ...] = (0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75)
    alerts_path: str = "output/alerts.log"
    telegram_webhook: str | None = None
    telegram_disable_web_preview: bool = True
    telegram_rate_limit_seconds: float = 1.0
    telegram_max_message_len: int = 3800
    match_url_template: str = ""
    telegram_include_event_id: bool = True

    @property
    def sports_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.sports_ids_raw.split(",") if x.strip()]

    @property
    def allowed_market_groups(self) -> list[str]:
        return [x.strip().lower() for x in self.allowed_market_groups_raw.split(",") if x.strip()]

    def api_mapping(self) -> dict:
        return {
            "events": {"items_key": "events"},
            "odds": {"markets_key": "markets"},
            "results": {"items_key": "results"},
        }


def _env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default) == "1"


def get_settings() -> Settings:
    return Settings(
        bets_api_base_url=os.getenv("BETS_API_BASE_URL", "https://api.betsapi.com"),
        bets_api_key=os.getenv("BETS_API_KEY", ""),
        inplay_endpoint=os.getenv("BETS_INPLAY_ENDPOINT", "/v1/1xbet/inplay"),
        upcoming_endpoint=os.getenv("BETS_UPCOMING_ENDPOINT", "/v1/1xbet/upcoming"),
        event_endpoint=os.getenv("BETS_EVENT_ENDPOINT", "/v1/1xbet/event"),
        result_endpoint=os.getenv("BETS_RESULT_ENDPOINT", "/v1/1xbet/result"),
        db_path=os.getenv("DB_PATH", "data/app.db"),
        sports_ids_raw=os.getenv("SPORTS_IDS", "1,3,2"),
        allowed_market_groups_raw=os.getenv("ALLOWED_MARKET_GROUPS", "1X2,totals,handicap"),
        lookahead_minutes=int(os.getenv("LOOKAHEAD_MINUTES", "60")),
        min_minutes_to_kickoff=int(os.getenv("MIN_MINUTES_TO_KICKOFF", "5")),
        max_alerts_per_day=int(os.getenv("MAX_ALERTS_PER_DAY", "10")),
        min_score_threshold=float(os.getenv("MIN_SCORE_THRESHOLD", "0.03")),
        max_events_per_cycle=int(os.getenv("MAX_EVENTS_PER_CYCLE", "200")),
        max_analyst_evals_per_cycle=int(os.getenv("MAX_ANALYST_EVALS_PER_CYCLE", "30")),
        inplay_interval_seconds=int(os.getenv("INPLAY_INTERVAL_SECONDS", "60")),
        upcoming_interval_seconds=int(os.getenv("UPCOMING_INTERVAL_SECONDS", "600")),
        upcoming_only=_env_bool("UPCOMING_ONLY", "1"),
        steam_window_minutes=int(os.getenv("STEAM_WINDOW_MINUTES", "10")),
        steam_prob_delta=float(os.getenv("STEAM_PROB_DELTA", "0.03")),
        steam_min_books=int(os.getenv("STEAM_MIN_BOOKS", "2")),
        outlier_threshold=float(os.getenv("OUTLIER_THRESHOLD", "0.05")),
        ev_threshold=float(os.getenv("EV_THRESHOLD", "0.03")),
        cooldown_minutes=int(os.getenv("COOLDOWN_MINUTES", "30")),
        max_overround=float(os.getenv("MAX_OVERROUND", "1.06")),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
        concurrency_limit=int(os.getenv("CONCURRENCY_LIMIT", "5")),
        telegram_enabled=_env_bool("TELEGRAM_ENABLED", "0"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        telegram_parse_mode=os.getenv("TELEGRAM_PARSE_MODE", "Markdown"),
        api_base_url=os.getenv("API_BASE_URL", os.getenv("BETS_API_BASE_URL", "https://api.betsapi.com")),
        api_key=os.getenv("API_KEY", os.getenv("BETS_API_KEY", "")),
        api_events_endpoint=os.getenv("API_EVENTS_ENDPOINT", "/events"),
        api_odds_endpoint=os.getenv("API_ODDS_ENDPOINT", "/odds"),
        api_results_endpoint=os.getenv("API_RESULTS_ENDPOINT", "/results"),
        mock_mode=_env_bool("MOCK_MODE", "0"),
        rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "1800")),
        overround_max=float(os.getenv("OVERROUND_MAX", "0.08")),
        edge_threshold=float(os.getenv("EDGE_THRESHOLD", "0.02")),
        alerts_path=os.getenv("ALERTS_PATH", "output/alerts.log"),
        telegram_webhook=os.getenv("TELEGRAM_WEBHOOK"),
        telegram_disable_web_preview=_env_bool("TELEGRAM_DISABLE_WEB_PREVIEW", "1"),
        telegram_rate_limit_seconds=float(os.getenv("TELEGRAM_RATE_LIMIT_SECONDS", "1.0")),
        telegram_max_message_len=int(os.getenv("TELEGRAM_MAX_MESSAGE_LEN", "3800")),
        match_url_template=os.getenv("MATCH_URL_TEMPLATE", ""),
        telegram_include_event_id=_env_bool("TELEGRAM_INCLUDE_EVENT_ID", "1"),
    )


def missing_required_settings(settings: Settings) -> list[str]:
    missing: list[str] = []
    if not settings.bets_api_key:
        missing.append("BETS_API_KEY")
    if settings.telegram_enabled:
        if not settings.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not settings.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
    return missing


def validate_settings(settings: Settings) -> Settings:
    missing = missing_required_settings(settings)

    hard_missing = [item for item in missing if item == "BETS_API_KEY"]
    if hard_missing:
        logger.error("Missing required settings: %s", ", ".join(hard_missing))
        raise SystemExit(1)

    tg_missing = [item for item in missing if item.startswith("TELEGRAM_")]
    if tg_missing:
        logger.warning("Missing Telegram settings: %s. Disabling Telegram.", ", ".join(tg_missing))
        settings.telegram_enabled = False

    if settings.min_minutes_to_kickoff < 0:
        logger.warning("MIN_MINUTES_TO_KICKOFF < 0; forcing to 0")
        settings.min_minutes_to_kickoff = 0
    if settings.lookahead_minutes <= settings.min_minutes_to_kickoff:
        logger.warning(
            "LOOKAHEAD_MINUTES (%s) <= MIN_MINUTES_TO_KICKOFF (%s); increasing lookahead by +10 minutes.",
            settings.lookahead_minutes,
            settings.min_minutes_to_kickoff,
        )
        settings.lookahead_minutes = settings.min_minutes_to_kickoff + 10
    return settings
