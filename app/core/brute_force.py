"""
brute_force.py - protection against login brute force attacks
locks out users after too many failed attempts
"""

from fastapi import HTTPException, status, Request
import redis.asyncio as redis
from typing import Optional


class BruteForceProtector:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_attempts = 5   # lockout after 5 fails
        self.window = 300       # 5 min window

    def _get_key(self, identifier: str) -> str:
        return f"bf_login:{identifier}"

    async def check(self, identifier: str) -> None:
        """check if user is locked out"""
        key = self._get_key(identifier)
        count = await self.redis.get(key)
        
        if count and int(count) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {self.window//60} minutes."
            )

    async def register_failure(self, identifier: str) -> int:
        """increment fail count"""
        key = self._get_key(identifier)
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        results = await pipe.execute()
        return results[0]

    async def reset(self, identifier: str) -> None:
        """reset on successful login"""
        key = self._get_key(identifier)
        await self.redis.delete(key)


async def get_brute_force_protector(request: Request) -> Optional[BruteForceProtector]:
    """dependency to get brute force protector"""
    if not hasattr(request.app.state, "redis") or request.app.state.redis is None:
        return None
    return BruteForceProtector(request.app.state.redis)
