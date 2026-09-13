"""
Loads the generated historical CSV data into the PostgreSQL database.
Run: python scripts/load_historical_data.py
"""

import asyncio
import csv
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import 'app'
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, delete

from app.core.database import async_session_factory
from app.models.historical import HistoricalDrive, HistoricalStudentOutcome, YearlyBatchSummary


async def load_data():
    print("Connecting to database and starting historical data load...")

    data_dir = backend_dir / "data"
    drives_csv = data_dir / "historical_drives.csv"
    students_csv = data_dir / "historical_student_outcomes.csv"
    summary_csv = data_dir / "historical_batch_summary.csv"

    if not drives_csv.exists():
        print(f"Error: {drives_csv} not found. Did you run generate_historical_data.py?")
        return

    async with async_session_factory() as session:
        print("Clearing existing historical data...")
        await session.execute(delete(YearlyBatchSummary))
        await session.execute(delete(HistoricalStudentOutcome))
        await session.execute(delete(HistoricalDrive))
        await session.commit()

        # 1. Load Drives
        print("Loading Drives...")
        drives = []
        with open(drives_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                drives.append(HistoricalDrive(
                    id=int(row["id"]),
                    academic_year=int(row["academic_year"]),
                    company_name=row["company_name"],
                    industry=row["industry"],
                    job_role=row["job_role"],
                    offer_type=row["offer_type"],
                    branches_eligible=row["branches_eligible"],
                    min_cgpa_required=float(row["min_cgpa_required"]),
                    backlog_allowed=row["backlog_allowed"] == "True",
                    bond_years=int(row["bond_years"]),
                    job_location=row["job_location"],
                    selection_rounds=row["selection_rounds"],
                    visit_month=row["visit_month"],
                    branch=row["branch"],
                    funnel_applied=int(row["funnel_applied"]),
                    funnel_shortlisted=int(row["funnel_shortlisted"]),
                    funnel_interviewed=int(row["funnel_interviewed"]),
                    funnel_selected=int(row["funnel_selected"]),
                    ctc_offered_lpa=float(row["ctc_offered_lpa"]),
                ))
        session.add_all(drives)
        await session.commit()
        print(f"Loaded {len(drives)} drives.")

        # 2. Load Student Outcomes (Chunked for memory efficiency)
        print("Loading Student Outcomes...")
        students = []
        with open(students_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                students.append(HistoricalStudentOutcome(
                    student_id=row["student_id"],
                    academic_year=int(row["academic_year"]),
                    branch=row["branch"],
                    gender=row["gender"],
                    cgpa=float(row["cgpa"]),
                    had_backlogs=row["had_backlogs"] == "True",
                    placed=row["placed"] == "True",
                    total_offers_received=int(row["total_offers_received"]),
                    highest_ctc_lpa=float(row["highest_ctc_lpa"]),
                    company_joined=row["company_joined"] if row["company_joined"] else None,
                ))
                
                # Commit in chunks of 2000
                if len(students) >= 2000:
                    session.add_all(students)
                    await session.commit()
                    students = []

        if students:
            session.add_all(students)
            await session.commit()
        print(f"Loaded student outcomes.")

        # 3. Load Batch Summary
        print("Loading Batch Summary...")
        summaries = []
        with open(summary_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                summaries.append(YearlyBatchSummary(
                    academic_year=int(row["academic_year"]),
                    branch=row["branch"],
                    total_students=int(row["total_students"]),
                    total_placed=int(row["total_placed"]),
                    total_unplaced=int(row["total_unplaced"]),
                    placement_percentage=float(row["placement_percentage"]),
                    highest_ctc_lpa=float(row["highest_ctc_lpa"]),
                    average_ctc_lpa=float(row["average_ctc_lpa"]),
                    median_ctc_lpa=float(row["median_ctc_lpa"]),
                    total_companies_visited=int(row["total_companies_visited"]),
                ))
        session.add_all(summaries)
        await session.commit()
        print(f"Loaded {len(summaries)} summaries.")

    print("✅ All historical data successfully loaded into PostgreSQL!")


if __name__ == "__main__":
    asyncio.run(load_data())
