from fastapi import FastAPI
import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api import auth, keys, messages
from app.db.session import engine
from app.db.base import metadata
from app.core.config import settings

app = FastAPI(
    title="E2EE Messaging API",
    description="A real end-to-end encrypted messaging backend. No plaintext stored.",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(messages.router)


@app.on_event("startup")
async def startup():
    # Drop and recreate all tables (clears DB) - WARNING: destructive
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    # Redis connection using redis.asyncio
    app.state.redis = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=10
    )

    print("Redis connected!")


@app.on_event("shutdown")
async def shutdown():
    redis_client = getattr(app.state, "redis", None)
    if redis_client:
        await redis_client.aclose()


@app.get("/health")
async def health():
    return {"status": "ok"}
