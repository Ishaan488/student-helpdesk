from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, RoleEnum
from app.models.escalation import EscalatedQuery
from app.models.chat import ChatMessage, Thread

router = APIRouter()


class EscalatedQueryResponse(BaseModel):
    id: UUID
    thread_id: UUID
    user_id: UUID
    query_text: str
    status: str
    created_at: str
    resolved_at: str | None = None
    user_email: str
    admin_reply: str | None = None
    
    class Config:
        from_attributes = True


class ResolveEscalationRequest(BaseModel):
    reply_text: str


from sqlalchemy.orm import joinedload

@router.get("/", response_model=List[EscalatedQueryResponse])
async def get_escalations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch all escalated queries (Admin/TPO only)."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to view escalations")

    result = await db.execute(
        select(EscalatedQuery)
        .options(joinedload(EscalatedQuery.user))
        .order_by(EscalatedQuery.created_at.asc())
    )
    queries = result.scalars().all()
    
    return [
        EscalatedQueryResponse(
            id=q.id,
            thread_id=q.thread_id,
            user_id=q.user_id,
            query_text=q.query_text,
            status=q.status,
            created_at=q.created_at.isoformat(),
            resolved_at=q.resolved_at.isoformat() if q.resolved_at else None,
            user_email=q.user.email if q.user else "Unknown",
            admin_reply=q.admin_reply
        ) for q in queries
    ]


@router.post("/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: UUID,
    request: ResolveEscalationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolves an escalated query and injects the admin's reply 
    directly into the student's chat thread!
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to resolve escalations")

    # 1. Get the ticket
    result = await db.execute(select(EscalatedQuery).filter(EscalatedQuery.id == escalation_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Escalated query not found")
        
    if ticket.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="Query is already resolved")

    # 2. Get the thread to ensure it exists
    thread_result = await db.execute(select(Thread).filter(Thread.id == ticket.thread_id))
    thread = thread_result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Original chat thread not found")

    # 3. Mark ticket as resolved
    ticket.status = "RESOLVED"
    ticket.resolved_at = datetime.utcnow()
    ticket.admin_reply = request.reply_text

    # 4. Inject the Admin's response as an AI message in the student's chat thread
    # We prefix it to make it clear it came from a human
    formatted_reply = f"**[Message from Placement Office Admin]**\n\n{request.reply_text}"
    
    ai_msg_record = ChatMessage(
        thread_id=thread.id, 
        role="ai", 
        content=formatted_reply
    )
    
    db.add(ai_msg_record)
    await db.commit()
    
    return {"status": "success", "message": "Ticket resolved and replied to student."}
