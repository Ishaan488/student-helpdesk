from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EscalatedQuery(Base):
    """
    Represents a query that the AI could not answer and was escalated to human administration (HITL).
    """
    __tablename__ = "escalated_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    query_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN")  # OPEN, RESOLVED
    admin_reply = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    thread = relationship("Thread")
    user = relationship("User")
