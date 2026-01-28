from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    expires_at: float
    value: Any


class SimpleTTLCache:
    def __init__(self) -> None:
        self._store: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = CacheEntry(time.time() + ttl, value)


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate_per_sec
        self.last_check = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_check
        self.last_check = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def wait_for_token(self, amount: float = 1.0) -> None:
        while not self.consume(amount):
            time.sleep(0.5)


class HttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        rate_limit_per_day: int,
        cache: SimpleTTLCache | None = None,
        retries: int = 3,
        backoff: float = 1.5,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.cache = cache or SimpleTTLCache()
        self.retries = retries
        self.backoff = backoff
        refill_rate = rate_limit_per_day / 86400
        self.bucket = TokenBucket(rate_limit_per_day, refill_rate)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, ttl: int = 0) -> Any:
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        if ttl:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        url = urljoin(self.base_url, endpoint)
        if params:
            query = "&".join(f"{key}={value}" for key, value in params.items())
            url = f"{url}?{query}"

        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(1, self.retries + 1):
            self.bucket.wait_for_token()
            try:
                request = Request(url, headers=headers)
                with urlopen(request, timeout=20) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    if ttl:
                        self.cache.set(cache_key, payload, ttl)
                    return payload
            except Exception as exc:  # pragma: no cover - logs only
                wait = self.backoff ** attempt
                logger.warning("HTTP error on attempt %s: %s. Retrying in %.2fs", attempt, exc, wait)
                time.sleep(wait)
        raise RuntimeError(f"Failed to fetch {url} after {self.retries} attempts")
