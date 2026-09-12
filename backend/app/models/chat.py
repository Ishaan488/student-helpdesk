from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Thread(Base):
    """
    Represents a single conversation thread for a specific user.
    Holds the rolling summary of the conversation to prevent context bloat.
    """
    __tablename__ = "threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Title could be auto-generated based on first message, but we'll leave it simple for now
    title = Column(String(255), nullable=True, default="New Conversation")
    
    # The running summary of all messages that have fallen off the sliding window
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="thread", order_by="ChatMessage.created_at.asc()", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    An individual message within a conversation thread.
    Role will be 'human' or 'ai'.
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, index=True)
    
    role = Column(String(50), nullable=False)  # e.g., 'human' or 'ai'
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    thread = relationship("Thread", back_populates="messages")
