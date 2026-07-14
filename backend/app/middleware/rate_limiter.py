"""Redis-backed rate limiter — per-IP and per-user.

Per ARCHITECTURE.md §8: Rate limiting per-IP and per-user (Redis-backed).
Super Admin login has its own stricter rate limiter.
"""
import time
from typing import Optional

from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis

from app.config import settings


class RateLimiter:
    """Sliding-window rate limiter using Redis."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> bool:
        """Check if the key has exceeded the rate limit.
        Returns True if allowed, raises 429 if exceeded."""
        redis = await self.get_redis()
        now = time.time()
        window_start = now - window_seconds
        pipe_key = f"ratelimit:{key}"

        pipe = redis.pipeline()
        pipe.zremrangebyscore(pipe_key, 0, window_start)
        pipe.zadd(pipe_key, {str(now): now})
        pipe.zcard(pipe_key)
        pipe.expire(pipe_key, window_seconds)
        results = await pipe.execute()

        request_count = results[2]
        if request_count > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window_seconds} seconds.",
            )
        return True

    async def check_ip_rate_limit(self, request: Request):
        """Standard per-IP rate limit."""
        client_ip = request.client.host if request.client else "unknown"
        await self.check_rate_limit(
            f"ip:{client_ip}",
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        )

    async def check_superadmin_login_rate(self, identifier: str):
        """Stricter rate limit for Super Admin login attempts.
        5 attempts / 15 min lockout."""
        await self.check_rate_limit(
            f"superadmin_login:{identifier}",
            max_requests=settings.RATE_LIMIT_SUPERADMIN_LOGIN_ATTEMPTS,
            window_seconds=settings.RATE_LIMIT_SUPERADMIN_LOCKOUT_MINUTES * 60,
        )


rate_limiter = RateLimiter()
