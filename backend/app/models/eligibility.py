import json
from uuid import uuid4

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, JSON

from app.core.database import Base


class StringArray(TypeDecorator):
    """
    Custom type that maps to postgresql.ARRAY(String) on Postgres
    and JSON on SQLite (for testing).
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.loads(value)
        return value


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
    
    # ARRAY requires PostgreSQL specific dialect, we use custom StringArray for SQLite testing support
    allowed_branches = Column(StringArray, nullable=False)
    
    additional_conditions = Column(Text, nullable=True)

    # Relationships
    drive = relationship("PlacementDrive", back_populates="eligibility_rule")
