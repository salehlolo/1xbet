from __future__ import annotations

from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.models import Signal


class TelegramClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(4), reraise=True)
    async def send_telegram_alert(self, signal: Signal) -> None:
        if not self.settings.telegram_enabled:
            return
        text = self._format_message(signal)
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_chat_id,
            "text": text,
            "parse_mode": self.settings.telegram_parse_mode,
            "disable_web_page_preview": True,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

    def _format_message(self, signal: Signal) -> str:
        return (
            f"*Signal Alert*\n"
            f"Type: `{signal.signal_type}`\n"
            f"Sport: *{signal.sport}*\n"
            f"League: {signal.league}\n"
            f"Match: {signal.teams}\n"
            f"Market: `{signal.market}`\n"
            f"Outcome: `{signal.outcome}`\n"
            f"Book: {signal.bookmaker}\n"
            f"Odds: {signal.odds:.3f}\n"
            f"Fair p: {signal.fair_probability:.3f}\n"
            f"EV: {signal.ev:.3f}\n"
            f"Time: {signal.timestamp.isoformat()}\n"
            f"Note: {signal.note}"
        )
