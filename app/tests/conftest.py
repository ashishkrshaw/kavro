"""
conftest.py - pytest fixtures for Kavro tests

This file contains shared test fixtures that can be used across all test files.
Fixtures help us:
1. Set up test database connections
2. Create test clients
3. Generate test users and tokens
"""

import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Set test environment variables BEFORE importing app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from app.main import app
from app.db.base import metadata
from app.db.session import engine


@pytest.fixture(scope="function")
async def setup_database():
    """
    Create database tables before each test, drop after.
    
    This ensures test isolation - each test starts fresh.
    """
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    
    yield
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for making HTTP requests.
    
    This client can be used to test API endpoints like:
        response = await client.post("/auth/register", json={...})
    
    Note: Depends on setup_database to ensure clean state.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "TestPassword123"
    }


@pytest.fixture
def test_user_data_2() -> dict:
    """Second sample user for testing messaging."""
    return {
        "username": "testuser2", 
        "password": "TestPassword456"
    }


@pytest.fixture
async def registered_user(client: AsyncClient, test_user_data: dict) -> dict:
    """
    Register a test user and return their data with token.
    
    Returns:
        dict with 'username', 'password', and 'access_token'
    """
    response = await client.post("/auth/register", json=test_user_data)
    
    # Return user data with token
    return {
        **test_user_data,
        "access_token": response.json().get("access_token")
    }


@pytest.fixture
def auth_headers(registered_user: dict) -> dict:
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}
