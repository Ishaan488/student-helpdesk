from typing import List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.config import settings
from app.models.chat import Thread, ChatMessage

# Use the lighter, faster model for background summarization
summarizer_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.2,
    google_api_key=settings.GEMINI_API_KEY
)

async def summarize_and_update_thread(
    db: AsyncSession, 
    thread: Thread, 
    messages_to_summarize: List[ChatMessage]
) -> str:
    """
    Takes an existing Thread summary and a list of old messages that are 
    falling off the sliding window, and generates a new updated summary.
    Saves the new summary back to the database.
    
    This is an O(1) operation regarding token count because we only ever 
    process the delta (the new messages) against the existing summary.
    """
    
    # Format the old messages into a readable text block
    conversation_text = ""
    for msg in messages_to_summarize:
        role_label = "User" if msg.role == "human" else "AI Assistant"
        conversation_text += f"[{role_label}]: {msg.content}\n"
    
    current_summary = thread.summary or "No previous summary exists."
    
    prompt = f"""You are a memory-compression assistant for a College Placement Platform.
    
Here is the summary of the conversation so far:
<current_summary>
{current_summary}
</current_summary>

Here are the subsequent messages that just occurred in the chat:
<new_messages>
{conversation_text}
</new_messages>

Please write a new, consolidated summary that combines the old summary with the new messages. 
Keep it incredibly concise, factual, and strictly focused on what the user was asking about 
(e.g. which companies, which policies, their profile data). Do not include conversational filler.
"""

    response = await summarizer_llm.ainvoke([HumanMessage(content=prompt)])
    new_summary = response.content.strip()
    
    # Update the database
    thread.summary = new_summary
    await db.commit()
    
    return new_summary
