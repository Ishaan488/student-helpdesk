from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import agent_app
from app.core.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str | None = None

@router.post("/message", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a message to the Agentic RAG assistant.
    Requires authentication. The agent will fetch context deterministically
    based on the logged-in user's profile.
    """
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "current_user_id": current_user.id,
        "intent": None,
        "extracted_company": None,
        "eligibility_results": None
    }
    
    # Pass the AsyncSession via RunnableConfig to the graph tools
    config = {"configurable": {"db": db}}
    
    # Execute the LangGraph workflow
    final_state = await agent_app.ainvoke(initial_state, config=config)
    
    # Extract the AI's final response
    final_message = final_state["messages"][-1]
    
    return ChatResponse(
        response=final_message.content,
        intent=final_state.get("intent")
    )
