from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RoleEnum
from app.core.dependencies import get_db, get_current_user
from app.schemas.drive import PlacementDriveResponse
from app.schemas.student import StudentResponse, StudentUpdate
from app.services.placement_service import PlacementService

router = APIRouter()

@router.put(
    "/me",
    response_model=StudentResponse,
    summary="Update student profile",
    description="Update the authenticated student's profile details.",
)
async def update_my_profile(
    profile_data: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != RoleEnum.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can update their profiles.")
        
    from sqlalchemy import select
    from app.models.student import Student
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    if profile_data.branch is not None:
        student.branch = profile_data.branch
    if profile_data.batch is not None:
        student.batch = profile_data.batch
    if profile_data.cgpa is not None:
        student.cgpa = profile_data.cgpa
    if profile_data.active_backlogs is not None:
        student.active_backlogs = profile_data.active_backlogs
        
    await db.commit()
    await db.refresh(student)
    return student


@router.get(
    "/",
    response_model=List[StudentResponse],
    summary="List all student profiles",
    description="Retrieve all registered student profiles with account information.",
)
async def list_students(
    db: AsyncSession = Depends(get_db),
):
    return await PlacementService.get_students(db)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get student profile",
    description="Retrieve full profile details for a specific student.",
)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    student = await PlacementService.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found.",
        )
    return student


@router.get(
    "/{student_id}/eligible-drives",
    response_model=List[PlacementDriveResponse],
    summary="List all eligible drives for student",
    description="Evaluates all active placement drives against this student's profile via the Rules Engine and returns eligible drives.",
)
async def list_eligible_drives(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    drives = await PlacementService.get_eligible_drives_for_student(db, student_id)
    if drives is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found.",
        )
    return drives
