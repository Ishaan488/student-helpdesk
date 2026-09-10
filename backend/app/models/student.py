from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    """
    Domain-specific entity for students.
    Linked 1-to-1 with User.
    """
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    college_id = Column(String(50), unique=True, index=True, nullable=False)
    branch = Column(String(50), nullable=False)
    batch = Column(Integer, nullable=False)  # e.g., 2026
    
    # Eligibility Data
    cgpa = Column(Float, nullable=False, default=0.0)
    active_backlogs = Column(Integer, nullable=False, default=0)
    
    placement_status = Column(String(50), default="UNPLACED", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")
