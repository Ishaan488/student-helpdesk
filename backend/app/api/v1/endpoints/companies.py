from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.company import CompanyResponse
from app.services.placement_service import PlacementService

router = APIRouter()


@router.get(
    "/",
    response_model=List[CompanyResponse],
    summary="List all visiting companies",
    description="Retrieve list of all registered recruiting companies.",
)
async def list_companies(
    db: AsyncSession = Depends(get_db),
):
    return await PlacementService.get_companies(db)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get company profile",
    description="Retrieve details for a specific recruiting company.",
)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    company = await PlacementService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found.",
        )
    return company
