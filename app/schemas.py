import re
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match("^[a-zA-Z0-9_-]+$", v):
            raise ValueError('Username must be alphanumeric (can include _ or -)')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        errors = []
        if len(v) < 8:
            errors.append("8+ characters")
        if not any(c.isupper() for c in v):
            errors.append("1 uppercase")
        if not any(c.islower() for c in v):
            errors.append("1 lowercase")
        if not any(c.isdigit() for c in v):
            errors.append("1 number")
        
        if errors:
            raise ValueError(f"Password needs: {', '.join(errors)}")
        return v


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
    
    model_config = {"from_attributes": True}
