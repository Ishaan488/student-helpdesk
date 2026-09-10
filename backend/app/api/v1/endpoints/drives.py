from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.drive import PlacementDriveResponse
from app.schemas.eligibility import EligibilityEvaluationResult
from app.services.placement_service import PlacementService

router = APIRouter()


@router.get(
    "/",
    response_model=List[PlacementDriveResponse],
    summary="List all placement drives",
    description="Retrieve a list of placement drives, optionally filtered by status.",
)
async def list_drives(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await PlacementService.get_drives(db, status=status_filter)


@router.get(
    "/{drive_id}",
    response_model=PlacementDriveResponse,
    summary="Get drive by ID",
    description="Retrieve detailed information about a placement drive including company and eligibility criteria.",
)
async def get_drive(
    drive_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    drive = await PlacementService.get_drive_by_id(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement drive with ID '{drive_id}' not found.",
        )
    return drive


@router.get(
    "/{drive_id}/eligibility/{student_id}",
    response_model=EligibilityEvaluationResult,
    summary="Check student eligibility for a drive",
    description="Deterministically evaluates whether a student meets the criteria for this drive using the Rules Engine.",
)
async def check_drive_eligibility(
    drive_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await PlacementService.evaluate_student_for_drive(
        db, drive_id=drive_id, student_id=student_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive or Student not found, or drive has no configured eligibility rules.",
        )
    return result
