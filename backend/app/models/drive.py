from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlacementDrive(Base):
    """
    A specific recruitment drive conducted by a company in a given academic year.
    """
    __tablename__ = "placement_drives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    academic_year = Column(String(20), nullable=False)  # e.g., "2025-2026"
    role = Column(String(100), nullable=False)
    ctc = Column(Float, nullable=True)  # Using float for LPA
    location = Column(String(100), nullable=True)
    
    status = Column(String(50), default="UPCOMING", nullable=False)  # UPCOMING, ACTIVE, COMPLETED
    
    registration_deadline = Column(DateTime, nullable=True)
    test_date = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="drives")
    eligibility_rule = relationship("EligibilityRule", back_populates="drive", uselist=False)
