from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.config import settings

# LangChain uses the fast/cheap model for intent classification
# We use gemini-1.5-flash-latest for speed and low cost
llm_router = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", 
    temperature=0.0,
    google_api_key=settings.GEMINI_API_KEY
)


class IntentClassification(BaseModel):
    """Structured output for intent routing."""
    intent: Literal["ELIGIBILITY_CHECK", "UPCOMING_DRIVES", "COMPANY_FACT", "GENERAL_CHAT"] = Field(
        description="The primary intent of the user's message."
    )
    extracted_company: str = Field(
        default="", 
        description="If the user is asking about a specific company, extract its name here. Otherwise leave empty."
    )


router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the intelligent router for a College Placement chatbot.
Classify the user's latest query into one of these intents:
1. ELIGIBILITY_CHECK: The user wants to know if they can apply to a drive, or what drives they are eligible for.
2. UPCOMING_DRIVES: The user is asking what companies are coming to campus generally.
3. COMPANY_FACT: The user wants to know details about a specific company (e.g. what does Google do, what is TCS package).
4. GENERAL_CHAT: Anything else (greetings, unrelated questions).

If they mention a specific company, extract its name."""),
    ("user", "{messages}")
])

intent_chain = router_prompt | llm_router.with_structured_output(IntentClassification)


async def classify_intent(messages: list[BaseMessage]) -> IntentClassification:
    """
    Invokes the LLM to classify the user's intent based on conversation history.
    """
    # Only pass the last 3 messages to save tokens on routing
    recent_messages = messages[-3:] if len(messages) > 3 else messages
    
    # We must format messages to strings for the prompt template or pass them directly
    # ChatPromptTemplate handles list of BaseMessages if passed correctly, but to be safe:
    formatted_chat = "\n".join([f"{m.type}: {m.content}" for m in recent_messages])
    
    result = await intent_chain.ainvoke({"messages": formatted_chat})
    return result
