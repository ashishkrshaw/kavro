import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.audit import log_security_event
from app.core.encryption import encryptor
from app.core.rate_limiter import limiter
from app.core.security import auth_and_set_state
from app.db.session import AsyncSessionLocal
from app.models import audit_logs, devices, users
from app.schemas import PublishKey

router = APIRouter(prefix="/keys", tags=["keys"])


@router.post("/publish", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limiter(limit=20, window=60, by="user"))])
async def publish_key(payload: PublishKey, user_id: int = Depends(auth_and_set_state)):
    async with AsyncSessionLocal() as session:
        q = sa.select(users.c.id).where(users.c.id == user_id)
        r = await session.execute(q)
        if not r.first():
            raise HTTPException(status_code=404, detail="User account not found.")

        enc_device_name = encryptor.encrypt(payload.device_name)

        ins = devices.insert().values(
            user_id=user_id,
            identity_pubkey=payload.identity_pubkey,
            device_name=enc_device_name
        )
        await session.execute(ins)

        await session.execute(
            audit_logs.insert().values(
                user_id=user_id,
                action="publish_key",
                details={"device_name": payload.device_name}
            )
        )
        await log_security_event("publish_key", str(user_id), "success",
                                 details={"device": payload.device_name})
        await session.commit()

    return {"status": "public key stored"}


@router.get("/{user_id}", dependencies=[Depends(limiter(limit=30, window=30, by="ip"))])
async def get_public_keys(user_id: int):
    async with AsyncSessionLocal() as session:
        q = sa.select(devices).where(devices.c.user_id == user_id)
        r = await session.execute(q)

        rows = []
        for row in r.fetchall():
            d = dict(row._mapping)
            d["device_name"] = encryptor.decrypt(d["device_name"])
            rows.append(d)

        return {"devices": rows}
