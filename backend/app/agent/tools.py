from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.drive import PlacementDrive
from app.services.placement_service import PlacementService


async def fetch_student_eligibility(db: AsyncSession, student_id: UUID) -> List[Dict[str, Any]]:
    """
    Deterministically fetches all drives a student is eligible for.
    Used by the Agent graph to inject ground-truth before the LLM generates a response.
    """
    drives = await PlacementService.get_eligible_drives_for_student(db, student_id)
    if drives is None:
        return [{"error": "Student profile not found. Are you an admin or TPO?"}]

    results = []
    for d in drives:
        results.append({
            "company": d.company.name if d.company else "Unknown",
            "role": d.role,
            "ctc": f"{d.ctc} LPA" if d.ctc else "Not specified",
            "location": d.location,
            "status": d.status
        })
    return results


async def fetch_upcoming_drives(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetches all upcoming placement drives regardless of eligibility.
    """
    drives = await PlacementService.get_drives(db, status="UPCOMING")
    results = []
    for d in drives:
        results.append({
            "company": d.company.name if d.company else "Unknown",
            "role": d.role,
            "ctc": f"{d.ctc} LPA" if d.ctc else "Not specified",
            "deadline": d.registration_deadline.isoformat() if d.registration_deadline else "TBD"
        })
    return results


async def fetch_company_facts(db: AsyncSession, company_name: str) -> Dict[str, Any]:
    """
    Fetches details about a specific company.
    """
    query = select(Company).where(Company.name.ilike(f"%{company_name}%")).limit(1)
    res = await db.execute(query)
    company = res.scalar_one_or_none()
    
    if not company:
        return {"error": f"No information found for company '{company_name}'."}
        
    return {
        "name": company.name,
        "industry": company.industry,
        "description": company.description,
        "website": company.official_website
    }
