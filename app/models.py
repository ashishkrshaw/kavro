# models.py

import datetime
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, JSON

from app.db.base import metadata


users = sa.Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
)

devices = sa.Table(
    "devices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("identity_pubkey", String, nullable=False),
    Column("device_name", String, nullable=True),
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
)

messages = sa.Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sender_id", Integer, nullable=False),
    Column("recipient_id", Integer, nullable=False),
    Column("ciphertext", LargeBinary, nullable=False),
    Column("ephemeral_pubkey", String, nullable=False),
    Column("metadata", JSON, nullable=True),
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
    Column("delivered", Boolean, default=False),
)

audit_logs = sa.Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=True),
    Column("action", String, nullable=False),
    Column("details", JSON),
    Column("timestamp", DateTime, default=datetime.datetime.utcnow),
)
