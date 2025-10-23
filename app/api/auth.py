from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
import sqlalchemy as sa

from app.schemas import UserCreate, Token
from app.models import users
from app.db.session import AsyncSessionLocal
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.rate_limiter import limiter
from app.core.brute_force import get_brute_force_protector, BruteForceProtector
from app.core.audit import log_security_event


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limiter(limit=3, window=3600, by="ip"))])
async def register(payload: UserCreate, request: Request):
    async with AsyncSessionLocal() as session:
        q = sa.select(users).where(users.c.username == payload.username)
        r = await session.execute(q)
        
        if r.first():
            await log_security_event("register", payload.username, "failure", 
                                     request.client.host, {"reason": "username_exists"})
            raise HTTPException(status_code=400, 
                              detail="This username is already taken. Try another one.")
        
        pwd_hash = hash_password(payload.password)
        ins = users.insert().values(username=payload.username, password_hash=pwd_hash)
        res = await session.execute(ins)
        await session.commit()
        
        user_id = res.inserted_primary_key[0]
        await log_security_event("register", payload.username, "success", request.client.host)
        
        token = create_access_token(user_id)
        return {"access_token": token}


@router.post("/login", response_model=Token,
             dependencies=[Depends(limiter(limit=5, window=900, by="ip"))])
async def login(payload: UserCreate, request: Request,
                bf: Optional[BruteForceProtector] = Depends(get_brute_force_protector)):
    if bf:
        await bf.check(payload.username)
    
    async with AsyncSessionLocal() as session:
        q = sa.select(users).where(users.c.username == payload.username)
        r = await session.execute(q)
        row = r.first()
        
        if not row:
            if bf: 
                await bf.register_failure(payload.username)
            await log_security_event("login", payload.username, "failure", 
                                     request.client.host, {"reason": "user_not_found"})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                              detail="Incorrect username or password.")
        
        user = row._mapping
        
        if not verify_password(payload.password, user["password_hash"]):
            if bf: 
                await bf.register_failure(payload.username)
            await log_security_event("login", payload.username, "failure", 
                                     request.client.host, {"reason": "bad_password"})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                              detail="Incorrect username or password.")
        
        if bf:
            await bf.reset(payload.username)
        await log_security_event("login", payload.username, "success", request.client.host)
        
        token = create_access_token(user["id"])
        return {"access_token": token}


@router.get("/me")
async def me(current_user_id: int = Depends(get_current_user)):
    return {"user_id": current_user_id}
