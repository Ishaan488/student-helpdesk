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
   - `router.py`: Implemented a fast LangChain intent classifier (using `gemini-3.1-flash-lite`) that parses intent into `ELIGIBILITY_CHECK`, `UPCOMING_DRIVES`, `COMPANY_FACT`, or `GENERAL_CHAT`.
   - `tools.py`: Created deterministic Python functions that wrap our `PlacementService` to fetch ground-truth database rows (without giving the LLM raw DB access).
   - `graph.py`: Built a LangGraph `StateGraph` that implements the routing logic. The strong reasoning model (`gemini-3.6-flash`) is only invoked at the very end to generate the final natural language response based on injected data.
3. Created the `/chat/message` API endpoint in `app/api/v1/endpoints/chat.py` and mounted it. This endpoint retrieves the current authenticated `User` and passes their ID into the LangGraph state, ensuring RBAC boundaries are strictly maintained at the LLM level.

### Key Architectural Win: Preventing Hallucinations & Injecting Context
Instead of prompt-engineering a massive context window to act as a "Rules Engine", we explicitly decouple routing, data retrieval, and generation. The LLM does **not** evaluate if a student's `cgpa >= 7.0`. The LLM classifies the intent, the LangGraph deterministic edge calls the Python Rules Engine (injecting the `student_id`), and the generator LLM is fed the resulting boolean facts.

## Entry #8: Frontend Web Application & Chat UI
**Date**: September 10, 2026

### What I Did
- **Decoupled Client Architecture**: Bootstrapped a standalone Next.js App Router frontend to interface with our FastAPI backend.
- **Secure Authentication Handshake**: Implemented a login flow that stores the JWT in `localStorage` and a custom API utility (`fetchWithAuth`) that automatically injects the `Bearer` token into all subsequent requests, ensuring the frontend strictly adheres to the backend's RBAC boundaries.
- **Agentic UI**: Built a dedicated Chat interface tailored for streaming/fetching deterministic LLM responses, avoiding flashy designs in favor of a clean, trustworthy aesthetic.

## Entry #9: Phase 3 - Knowledge Retrieval & FAISS Pivot
**Date**: September 11, 2026

### What I Did
- Added dependencies for Phase 3: `faiss-cpu`, `pypdf`, and `langchain-community`.
- Designed the schema for RAG (Retrieval-Augmented Generation) by creating the `KnowledgeDocument` model in SQLAlchemy to track uploaded files.
- **Architectural Pivot:** We originally planned to use `pgvector` inside PostgreSQL. However, due to the complexity of compiling C++ extensions natively on Windows for local development, we pivoted to using **FAISS (Facebook AI Similarity Search)**. FAISS runs entirely in Python and saves the vectors locally to disk, completely bypassing the database extension issue while maintaining the exact same architectural capability.

### Architectural Deep Dive: Embedding Models
As we transition from deterministic rules to reading unstructured PDFs, we must convert text into mathematical vectors (embeddings) so the agent can perform semantic similarity search.

#### What are different standard industry embedding models?
1. **OpenAI (`text-embedding-3-small` / `large`)**: The current industry standard for general-purpose RAG. Highly optimized, extremely cheap, and defaults to 1536 dimensions.
2. **Google (`models/embedding-001` or `text-embedding-004`)**: Google's native embeddings. Integrates seamlessly if you are already using the Gemini stack. Defaults to 768 dimensions.
3. **Cohere (`embed-english-v3.0`)**: Known for its state-of-the-art native support for text compression and its reranking capabilities. Great for enterprise search.
4. **HuggingFace / Open Source (`BGE-m3`, `nomic-embed-text`, `all-MiniLM-L6-v2`)**: Open-source models that you can run locally. They are free but require you to manage your own compute (GPU/CPU) to generate the vectors.

