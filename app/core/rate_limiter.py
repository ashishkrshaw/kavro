from fastapi import Depends, Request, HTTPException, status
from typing import Callable


def limiter(limit: int, window: int, by: str = "ip") -> Callable:
    """
    rate limit decorator/dependency
    limit: max requests
    window: time window in seconds
    by: "ip" or "user"
    """
    
    async def rate_limit_dependency(request: Request):
        redis_client = getattr(request.app.state, "redis", None)
        if not redis_client:
            return  # no redis = no rate limiting
        
        # get identifier
        if by == "user":
            user_id = getattr(request.state, "user_id", None)
            if not user_id:
                return
            identifier = f"rl:user:{user_id}"
        else:
            identifier = f"rl:ip:{request.client.host}"
        
        # check count
        count = await redis_client.get(identifier)
        if count and int(count) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window} seconds."
            )
        
        # increment
        pipe = redis_client.pipeline()
        pipe.incr(identifier)
        pipe.expire(identifier, window)
        await pipe.execute()
    
    return rate_limit_dependency
