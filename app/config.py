from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    api_base_url: str = os.getenv("API_BASE_URL", "https://example.com")
    api_key: str = os.getenv("API_KEY", "")
    api_events_endpoint: str = os.getenv("API_EVENTS_ENDPOINT", "/events")
    api_odds_endpoint: str = os.getenv("API_ODDS_ENDPOINT", "/odds")
    api_results_endpoint: str = os.getenv("API_RESULTS_ENDPOINT", "/results")
    api_mapping_path: str | None = os.getenv("API_MAPPING_PATH")

    db_path: str = os.getenv("DB_PATH", "data/app.db")
    mock_mode: bool = os.getenv("MOCK_MODE", "0") == "1"

    cache_ttl_events: int = int(os.getenv("CACHE_TTL_EVENTS", "120"))
    cache_ttl_odds: int = int(os.getenv("CACHE_TTL_ODDS", "45"))

    rate_limit_per_day: int = int(os.getenv("RATE_LIMIT_PER_DAY", "1800"))

    overround_max: float = float(os.getenv("OVERROUND_MAX", "0.08"))
    edge_threshold: float = float(os.getenv("EDGE_THRESHOLD", "0.02"))

    common_total_lines: tuple[float, ...] = (
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5,
    )
    common_asian_lines: tuple[float, ...] = (
        0.25,
        0.75,
        1.25,
        1.75,
        2.25,
        2.75,
        3.25,
        3.75,
    )

    alerts_path: str = os.getenv("ALERTS_PATH", "output/alerts.log")
    telegram_webhook: str | None = os.getenv("TELEGRAM_WEBHOOK")
    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "0") == "1"
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_parse_mode: str = os.getenv("TELEGRAM_PARSE_MODE", "Markdown")
    telegram_disable_web_preview: bool = os.getenv("TELEGRAM_DISABLE_WEB_PREVIEW", "1") == "1"
    telegram_rate_limit_seconds: float = float(os.getenv("TELEGRAM_RATE_LIMIT_SECONDS", "1.0"))
    telegram_max_message_len: int = int(os.getenv("TELEGRAM_MAX_MESSAGE_LEN", "3800"))
    telegram_lang: str = os.getenv("TELEGRAM_LANG", "ar")
    match_url_template: str = os.getenv("MATCH_URL_TEMPLATE", "")
    telegram_include_link: bool = os.getenv("TELEGRAM_INCLUDE_LINK", "1") == "1"
    telegram_include_league: bool = os.getenv("TELEGRAM_INCLUDE_LEAGUE", "1") == "1"
    telegram_include_event_id: bool = os.getenv("TELEGRAM_INCLUDE_EVENT_ID", "1") == "1"

    def api_mapping(self) -> Dict[str, Any]:
        if not self.api_mapping_path:
            return {
                "events": {
                    "items_key": "events",
                },
                "odds": {
                    "markets_key": "markets",
                },
                "results": {
                    "items_key": "results",
                },
            }
        path = Path(self.api_mapping_path)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}


def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> Settings:
    if not settings.mock_mode:
        missing = []
        if not settings.api_base_url:
            missing.append("API_BASE_URL")
        if not settings.api_key:
            missing.append("API_KEY")
        if not settings.api_odds_endpoint:
            missing.append("API_ODDS_ENDPOINT")
        if missing:
            logger.error("Missing required settings for live mode: %s", ", ".join(missing))
            raise SystemExit(1)
    if settings.telegram_enabled:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.warning("Telegram enabled but missing bot token or chat id. Disabling Telegram.")
            settings.telegram_enabled = False
    return settings