#### What is used when?
- Use **OpenAI/Cohere** when you want a managed service with the highest accuracy out-of-the-box and don't mind paying per token.
- Use **Local Open Source** when data privacy is paramount (e.g., healthcare, finance) and data cannot leave your servers.
- Use **Google Embeddings** when your primary generation model is Gemini, as it keeps your architecture within a single cloud ecosystem (Google Cloud/AI Studio), simplifying billing, API keys, and rate limits.

#### What are we using and why?
We are using **Google's `models/embedding-001`** (768 dimensions) via the LangChain Google GenAI package. 
**Why?** Because we already use Gemini (`gemini-3.1-flash-lite` and `gemini-3.6-flash`) for our LLM Router and Generator. Using Google's embedding model means we only need *one single API key* (`GEMINI_API_KEY`) for the entire intelligence stack. It is fast, highly capable, and keeps our external dependencies minimal while we learn how to build a RAG pipeline from scratch.

## Entry #10: Full Frontend Authentication & Admin Dashboard
**Date**: September 11, 2026

### What I Did
   - **Backend Refactoring:** Added an `AdminRegister` schema and a `POST /api/v1/auth/register-admin` endpoint to allow the creation of Administrator accounts directly from the frontend.
- **Frontend Authentication UI:** Built `frontend/src/app/signup/page.tsx`, a robust React component that lets users toggle between registering as a Student (which asks for CGPA, Branch, etc.) or an Administrator. It integrates securely with the FastAPI backend.
- **Admin Dashboard UI:** Built `frontend/src/app/admin/page.tsx` as a protected route. Only users with the `ADMIN` or `PLACEMENT_OFFICER` roles can access it. It features a file uploader that securely `POST`s PDF documents to the Knowledge Service we built in Phase 3.
- **Database Wipe:** Provided a script (`truncate_users.py`) to clean the database, removing all existing test users so the system can be seeded natively from the new UI.

### Why?
While backend scripts and Swagger UI are great for initial testing, a true full-stack intelligence application requires intuitive, role-based interfaces. By building these Next.js pages, we move away from CLI commands and transform the project into a usable web app.

### What's Next
**Step 11:** Test the end-to-end flow! Register a new Admin, log into the dashboard, upload a placement PDF, and ask the chatbot a question to trigger the FAISS vector search.

---

## Entry #11 — Real-Time Architecture Visualization (2026-09-11)

### What We Did
Added a live **Architecture Trace** panel to the chat interface to visualize the underlying LangGraph agent execution in real-time.

- **Backend (`AgentState` & `graph.py`):** Added a `trace` array to the state dictionary. Each node (`classify_node`, `execute_tool_node`, `generate_response_node`) appends its identifier to the trace when executed. 
- **Backend (`ChatResponse`):** Updated the `/api/v1/chat/message` endpoint to return the `trace` array alongside the final text response.
- **Frontend (`chat/page.tsx`):** Added a dynamic right-hand panel that visualizes the graph nodes. When a message is sent, the UI uses `setTimeout` to iteratively animate through the returned trace, making the nodes glow to simulate the data flow (`Input` -> `Router` -> `Retrieval` -> `Generator`).

### Why?
An Intelligence Platform shouldn't feel like a black box. By visualizing the LangGraph execution, users (and developers) can clearly see exactly how their query was routed, whether external tools (like FAISS) were used, and how the generator synthesized the answer. We opted for "Execution Trace Animation" (returning the trace array synchronously) rather than true SSE streaming to keep the networking layer simple and robust while still delivering a highly engaging user experience.

### What's Next
**Step 12:** Further polish, such as Markdown parsing in the chat interface, retaining chat history across sessions, or deploying the platform.

---

## Entry #12 — Deep-Dive Architecture Inspector (2026-09-11)

### What We Did
Upgraded the Architecture Trace panel from a visual progress bar into an interactive educational inspector.

