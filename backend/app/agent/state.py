from typing import TypedDict, Annotated, Sequence, Any, Dict, List
from langchain_core.messages import BaseMessage
import operator
from uuid import UUID

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_user_id: UUID | None
    intent: str | None
    extracted_company: str | None
    eligibility_results: List[Dict[str, Any]] | None
    trace: List[str]
    debug_log: Dict[str, Any]
