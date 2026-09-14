import pytest
from app.agent.state import AgentState
from app.agent.graph import classify_node
from langchain_core.messages import HumanMessage
import uuid

@pytest.mark.asyncio
async def test_router_eligibility_intent():
    """Test that the router correctly identifies an eligibility question."""
    # We construct a minimal AgentState
    state = AgentState(
        messages=[HumanMessage(content="Am I eligible for Google?")],
        intent="",
        eligibility_results=[],
        context_used=[],
        user_id=str(uuid.uuid4()),
        extracted_company=None,
        trace=[],
        is_safe=True
    )
    
    # We pass the state to the node function directly
    result = await classify_node(state)
    
    assert "intent" in result
    assert result["intent"] == "ELIGIBILITY_CHECK"
    assert "trace" in result
    assert "classify_node" in result["trace"]

@pytest.mark.asyncio
async def test_router_upcoming_drives_intent():
    """Test that the router correctly identifies a query about upcoming placement drives."""
    state = AgentState(
        messages=[HumanMessage(content="What are the upcoming companies visiting campus?")],
        intent="",
        eligibility_results=[],
        context_used=[],
        user_id=str(uuid.uuid4()),
        extracted_company=None,
        trace=[],
        is_safe=True
    )
    
    result = await classify_node(state)
    
    assert "intent" in result
    assert result["intent"] == "UPCOMING_DRIVES"

@pytest.mark.asyncio
async def test_router_out_of_scope_intent():
    """Test that the router correctly identifies an out of scope question."""
    state = AgentState(
        messages=[HumanMessage(content="Write a python script to sort an array.")],
        intent="",
        eligibility_results=[],
        context_used=[],
        user_id=str(uuid.uuid4()),
        extracted_company=None,
        trace=[],
        is_safe=True
    )
    
    result = await classify_node(state)
    
    assert "intent" in result
    assert result["intent"] == "OUT_OF_SCOPE"

@pytest.mark.asyncio
async def test_router_escalation_intent():
    """Test that the router correctly identifies an escalation request."""
    state = AgentState(
        messages=[HumanMessage(content="I want to talk to a human admin right now.")],
        intent="",
        eligibility_results=[],
        context_used=[],
        user_id=str(uuid.uuid4()),
        extracted_company=None,
        trace=[],
        is_safe=True
    )
    
    result = await classify_node(state)
    
    assert "intent" in result
    assert result["intent"] == "ESCALATE_TO_ADMIN"
