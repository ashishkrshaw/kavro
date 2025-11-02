from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

from app.api import auth, keys, messages
from app.api.router import api_v1_router
from app.db.session import engine
from app.db.base import metadata
from app.core.config import settings
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.middleware import LimitUploadSize
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)


app = FastAPI(
    title="E2EE Messaging API",
    description="End-to-end encrypted messaging backend",
    version="1.0.0"
)

# middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LimitUploadSize, max_upload_size=1_048_576)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes - versioned API (HENNGE best practice)
app.include_router(api_v1_router)  # /api/v1/* endpoints

# Also keep routes at root level for backward compatibility
# This allows existing clients to work while new clients use /api/v1/
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(messages.router)

# exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    
    app.state.redis = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=10
    )
    print("Redis connected!")


@app.on_event("shutdown")
async def shutdown():
    r = getattr(app.state, "redis", None)
    if r:
        await r.aclose()


@app.get("/health")
@app.get("/api/v1/health")  # Also available at versioned path
async def health():
    """
    Health check endpoint.
    
    Returns service status and version info.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "ok",
        "service": "kavro",
        "version": "1.0.0"
    }
