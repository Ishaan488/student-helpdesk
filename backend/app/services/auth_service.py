from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.models.student import Student
from app.models.user import RoleEnum, User
from app.schemas.auth import StudentRegister, AdminRegister


class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        query = (
            select(User)
            .options(selectinload(User.student_profile))
            .where(User.email == email)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def register_student(
        db: AsyncSession, student_in: StudentRegister
    ) -> User:
        # Check if email is already taken
        user_check = await db.execute(select(User).where(User.email == student_in.email))
        if user_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        # Check if college_id is already taken
        student_check = await db.execute(
            select(Student).where(Student.college_id == student_in.college_id)
        )
        if student_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this College ID already exists.",
            )

        # Create user
        new_user = User(
            email=student_in.email,
            hashed_password=get_password_hash(student_in.password),
            role=RoleEnum.STUDENT,
        )
        db.add(new_user)
        await db.flush()  # Generates new_user.id

        # Create student profile
        new_student = Student(
            user_id=new_user.id,
            college_id=student_in.college_id,
            branch=student_in.branch,
            batch=student_in.batch,
            cgpa=student_in.cgpa,
            active_backlogs=student_in.active_backlogs,
        )
        db.add(new_student)
        await db.commit()
        # Reload with profile
        query = (
            select(User)
            .options(selectinload(User.student_profile))
            .where(User.id == new_user.id)
        )
        result = await db.execute(query)
        return result.scalar_one()


    @staticmethod
    async def register_admin(
        db: AsyncSession, admin_in: AdminRegister
    ) -> User:
        user_check = await db.execute(select(User).where(User.email == admin_in.email))
        if user_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        new_user = User(
            email=admin_in.email,
            hashed_password=get_password_hash(admin_in.password),
            role=RoleEnum.ADMIN,
        )
        db.add(new_user)
        await db.commit()
        
        query = (
            select(User)
            .options(selectinload(User.student_profile))
            .where(User.id == new_user.id)
        )
        result = await db.execute(query)
        return result.scalar_one()
