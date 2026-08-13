import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-process safety valve; replace with a Redis bucket at multi-instance scale."""

    def __init__(self, app, limit: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = self.requests[key]
        while bucket and bucket[0] <= now - self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return Response(status_code=429, content='{"detail":"Rate limit exceeded"}', media_type="application/json", headers={"Retry-After": str(self.window_seconds)})
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        return response

