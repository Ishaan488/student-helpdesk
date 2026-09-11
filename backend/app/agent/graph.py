import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from app.agent.router import classify_intent
from app.agent.state import AgentState
from app.agent.tools import fetch_company_facts, fetch_student_eligibility, fetch_upcoming_drives, search_knowledge_base
from app.config import settings

# Strong reasoning model for generating the final response (using gemini-3.6-flash)
llm_generator = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.7,
    google_api_key=settings.GEMINI_API_KEY
)

async def classify_node(state: AgentState) -> Dict[str, Any]:
    """Classifies the user's intent."""
    classification = await classify_intent(state["messages"])
    return {
        "intent": classification.intent,
        "extracted_company": classification.extracted_company
    }

async def execute_tool_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Fetches deterministic structured data."""
    intent = state.get("intent")
    company = state.get("extracted_company")
    student_id = state.get("current_user_id")
    messages = state.get("messages", [])
    
    # Retrieve the db session injected at runtime!
    db = config["configurable"]["db"]
    
    results = []
    
    if intent == "ELIGIBILITY_CHECK":
        results = await fetch_student_eligibility(db, student_id)
        # If they asked for a specific company, filter it!
        if company:
            results = [r for r in results if company.lower() in r.get("company", "").lower()]
            if not results:
                results = [{"info": f"You are not currently eligible for any drives at {company}, or they are not visiting."}]
    
    elif intent == "UPCOMING_DRIVES":
        results = await fetch_upcoming_drives(db)
        
    elif intent == "COMPANY_FACT" and company:
        fact = await fetch_company_facts(db, company)
        results = [fact]
        
    elif intent == "DOCUMENT_QUERY":
        query = messages[-1].content
        docs = await search_knowledge_base(query)
        results = [{"knowledge_base_extracts": docs}]
        
    return {"eligibility_results": results}

async def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """Generates the final response based on intent and ground-truth data."""
    intent = state.get("intent")
    results = state.get("eligibility_results", [])
    messages = state["messages"]
    
    sys_prompt = f"""You are the College Placement Intelligence Platform assistant.
Your goal is to answer the user's question clearly and politely.

CURRENT INTENT: {intent}

GROUND TRUTH DATA:
{json.dumps(results, indent=2) if results else "No structured data available or required for this query."}

IMPORTANT RULES:
- If ground truth data is provided, YOU MUST base your answer strictly on it.
- Do NOT hallucinate eligibility, CTC, or package details.
- Be concise but helpful.
"""
    
    full_messages = [SystemMessage(content=sys_prompt)] + messages
    
    response = await llm_generator.ainvoke(full_messages)
    return {"messages": [response]}


def should_execute_tool(state: AgentState) -> str:
    """Conditional edge logic."""
    intent = state.get("intent")
    if intent in ["ELIGIBILITY_CHECK", "UPCOMING_DRIVES", "COMPANY_FACT", "DOCUMENT_QUERY"]:
        return "execute_tool"
    return "generate_response"


# Build the Graph
builder = StateGraph(AgentState)

builder.add_node("classify", classify_node)
builder.add_node("execute_tool", execute_tool_node)
builder.add_node("generate_response", generate_response_node)

builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",
    should_execute_tool,
    {
        "execute_tool": "execute_tool",
        "generate_response": "generate_response"
    }
)
builder.add_edge("execute_tool", "generate_response")
builder.add_edge("generate_response", END)

# Compile into a runnable
agent_app = builder.compile()
