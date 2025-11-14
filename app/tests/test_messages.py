"""
test_messages.py - Tests for messaging endpoints

Tests cover:
1. Sending encrypted messages
2. Fetching inbox
3. Acknowledging messages
4. Authorization checks
"""

import pytest
import base64
from httpx import AsyncClient


class TestSendMessage:
    """Tests for POST /messages/ endpoint."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, client: AsyncClient):
        """Test successful message sending."""
        # Register two users
        sender_resp = await client.post(
            "/auth/register",
            json={"username": "sender1", "password": "ValidPass123"}
        )
        sender_token = sender_resp.json()["access_token"]
        
        recipient_resp = await client.post(
            "/auth/register",
            json={"username": "recipient1", "password": "ValidPass123"}
        )
        recipient_token = recipient_resp.json()["access_token"]
        
        # Get recipient's user_id
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        recipient_id = me_resp.json()["user_id"]
        
        # Send message (ciphertext must be base64 encoded)
        ciphertext = base64.b64encode(b"encrypted message content").decode()
        
        response = await client.post(
            "/messages/",
            json={
                "recipient_id": recipient_id,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "ephemeral_key_12345"
            },
            headers={"Authorization": f"Bearer {sender_token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["status"] == "stored"
    
    @pytest.mark.asyncio
    async def test_send_message_unauthenticated(self, client: AsyncClient):
        """Test message sending fails without authentication."""
        ciphertext = base64.b64encode(b"test").decode()
        
        response = await client.post(
            "/messages/",
            json={
                "recipient_id": 1,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "key"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_ciphertext(self, client: AsyncClient):
        """Test message sending fails with invalid base64 ciphertext."""
        reg_resp = await client.post(
            "/auth/register",
            json={"username": "sender2", "password": "ValidPass123"}
        )
        token = reg_resp.json()["access_token"]
        
        response = await client.post(
            "/messages/",
            json={
                "recipient_id": 1,
                "ciphertext": "not valid base64!!!",
                "ephemeral_pubkey": "key"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_send_message_nonexistent_recipient(self, client: AsyncClient):
        """Test message sending fails for non-existent recipient."""
        reg_resp = await client.post(
            "/auth/register",
            json={"username": "sender3", "password": "ValidPass123"}
        )
        token = reg_resp.json()["access_token"]
        
        ciphertext = base64.b64encode(b"test").decode()
        
        response = await client.post(
            "/messages/",
            json={
                "recipient_id": 99999,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "key"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


class TestInbox:
    """Tests for GET /messages/inbox endpoint."""
    
    @pytest.mark.asyncio
    async def test_fetch_inbox_empty(self, client: AsyncClient):
        """Test fetching empty inbox."""
        reg_resp = await client.post(
            "/auth/register",
            json={"username": "inboxuser1", "password": "ValidPass123"}
        )
        token = reg_resp.json()["access_token"]
        
        response = await client.get(
            "/messages/inbox",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "messages" in response.json()
    
    @pytest.mark.asyncio
    async def test_fetch_inbox_with_messages(self, client: AsyncClient):
        """Test fetching inbox with messages."""
        # Register sender and recipient
        sender_resp = await client.post(
            "/auth/register",
            json={"username": "msgsender", "password": "ValidPass123"}
        )
        sender_token = sender_resp.json()["access_token"]
        
        recipient_resp = await client.post(
            "/auth/register",
            json={"username": "msgrecipient", "password": "ValidPass123"}
        )
        recipient_token = recipient_resp.json()["access_token"]
        
        # Get recipient ID
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        recipient_id = me_resp.json()["user_id"]
        
        # Send a message
        ciphertext = base64.b64encode(b"hello there").decode()
        await client.post(
            "/messages/",
            json={
                "recipient_id": recipient_id,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "ephkey"
            },
            headers={"Authorization": f"Bearer {sender_token}"}
        )
        
        # Fetch inbox
        response = await client.get(
            "/messages/inbox",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert len(messages) >= 1
    
    @pytest.mark.asyncio
    async def test_fetch_inbox_unauthenticated(self, client: AsyncClient):
        """Test inbox fetch fails without authentication."""
        response = await client.get("/messages/inbox")
        
        assert response.status_code == 401


class TestAckMessage:
    """Tests for POST /messages/{id}/ack endpoint."""
    
    @pytest.mark.asyncio
    async def test_ack_message_success(self, client: AsyncClient):
        """Test successful message acknowledgment."""
        # Setup: create sender and recipient, send message
        sender_resp = await client.post(
            "/auth/register",
            json={"username": "acksender", "password": "ValidPass123"}
        )
        sender_token = sender_resp.json()["access_token"]
        
        recipient_resp = await client.post(
            "/auth/register",
            json={"username": "ackrecipient", "password": "ValidPass123"}
        )
        recipient_token = recipient_resp.json()["access_token"]
        
        # Get recipient ID
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        recipient_id = me_resp.json()["user_id"]
        
        # Send message
        ciphertext = base64.b64encode(b"ack test message").decode()
        await client.post(
            "/messages/",
            json={
                "recipient_id": recipient_id,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "ephkey"
            },
            headers={"Authorization": f"Bearer {sender_token}"}
        )
        
        # Get message id from inbox
        inbox_resp = await client.get(
            "/messages/inbox",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        message_id = inbox_resp.json()["messages"][0]["id"]
        
        # Acknowledge the message
        response = await client.post(
            f"/messages/{message_id}/ack",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"
    
    @pytest.mark.asyncio
    async def test_ack_message_not_owner(self, client: AsyncClient):
        """Test cannot ack message that belongs to someone else."""
        # Setup users
        sender_resp = await client.post(
            "/auth/register",
            json={"username": "acksender2", "password": "ValidPass123"}
        )
        sender_token = sender_resp.json()["access_token"]
        
        recipient_resp = await client.post(
            "/auth/register",
            json={"username": "ackrecipient2", "password": "ValidPass123"}
        )
        recipient_token = recipient_resp.json()["access_token"]
        
        other_resp = await client.post(
            "/auth/register",
            json={"username": "otheruserack", "password": "ValidPass123"}
        )
        other_token = other_resp.json()["access_token"]
        
        # Get recipient ID
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        recipient_id = me_resp.json()["user_id"]
        
        # Send message
        ciphertext = base64.b64encode(b"private message").decode()
        await client.post(
            "/messages/",
            json={
                "recipient_id": recipient_id,
                "ciphertext": ciphertext,
                "ephemeral_pubkey": "ephkey"
            },
            headers={"Authorization": f"Bearer {sender_token}"}
        )
        
        # Get message id from recipient's inbox
        inbox_resp = await client.get(
            "/messages/inbox",
            headers={"Authorization": f"Bearer {recipient_token}"}
        )
        message_id = inbox_resp.json()["messages"][0]["id"]
        
        # Try to ack with OTHER user (not the recipient)
        response = await client.post(
            f"/messages/{message_id}/ack",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
