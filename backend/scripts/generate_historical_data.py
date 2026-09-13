"""
Historical Placement Data Generator
====================================
Generates realistic synthetic placement data for 10 years (2015-2024).
Produces 3 CSV files matching our finalized schema:
  1. historical_drives.csv
  2. historical_student_outcomes.csv
  3. yearly_batch_summary.csv

Run: python scripts/generate_historical_data.py
Output: backend/data/*.csv
"""

import os
import random
import math
import csv
from collections import defaultdict

# Seed for reproducibility
random.seed(42)

# ============================================================
# CONFIGURATION: Realistic Company Profiles
# ============================================================

BRANCHES = ["Computer Science", "Information Technology", "Electronics", "Electrical", "Mechanical", "Civil"]

# Each company profile defines realistic hiring behavior
COMPANY_PROFILES = [
    # --- Product / Tech Giants ---
    {"name": "Google", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 8.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Software Engineer", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 8, "base_ctc": 32, "ctc_variance": 12, "base_hires": 5, "hire_variance": 5},

    {"name": "Microsoft", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.5, "backlog": False, "bond": 0, "location": "Hyderabad/Noida", "offer_type": "Full-Time",
     "role": "Software Development Engineer", "rounds": "Online Test + 3 Technical + 1 HR",
     "visit_month": 8, "base_ctc": 28, "ctc_variance": 15, "base_hires": 8, "hire_variance": 6},

    {"name": "Amazon", "industry": "Tech/E-Commerce", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore/Hyderabad", "offer_type": "Full-Time",
     "role": "SDE-1", "rounds": "Online Test + 2 Technical + 1 Bar Raiser",
     "visit_month": 9, "base_ctc": 26, "ctc_variance": 18, "base_hires": 12, "hire_variance": 8},

    {"name": "Adobe", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.5, "backlog": False, "bond": 0, "location": "Noida/Bangalore", "offer_type": "Full-Time",
     "role": "Member of Technical Staff", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 9, "base_ctc": 22, "ctc_variance": 10, "base_hires": 6, "hire_variance": 4},

    {"name": "Goldman Sachs", "industry": "Finance/Tech", "branches": ["Computer Science", "Information Technology", "Electronics"],
     "min_cgpa": 8.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Analyst - Engineering", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 9, "base_ctc": 25, "ctc_variance": 8, "base_hires": 5, "hire_variance": 3},

    {"name": "Flipkart", "industry": "Tech/E-Commerce", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Software Development Engineer", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 9, "base_ctc": 18, "ctc_variance": 8, "base_hires": 10, "hire_variance": 5},

    {"name": "Oracle", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore/Hyderabad", "offer_type": "Full-Time",
     "role": "Application Engineer", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 10, "base_ctc": 12, "ctc_variance": 5, "base_hires": 15, "hire_variance": 5},

    {"name": "Razorpay", "industry": "Fintech", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Backend Engineer", "rounds": "Online Test + 2 Technical + 1 Culture Fit",
     "visit_month": 10, "base_ctc": 16, "ctc_variance": 6, "base_hires": 5, "hire_variance": 3},

    {"name": "PhonePe", "industry": "Fintech", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Software Engineer", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 10, "base_ctc": 15, "ctc_variance": 5, "base_hires": 6, "hire_variance": 4},

    {"name": "DE Shaw", "industry": "Finance/Quant", "branches": ["Computer Science", "Information Technology", "Electronics"],
     "min_cgpa": 8.5, "backlog": False, "bond": 0, "location": "Hyderabad", "offer_type": "Full-Time",
     "role": "Software Developer", "rounds": "Online Test + 3 Technical",
     "visit_month": 8, "base_ctc": 30, "ctc_variance": 10, "base_hires": 3, "hire_variance": 2},

    # --- IT Services (Mass Recruiters) ---
    {"name": "TCS", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": False, "bond": 1, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Systems Engineer", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 1, "base_ctc": 3.5, "ctc_variance": 1.5, "base_hires": 250, "hire_variance": 100},

    {"name": "TCS Digital", "industry": "IT Services", "branches": ["Computer Science", "Information Technology", "Electronics"],
     "min_cgpa": 7.5, "backlog": False, "bond": 1, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Digital Engineer", "rounds": "Online Test + 1 Technical + 1 Managerial",
     "visit_month": 11, "base_ctc": 7, "ctc_variance": 2, "base_hires": 30, "hire_variance": 15},

    {"name": "Infosys", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": False, "bond": 1, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Systems Engineer", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 1, "base_ctc": 3.6, "ctc_variance": 1.2, "base_hires": 200, "hire_variance": 80},

    {"name": "Infosys (Power Programmer)", "industry": "IT Services", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.5, "backlog": False, "bond": 1, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Specialist Programmer", "rounds": "Online Test + 1 Coding + 1 HR",
     "visit_month": 11, "base_ctc": 8, "ctc_variance": 2, "base_hires": 15, "hire_variance": 8},

    {"name": "Wipro", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": False, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Project Engineer", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 2, "base_ctc": 3.5, "ctc_variance": 1.0, "base_hires": 180, "hire_variance": 60},

    {"name": "Cognizant", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": False, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Programmer Analyst", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 2, "base_ctc": 4.0, "ctc_variance": 1.0, "base_hires": 150, "hire_variance": 50},

    {"name": "HCL Technologies", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": True, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Software Engineer", "rounds": "Online Test + 1 HR",
     "visit_month": 2, "base_ctc": 3.8, "ctc_variance": 1.0, "base_hires": 120, "hire_variance": 40},

    {"name": "Tech Mahindra", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": True, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Associate Software Engineer", "rounds": "Group Discussion + 1 Technical + 1 HR",
     "visit_month": 3, "base_ctc": 3.5, "ctc_variance": 0.8, "base_hires": 100, "hire_variance": 40},

    {"name": "Capgemini", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.0, "backlog": False, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Analyst", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 3, "base_ctc": 4.0, "ctc_variance": 1.5, "base_hires": 100, "hire_variance": 40},

    {"name": "Accenture", "industry": "IT Services", "branches": BRANCHES,
     "min_cgpa": 6.5, "backlog": False, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Associate Software Engineer", "rounds": "Online Test + 1 HR",
     "visit_month": 12, "base_ctc": 4.5, "ctc_variance": 1.5, "base_hires": 130, "hire_variance": 50},

    # --- Core / Manufacturing ---
    {"name": "Tata Motors", "industry": "Automotive", "branches": ["Mechanical", "Electrical", "Electronics"],
     "min_cgpa": 6.5, "backlog": False, "bond": 0, "location": "Pune/Jamshedpur", "offer_type": "Full-Time",
     "role": "Graduate Engineer Trainee", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 11, "base_ctc": 6.5, "ctc_variance": 2, "base_hires": 15, "hire_variance": 8},

    {"name": "Larsen & Toubro", "industry": "Infrastructure", "branches": ["Mechanical", "Electrical", "Civil"],
     "min_cgpa": 6.5, "backlog": False, "bond": 0, "location": "Mumbai/Chennai", "offer_type": "Full-Time",
     "role": "Graduate Engineer Trainee", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 11, "base_ctc": 6.0, "ctc_variance": 1.5, "base_hires": 20, "hire_variance": 10},

    {"name": "Siemens", "industry": "Industrial/Tech", "branches": ["Electronics", "Electrical", "Mechanical"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore/Mumbai", "offer_type": "Full-Time",
     "role": "Graduate Trainee Engineer", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 10, "base_ctc": 8.0, "ctc_variance": 2, "base_hires": 8, "hire_variance": 4},

    {"name": "Bosch", "industry": "Automotive/IoT", "branches": ["Electronics", "Electrical", "Mechanical", "Computer Science"],
     "min_cgpa": 7.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Full-Time",
     "role": "Associate Software Engineer", "rounds": "Online Test + 2 Technical + 1 HR",
     "visit_month": 10, "base_ctc": 9.0, "ctc_variance": 3, "base_hires": 10, "hire_variance": 5},

    {"name": "Mahindra & Mahindra", "industry": "Automotive", "branches": ["Mechanical", "Electrical"],
     "min_cgpa": 6.5, "backlog": False, "bond": 0, "location": "Mumbai/Chennai", "offer_type": "Full-Time",
     "role": "Graduate Engineer Trainee", "rounds": "Online Test + 1 Technical + 1 HR",
     "visit_month": 12, "base_ctc": 6.0, "ctc_variance": 1.5, "base_hires": 10, "hire_variance": 5},

    {"name": "BHEL", "industry": "Power/Energy", "branches": ["Mechanical", "Electrical", "Electronics"],
     "min_cgpa": 6.0, "backlog": True, "bond": 0, "location": "PAN India", "offer_type": "Full-Time",
     "role": "Engineer Trainee", "rounds": "Written Test + 1 Technical + 1 HR",
     "visit_month": 12, "base_ctc": 5.0, "ctc_variance": 1.0, "base_hires": 12, "hire_variance": 5},

    # --- Internship drives (select companies) ---
    {"name": "Google (Intern)", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 8.0, "backlog": False, "bond": 0, "location": "Bangalore", "offer_type": "Internship",
     "role": "Software Engineering Intern", "rounds": "Online Test + 2 Technical",
     "visit_month": 7, "base_ctc": 1.5, "ctc_variance": 0.5, "base_hires": 3, "hire_variance": 2},

    {"name": "Microsoft (Intern)", "industry": "Tech/Product", "branches": ["Computer Science", "Information Technology"],
     "min_cgpa": 7.5, "backlog": False, "bond": 0, "location": "Hyderabad/Noida", "offer_type": "Internship",
     "role": "SDE Intern", "rounds": "Online Test + 2 Technical",
     "visit_month": 7, "base_ctc": 1.2, "ctc_variance": 0.3, "base_hires": 5, "hire_variance": 3},
]

# Branch-wise batch sizes (students per year)
BATCH_SIZES = {
    "Computer Science": 180,
    "Information Technology": 120,
    "Electronics": 120,
    "Electrical": 60,
    "Mechanical": 120,
    "Civil": 60,
}

YEARS = list(range(2015, 2025))  # 2015 to 2024

MONTH_NAMES = {1: "January", 2: "February", 3: "March", 7: "July", 8: "August",
               9: "September", 10: "October", 11: "November", 12: "December"}


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def generate_drives():
    """Generate historical_drives.csv rows."""
    drives = []
    drive_id = 0

    for year in YEARS:
        # Year-over-year CTC growth factor (~5% per year from 2015 baseline)
        year_factor = 1 + 0.05 * (year - 2015)
        
        for profile in COMPANY_PROFILES:
            # Some companies may not visit every single year (randomize)
            if random.random() < 0.12:
                continue  # ~12% chance a company skips a year

            for branch in profile["branches"]:
                drive_id += 1
                branch_size = BATCH_SIZES[branch]

                # Calculate realistic funnel numbers
                max_eligible = int(branch_size * 0.7)  # ~70% meet CGPA cutoff
                applied = clamp(random.randint(int(max_eligible * 0.4), max_eligible), 10, branch_size)
                shortlisted = clamp(int(applied * random.uniform(0.15, 0.45)), 1, applied)
                interviewed = clamp(int(shortlisted * random.uniform(0.4, 0.8)), 1, shortlisted)

                # Hires: scale by branch size ratio relative to CS
                hire_scale = branch_size / BATCH_SIZES["Computer Science"]
                raw_hires = profile["base_hires"] + random.randint(-profile["hire_variance"], profile["hire_variance"])
                hires_for_branch = max(1, int(raw_hires * hire_scale / len(profile["branches"])))
                selected = clamp(hires_for_branch, 0, interviewed)

                # CTC with year growth + variance
                base = profile["base_ctc"] * year_factor
                ctc = round(base + random.uniform(-profile["ctc_variance"] * 0.3, profile["ctc_variance"] * 0.5), 2)
                ctc = max(2.0, ctc)

                month_num = profile["visit_month"]

                drives.append({
                    "id": drive_id,
                    "academic_year": year,
                    "company_name": profile["name"],
                    "industry": profile["industry"],
                    "job_role": profile["role"],
                    "offer_type": profile["offer_type"],
                    "branches_eligible": ", ".join(profile["branches"]),
                    "min_cgpa_required": profile["min_cgpa"],
                    "backlog_allowed": profile["backlog"],
                    "bond_years": profile["bond"],
                    "job_location": profile["location"],
                    "selection_rounds": profile["rounds"],
                    "visit_month": MONTH_NAMES.get(month_num, "Unknown"),
                    "branch": branch,
                    "funnel_applied": applied,
                    "funnel_shortlisted": shortlisted,
                    "funnel_interviewed": interviewed,
                    "funnel_selected": selected,
                    "ctc_offered_lpa": ctc,
                })

    return drives


def generate_student_outcomes(drives):
    """Generate historical_student_outcomes.csv from drive data."""
    students = []
    student_counter = 0

    for year in YEARS:
        for branch in BRANCHES:
            batch_size = BATCH_SIZES[branch]

            # Collect all selections for this year+branch
            year_branch_drives = [d for d in drives if d["academic_year"] == year and d["branch"] == branch]

            # Generate individual students
            branch_students = []
            for i in range(batch_size):
                student_counter += 1
                cgpa = round(random.gauss(7.2, 1.2), 2)
                cgpa = clamp(cgpa, 4.0, 10.0)
                had_backlogs = random.random() < 0.15  # 15% had backlogs at some point
                gender = random.choice(["Male"] * 65 + ["Female"] * 35)  # ~65/35 ratio in engineering
                
                BRANCH_CODES = {
                    "Computer Science": "CS",
                    "Information Technology": "IT",
                    "Electronics": "EC",
                    "Electrical": "EE",
                    "Mechanical": "ME",
                    "Civil": "CE",
                }

                branch_students.append({
                    "student_id": f"STU-{year}-{BRANCH_CODES[branch]}-{i+1:04d}",
                    "academic_year": year,
                    "branch": branch,
                    "gender": gender,
                    "cgpa": cgpa,
                    "had_backlogs": had_backlogs,
                    "placed": False,
                    "total_offers_received": 0,
                    "highest_ctc_lpa": 0.0,
                    "company_joined": None,
                })

            # Simulate placement process: assign offers from drives
            for drive in sorted(year_branch_drives, key=lambda d: d["ctc_offered_lpa"], reverse=True):
                eligible = [s for s in branch_students
                            if s["cgpa"] >= drive["min_cgpa_required"]
                            and (drive["backlog_allowed"] or not s["had_backlogs"])]

                if not eligible:
                    continue

                # Prioritize by CGPA (higher CGPA -> more likely selected)
                eligible.sort(key=lambda s: s["cgpa"], reverse=True)
                num_to_select = min(drive["funnel_selected"], len(eligible))

                for s in eligible[:num_to_select]:
                    s["total_offers_received"] += 1
                    if drive["ctc_offered_lpa"] > s["highest_ctc_lpa"]:
                        s["highest_ctc_lpa"] = drive["ctc_offered_lpa"]
                        s["company_joined"] = drive["company_name"]
                    s["placed"] = True

            students.extend(branch_students)

    return students


def generate_batch_summary(students):
    """Generate yearly_batch_summary.csv from student outcomes."""
    summary = []
    grouped = defaultdict(list)

    for s in students:
        grouped[(s["academic_year"], s["branch"])].append(s)

    for (year, branch), group in sorted(grouped.items()):
        total = len(group)
        placed = [s for s in group if s["placed"]]
        placed_count = len(placed)
        ctcs = [s["highest_ctc_lpa"] for s in placed if s["highest_ctc_lpa"] > 0]

        if ctcs:
            sorted_ctcs = sorted(ctcs)
            median_idx = len(sorted_ctcs) // 2
            median = sorted_ctcs[median_idx] if len(sorted_ctcs) % 2 == 1 else round((sorted_ctcs[median_idx - 1] + sorted_ctcs[median_idx]) / 2, 2)
        else:
            median = 0.0

        # Count unique companies that hired from this branch+year
        companies = set(s["company_joined"] for s in placed if s["company_joined"])

        summary.append({
            "academic_year": year,
            "branch": branch,
            "total_students": total,
            "total_placed": placed_count,
            "total_unplaced": total - placed_count,
            "placement_percentage": round((placed_count / total) * 100, 1) if total > 0 else 0,
            "highest_ctc_lpa": round(max(ctcs), 2) if ctcs else 0,
            "average_ctc_lpa": round(sum(ctcs) / len(ctcs), 2) if ctcs else 0,
            "median_ctc_lpa": round(median, 2),
            "total_companies_visited": len(companies),
        })

    return summary


def write_csv(filename, data, fieldnames):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  Written: {filename} ({len(data)} rows)")


def main():
    print("Generating Historical Placement Data...")
    print("=" * 50)

    # 1. Generate Drives
    drives = generate_drives()

    # 2. Generate Student Outcomes (based on drives)
    students = generate_student_outcomes(drives)

    # 3. Generate Batch Summary (based on students)
    summary = generate_batch_summary(students)

    # 4. Write to CSV
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    write_csv(
        os.path.join(base_dir, "historical_drives.csv"), drives,
        ["id", "academic_year", "company_name", "industry", "job_role", "offer_type",
         "branches_eligible", "min_cgpa_required", "backlog_allowed", "bond_years",
         "job_location", "selection_rounds", "visit_month", "branch",
         "funnel_applied", "funnel_shortlisted", "funnel_interviewed", "funnel_selected",
         "ctc_offered_lpa"]
    )

    write_csv(
        os.path.join(base_dir, "historical_student_outcomes.csv"), students,
        ["student_id", "academic_year", "branch", "gender", "cgpa", "had_backlogs",
         "placed", "total_offers_received", "highest_ctc_lpa", "company_joined"]
    )

    write_csv(
        os.path.join(base_dir, "historical_batch_summary.csv"), summary,
        ["academic_year", "branch", "total_students", "total_placed", "total_unplaced",
         "placement_percentage", "highest_ctc_lpa", "average_ctc_lpa", "median_ctc_lpa",
         "total_companies_visited"]
    )

    # Print stats
    print(f"\nTotal Drive Records: {len(drives)}")
    print(f"Total Student Records: {len(students)}")
    print(f"Total Summary Records: {len(summary)}")
    print(f"\nYears Covered: {YEARS[0]} - {YEARS[-1]}")
    print(f"Companies: {len(set(d['company_name'] for d in drives))}")
    print(f"Branches: {len(BRANCHES)}")
    print("\nDone! CSV files saved to backend/data/")


if __name__ == "__main__":
    main()
