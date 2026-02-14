from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Iterable, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.models import BetsAPIResponse, EventModel, MarketModel, OutcomeModel


def _parse_start_time(raw: dict[str, Any]) -> datetime | None:
    value = raw.get("time") or raw.get("start_time") or raw.get("starts_at")
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


class BetsAPIFetcher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._sem = asyncio.Semaphore(settings.concurrency_limit)
        self._client = httpx.AsyncClient(base_url=settings.bets_api_base_url, timeout=settings.request_timeout)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(4), reraise=True)
    async def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        async with self._sem:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()

    async def fetch_events(self, mode: str, sport_id: int, days: int = 1) -> List[str]:
        endpoint = self.settings.inplay_endpoint if mode == "inplay" else self.settings.upcoming_endpoint
        params: dict[str, Any] = {"sport_id": sport_id, "token": self.settings.bets_api_key}
        if mode == "upcoming":
            params["days"] = days
        payload = await self._get(endpoint, params)
        parsed = BetsAPIResponse(**payload)
        results = parsed.results or []
        ids: List[str] = []
        for event in results:
            event_id = event.get("id") or event.get("event_id")
            if event_id:
                ids.append(str(event_id))
        return ids

    async def fetch_event_details(self, event_ids: Iterable[str]) -> List[EventModel]:
        event_ids = list(event_ids)
        if not event_ids:
            return []
        payload = await self._get(
            self.settings.event_endpoint,
            {"event_id": ",".join(event_ids), "token": self.settings.bets_api_key},
        )
        parsed = BetsAPIResponse(**payload)
        results = parsed.results or []
        events: List[EventModel] = []
        for raw in results:
            events.append(self._parse_event(raw))
        return events

    async def fetch_result(self, event_id: str) -> dict[str, Any]:
        return await self._get(self.settings.result_endpoint, {"event_id": event_id, "token": self.settings.bets_api_key})

    def _parse_event(self, raw: dict[str, Any]) -> EventModel:
        markets: List[MarketModel] = []
        raw_markets = raw.get("markets") or raw.get("odds") or []
        for rm in raw_markets:
            outcomes = [
                OutcomeModel(name=str(o.get("name", "outcome")), odds=float(o.get("odds", o.get("price", 0))), bookmaker=str(o.get("bookmaker", "1xbet")))
                for o in rm.get("outcomes", [])
                if float(o.get("odds", o.get("price", 0) or 0)) > 1
            ]
            if outcomes:
                markets.append(MarketModel(market_name=str(rm.get("name", "market")), outcomes=outcomes))

        return EventModel(
            event_id=str(raw.get("id") or raw.get("event_id")),
            sport_id=int(raw.get("sport_id", 0)),
            sport=str(raw.get("sport", "unknown")),
            league=str(raw.get("league", "unknown")),
            home=str(raw.get("home", raw.get("home_name", "Home"))),
            away=str(raw.get("away", raw.get("away_name", "Away"))),
            markets=markets,
            inplay=bool(raw.get("inplay", False)),
            start_time=_parse_start_time(raw),
        )
