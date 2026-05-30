from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from db.models.message import MessageModel
from db.models.session import SessionModel
from models.response import ResponseModel
from models.session import SessionCreate, SessionInfo, SessionMessage

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=ResponseModel[SessionInfo], status_code=201)
async def create_session(
    body: SessionCreate, db: AsyncSession = Depends(get_db)
) -> ResponseModel[SessionInfo]:
    from common.utils import generate_id, utc_now

    session = SessionModel(
        session_id=generate_id(),
        user_id=body.user_id,
        platform=body.platform,
        group_id=body.group_id,
        tenant_id=body.tenant_id,
        metadata_=body.metadata,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(session)
    await db.flush()

    return ResponseModel(
        data=SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            platform=session.platform,
            group_id=session.group_id,
            tenant_id=session.tenant_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    )


@router.get("/{session_id}", response_model=ResponseModel[SessionInfo])
async def get_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ResponseModel[SessionInfo]:
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ResponseModel(
        data=SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            platform=session.platform,
            group_id=session.group_id,
            tenant_id=session.tenant_id,
            status=session.status,
            message_count=session.message_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            metadata=session.metadata_,
        )
    )


@router.delete("/{session_id}", response_model=ResponseModel)
async def close_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ResponseModel:
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "closed"
    await db.flush()
    return ResponseModel(message="Session closed")


@router.get("/{session_id}/messages", response_model=ResponseModel[list[SessionMessage]])
async def get_session_messages(
    session_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
) -> ResponseModel[list[SessionMessage]]:
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()

    return ResponseModel(
        data=[
            SessionMessage(
                message_id=m.message_id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                created_at=m.created_at,
            )
            for m in messages
        ]
    )
