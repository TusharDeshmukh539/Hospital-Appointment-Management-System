import threading
import time

from fastapi import Request

from app.core.config import get_settings
from app.exceptions import RateLimitError


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}  # ip address -> list of attempt times
        self._lock = threading.Lock()  # makes it safe when several requests run together

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        """Record one attempt for `key`; raise RateLimitError if over the limit."""
        now = time.monotonic()
        with self._lock:
            # keep only the attempts that happened inside the time window
            recent = [t for t in self._hits.get(key, []) if now - t < window_seconds]
            if len(recent) >= limit:
                self._hits[key] = recent
                raise RateLimitError("Too many login attempts. Please wait a minute and try again.")
            recent.append(now)
            self._hits[key] = recent

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


login_rate_limiter = RateLimiter()


def login_rate_limit(request: Request) -> None:
    ip_address = request.client.host if request.client else "unknown"
    login_rate_limiter.check(ip_address, get_settings().LOGIN_RATE_LIMIT_PER_MINUTE)
