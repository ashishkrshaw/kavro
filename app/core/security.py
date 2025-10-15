from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    if len(password.encode()) > 72:
        password = password.encode()[:72].decode(errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode()) > 72:
        plain_password = plain_password.encode()[:72].decode(errors="ignore")
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": str(user_id), "exp": expire}
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return int(payload.get("sub"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    return decode_token(token)


async def auth_and_set_state(request: Request, token: str = Depends(oauth2_scheme)) -> int:
    user_id = decode_token(token)
    request.state.user_id = user_id
    return user_id
