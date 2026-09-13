"""
Historical Placement Data Models.

These models store 10+ years of anonymized placement statistics,
enabling the AI agent to answer complex analytical queries via SQL.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class HistoricalDrive(Base):
    """Tracks every company drive that visited campus, per branch, per year."""
    __tablename__ = "historical_drives"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(Integer, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    industry = Column(String, nullable=False)
    job_role = Column(String, nullable=False)
    offer_type = Column(String, nullable=False)  # Full-Time, Internship
    branches_eligible = Column(String, nullable=False)
    min_cgpa_required = Column(Float, nullable=False)
    backlog_allowed = Column(Boolean, nullable=False, default=False)
    bond_years = Column(Integer, nullable=False, default=0)
    job_location = Column(String, nullable=False)
    selection_rounds = Column(String, nullable=False)
    visit_month = Column(String, nullable=False)
    branch = Column(String, nullable=False, index=True)
    funnel_applied = Column(Integer, nullable=False)
    funnel_shortlisted = Column(Integer, nullable=False)
    funnel_interviewed = Column(Integer, nullable=False)
    funnel_selected = Column(Integer, nullable=False)
    ctc_offered_lpa = Column(Float, nullable=False)


class HistoricalStudentOutcome(Base):
    """Anonymized student-level placement results."""
    __tablename__ = "historical_student_outcomes"

    student_id = Column(String, primary_key=True)
    academic_year = Column(Integer, nullable=False, index=True)
    branch = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    had_backlogs = Column(Boolean, nullable=False, default=False)
    placed = Column(Boolean, nullable=False, default=False)
    total_offers_received = Column(Integer, nullable=False, default=0)
    highest_ctc_lpa = Column(Float, nullable=False, default=0.0)
    company_joined = Column(String, nullable=True)


class YearlyBatchSummary(Base):
    """Pre-aggregated batch-level placement statistics."""
    __tablename__ = "yearly_batch_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(Integer, nullable=False, index=True)
    branch = Column(String, nullable=False, index=True)
    total_students = Column(Integer, nullable=False)
    total_placed = Column(Integer, nullable=False)
    total_unplaced = Column(Integer, nullable=False)
    placement_percentage = Column(Float, nullable=False)
    highest_ctc_lpa = Column(Float, nullable=False)
    average_ctc_lpa = Column(Float, nullable=False)
    median_ctc_lpa = Column(Float, nullable=False)
    total_companies_visited = Column(Integer, nullable=False)
