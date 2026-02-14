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
    sports_ids: str = os.getenv("SPORTS_IDS", "1,18,13,4,16")

    inplay_interval_seconds: int = int(os.getenv("INPLAY_INTERVAL_SECONDS", "60"))
    upcoming_interval_seconds: int = int(os.getenv("UPCOMING_INTERVAL_SECONDS", "600"))

    steam_window_minutes: int = int(os.getenv("STEAM_WINDOW_MINUTES", "10"))
    steam_prob_delta: float = float(os.getenv("STEAM_PROB_DELTA", "0.03"))
    steam_min_books: int = int(os.getenv("STEAM_MIN_BOOKS", "2"))
    outlier_threshold: float = float(os.getenv("OUTLIER_THRESHOLD", "0.05"))
    ev_threshold: float = float(os.getenv("EV_THRESHOLD", "0.03"))
    cooldown_minutes: int = int(os.getenv("COOLDOWN_MINUTES", "30"))

    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    concurrency_limit: int = int(os.getenv("CONCURRENCY_LIMIT", "5"))

    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "0") == "1"
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_parse_mode: str = os.getenv("TELEGRAM_PARSE_MODE", "Markdown")



def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> Settings:
    missing = []
    if not settings.bets_api_key:
        missing.append("BETS_API_KEY")
    if missing:
        logger.error("Missing required settings: %s", ", ".join(missing))
        raise SystemExit(1)

    if settings.telegram_enabled and (not settings.telegram_bot_token or not settings.telegram_chat_id):
        logger.warning("Telegram enabled but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing. Disabling Telegram.")
        settings.telegram_enabled = False
    return settings
