# College Placement Intelligence Platform (Agentic RAG)

A full-stack Placement Helpdesk for universities built with FastAPI, Next.js, and LangGraph. 

This platform implements a multi-node Agentic AI architecture designed to strictly isolate deterministic business logic from probabilistic generation. It intelligently routes queries between a PostgreSQL rules engine (for precise eligibility calculation) and a FAISS Vector Database (for unstructured policy retrieval), ensuring zero hallucinations for sensitive student data.

---

## Architectural Highlights

* **Agentic Routing (LangGraph)**: Queries are classified in real-time by a lightweight reasoning model (`gemini-3.1-flash-lite`). Eligibility queries are routed to the relational database, while policy questions are routed to the vector store.
* **Deterministic Rules Engine**: The LLM is strictly prohibited from evaluating eligibility logic. A secure Python service queries PostgreSQL, evaluates the student's academic profile against the company's requirements, and the final generation node (`gemini-3.6-flash`) merely synthesizes the resulting boolean facts.
* **Local Vector Retrieval (FAISS)**: Uploaded placement policy PDFs are chunked, embedded via Google GenAI (`models/embedding-001`), and saved locally. This prevents the need for complex database extensions while maintaining semantic search capabilities.
* **Telemetry and Observability UI**: A custom Next.js Chat interface exposes the internal state of the agent in real-time. It displays execution traces, node latency, prompt token usage, FAISS L2 cosine distances, and intercepted raw SQL queries.
* **Layered Security (RBAC)**: Authentication is handled via JWT and bcrypt. Role-Based Access Control (RBAC) separates STUDENT and TPO (Training & Placement Officer) roles. The AI agent strictly inherits the user's ID to enforce permission boundaries during data retrieval.

---

## Technology Stack

### Backend (Core & AI Layer)
* **Framework**: FastAPI (Async Python)
* **Database**: PostgreSQL (Relational Data)
* **ORM & Migrations**: Async SQLAlchemy & Alembic
* **Authentication**: JWT (JSON Web Tokens) & bcrypt
* **Agentic Framework**: LangChain, LangGraph, Google GenAI
* **Vector Store**: FAISS (Facebook AI Similarity Search)

### Frontend (Client & Admin)
* **Framework**: Next.js 14+ (App Router)
* **Language**: TypeScript
* **Styling**: Tailwind CSS

---

## Local Development Setup

### 1. Database & Backend Setup
1. Ensure PostgreSQL is installed and running locally.
2. Create a database named `student_helpdesk`.
3. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   python -m venv venv
   # Activate venv: `venv\Scripts\activate` on Windows OR `source venv/bin/activate` on Mac/Linux
   pip install -r requirements.txt
   ```
4. Copy the `.env.example` to `.env` and configure your credentials:
   ```ini
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/student_helpdesk
   GEMINI_API_KEY=your_google_ai_studio_key
   ```
5. Apply migrations and start the application:
   ```bash
   alembic upgrade head
   python scripts/seed.py  # (Optional) Seed the database with mock data
   uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open http://localhost:3000 in your browser.

---

## Documentation
For a detailed chronological breakdown of the engineering process, architectural pivots, and decision rationales, refer to the [Build Journal](docs/BUILD_JOURNAL.md).