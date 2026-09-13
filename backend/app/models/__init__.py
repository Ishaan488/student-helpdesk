"""
Import all models here.

This is critical for Alembic autogenerate.
Alembic imports Base from app.core.database, but it won't know about 
these tables unless they are imported somewhere before Alembic runs.
"""

from app.models.chat import ChatMessage, Thread
from app.models.company import Company
from app.models.document import KnowledgeDocument
from app.models.drive import PlacementDrive
from app.models.eligibility import EligibilityRule
from app.models.historical import HistoricalDrive, HistoricalStudentOutcome, YearlyBatchSummary
from app.models.student import Student
from app.models.user import User

__all__ = [
    "User", "Student", "Company", "PlacementDrive", "EligibilityRule",
    "KnowledgeDocument", "Thread", "ChatMessage",
    "HistoricalDrive", "HistoricalStudentOutcome", "YearlyBatchSummary",
]
