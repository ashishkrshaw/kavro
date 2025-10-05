from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import UserCreate, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.core.rate_limiter import limiter
from app.db.session import AsyncSessionLocal
import sqlalchemy as sa
from app.models import users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limiter(limit=5, window=60, by="ip"))]
)
async def register(payload: UserCreate):
    async with AsyncSessionLocal() as session:
        q = sa.select(users).where(users.c.username == payload.username)
        r = await session.execute(q)
        if r.first():
            raise HTTPException(status_code=400, detail="username already exists")

        pwd_hash = hash_password(payload.password)
        ins = users.insert().values(username=payload.username, password_hash=pwd_hash)
        res = await session.execute(ins)
        await session.commit()

        user_id = res.inserted_primary_key[0]
        token = create_access_token(user_id)
        return {"access_token": token}


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(limiter(limit=10, window=60, by="ip"))]
)
async def login(payload: UserCreate):
    async with AsyncSessionLocal() as session:
        q = sa.select(users).where(users.c.username == payload.username)
        r = await session.execute(q)
        row = r.first()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user = row._mapping

        if not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(user["id"])
        return {"access_token": token}


@router.get("/me")
async def me(current_user_id: int = Depends(get_current_user)):
    return {"user_id": current_user_id}
