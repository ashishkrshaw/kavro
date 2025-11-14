"""
test_keys.py - Tests for key management endpoints

Tests cover:
1. Publishing public keys
2. Retrieving public keys
3. Authentication requirements
"""

import pytest
from httpx import AsyncClient


class TestPublishKey:
    """Tests for POST /keys/publish endpoint."""
    
    @pytest.mark.asyncio
    async def test_publish_key_success(self, client: AsyncClient):
        """Test successful key publishing."""
        # Register user and get token
        reg_response = await client.post(
            "/auth/register",
            json={"username": "keyuser1", "password": "ValidPass123"}
        )
        token = reg_response.json()["access_token"]
        
        # Publish a key
        response = await client.post(
            "/keys/publish",
            json={
                "identity_pubkey": "test_public_key_12345",
                "device_name": "My Phone"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["status"] == "public key stored"
    
    @pytest.mark.asyncio
    async def test_publish_key_unauthenticated(self, client: AsyncClient):
        """Test key publishing fails without authentication."""
        response = await client.post(
            "/keys/publish",
            json={
                "identity_pubkey": "test_public_key",
                "device_name": "My Device"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_publish_key_without_device_name(self, client: AsyncClient):
        """Test key publishing works without device name (optional field)."""
        # Register user
        reg_response = await client.post(
            "/auth/register",
            json={"username": "keyuser2", "password": "ValidPass123"}
        )
        token = reg_response.json()["access_token"]
        
        # Publish key without device name
        response = await client.post(
            "/keys/publish",
            json={"identity_pubkey": "test_public_key_67890"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201


class TestGetKeys:
    """Tests for GET /keys/{user_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_keys_success(self, client: AsyncClient):
        """Test retrieving published keys."""
        # Register user and publish a key
        reg_response = await client.post(
            "/auth/register",
            json={"username": "keyuser3", "password": "ValidPass123"}
        )
        token = reg_response.json()["access_token"]
        
        # Get user_id from /me
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        user_id = me_response.json()["user_id"]
        
        # Publish a key
        await client.post(
            "/keys/publish",
            json={
                "identity_pubkey": "public_key_for_retrieval",
                "device_name": "Test Device"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Retrieve keys
        response = await client.get(f"/keys/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert len(data["devices"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_keys_nonexistent_user(self, client: AsyncClient):
        """Test retrieving keys for non-existent user returns empty list."""
        response = await client.get("/keys/99999")
        
        assert response.status_code == 200
        assert response.json()["devices"] == []
