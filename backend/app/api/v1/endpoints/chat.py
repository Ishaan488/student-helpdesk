from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.agent.graph import agent_app

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str | None = None
    trace: list[str] = []
    debug_log: dict | None = None
    memory_state: dict | None = None

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
        "eligibility_results": None,
        "trace": [],
        "debug_log": {}
    }
    
    # Pass the AsyncSession via RunnableConfig to the graph tools
    config = {"configurable": {"db": db}}
    
    # Execute the LangGraph workflow
    final_state = await agent_app.ainvoke(initial_state, config=config)
    
    # Extract the AI's final response
    final_message = final_state["messages"][-1]
    
    # Serialize state for the frontend (avoid complex Langchain message objects)
    serializable_state = {k: v for k, v in final_state.items() if k != "messages"}
    serializable_state["messages"] = [{"role": m.type, "content": m.content} for m in final_state["messages"]]
    
    return ChatResponse(
        response=final_message.content,
        intent=final_state.get("intent"),
        trace=final_state.get("trace", []),
        debug_log=final_state.get("debug_log", {}),
        memory_state=serializable_state
    )
