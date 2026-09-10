from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EligibilityRuleBase(BaseModel):
    minimum_cgpa: float
    maximum_active_backlogs: int
    allowed_branches: List[str]
    additional_conditions: Optional[str] = None


class EligibilityRuleCreate(EligibilityRuleBase):
    pass


class EligibilityRuleResponse(EligibilityRuleBase):
    id: UUID
    placement_drive_id: UUID

    model_config = ConfigDict(from_attributes=True)


class EligibilityEvaluationResult(BaseModel):
    student_id: UUID
    drive_id: UUID
    is_eligible: bool
    reasons: List[str]
