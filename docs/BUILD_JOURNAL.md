# 🏗️ Build Journal — College Placement Intelligence Platform

> **Purpose:** This is a living document. Every time we build something, I'll log *what* we built, *why* we made specific decisions, *what techniques* we used, and *what you should learn from it*. This grows step-by-step — nothing is pre-filled.

**Started:** 2026-09-10  
**Status:** 🟢 Active

---

# Build Log

## Entry #0 — Project Kickoff & Architecture Analysis (2026-09-10)

### What We Did
Analyzed the full architecture document (1675 lines). Understood the system we're going to build.

### What This Project Is
An AI-powered Placement Intelligence Platform — NOT a simple chatbot. The key difference:

- A **simple chatbot**: Upload PDFs → vector search → LLM answers. One pipeline for everything.
- **This system**: Different question types hit different backends. The LLM is just the interface layer.

### The Core Principle

```
DATABASE / RULES ENGINE = TRUTH
LLM = INTERPRETATION AND LANGUAGE
```

The LLM never decides if a student is eligible. The rules engine does. The LLM just explains the result in natural language.

### Why We're NOT Starting With AI
The architecture doc explicitly says: *"Do not build RAG first."*

**Reason:** AI needs reliable data underneath. If your database schema is wrong, your rules engine can't work. If your APIs aren't secure, guardrails are meaningless. Foundation first, intelligence later.

### The 6-Phase Roadmap (from architecture doc)

| Phase | What | AI Involved? |
|-------|------|:---:|
| 1 — Foundation | Auth, DB, APIs, Admin panel | ❌ |
| 2 — Chat Intelligence | Query routing, tools, rules engine | ✅ |
| 3 — Knowledge Retrieval | RAG pipeline, embeddings, hybrid search | ✅ |
| 4 — Security | ABAC, guardrails, permission-aware retrieval | ✅ |
| 5 — Optimization | Caching, model routing, monitoring | ✅ |
| 6 — Advanced | Knowledge graph, recommendations, web search | ✅ |

### Decision #1: Tech Stack

**The big debate: Python vs Node.js for the backend?**

The architecture doc recommended NestJS (Node.js). But our primary goal is **learning agentic AI and RAG**. 90% of AI/ML libraries — LangChain, LlamaIndex, OpenAI SDK, embedding models, PDF parsers — are Python-first. Fighting against this in Node.js would mean more time wrestling with JS wrappers and less time learning AI concepts.

**Verdict:** Python backend. Every AI tutorial, library, and example we'll reference will work natively.

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **Python + FastAPI** | Async, fast, auto-docs, Pydantic validation. The AI ecosystem lives in Python. |
| Frontend | **Next.js + TypeScript** | SSR, React ecosystem, good for chat UI + admin panel |
| Database | **PostgreSQL + pgvector** | One DB for structured data AND vector search. Simpler ops. |
| ORM | **SQLAlchemy + Alembic** | Industry standard Python ORM. Alembic for migrations. |
| AI Framework | **LangChain + Gemini/OpenAI** | LangChain teaches agentic patterns. Gemini has a free tier for learning. |
| Cache | **Redis** | Caching, rate limiting, job queues |
| PDF Parsing | **PyMuPDF / Unstructured** | Extract text from placement policy PDFs |

### What's Next
**Step 1:** Scaffold the FastAPI backend project with basic folder structure.

---

---

## Entry #1 — FastAPI Backend Scaffold (2026-09-10)

### What We Did
Created the entire backend project structure inside `backend/`. No business logic — just the skeleton that everything else will plug into.

### Files Created & Why Each Matters

#### `requirements.txt`
Pinned versions for all dependencies. Why pin? Because `pip install fastapi` today might install 0.115 but next month it could be 0.120 with breaking changes. Pinned = reproducible.

#### `app/config.py` — Settings Management
```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://..."
    SECRET_KEY: str = "change-me"
    DEBUG: bool = False
```
**Why pydantic-settings?** It validates your environment variables at startup. If `DATABASE_URL` is missing or malformed, the app crashes immediately with a clear error — not 10 minutes later when a user hits an endpoint. Fail fast.

#### `app/core/database.py` — Async SQLAlchemy
```python
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
```
**Why async?** FastAPI is async-native. Using sync SQLAlchemy would block the event loop on every DB call, defeating the purpose. `asyncpg` is the fastest PostgreSQL driver for Python.

**Why `echo=settings.DEBUG`?** In development, you see every SQL query in the console. Great for learning what your ORM is actually doing. In production, it's silenced.

