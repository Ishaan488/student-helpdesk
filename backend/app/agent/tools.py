from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.drive import PlacementDrive
from app.services.placement_service import PlacementService


async def fetch_student_eligibility(db: AsyncSession, student_id: UUID) -> Dict[str, Any]:
    """
    Deterministically fetches all drives a student is eligible for.
    Used by the Agent graph to inject ground-truth before the LLM generates a response.
    """
    drives = await PlacementService.get_eligible_drives_for_student(db, student_id)
    if drives is None:
        return {"data": [{"error": "Student profile not found. Are you an admin or TPO?"}], "query": "None"}

    results = []
    for d in drives:
        results.append({
            "company": d.company.name if d.company else "Unknown",
            "role": d.role,
            "ctc": f"{d.ctc} LPA" if d.ctc else "Not specified",
            "location": d.location,
            "status": d.status
        })
        
    query = select(PlacementDrive).where(PlacementDrive.status == "UPCOMING") # Simplified illustration
    raw_sql = str(query.compile(compile_kwargs={"literal_binds": True}))
    
    return {"data": results, "query": raw_sql}


async def fetch_upcoming_drives(db: AsyncSession) -> Dict[str, Any]:
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
        
    query = select(PlacementDrive).where(PlacementDrive.status == "UPCOMING")
    raw_sql = str(query.compile(compile_kwargs={"literal_binds": True}))
    
    return {"data": results, "query": raw_sql}


async def fetch_company_facts(db: AsyncSession, company_name: str) -> Dict[str, Any]:
    """
    Fetches details about a specific company.
    """
    query = select(Company).where(Company.name.ilike(f"%{company_name}%")).limit(1)
    res = await db.execute(query)
    company = res.scalar_one_or_none()
    
    if not company:
        return {"data": [{"error": f"No information found for company '{company_name}'."}], "query": str(query.compile(compile_kwargs={"literal_binds": True}))}
        
    return {
        "data": [{
            "name": company.name,
            "industry": company.industry,
            "description": company.description,
        }],
        "query": str(query.compile(compile_kwargs={"literal_binds": True}))
    }

async def search_knowledge_base(query: str) -> str:
    """
    Searches the FAISS vector database for unstructured knowledge regarding policies, rules, or unstructured company data.
    """
    from app.services.knowledge_service import knowledge_service
    return knowledge_service.search_knowledge_base(query=query)


async def query_historical_database(query: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Text-to-SQL Agent tool.
    Uses Gemini 3.6 Flash to translate a natural language query into PostgreSQL.
    Strictly validates the SQL using sqlglot (AST parsing) to ensure it's a read-only
    SELECT query touching only historical tables.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from sqlalchemy import text
    import sqlglot
    from sqlglot import exp
    from app.config import settings

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash", 
        temperature=0.0,
        google_api_key=settings.GEMINI_API_KEY
    )

    schema = """
    Table: historical_drives
    Columns: id (INT), academic_year (INT), company_name (VARCHAR), industry (VARCHAR), job_role (VARCHAR), offer_type (VARCHAR), branches_eligible (VARCHAR), min_cgpa_required (FLOAT), backlog_allowed (BOOLEAN), bond_years (INT), job_location (VARCHAR), selection_rounds (VARCHAR), visit_month (VARCHAR), branch (VARCHAR), funnel_applied (INT), funnel_shortlisted (INT), funnel_interviewed (INT), funnel_selected (INT), ctc_offered_lpa (FLOAT)
    
    Table: historical_student_outcomes
    Columns: student_id (VARCHAR), academic_year (INT), branch (VARCHAR), gender (VARCHAR), cgpa (FLOAT), had_backlogs (BOOLEAN), placed (BOOLEAN), total_offers_received (INT), highest_ctc_lpa (FLOAT), company_joined (VARCHAR)
    
    Table: yearly_batch_summary
    Columns: id (INT), academic_year (INT), branch (VARCHAR), total_students (INT), total_placed (INT), total_unplaced (INT), placement_percentage (FLOAT), highest_ctc_lpa (FLOAT), average_ctc_lpa (FLOAT), median_ctc_lpa (FLOAT), total_companies_visited (INT)
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert PostgreSQL Data Analyst. Write a raw PostgreSQL query to answer the user's question based strictly on this schema:

{schema}

CRITICAL OPTIMIZATION RULES:
1. NEVER write "SELECT *" or return large datasets. You MUST use strict WHERE clauses based on the user's question (e.g., if they ask for 2018, use WHERE academic_year = 2018).
2. Let PostgreSQL do the math. If the user asks "how many" or "what is the average", use SQL aggregations (COUNT, SUM, AVG, MAX) instead of returning raw rows.
3. Keep the returned JSON payload as tiny as mathematically possible (ideally 1 to 5 rows).
4. Do NOT use ILIKE '%CS%' for branches. The exact branch names in the DB are: 'Computer Science', 'Information Technology', 'Electronics', 'Electrical', 'Mechanical', 'Civil'.

IMPORTANT: Output ONLY the raw SQL query. No markdown formatting, no explanation, no backticks. Do not include ```sql."""),
        ("user", "{query}")
    ])

    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"schema": schema, "query": query})
        raw_sql = response.content.strip().strip('`').strip()
        if raw_sql.lower().startswith("sql"):
            raw_sql = raw_sql[3:].strip()
            
        # Security: AST Validation using sqlglot
        try:
            parsed = sqlglot.parse_one(raw_sql, read="postgres")
        except Exception as e:
            return {"data": [{"error": f"Failed to parse SQL: {str(e)}"}], "query": raw_sql}

        # 1. Must be a SELECT statement
        if not isinstance(parsed, exp.Select):
            return {"data": [{"error": "SECURITY BLOCK: Only SELECT queries are allowed."}], "query": raw_sql}

        # 2. Must not contain destructive operations
        if list(parsed.find_all((exp.Delete, exp.Update, exp.Insert, exp.Drop))):
            return {"data": [{"error": "SECURITY BLOCK: Destructive operations detected."}], "query": raw_sql}

        # 3. Must only hit allowed tables
        allowed_tables = {"historical_drives", "historical_student_outcomes", "yearly_batch_summary"}
        for table in parsed.find_all(exp.Table):
            if table.name.lower() not in allowed_tables:
                return {"data": [{"error": f"SECURITY BLOCK: Unauthorized table access '{table.name}'."}], "query": raw_sql}

        # Execution
        result = await db.execute(text(raw_sql))
        rows = result.mappings().all()
        
        # Convert rows to dict for JSON serialization
        data = [dict(row) for row in rows]
        if not data:
            data = [{"info": "Query executed successfully, but returned 0 rows."}]
            
        return {"data": data, "query": raw_sql}

    except Exception as e:
        return {"data": [{"error": str(e)}], "query": "Error generating/executing SQL"}
