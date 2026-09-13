import json
import time
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
    temperature=0.0,
    google_api_key=settings.GEMINI_API_KEY
)

async def classify_node(state: AgentState) -> Dict[str, Any]:
    """Uses LLM to classify the intent of the user's message."""
    start_time = time.time()
    classification = await classify_intent(state["messages"])
    duration = int((time.time() - start_time) * 1000)
    
    trace = state.get("trace", [])
    trace.append("classify_node")
    
    debug_log = state.get("debug_log", {})
    debug_log["classify_node"] = {
        "latency_ms": duration,
        "classified_intent": classification.intent,
        "extracted_company": classification.extracted_company,
        "action": "Routing to execute_tool_node" if classification.intent != "UNKNOWN" else "Routing to generate_response_node"
    }

    return {
        "intent": classification.intent,
        "extracted_company": classification.extracted_company,
        "trace": trace,
        "debug_log": debug_log
    }

async def execute_tool_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Executes the appropriate tool based on intent."""
    start_time = time.time()
    intent = state["intent"]
    company = state.get("extracted_company")
    messages = state["messages"]
    user_id = state.get("current_user_id")
    db = config["configurable"]["db"]
    
    results = []
    raw_query = None

    if intent == "ELIGIBILITY_CHECK" and user_id:
        tool_res = await fetch_student_eligibility(db, user_id)
        results = tool_res.get("data", [])
        raw_query = tool_res.get("query")
    elif intent == "UPCOMING_DRIVES":
        tool_res = await fetch_upcoming_drives(db)
        results = tool_res.get("data", [])
        raw_query = tool_res.get("query")
    elif intent == "COMPANY_FACT" and company:
        tool_res = await fetch_company_facts(db, company)
        results = tool_res.get("data", [])
        raw_query = tool_res.get("query")
    elif intent == "DOCUMENT_QUERY":
        query = messages[-1].content
        user_role = state.get("current_user_role", "ALL")
        docs = await search_knowledge_base(query, user_role)
        results = [{"knowledge_base_extracts": docs}]
        raw_query = f"FAISS Vector Search\nQuery: {query}\nRole Filter: {user_role}\nMetric: L2 Cosine Distance"
        
    duration = int((time.time() - start_time) * 1000)
    
    trace = state.get("trace", [])
    trace.append("execute_tool_node")
    
    debug_log = state.get("debug_log", {})
    debug_log["execute_tool_node"] = {
        "latency_ms": duration,
        "action": f"Executed tool for intent: {intent}",
        "raw_query": raw_query,
        "raw_payload": results
    }
        
    return {"eligibility_results": results, "trace": trace, "debug_log": debug_log}

async def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Evaluates the retrieved FAISS chunks to ensure no sensitive data leaks."""
    start_time = time.time()
    intent = state.get("intent")
    user_role = state.get("current_user_role", "ALL")
    results = state.get("eligibility_results", [])
    
    # We only guardrail DOCUMENT_QUERY (FAISS retrieval)
    if intent != "DOCUMENT_QUERY" or not results:
        return {"is_safe": True}
        
    extracted_text = json.dumps(results)
    
    # Fast, cheap evaluator prompt
    eval_llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0.0,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    prompt = f"""You are a strict security evaluator.
A user with role [{user_role}] is about to see the following retrieved database chunks.

CHUNKS:
{extracted_text}

Task: Does this text contain strictly confidential administrative, faculty, or TPO-only data that a {user_role} should NOT see? 
Answer with a single word: YES or NO."""

    eval_res = await eval_llm.ainvoke(prompt)
    is_safe = "YES" not in eval_res.content.upper()
    
    duration = int((time.time() - start_time) * 1000)
    trace = state.get("trace", [])
    trace.append("guardrail_node")
    
    debug_log = state.get("debug_log", {})
    debug_log["guardrail_node"] = {
        "latency_ms": duration,
        "is_safe": is_safe,
        "eval_response": eval_res.content
    }
    
    return {"is_safe": is_safe, "trace": trace, "debug_log": debug_log}

async def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """Generates the final response based on intent and ground-truth data."""
    intent = state.get("intent")
    results = state.get("eligibility_results", [])
    messages = state["messages"]
    
    is_safe = state.get("is_safe", True)
    
    if not is_safe:
        sys_prompt = "The user queried confidential information that they are not authorized to see. Politely refuse to answer the question citing security policies."
    else:
        sys_prompt = f"""You are the College Placement Intelligence Platform assistant.
Your goal is to answer the user's question clearly and politely.

CURRENT INTENT: {intent}

GROUND TRUTH DATA:
{json.dumps(results, indent=2) if results else "No structured data available or required for this query."}
"""

        summary = state.get("summary")
        if summary:
            sys_prompt += f"\nPREVIOUS CONVERSATION SUMMARY:\n{summary}\n"

        sys_prompt += """
IMPORTANT RULES:
- If ground truth data is provided, YOU MUST base your answer strictly on it.
- Do NOT hallucinate eligibility, CTC, or package details.
- Be concise but helpful.
"""
    
    full_messages = [SystemMessage(content=sys_prompt)] + list(messages)
    # Execute the LLM
    start_time = time.time()
    response = await llm_generator.ainvoke(full_messages)
    duration = int((time.time() - start_time) * 1000)
    
    trace = state.get("trace", [])
    trace.append("generate_response_node")
    
    # Extract token usage safely
    tokens = response.response_metadata.get("token_usage", {}) if hasattr(response, "response_metadata") else {}
    prompt_tokens = tokens.get("prompt_token_count", "N/A")
    completion_tokens = tokens.get("candidates_token_count", "N/A")
    
    debug_log = state.get("debug_log", {})
    debug_log["generate_response_node"] = {
        "latency_ms": duration,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "system_prompt": sys_prompt,
        "model": "gemini-3.6-flash",
        "temperature": 0.0
    }
    
    return {"messages": [response], "trace": trace, "debug_log": debug_log}


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
builder.add_node("guardrail", guardrail_node)
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
builder.add_edge("execute_tool", "guardrail")
builder.add_edge("guardrail", "generate_response")
builder.add_edge("generate_response", END)

# Compile into a runnable
agent_app = builder.compile()
