from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.api.base import Adapter, Event, Market, OddsSnapshot, Outcome, Result
from app.api.http_client import HttpClient


class GenericJSONAdapter(Adapter):
    def __init__(
        self,
        http_client: HttpClient,
        mapping: Dict[str, Any],
        mock_mode: bool = False,
    ) -> None:
        self.http_client = http_client
        self.mapping = mapping
        self.mock_mode = mock_mode
        self.mock_dir = Path(__file__).parent / "mock_data"

    def _load_mock(self, name: str) -> Any:
        path = self.mock_dir / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _parse_datetime(self, value: str) -> datetime:
        return datetime.fromisoformat(value)

    def list_events(self, sport: str, date_range: Iterable[str]) -> List[Event]:
        if self.mock_mode:
            payload = self._load_mock("events")
        else:
            payload = self.http_client.get(
                self.mapping["events"].get("endpoint", "/events"),
                {"sport": sport, "dates": ",".join(date_range)},
                ttl=self.mapping["events"].get("ttl", 0),
            )
        items = payload[self.mapping["events"].get("items_key", "events")]
        events = [
            Event(
                id=item["id"],
                sport=item["sport"],
                league=item["league"],
                start_time=self._parse_datetime(item["start_time"]),
                home=item["home"],
                away=item["away"],
                status=item.get("status", "scheduled"),
                match_url=item.get("url") or item.get("link") or item.get("match_url"),
            )
            for item in items
            if item["sport"] == sport
        ]
        return events

    def get_event_odds(self, event_id: str) -> OddsSnapshot:
        if self.mock_mode:
            payload = self._load_mock("odds")
        else:
            payload = self.http_client.get(
                self.mapping["odds"].get("endpoint", "/odds"),
                {"event_id": event_id},
                ttl=self.mapping["odds"].get("ttl", 0),
            )
        data = payload["events"][event_id]
        markets = []
        for market in data["markets"]:
            outcomes = [Outcome(name=o["name"], price=float(o["price"])) for o in market["outcomes"]]
            markets.append(
                Market(
                    name=market["name"],
                    group="raw",
                    line=None,
                    side=None,
                    outcomes=outcomes,
                    raw_name=market["name"],
                )
            )
        return OddsSnapshot(event_id=event_id, ts=self._parse_datetime(data["ts"]), markets=markets)

    def get_results(self, date_range: Iterable[str]) -> List[Result]:
        if self.mock_mode:
            payload = self._load_mock("results")
        else:
            payload = self.http_client.get(
                self.mapping["results"].get("endpoint", "/results"),
                {"dates": ",".join(date_range)},
                ttl=self.mapping["results"].get("ttl", 0),
            )
        items = payload[self.mapping["results"].get("items_key", "results")]
        return [
            Result(
                event_id=item["event_id"],
                home_score=item["home_score"],
                away_score=item["away_score"],
                final_total=item["final_total"],
                winner=item["winner"],
            )
            for item in items
        ]

    def serialize(self) -> Dict[str, Any]:
        return asdict(self)
