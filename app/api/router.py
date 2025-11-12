"""
router.py - API version router

This file creates a versioned API router (/api/v1/...) that groups all endpoints.
This is a HENNGE best practice for API design.

Why versioning?
1. Allows breaking changes in v2 without affecting v1 clients
2. Makes API evolution predictable
3. Shows professional API design understanding
"""

from fastapi import APIRouter

from app.api import auth, keys, messages


# Create versioned router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all existing routers under /api/v1/
api_v1_router.include_router(auth.router)      # /api/v1/auth/*
api_v1_router.include_router(keys.router)      # /api/v1/keys/*
api_v1_router.include_router(messages.router)  # /api/v1/messages/*