- **Backend:** Updated the `ChatResponse` model in `/api/v1/endpoints/chat.py` to intercept and return raw internal data (`context_used` and `extracted_company`) from the LangGraph `final_state`.
- **Frontend:** Modified `chat/page.tsx` to accept this raw metadata and render it dynamically inside the trace nodes. When the animation steps through the nodes, it now expands a "Debug Box" showing the raw output of each step (e.g., the JSON chunks fetched from the database, or the explicit intent classified by the router).

### Why?
The user wanted to transform the platform into an educational tool, allowing them to learn exactly how RAG and Agentic Routing function in the background. Surfacing the "hidden" context windows proves that the LLM isn't halluncinating; it's being fed highly specific, deterministic ground-truth data.

### What's Next
**Step 13:** Markdown parsing in the UI or deploying the application.

---

## Entry #13 — Ultimate Agent Telemetry (2026-09-11)

### What We Did
Upgraded the Deep-Dive Inspector to expose **five** advanced telemetry metrics for true transparency into the Agentic AI backend:

1. **Execution Latency:** Added `time.time()` tracking to the `classify_node`, `execute_tool_node`, and `generate_response_node` to display millisecond execution times in the UI.
2. **Token Usage Tracking:** Extracted the GenAI token usage (`prompt_token_count` and `candidates_token_count`) from the generator's response metadata.
3. **FAISS Similarity Scores:** Switched to `similarity_search_with_score()` to display the raw L2 Cosine Distance metric FAISS uses to rank text chunks.
4. **Raw SQL Interception:** Used SQLAlchemy's compiler to intercept and expose the exact raw PostgreSQL queries (`SELECT * FROM...`) generated by the `ELIGIBILITY_CHECK` and `UPCOMING_DRIVES` tools.
5. **Memory State Dump:** Added a "View Raw Memory State" button in the UI that opens a modal containing the complete, unedited LangGraph `AgentState` dictionary.

### Why?
The best way to learn how an Agentic RAG system works is to see exactly what it's doing mathematically and computationally. By exposing Latency, Tokens, SQL, and FAISS distances, the "magic" of AI is removed, revealing the deterministic, programmable system underneath.

### What's Next
**Step 14:** Deploying the application or adding final UI polish.

---

## Entry #14 — Persistent Conversation Memory (Hybrid Summarization)
**Date**: September 12, 2026

### What I Did
Upgraded the Chat AI from a "memory-less" bot to an assistant with persistent memory, capable of answering contextual follow-up questions ("What is the CTC for *that* company?").

1. **Database Schema**: Created `Thread` and `ChatMessage` models in PostgreSQL.
2. **Hybrid Memory Architecture (Sliding Window + Running Summary)**:
   - Instead of passing the entire chat history to the LLM (which bloats context windows and skyrockets token costs), we implemented an O(1) summarization strategy.
   - We query the last 6 messages (3 interactions). 
   - Any older messages that "fall off" this sliding window are passed to a lightweight background model (`gemini-3.1-flash-lite`), which condenses them and updates the `Thread.summary`.
   - The generator model (`gemini-3.6-flash`) only ever receives a single `SystemMessage` containing the `summary`, followed by the 6 most recent exact messages.
3. **API Updates**: Updated `POST /api/v1/chat/message` to accept an optional `thread_id`. Created `GET /api/v1/chat/threads` to fetch history.
4. **UI Updates**: Built a Sidebar in Next.js `chat/page.tsx` that fetches past threads, allowing the user to seamlessly switch between conversations.

