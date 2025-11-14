"""
test_auth.py - Tests for authentication endpoints

Tests cover:
1. User registration
2. User login
3. Get current user (/auth/me)
4. Error cases (invalid credentials, duplicate users)
"""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /auth/register endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={"username": "newuser", "password": "ValidPass123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type", "bearer") == "bearer"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration fails for duplicate username."""
        user_data = {"username": "duplicate", "password": "ValidPass123"}
        
        # First registration should succeed
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same username should fail
        response2 = await client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already taken" in response2.json().get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration fails for weak password."""
        response = await client.post(
            "/auth/register",
            json={"username": "weakpassuser", "password": "weak"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_invalid_username(self, client: AsyncClient):
        """Test registration fails for invalid username format."""
        response = await client.post(
            "/auth/register",
            json={"username": "invalid user!", "password": "ValidPass123"}
        )
        
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for POST /auth/login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # First register the user
        user_data = {"username": "logintest", "password": "ValidPass123"}
        await client.post("/auth/register", json=user_data)
        
        # Then login
        response = await client.post("/auth/login", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login fails with wrong password."""
        # Register user
        await client.post(
            "/auth/register",
            json={"username": "wrongpass", "password": "ValidPass123"}
        )
        
        # Try login with wrong password
        response = await client.post(
            "/auth/login",
            json={"username": "wrongpass", "password": "WrongPass456"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login fails for non-existent user."""
        response = await client.post(
            "/auth/login",
            json={"username": "doesnotexist", "password": "ValidPass123"}
        )
        
        assert response.status_code == 401


class TestMe:
    """Tests for GET /auth/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient):
        """Test /me returns user info when authenticated."""
        # Register and get token
        response = await client.post(
            "/auth/register",
            json={"username": "metest", "password": "ValidPass123"}
        )
        token = response.json()["access_token"]
        
        # Call /me with token
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "user_id" in response.json()
    
    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me fails without token."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client: AsyncClient):
        """Test /me fails with invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"}
        )
        
        assert response.status_code == 401
