from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSummary(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class StudentBase(BaseModel):
    college_id: str
    branch: str
    batch: int
    cgpa: float
    active_backlogs: int = 0
    placement_status: str = "UNPLACED"


class StudentCreate(StudentBase):
    user_id: UUID

class StudentUpdate(BaseModel):
    branch: Optional[str] = None
    batch: Optional[int] = None
    cgpa: Optional[float] = None
    active_backlogs: Optional[int] = None


class StudentResponse(StudentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    user: Optional[UserSummary] = None

    model_config = ConfigDict(from_attributes=True)