**Why `expire_on_commit=False`?** After `session.commit()`, sync SQLAlchemy lazily reloads attributes on next access. But lazy loading requires a sync DB call, which doesn't work in async. So we disable it.

#### `app/core/dependencies.py` — Dependency Injection
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```
**Key pattern:** `yield` makes this a FastAPI dependency. The route gets a session, does its work, and the dependency handles commit/rollback/close automatically. One place for transaction management instead of try/except in every route.

#### `app/main.py` — The App Entry Point
- **Lifespan handler** instead of deprecated `@app.on_event("startup")`. Modern FastAPI pattern.
- **CORS middleware** allows frontend requests. `allow_origins=["*"]` is dev-only — must be restricted in production.
- **/health endpoint** — every production service needs one. Load balancers ping this to know if your service is alive.

#### `app/api/v1/router.py` — API Versioning
Empty now, but the structure is important. When we add students, companies, chat endpoints — they all register under `/api/v1/`. If we ever need breaking changes, we create `/api/v2/` without breaking existing clients.

### Project Structure
```
backend/
├── app/
│   ├── main.py              # App entry point
│   ├── config.py            # Settings
│   ├── api/v1/router.py     # API routes (empty)
│   ├── core/
│   │   ├── database.py      # SQLAlchemy setup
│   │   └── dependencies.py  # get_db dependency
│   ├── models/              # ORM models (empty)
│   ├── schemas/             # Pydantic schemas (empty)
│   └── services/            # Business logic (empty)
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Key Learning: Why This Structure?
This is a **layered architecture**:
- **API layer** (`api/`) — thin, just handles HTTP request/response
- **Service layer** (`services/`) — business logic, rules, orchestration  
- **Model layer** (`models/`) — database structure
- **Schema layer** (`schemas/`) — what goes in/out of the API

Why separate models from schemas? Because your database structure and your API contract are different things. A `Student` model has `password_hash` but you'd never include that in an API response schema.

### Decision: Async Everything
We went fully async (async engine, async sessions, async routes). This is slightly more complex but:
1. FastAPI is async-first
2. All our future AI calls (LLM, embeddings) will be async
3. Better concurrency under load

### What's Next
**Step 2:** Create the database models — `User`, `Student`, `Company`, `PlacementDrive`, `EligibilityRule`.