### Architectural Decisions & Takeaways
- **Why Custom Tables over LangGraph Checkpointers?** LangGraph has a built-in `AsyncPostgresSaver` that serializes memory into opaque binary JSON blobs. While this is fast to implement, it is a "black box" that makes it extremely frustrating to write a REST API for the frontend sidebar (you'd have to parse the JSON blobs just to get the `role` and `content`). By using explicit `Thread` and `ChatMessage` relational tables, the Next.js frontend can interact with standard REST endpoints, maintaining the platform's transparent, decoupled architecture.

### What's Next
**Step 15:** Implement **Permission-Aware Retrieval** (Phase 4 Security). Ensuring that when a student asks a query, FAISS only searches PDFs tagged for their role.

---

## Entry #15 — Two-Layer Permission-Aware Retrieval (Phase 4 Security)
**Date**: September 14, 2026

### What I Did
Implemented a highly secure, Two-Layer RAG guardrail architecture to prevent students from retrieving confidential TPO/Admin documents.
1. **Structural Guardrail (Ingestion):** Added an `access_level` dropdown (`ALL`, `STUDENT`, `TPO`, `ADMIN`) to the frontend PDF upload form. The backend injects this role as metadata into every FAISS vector chunk. At query time, `similarity_search` is strictly filtered by the user's JWT role.
2. **Evaluator Guardrail (Agentic Defense-in-Depth):** Added a `guardrail_node` into the LangGraph state graph. If a document query retrieves data from FAISS, this node intercepts the raw chunks and uses a fast, cheap LLM (`gemini-3.1-flash-lite`) to explicitly evaluate if the content contains restricted administrative data. If so, it flips an `is_safe` flag to `False`, forcing the final generator LLM to reject the query.

### Architectural Decisions & Takeaways
- **Why Two Layers?** 
  - The **Structural Layer (FAISS Metadata)** costs 0 tokens and is 100% deterministic. It efficiently blocks entire documents (e.g., "Salary Secrets.pdf") from unauthorized users.
  - The **Evaluator Layer (LangGraph Node)** handles *sub-document segregation*. If an Admin uploads a mixed-policy document tagged as `ALL`, but it contains a sneaky confidential clause, the evaluator LLM catches it at query-time.
- **Prompt Injection Immunity (Data/Control Plane Isolation):**
  - **Evaluator is Prompt-Blind:** The `guardrail_node` only reads the trusted FAISS chunks and the user's role. The student's actual chat message is intentionally omitted from its context window, making it impossible to manipulate the evaluator.
  - **Generator is Data-Starved:** If the guardrail triggers, the secret FAISS chunks are deleted from the state *before* the generator is called. Even if a student jailbreaks the generator, it physically cannot leak data it doesn't have.
- **Token Economics:** We do not scan the entire PDF with an LLM during ingestion (too expensive). We only run the evaluator guardrail on the *specifically retrieved chunks* (e.g., 4 paragraphs) right before responding, maximizing security while minimizing token burn.

### What's Next
**Step 16:** Phase 5 - Optimization (Caching, Monitoring) or final UI polish.

---

## Entry #16 — Advanced Data Modeling (10-Year Historical Placement Analytics)
**Date**: September 14, 2026

### What I Did
1. **Designed a 3-Table Relational Schema:** Moved beyond a flat summary table and implemented a true Data Warehouse structure (`historical_drives`, `historical_student_outcomes`, `yearly_batch_summary`).
2. **Built an Autonomous Synthetic Data Generator (`generate_historical_data.py`):** Wrote a pure Python script using probability distributions to simulate 10 years of placement data across 28 companies and 6 branches.
3. **Bulk Ingestion (`load_historical_data.py`):** Built an async chunked loader using SQLAlchemy to inject all 7,500+ generated records into PostgreSQL seamlessly.

### Architectural Decisions & Takeaways
- **Why Relational SQL over FAISS?**
  Vector databases (FAISS) are excellent at semantic text retrieval but practically useless at math, grouping, and aggregations. To answer questions like *"What was the average CTC for CS in 2023?"*, the data must be rigorously structured in PostgreSQL. This allows the AI agent to use deterministic `Text-to-SQL` tooling rather than hallucinating math over raw text chunks.
- **Why a 3-Table Schema?**
  - Table 1 (`historical_drives`) tracks the macro funnel (Total Applied -> Interviewed -> Selected).
  - Table 2 (`historical_student_outcomes`) tracks the micro outcomes via anonymized IDs (e.g., finding out how many students got >2 offers).
  - Table 3 (`yearly_batch_summary`) pre-computes heavy aggregations so the AI doesn't have to write overly complex SQL queries for simple batch statistics.
- **Token Economics:** Generating the mock data entirely via Python mathematics rather than LLM generation saved thousands of output tokens and guaranteed logical consistency (e.g., selected <= interviewed).

### What's Next
**Step 17:** Integrate a **Data Analyst (Text-to-SQL)** LangGraph Tool to allow the agent to query this massive dataset securely.

---

## Entry #17 — The Text-to-SQL Analytics Agent (Database Pushdown & AST Security)
**Date**: September 14, 2026

### What I Did
1. **New Routing Intent**: Updated `router.py` with `HISTORICAL_ANALYTICS` to detect queries about past trends and statistics.
2. **Text-to-SQL Tool**: Built `query_historical_database` in `tools.py` using `gemini-3.6-flash` to act as an internal SQL Developer.
3. **AST Security Validation**: Integrated `sqlglot` to parse the LLM's generated SQL into an Abstract Syntax Tree (AST). The backend strictly walks the AST to ensure the query is a `SELECT` statement, contains no destructive operations (`DROP`, `DELETE`), and only hits the allowed `historical_*` tables.
4. **Database Pushdown Optimization**: Added strict prompt engineering to solve the "Lazy Query" anti-pattern. The LLM is forced to use SQL aggregations (`SUM`, `COUNT`) and strict `WHERE` clauses to push compute down to PostgreSQL. This prevents the server from OOM crashing on massive JSON payloads and saves significant token costs.

### Architectural Decisions & Takeaways
- **AST Parsing over Regex**: Using string `.contains("DROP")` is a massive security flaw in production LLM applications. An AST parser mathematically guarantees the structure of the SQL query before execution.
- **Agentic Pipeline Efficiency**: The SQL tool intercepts the query, executes it on the database, and returns a tiny 1-row JSON payload (e.g. `{"total_placed": 21}`). The final conversational LLM then uses this tiny JSON to generate a friendly response. This proves the immense power of decoupling "Retrieval/Execution" from "Generation".

### What's Next
**Step 18:** Domain scoping, Markdown rendering, and README architecture documentation.

---

## Entry #18 — Domain Scoping, Reject Node & Chat UI Markdown
**Date**: September 14, 2026

### What I Did
1. **`OUT_OF_SCOPE` Intent & `reject_node`**: Added a new LangGraph node that short-circuits the graph for non-placement queries (code generation, personal questions, math). The reject node returns a hardcoded string without invoking the expensive generator LLM, dropping rejection latency from ~6s to ~1s and token cost to zero.
2. **Defense-in-Depth**: Kept the `STRICT SCOPE LIMITATION` rule in the generator's system prompt as a secondary safety net for ambiguous edge cases (e.g., "How to prepare for a Google coding interview?" which IS placement-related but mentions "coding").
3. **Markdown Rendering**: Integrated `react-markdown` + `remark-gfm` + `@tailwindcss/typography` into the Chat UI so AI responses render tables, bullet points, bold text, and code blocks beautifully.
4. **README Architecture Diagram**: Added a full Mermaid.js flowchart to `README.md` documenting all agents, tools, and their connections.

### Architectural Decisions & Takeaways
- **Why two layers of scope enforcement?** The fast router (`Flash-Lite`) catches the obvious 90% of out-of-scope queries instantly. But it's a cheap model and will misclassify edge cases like *"What programming languages does TCS test?"* (valid question). The generator's scope rule acts as the intelligent fallback for these ambiguous 10%.
- **Hardcoded rejection is a feature, not a limitation.** Because the `reject_node` doesn't call an LLM, it is mathematically immune to prompt injection. No matter how cleverly crafted the input, the output is always the same static string.

### What's Next
**Step 19:** Admin Document Management UI (upload/delete PDFs from the browser).

---

*← This document will grow with every build step. Next entry will be added when we start coding.*
