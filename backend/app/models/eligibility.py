from uuid import uuid4

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EligibilityRule(Base):
    """
    Deterministic rules for determining if a student can apply for a placement drive.
    The Rules Engine will consume this data.
    """
    __tablename__ = "eligibility_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    placement_drive_id = Column(UUID(as_uuid=True), ForeignKey("placement_drives.id"), unique=True, nullable=False)
    
    minimum_cgpa = Column(Float, nullable=False, default=0.0)
    maximum_active_backlogs = Column(Integer, nullable=False, default=0)
    
    # ARRAY requires PostgreSQL specific dialect
    allowed_branches = Column(ARRAY(String), nullable=False)
    
    additional_conditions = Column(Text, nullable=True)

    # Relationships
    drive = relationship("PlacementDrive", back_populates="eligibility_rule")
