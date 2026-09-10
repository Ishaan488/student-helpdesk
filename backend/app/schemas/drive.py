from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.company import CompanyResponse
from app.schemas.eligibility import EligibilityRuleResponse


class PlacementDriveBase(BaseModel):
    academic_year: str
    role: str
    ctc: Optional[float] = None
    location: Optional[str] = None
    status: str = "UPCOMING"
    registration_deadline: Optional[datetime] = None
    test_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None


class PlacementDriveCreate(PlacementDriveBase):
    company_id: UUID


class PlacementDriveResponse(PlacementDriveBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    company: Optional[CompanyResponse] = None
    eligibility_rule: Optional[EligibilityRuleResponse] = None

    model_config = ConfigDict(from_attributes=True)
