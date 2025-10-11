import time
from typing import Optional
from fastapi import Request, HTTPException, status
import redis.asyncio as redis


DEFAULT_LIMIT = 60       # events
DEFAULT_WINDOW = 60      # seconds


def _redis_key(prefix: str, identifier: str, now: Optional[float] = None) -> str:
    ts = int(now or time.time())
    return f"rl:{prefix}:{identifier}:{ts}"


async def rate_limit_check(
    redis_client: redis.Redis,
    key: str,
    limit: int,
    window: int
) -> None:
    cnt = await redis_client.incr(key)
    if cnt == 1:
        await redis_client.expire(key, window)

    if cnt > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Allowed {limit} requests per {window} seconds."
        )


async def _key_by_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    client = request.client.host if request.client else "unknown"
    return f"anon_ip:{client}"


async def _key_by_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        client = xff.split(",")[0].strip()
    else:
        client = request.client.host if request.client else "unknown"
    return f"ip:{client}"


def limiter(limit: int = DEFAULT_LIMIT, window: int = DEFAULT_WINDOW, by: str = "user"):
    if by not in ("user", "ip"):
        raise ValueError("by must be 'user' or 'ip'")

    async def _dependency(request: Request):
        redis_client: redis.Redis = request.app.state.redis
        if redis_client is None:
            return None

        if by == "user":
            identifier = await _key_by_user(request)
            prefix = "u"
        else:
            identifier = await _key_by_ip(request)
            prefix = "i"

        now = time.time()
        bucket = int(now) // window
        key = f"rl:{prefix}:{identifier}:{bucket}"

        await rate_limit_check(redis_client, key, limit, window)

    return _dependency
