from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    bets_api_base_url: str = os.getenv("BETS_API_BASE_URL", "https://api.betsapi.com")
    bets_api_key: str = os.getenv("BETS_API_KEY", "")

    inplay_endpoint: str = os.getenv("BETS_INPLAY_ENDPOINT", "/v1/1xbet/inplay")
    upcoming_endpoint: str = os.getenv("BETS_UPCOMING_ENDPOINT", "/v1/1xbet/upcoming")
    event_endpoint: str = os.getenv("BETS_EVENT_ENDPOINT", "/v1/1xbet/event")
    result_endpoint: str = os.getenv("BETS_RESULT_ENDPOINT", "/v1/1xbet/result")

    db_path: str = os.getenv("DB_PATH", "data/app.db")
    sports_ids_raw: str = os.getenv("SPORTS_IDS", "1,3,2")
    allowed_market_groups_raw: str = os.getenv("ALLOWED_MARKET_GROUPS", "1X2,totals,handicap")

    lookahead_minutes: int = int(os.getenv("LOOKAHEAD_MINUTES", "60"))
    max_alerts_per_day: int = int(os.getenv("MAX_ALERTS_PER_DAY", "10"))
    min_score_threshold: float = float(os.getenv("MIN_SCORE_THRESHOLD", "0.03"))
    max_events_per_cycle: int = int(os.getenv("MAX_EVENTS_PER_CYCLE", "200"))

    inplay_interval_seconds: int = int(os.getenv("INPLAY_INTERVAL_SECONDS", "60"))
    upcoming_interval_seconds: int = int(os.getenv("UPCOMING_INTERVAL_SECONDS", "600"))

    steam_window_minutes: int = int(os.getenv("STEAM_WINDOW_MINUTES", "10"))
    steam_prob_delta: float = float(os.getenv("STEAM_PROB_DELTA", "0.03"))
    steam_min_books: int = int(os.getenv("STEAM_MIN_BOOKS", "2"))
    outlier_threshold: float = float(os.getenv("OUTLIER_THRESHOLD", "0.05"))
    ev_threshold: float = float(os.getenv("EV_THRESHOLD", "0.03"))
    cooldown_minutes: int = int(os.getenv("COOLDOWN_MINUTES", "30"))
    max_overround: float = float(os.getenv("MAX_OVERROUND", "1.06"))

    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    concurrency_limit: int = int(os.getenv("CONCURRENCY_LIMIT", "5"))

    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "0") == "1"
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_parse_mode: str = os.getenv("TELEGRAM_PARSE_MODE", "Markdown")

    # legacy compatibility for existing CLI modules
    api_base_url: str = os.getenv("API_BASE_URL", os.getenv("BETS_API_BASE_URL", "https://api.betsapi.com"))
    api_key: str = os.getenv("API_KEY", os.getenv("BETS_API_KEY", ""))
    api_events_endpoint: str = os.getenv("API_EVENTS_ENDPOINT", "/events")
    api_odds_endpoint: str = os.getenv("API_ODDS_ENDPOINT", "/odds")
    api_results_endpoint: str = os.getenv("API_RESULTS_ENDPOINT", "/results")
    mock_mode: bool = os.getenv("MOCK_MODE", "0") == "1"
    rate_limit_per_day: int = int(os.getenv("RATE_LIMIT_PER_DAY", "1800"))
    overround_max: float = float(os.getenv("OVERROUND_MAX", "0.08"))
    edge_threshold: float = float(os.getenv("EDGE_THRESHOLD", "0.02"))
    common_total_lines: tuple[float, ...] = (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
    common_asian_lines: tuple[float, ...] = (0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75)
    alerts_path: str = os.getenv("ALERTS_PATH", "output/alerts.log")
    telegram_webhook: str | None = os.getenv("TELEGRAM_WEBHOOK")
    telegram_disable_web_preview: bool = os.getenv("TELEGRAM_DISABLE_WEB_PREVIEW", "1") == "1"
    telegram_rate_limit_seconds: float = float(os.getenv("TELEGRAM_RATE_LIMIT_SECONDS", "1.0"))
    telegram_max_message_len: int = int(os.getenv("TELEGRAM_MAX_MESSAGE_LEN", "3800"))
    match_url_template: str = os.getenv("MATCH_URL_TEMPLATE", "")
    telegram_include_event_id: bool = os.getenv("TELEGRAM_INCLUDE_EVENT_ID", "1") == "1"

    @property
    def sports_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.sports_ids_raw.split(",") if x.strip()]

    @property
    def allowed_market_groups(self) -> list[str]:
        return [x.strip().lower() for x in self.allowed_market_groups_raw.split(",") if x.strip()]


    def api_mapping(self) -> dict:
        return {"events": {"items_key": "events"}, "odds": {"markets_key": "markets"}, "results": {"items_key": "results"}}


def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> Settings:
    if not settings.bets_api_key:
        logger.error("Missing required settings: BETS_API_KEY")
        raise SystemExit(1)

    if settings.telegram_enabled and (not settings.telegram_bot_token or not settings.telegram_chat_id):
        logger.warning("Telegram enabled but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing. Disabling Telegram.")
        settings.telegram_enabled = False
    return settings
