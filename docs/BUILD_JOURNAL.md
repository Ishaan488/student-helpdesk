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

*← This document will grow with every build step. Next entry will be added when we start coding.*
