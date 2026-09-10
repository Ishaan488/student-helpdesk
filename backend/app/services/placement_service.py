from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.drive import PlacementDrive
from app.models.student import Student
from app.schemas.eligibility import EligibilityEvaluationResult
from app.services.rules_engine import RulesEngine


class PlacementService:
    @staticmethod
    async def get_drives(
        db: AsyncSession, status: Optional[str] = None
    ) -> List[PlacementDrive]:
        query = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_rule),
            )
            .order_by(PlacementDrive.created_at.desc())
        )
        if status:
            query = query.where(PlacementDrive.status == status)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_drive_by_id(
        db: AsyncSession, drive_id: UUID
    ) -> Optional[PlacementDrive]:
        query = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_rule),
            )
            .where(PlacementDrive.id == drive_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_companies(db: AsyncSession) -> List[Company]:
        query = select(Company).order_by(Company.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_company_by_id(
        db: AsyncSession, company_id: UUID
    ) -> Optional[Company]:
        query = select(Company).where(Company.id == company_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_students(db: AsyncSession) -> List[Student]:
        query = (
            select(Student)
            .options(selectinload(Student.user))
            .order_by(Student.college_id.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_student_by_id(
        db: AsyncSession, student_id: UUID
    ) -> Optional[Student]:
        query = (
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id == student_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def evaluate_student_for_drive(
        db: AsyncSession, drive_id: UUID, student_id: UUID
    ) -> Optional[EligibilityEvaluationResult]:
        drive = await PlacementService.get_drive_by_id(db, drive_id)
        if not drive or not drive.eligibility_rule:
            return None

        student = await PlacementService.get_student_by_id(db, student_id)
        if not student:
            return None

        return RulesEngine.evaluate(
            student=student, rule=drive.eligibility_rule, drive_id=drive.id
        )

    @staticmethod
    async def get_eligible_drives_for_student(
        db: AsyncSession, student_id: UUID
    ) -> Optional[List[PlacementDrive]]:
        student = await PlacementService.get_student_by_id(db, student_id)
        if not student:
            return None

        all_drives = await PlacementService.get_drives(db)
        eligible_drives: List[PlacementDrive] = []

        for drive in all_drives:
            if drive.eligibility_rule:
                eval_res = RulesEngine.evaluate(
                    student=student, rule=drive.eligibility_rule, drive_id=drive.id
                )
                if eval_res.is_eligible:
                    eligible_drives.append(drive)

        return eligible_drives
