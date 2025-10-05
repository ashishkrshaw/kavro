from pydantic import BaseModel
from typing import Optional, Any


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PublishKey(BaseModel):
    identity_pubkey: str
    device_name: Optional[str] = None


class MessageIn(BaseModel):
    recipient_id: int
    ciphertext: str
    ephemeral_pubkey: str
    metadata: Optional[Any] = None


class MessageOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    ciphertext: str
    ephemeral_pubkey: str
    metadata: Optional[Any] = None

    model_config = {
        "from_attributes": True
    }
