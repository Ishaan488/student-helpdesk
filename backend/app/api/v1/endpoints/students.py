from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.drive import PlacementDriveResponse
from app.schemas.student import StudentResponse
from app.services.placement_service import PlacementService

router = APIRouter()


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
