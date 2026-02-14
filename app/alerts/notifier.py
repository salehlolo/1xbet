from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.api.base import Event
    from app.strategies.base import Signal


@dataclass
class Alert:
    message: str
    created_at: datetime
    level: str = "info"


class Notifier:
    def __init__(self, log_path: str, telegram_webhook: str | None = None) -> None:
        self.log_path = Path(log_path)
        self.telegram_webhook = telegram_webhook
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alert: Alert) -> None:
        line = f"{alert.created_at.isoformat()} [{alert.level}] {alert.message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        logger.info(line)
        if self.telegram_webhook:
            self._send_telegram(alert.message)

    def _send_telegram(self, message: str) -> None:
        data = json.dumps({"text": message}).encode("utf-8")
        request = Request(self.telegram_webhook, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10):
                return
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to send telegram alert: %s", exc)


AR_SPORT_NAMES = {
    "soccer": "كرة القدم",
    "basketball": "كرة السلة",
    "tennis": "التنس",
    "hockey": "الهوكي",
    "baseball": "البيسبول",
}


def escape_markdown(text: str) -> str:
    for char in ("*", "_", "`", "[", "]"):
        text = text.replace(char, f"\\{char}")
    return text


def format_one_match_ar(
    event: "Event",
    include_league: bool,
    include_link: bool,
    include_event_id: bool,
    match_url_template: str = "",
) -> str:
    date_str = event.start_time.strftime("%Y-%m-%d")
    time_str = event.start_time.strftime("%H:%M")
    lines = [
        f"🕒 {date_str} {time_str}",
        f"⚽ {escape_markdown(event.home)} × {escape_markdown(event.away)}",
    ]
    if include_league:
        lines.append(f"🏆 {escape_markdown(event.league)}")

    link = event.match_url or (match_url_template.format(event_id=event.id) if match_url_template else "")
    if include_link and link:
        lines.append(f"🔗 رابط المباراة: [افتح المباراة]({link})")
    if include_event_id:
        lines.append(f"🆔 رقم المباراة: {escape_markdown(event.id)}")
    return "\n".join(lines)


def format_matches_ar(
    matches: Iterable["Event"],
    sport_name_ar: str,
    title: str | None = None,
    include_league: bool = True,
    include_link: bool = True,
    include_event_id: bool = True,
    match_url_template: str = "",
) -> str:
    header = title or f"*📅 مباريات قادمة — {sport_name_ar}*"
    blocks = [header]
    for event in matches:
        blocks.append(
            format_one_match_ar(
                event,
                include_league=include_league,
                include_link=include_link,
                include_event_id=include_event_id,
                match_url_template=match_url_template,
            )
        )
    return "\n\n".join(blocks)


def chunk_text(text: str, max_len: int) -> List[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunk = remaining[:split_at].rstrip()
        chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()
    return [chunk for chunk in chunks if chunk]


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        parse_mode: str = "Markdown",
        disable_web_preview: bool = True,
        rate_limit_seconds: float = 1.0,
        max_message_len: int = 3800,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.disable_web_preview = disable_web_preview
        self.rate_limit_seconds = rate_limit_seconds
        self.max_message_len = max_message_len

    def send_message(self, text: str) -> None:
        for chunk in chunk_text(text, self.max_message_len):
            self._send_with_retry(chunk)
            time.sleep(self.rate_limit_seconds)

    def send_matches(
        self,
        matches: Iterable["Event"],
        sport: str,
        title: str | None = None,
        include_league: bool = True,
        include_link: bool = True,
        include_event_id: bool = True,
        match_url_template: str = "",
    ) -> None:
        sport_name = AR_SPORT_NAMES.get(sport, sport)
        message = format_matches_ar(
            matches,
            sport_name_ar=sport_name,
            title=title,
            include_league=include_league,
            include_link=include_link,
            include_event_id=include_event_id,
            match_url_template=match_url_template,
        )
        self.send_message(message)

    def send_signals(self, signals: Iterable["Signal"], title: str = "Signals") -> None:
        blocks = [f"*{escape_markdown(title)}*"]
        for signal in signals:
            group = signal.market_group or signal.market_name
            line = f"{signal.line:.2f}" if signal.line is not None else "-"
            side = signal.side or signal.selection
            overround = (
                f"{signal.market_overround:.3f}" if signal.market_overround is not None else "-"
            )
            blocks.append(
                f"*إشارة*: {escape_markdown(str(group))} | خط {line} | جهة {escape_markdown(str(side))} "
                f"| سعر {signal.price:.2f} | هامش {overround} | أفضلية {signal.edge:.3f}"
            )
        self.send_message("\n".join(blocks))

    def _send_with_retry(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": self.parse_mode,
                "disable_web_page_preview": self.disable_web_preview,
            }
        ).encode("utf-8")
        request = Request(url, data=payload, headers={"Content-Type": "application/json"})
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                with urlopen(request, timeout=15):
                    return
            except HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504):
                    wait = 1.5**attempt
                    logger.warning("Telegram HTTP %s on attempt %s. Retrying in %.2fs", exc.code, attempt, wait)
                    time.sleep(wait)
                    continue
                logger.error("Telegram error %s: %s", exc.code, exc.read())
                return
            except URLError as exc:
                wait = 1.5**attempt
                logger.warning("Telegram network error on attempt %s: %s", attempt, exc)
                time.sleep(wait)
        logger.error("Telegram message failed after retries")