### Verification Commands
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
# Check: http://localhost:8000/health
# Check: http://localhost:8000/docs
```

---

## Entry #2 — Database Models (2026-09-10)

### What We Did
Created the core SQLAlchemy ORM models: `User`, `Student`, `Company`, `PlacementDrive`, and `EligibilityRule`. 

### Architectural Decisions
- **Separated `User` from `Student`**: `User` handles authentication and global roles (Student, TPO, Admin). `Student` is a profile linked 1-to-1 with `User` that holds domain-specific data (CGPA, backlogs). This keeps auth logic clean from business logic.
- **`EligibilityRule` as a distinct model**: Instead of cluttering the `PlacementDrive` table, rules are their own entity. This allows the future Rules Engine to cleanly evaluate a `Student` against an `EligibilityRule` without loading unnecessary drive details.
- **UUIDs for Primary Keys**: Better security (harder to guess than sequential IDs) and prevents ID collision across distributed systems.

### What's Next
**Step 3:** Initialize Alembic, run the first database migration, and test creating records using a simple script.

---

## Entry #3 — Alembic Async Setup & Migration Configuration (2026-09-10)

### What We Did
Configured Alembic (`env.py`) to dynamically load environment settings (`DATABASE_URL`) from `app.config.settings` and auto-detect models via `Base.metadata`.

### Architectural Decision / Learning
- **Dynamic Config over Hardcoding:** Rather than hardcoding database URLs in `alembic.ini`, `env.py` programmatically overrides `sqlalchemy.url` from `app.config.settings`. This guarantees migrations run against the exact DB target specified in `.env`.

### What's Next
Generate the initial database migration script with `alembic revision --autogenerate` and execute `alembic upgrade head`.

---

## Entry #4 — Database Seeding & Deterministic Verification (2026-09-10)

### What We Did
Created an async database seeding script (`backend/scripts/seed.py`) that populates initial companies, placement drives, students, and deterministic eligibility rules into PostgreSQL.

### Architectural Decision / Learning
- **Eager Loading in Async SQLAlchemy (`selectinload`):** In async SQLAlchemy, implicit lazy loading raises an error because accessing unloaded relationship attributes triggers blocking I/O. Using `selectinload()` eagerly fetches related objects (like `drive.company` and `drive.eligibility_rule`) upfront in an async-safe query.

### What's Next
Build Pydantic request/response schemas and FastAPI REST endpoints for placement drives and student profiles.

---

## Entry #5 — Pydantic Schemas, Deterministic Rules Engine & REST Endpoints (2026-09-10)

### What We Did
1. **Defined Pydantic Schemas (`backend/app/schemas/`)**:
   - Structured schemas for `Student`, `Company`, `PlacementDrive`, and `EligibilityRule`.
   - Utilized Pydantic v2 `ConfigDict(from_attributes=True)` so SQLAlchemy model instances seamlessly serialize into API response payloads without manual dictionary translation.
2. **Built the Deterministic Rules Engine (`backend/app/services/rules_engine.py`)**:
   - Formulated a pure, decoupled evaluation engine: `RulesEngine.evaluate(student, rule, drive_id) -> EligibilityEvaluationResult`.
   - Checks CGPA, backlog thresholds, and eligible branch criteria, outputting deterministic booleans and structured reasons.
3. **Constructed the Placement Service Layer (`backend/app/services/placement_service.py`)**:
   - Encapsulated async database access with `selectinload` relationship loading for clean data retrieval and evaluation across all drives.
4. **Exposed REST API Endpoints (`backend/app/api/v1/endpoints/`)**:
   - `GET /api/v1/drives/` — List drives with nested company and eligibility rule information.
   - `GET /api/v1/drives/{drive_id}` — Detailed drive retrieval.
   - `GET /api/v1/drives/{drive_id}/eligibility/{student_id}` — Real-time deterministic eligibility computation for a student.
   - `GET /api/v1/students/` & `GET /api/v1/students/{student_id}` — Student profile management.
   - `GET /api/v1/students/{student_id}/eligible-drives` — Queries all drives and filters only those the student qualifies for.
   - `GET /api/v1/companies/` & `GET /api/v1/companies/{company_id}` — Company directories.
   - Mounted all routers under `/api/v1` via `app.api.v1.router.v1_router`.

### Architectural Decisions & Core Takeaways
- **Why Decouple the Rules Engine from the API Route?**:
  In a traditional CRUD app, developers often write validation checks directly inside the controller or route function. In this platform, however, the **same rules engine** must be callable by:
  1. REST endpoints (for the future web frontend).
  2. The **Agentic RAG / Chatbot Tool Layer** (as an LLM tool in Phase 2).
  By isolating `RulesEngine` in `app/services/rules_engine.py`, the LLM agent can call the exact same Python function or REST endpoint to obtain factual ground truth, adhering to the core principle:
  > *"Rules Engine decides. LLM explains."*
- **Preventing Implicit Lazy Loading Errors**:
  Because SQLAlchemy models have relationships (`drive.company`, `student.user`), returning ORM instances in FastAPI routes without eager loading causes `MissingGreenlet` exceptions during Pydantic serialization. Every service query explicitly requests necessary relations upfront with `options(selectinload(...))`.

### What's Next
**Step 6:** Authentication & JWT security (or moving into the Phase 2 Chat Intelligence / LangChain / LangGraph Agent layer).

---

## Entry #6 — Authentication, Authorization (RBAC) & JWT Security (2026-09-10)

### What We Did
1. **Added Security Dependencies (`backend/requirements.txt`)**:
   - `pyjwt` for encoding and decoding cryptographic JSON Web Tokens.
   - `passlib[bcrypt]` and `bcrypt` for secure salted password hashing.
   - `python-multipart` for parsing OAuth2 form-data logins.
2. **Built Core Security Utilities (`backend/app/core/security.py`)**:
   - `get_password_hash` and `verify_password` powered by standard Bcrypt.
   - `create_access_token` and `decode_access_token` using HMAC-SHA256 (`HS256`).
3. **Implemented Layered Authentication & RBAC Dependencies (`backend/app/core/dependencies.py`)**:
   - `get_current_user`: Intercepts `Authorization: Bearer <token>`, decodes claims, verifies user status, and eagerly loads their `Student` profile.
   - `require_roles(*allowed_roles)`: Dependency factory enforcing Role-Based Access Control (e.g. `RoleEnum.TPO`, `RoleEnum.ADMIN`) on restricted endpoints.
4. **Auth API Endpoints (`backend/app/api/v1/endpoints/auth.py`)**:
   - `POST /api/v1/auth/token`: RFC 6749 OAuth2 Password Request Form endpoint allowing native interactive login in Swagger UI (`/docs` "Authorize" button).
   - `POST /api/v1/auth/login`: Standard JSON login endpoint for frontend/mobile apps.
   - `POST /api/v1/auth/register`: Atomic registration of a `User` account with a linked `Student` academic profile.
   - `GET /api/v1/auth/me`: Profile endpoint returning the current user and their student attributes.
5. **Database Seed Password Migration (`backend/scripts/seed.py`)**:
   - Upgraded seed script to use real bcrypt hashes (`password123`) and automatically migrate any pre-existing mock records in PostgreSQL.

### Architectural Decisions & Core Takeaways
- **Prompt Instructions are NOT Security**:
  As emphasized in Section 13 of the architecture document:
  > *"Restricted information should never enter the LLM context for unauthorized users."*
  We do not rely on LLM prompts like "Please only show information for student Aryan". Instead, requests are cryptographically authenticated via JWT, extracting `current_user.id`. Any future RAG retrieval or SQL tools must inherit this verified identity before data is fetched.
- **Native `bcrypt` Over Deprecated `passlib`**:
  `passlib` hasn't received a release in years, and its internal version-sniffing hooks crash on modern `bcrypt>=4.1.0` and `5.0.0` with `AttributeError: module 'bcrypt' has no attribute '__about__'`. By calling `bcrypt.hashpw` and `bcrypt.checkpw` directly with UTF-8 byte encoding and automatic 72-byte truncation, we eliminate the fragile third-party wrapper completely.
- **FastAPI Dependency Injection for RBAC**:
  By structuring `require_roles` as a dependency factory, securing routes requires zero boilerplate inside handler functions:
  ```python
  @router.post("/drives", dependencies=[Depends(require_roles(RoleEnum.TPO))])
  ```
  If an unauthorized user attempts access, FastAPI immediately halts execution with HTTP 403 before any business logic executes.

## Entry #7: Phase 2 — Chat Intelligence & Agentic RAG Foundation
**Date**: September 10, 2026

### What I Did
1. Added **LangChain**, **LangGraph**, and **Google GenAI** dependencies to `requirements.txt`.
2. Created the **Agentic layer** in `backend/app/agent/`:
   - `state.py`: Defined `AgentState` containing conversation memory, intent, and ground-truth `eligibility_results`.
   - `router.py`: Implemented a fast LangChain intent classifier (using `gemini-1.5-flash`) that parses intent into `ELIGIBILITY_CHECK`, `UPCOMING_DRIVES`, `COMPANY_FACT`, or `GENERAL_CHAT`.
   - `tools.py`: Created deterministic Python functions that wrap our `PlacementService` to fetch ground-truth database rows (without giving the LLM raw DB access).
   - `graph.py`: Built a LangGraph `StateGraph` that implements the routing logic. The strong reasoning model (`gemini-1.5-pro`) is only invoked at the very end to generate the final natural language response based on injected data.
3. Created the `/chat/message` API endpoint in `app/api/v1/endpoints/chat.py` and mounted it. This endpoint retrieves the current authenticated `User` and passes their ID into the LangGraph state, ensuring RBAC boundaries are strictly maintained at the LLM level.

### Key Architectural Win: Preventing Hallucinations & Injecting Context
Instead of prompt-engineering a massive context window to act as a "Rules Engine", we explicitly decouple routing, data retrieval, and generation. The LLM does **not** evaluate if a student's `cgpa >= 7.0`. The LLM classifies the intent, the LangGraph deterministic edge calls the Python Rules Engine (injecting the `student_id`), and the generator LLM is fed the resulting boolean facts.

## Entry #8: Frontend Web Application & Chat UI
**Date**: September 10, 2026

### What I Did
- **Decoupled Client Architecture**: Bootstrapped a standalone Next.js App Router frontend to interface with our FastAPI backend.
- **Secure Authentication Handshake**: Implemented a login flow that stores the JWT in `localStorage` and a custom API utility (`fetchWithAuth`) that automatically injects the `Bearer` token into all subsequent requests, ensuring the frontend strictly adheres to the backend's RBAC boundaries.
- **Agentic UI**: Built a dedicated Chat interface tailored for streaming/fetching deterministic LLM responses, avoiding flashy designs in favor of a clean, trustworthy aesthetic.

### What's Next
**Step 9:** Admin Dashboard (Optional) or finalize documentation and cleanup.

---

*← This document will grow with every build step. Next entry will be added when we start coding.*




