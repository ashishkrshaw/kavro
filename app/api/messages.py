import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import MessageIn, MessageOut
from app.core.security import auth_and_set_state
from app.core.rate_limiter import limiter
from app.db.session import AsyncSessionLocal
import sqlalchemy as sa
from app.models import messages, users, audit_logs

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limiter(limit=30, window=60, by="user"))]
)
async def send_message(payload: MessageIn, sender_id: int = Depends(auth_and_set_state)):
    async with AsyncSessionLocal() as session:
        q = sa.select(users.c.id).where(users.c.id == payload.recipient_id)
        r = await session.execute(q)
        if not r.first():
            raise HTTPException(status_code=404, detail="Recipient not found")

        try:
            ciphertext_bytes = base64.b64decode(payload.ciphertext)
        except Exception:
            raise HTTPException(status_code=400, detail="ciphertext must be valid base64")

        ins = messages.insert().values(
            sender_id=sender_id,
            recipient_id=payload.recipient_id,
            ciphertext=ciphertext_bytes,
            ephemeral_pubkey=payload.ephemeral_pubkey,
            metadata=payload.metadata
        )
        await session.execute(ins)

        await session.execute(
            audit_logs.insert().values(
                user_id=sender_id,
                action="send_message",
                details={"to": payload.recipient_id}
            )
        )

        await session.commit()

    return {"status": "stored"}


@router.get(
    "/inbox",
    response_model=dict,
    dependencies=[Depends(limiter(limit=20, window=30, by="user"))]
)
async def fetch_inbox(limit: int = 50, user_id: int = Depends(auth_and_set_state)):
    async with AsyncSessionLocal() as session:
        q = sa.select(messages).where(messages.c.recipient_id == user_id).order_by(
            messages.c.created_at.desc()
        ).limit(limit)
        r = await session.execute(q)
        rows = [dict(row._mapping) for row in r.fetchall()]

        out: List[MessageOut] = []
        for row in rows:
            ct = row["ciphertext"]
            ct_b64 = base64.b64encode(ct).decode()
            out.append({
                "id": row["id"],
                "sender_id": row["sender_id"],
                "recipient_id": row["recipient_id"],
                "ciphertext": ct_b64,
                "ephemeral_pubkey": row["ephemeral_pubkey"],
                "metadata": row.get("metadata"),
            })

        await session.execute(
            audit_logs.insert().values(
                user_id=user_id,
                action="fetch_inbox",
                details={"count": len(out)}
            )
        )
        await session.commit()

    return {"messages": out}


@router.post(
    "/{message_id}/ack",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(limiter(limit=60, window=60, by="user"))]
)
async def ack_message(message_id: int, user_id: int = Depends(auth_and_set_state)):
    async with AsyncSessionLocal() as session:
        q = sa.select(messages).where(messages.c.id == message_id)
        r = await session.execute(q)
        row = r.first()
        if not row:
            raise HTTPException(status_code=404, detail="Message not found")

        record = row._mapping
        if record["recipient_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        upd = messages.update().where(messages.c.id == message_id).values(delivered=True)
        await session.execute(upd)

        await session.execute(
            audit_logs.insert().values(
                user_id=user_id,
                action="ack_message",
                details={"message_id": message_id}
            )
        )

        await session.commit()

    return {"status": "acknowledged"}
