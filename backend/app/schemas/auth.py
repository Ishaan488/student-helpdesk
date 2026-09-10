from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.student import StudentResponse


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # User ID as string
    email: str
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class StudentRegister(BaseModel):
    email: EmailStr
    password: str
    college_id: str
    branch: str
    batch: int
    cgpa: float
    active_backlogs: int = 0


class CurrentUserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    student_profile: Optional[StudentResponse] = None

    model_config = ConfigDict(from_attributes=True)
