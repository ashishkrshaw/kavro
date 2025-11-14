"""
test_health.py - Tests for health check endpoint

Simple tests to verify the API is running.
"""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Tests for GET /health endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint returns ok status."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
