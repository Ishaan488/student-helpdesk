"""
Database seeding script.

Populates the PostgreSQL database with realistic initial test data:
- TPO admin and students
- Tech & IT companies
- Placement drives with detailed roles and CTC
- Deterministic eligibility rules for each drive

Also runs a sample query and eligibility verification to confirm the database setup.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to sys.path so we can import 'app'
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.company import Company
from app.models.drive import PlacementDrive
from app.models.eligibility import EligibilityRule
from app.models.student import Student
from app.models.user import RoleEnum, User


async def seed_database():
    print("🌱 Connecting to database and starting seed process...")

    default_password = "password123"
    hashed_pwd = get_password_hash(default_password)

    async with async_session_factory() as session:
        # 1. Check if database already has data
        existing_users_res = await session.execute(select(User))
        existing_users = existing_users_res.scalars().all()
        if existing_users:
            print("⚠️  Database already contains users. Updating existing passwords to bcrypt hashes ('password123')...")
            for u in existing_users:
                u.hashed_password = hashed_pwd
            await session.commit()
            print(f"✅ Passwords updated to '{default_password}' for existing users.")
            return

        print("Creating users and student profiles...")

        # 2. Create Users & Students
        tpo_user = User(
            email="tpo.admin@college.edu",
            hashed_password=hashed_pwd,
            role=RoleEnum.TPO,
        )

        student_user_1 = User(
            email="aryan.sharma@college.edu",
            hashed_password=hashed_pwd,
            role=RoleEnum.STUDENT,
        )
        student_profile_1 = Student(
            user=student_user_1,
            college_id="CS2024001",
            branch="CSE",
            batch=2026,
            cgpa=8.85,
            active_backlogs=0,
            placement_status="UNPLACED",
        )

        student_user_2 = User(
            email="sneha.patel@college.edu",
            hashed_password=hashed_pwd,
            role=RoleEnum.STUDENT,
        )
        student_profile_2 = Student(
            user=student_user_2,
            college_id="EC2024042",
            branch="ECE",
            batch=2026,
            cgpa=7.20,
            active_backlogs=1,
            placement_status="UNPLACED",
        )

        session.add_all([tpo_user, student_user_1, student_profile_1, student_user_2, student_profile_2])
        await session.flush()

        print("Creating companies, placement drives, and eligibility rules...")

        # 3. Create Companies
        google = Company(
            name="Google",
            official_website="https://careers.google.com",
            industry="Technology / Software",
            description="Multinational technology company focusing on artificial intelligence, search engine, cloud computing, and computer software.",
        )

        tcs = Company(
            name="Tata Consultancy Services",
            official_website="https://www.tcs.com",
            industry="Information Technology & Consulting",
            description="Global leader in IT services, consulting, and business solutions.",
        )

        session.add_all([google, tcs])
        await session.flush()

        # 4. Create Placement Drives
        now = datetime.utcnow()

        google_drive = PlacementDrive(
            company_id=google.id,
            academic_year="2025-2026",
            role="Software Development Engineer (SDE-1)",
            ctc=28.5,
            location="Bangalore / Hyderabad",
            status="ACTIVE",
            registration_deadline=now + timedelta(days=14),
            test_date=now + timedelta(days=21),
            interview_date=now + timedelta(days=30),
        )

        tcs_drive = PlacementDrive(
            company_id=tcs.id,
            academic_year="2025-2026",
            role="Systems Engineer (Digital)",
            ctc=7.5,
            location="Pan-India",
            status="ACTIVE",
            registration_deadline=now + timedelta(days=10),
            test_date=now + timedelta(days=15),
            interview_date=now + timedelta(days=25),
        )

        session.add_all([google_drive, tcs_drive])
        await session.flush()

        # 5. Create Deterministic Eligibility Rules
        google_rule = EligibilityRule(
            placement_drive_id=google_drive.id,
            minimum_cgpa=8.0,
            maximum_active_backlogs=0,
            allowed_branches=["CSE", "IT"],
            additional_conditions="Must have cleared 10th and 12th with >= 75%.",
        )

        tcs_rule = EligibilityRule(
            placement_drive_id=tcs_drive.id,
            minimum_cgpa=6.5,
            maximum_active_backlogs=1,
            allowed_branches=["CSE", "ECE", "IT", "MECH", "CIVIL"],
            additional_conditions="No year drops during graduation.",
        )

        session.add_all([google_rule, tcs_rule])
        await session.commit()

        print("✅ Database seeding completed successfully!\n")


async def verify_seeded_data():
    """Reads back the data and demonstrates the deterministic rules logic."""
    print("=" * 60)
    print("🔍 VERIFYING SEEDED DATA & RELATIONSHIPS")
    print("=" * 60)

    async with async_session_factory() as session:
        # Fetch drives with company and eligibility rule
        stmt = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_rule),
            )
        )
        result = await session.execute(stmt)
        drives = result.scalars().all()

        # Fetch students with user info
        students_stmt = select(Student).options(selectinload(Student.user))
        students = (await session.execute(students_stmt)).scalars().all()

        print(f"\n📋 Active Placement Drives ({len(drives)} found):")
        for drive in drives:
            rule = drive.eligibility_rule
            print(f"  • {drive.company.name} — {drive.role} (CTC: {drive.ctc} LPA)")
            print(f"    - Min CGPA: {rule.minimum_cgpa}")
            print(f"    - Max Backlogs: {rule.maximum_active_backlogs}")
            print(f"    - Allowed Branches: {', '.join(rule.allowed_branches)}")

        print(f"\n🎓 Registered Students ({len(students)} found):")
        for st in students:
            print(f"  • {st.college_id} ({st.user.email}) — Branch: {st.branch}, CGPA: {st.cgpa}, Backlogs: {st.active_backlogs}")

        print("\n" + "=" * 60)
        print("⚡ PREVIEW: DETERMINISTIC ELIGIBILITY EVALUATION")
        print("=" * 60)

        # Show how the Database/Rules Engine acts as the source of truth
        for drive in drives:
            rule = drive.eligibility_rule
            print(f"\nTarget Drive: {drive.company.name} ({drive.role})")
            for st in students:
                is_eligible = True
                reasons = []

                if st.cgpa < rule.minimum_cgpa:
                    is_eligible = False
                    reasons.append(f"CGPA {st.cgpa} < {rule.minimum_cgpa}")
                if st.active_backlogs > rule.maximum_active_backlogs:
                    is_eligible = False
                    reasons.append(f"Backlogs {st.active_backlogs} > {rule.maximum_active_backlogs}")
                if st.branch not in rule.allowed_branches:
                    is_eligible = False
                    reasons.append(f"Branch '{st.branch}' not in {rule.allowed_branches}")

                status_tag = "✅ ELIGIBLE" if is_eligible else "❌ NOT ELIGIBLE"
                reason_str = f" [Reasons: {', '.join(reasons)}]" if reasons else ""
                print(f"  - Student {st.college_id} ({st.user.email}): {status_tag}{reason_str}")

    print("\n" + "=" * 60)


async def main():
    await seed_database()
    await verify_seeded_data()


if __name__ == "__main__":
    asyncio.run(main())
