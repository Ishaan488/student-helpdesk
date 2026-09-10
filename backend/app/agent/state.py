import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    The state of the LangGraph agent for Chat Intelligence.
    This replaces a massive prompt with an explicitly typed memory store.
    """
    # LangGraph standard pattern: append new messages rather than overwrite
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Context
    current_user_id: UUID
    
    # Extracted metadata
    intent: Optional[str]
    extracted_company: Optional[str]
    
    # Ground-truth fetched from the structured data layer
    # We do NOT let the LLM guess this. The tools inject it here.
    eligibility_results: Optional[List[Dict[str, Any]]]
