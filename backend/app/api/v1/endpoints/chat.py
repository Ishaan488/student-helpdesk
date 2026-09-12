from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.chat import Thread, ChatMessage
from app.agent.graph import agent_app
from app.agent.summarizer import summarize_and_update_thread

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[UUID] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: UUID
    intent: str | None = None
    trace: list[str] = []
    debug_log: dict | None = None
    memory_state: dict | None = None

class ThreadResponse(BaseModel):
    id: UUID
    title: str
    summary: str | None
    created_at: str
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True

@router.post("/message", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a message to the Agentic RAG assistant with persistent, rolling memory.
    """
    # 1. Thread Management
    if request.thread_id:
        result = await db.execute(select(Thread).filter(Thread.id == request.thread_id, Thread.user_id == current_user.id))
        thread = result.scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
    else:
        # Create a new thread
        thread = Thread(user_id=current_user.id, title=request.message[:50] + "...")
        db.add(thread)
        await db.flush()  # to get thread.id
        
    # 2. Save the incoming HumanMessage
    human_msg_record = ChatMessage(thread_id=thread.id, role="human", content=request.message)
    db.add(human_msg_record)
    await db.flush()

    # 3. Load past messages
    messages_result = await db.execute(
        select(ChatMessage).filter(ChatMessage.thread_id == thread.id).order_by(ChatMessage.created_at.asc())
    )
    all_messages = messages_result.scalars().all()
    
    # 4. Memory Management Logic (Sliding Window + Running Summary)
    MAX_MESSAGES_IN_WINDOW = 6  # Last 3 interactions
    
    if len(all_messages) > MAX_MESSAGES_IN_WINDOW:
        # Messages that are falling out of the window
        messages_to_summarize = all_messages[:-MAX_MESSAGES_IN_WINDOW]
        
        # In a highly optimized enterprise app, we'd fire this summarization in a background 
        # Celery/FastAPI BackgroundTask. For simplicity and demonstration, we await it here.
        await summarize_and_update_thread(db, thread, messages_to_summarize)
        
        # We only keep the most recent ones for the prompt
        recent_messages = all_messages[-MAX_MESSAGES_IN_WINDOW:]
    else:
        recent_messages = all_messages

    # 5. Reconstruct LangChain Messages
    langchain_messages = []
    
    for msg in recent_messages:
        if msg.role == "human":
            langchain_messages.append(HumanMessage(content=msg.content))
        else:
            langchain_messages.append(AIMessage(content=msg.content))
    
    # Initialize LangGraph state
    initial_state = {
        "messages": langchain_messages,
        "current_user_id": current_user.id,
        "intent": None,
        "extracted_company": None,
        "eligibility_results": None,
        "trace": [],
        "debug_log": {},
        "summary": thread.summary
    }
    
    config = {"configurable": {"db": db}}
    
    # 6. Execute the Agentic Workflow
    from google.api_core.exceptions import ResourceExhausted
    try:
        final_state = await agent_app.ainvoke(initial_state, config=config)
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "resourceexhausted" in error_msg or "quota" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="Google Gemini API Rate Limit Reached (Free Tier). Please wait 60 seconds before sending another message."
            )
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")
        
    # Extract the AI's final response
    final_ai_msg = final_state["messages"][-1]
    
    # 7. Save the outgoing AIMessage
    ai_msg_record = ChatMessage(thread_id=thread.id, role="ai", content=final_ai_msg.content)
    db.add(ai_msg_record)
    await db.commit()
    
    # Serialize state for frontend teleport
    serializable_state = {k: v for k, v in final_state.items() if k != "messages"}
    serializable_state["messages"] = [{"role": m.type, "content": m.content} for m in final_state["messages"]]
    
    return ChatResponse(
        response=final_ai_msg.content,
        thread_id=thread.id,
        intent=final_state.get("intent"),
        trace=final_state.get("trace", []),
        debug_log=final_state.get("debug_log", {}),
        memory_state=serializable_state
    )

@router.get("/threads", response_model=List[ThreadResponse])
async def get_threads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch all chat threads for the current user."""
    result = await db.execute(
        select(Thread).filter(Thread.user_id == current_user.id).order_by(Thread.updated_at.desc())
    )
    threads = result.scalars().all()
    
    return [
        ThreadResponse(
            id=t.id,
            title=t.title,
            summary=t.summary,
            created_at=t.created_at.isoformat()
        ) for t in threads
    ]

@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_thread_messages(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch message history for a specific thread."""
    # Verify ownership
    thread_result = await db.execute(select(Thread).filter(Thread.id == thread_id, Thread.user_id == current_user.id))
    if not thread_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Thread not found")
        
    messages_result = await db.execute(
        select(ChatMessage).filter(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat()
        ) for m in messages
    ]

