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

## Agentic Architecture (LangGraph)

The platform is powered by a directed acyclic graph (DAG) built with **LangGraph**. This state machine ensures the LLM follows a strict sequence of operations, preventing hallucination and enforcing security protocols.

### 1. Agents (Nodes)
* **`classify_node` (The Router)**: Uses `gemini-3.1-flash-lite` to instantly read the conversation history and classify the user's intent into one of 5 strict categories.
* **`reject_node` (The Bouncer)**: Short-circuits the graph instantly for out-of-scope queries (like coding or math questions), returning a hardcoded rejection without hitting the expensive LLM.
* **`escalate_node` (Human-in-the-Loop)**: Converts ambiguous or highly sensitive queries into asynchronous tickets that Human Admins can resolve via a dedicated Dashboard. Admin replies are seamlessly injected back into the student's chat interface.
* **`execute_tool_node` (The Worker)**: A deterministic Python node that fires the correct backend tool based on the router's intent. 
* **`guardrail_node` (The Security Evaluator)**: A post-retrieval security node. It uses a fast LLM to scan data retrieved from FAISS. If it detects highly confidential data (e.g. TPO-only memos) being sent to a student, it trips the circuit breaker (`is_safe = False`) and strips the data from the state before generation.
* **`generate_response_node` (The Synthesizer)**: The final node using `gemini-3.6-flash`. It takes the raw JSON/Text outputted by the tools and generates a conversational, human-friendly response.

### 2. Tools
The `execute_tool_node` has access to 5 deterministic tools:
1. **`fetch_student_eligibility`**: Queries PostgreSQL to calculate if the active student meets the CGPA/Backlog requirements for upcoming drives.
2. **`fetch_upcoming_drives`**: Queries PostgreSQL for all active drives.
3. **`fetch_company_facts`**: Queries PostgreSQL for static company information.
4. **`search_knowledge_base`**: Performs semantic search on the local FAISS index for unstructured PDF data.
5. **`query_historical_database`**: The **Text-to-SQL Agent**. Uses `gemini-3.6-flash` and `sqlglot` AST parsing to translate natural language into secure, read-only PostgreSQL aggregations over 10 years of placement history.

### 3. Graph Flow (Connections)

```mermaid
graph TD
    %% Styling
    classDef user fill:#8d99ae,stroke:#2b2d42,stroke-width:2px,color:#fff
    classDef agent fill:#2b2d42,stroke:#edf2f4,stroke-width:2px,color:#fff
    classDef tool fill:#fdf0d5,stroke:#c1121f,stroke-width:2px,color:#333
    classDef db fill:#003049,stroke:#669bbc,stroke-width:2px,color:#fff
    classDef sec fill:#780000,stroke:#c1121f,stroke-width:2px,color:#fff
    
    User((User Input)):::user --> Router
    
    %% Core Nodes
    subgraph StateMachine [LangGraph State Machine]
        Router[1. classify_node <br/> Model: Flash-Lite]:::agent
        Worker[2. execute_tool_node <br/> Python Runtime]:::agent
        Evaluator[3. guardrail_node <br/> Model: Flash-Lite]:::sec
        Generator[4. generate_response_node <br/> Model: Flash]:::agent
    end
    
    %% Routing logic
    Router -- "GENERAL_CHAT" --> Generator
    Router -- "Specific Intent" --> Worker
    Router -- "OUT_OF_SCOPE" --> Reject[5. reject_node]:::agent
    Router -- "ESCALATE_TO_ADMIN" --> Escalate[6. escalate_node]:::agent
    
    %% Tools Layer
    subgraph ToolsLayer [Tool Execution Layer]
        direction TB
        T_Elig(Student Eligibility Check):::tool
        T_Drive(Upcoming Drives Fetch):::tool
        T_Fact(Company Facts Fetch):::tool
        T_SQL(Text-to-SQL Analytics Agent):::tool
        T_RAG(FAISS Semantic Search):::tool
    end
    
    Worker -. "Triggers matching tool" .-> ToolsLayer
    
    %% Data Sources
    subgraph StorageLayer [Storage Layer]
        Postgres[(PostgreSQL <br/> Deterministic Data)]:::db
        FAISS[(FAISS <br/> Unstructured PDFs)]:::db
    end
    
    T_Elig --> Postgres
    T_Drive --> Postgres
    T_Fact --> Postgres
    T_SQL --> Postgres
    T_RAG --> FAISS
    
    ToolsLayer -. "Returns Raw JSON/Text" .-> Evaluator
    
    %% Post-Retrieval Security
    Evaluator -- "is_safe = True" --> Generator
    Evaluator -- "is_safe = False <br/> (Purges Data)" --> Generator
    
    Generator --> Output((Final Answer)):::user
```

---

## Technology Stack

### Backend (Core & AI Layer)
* **Framework**: FastAPI (Async Python)
* **Database**: PostgreSQL (Relational Data)
* **ORM & Migrations**: Async SQLAlchemy & Alembic
* **Testing**: Pytest, Pytest-Asyncio
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

### 3. Testing
We enforce a strict testing policy. The deterministic Rules Engine and Auth API are tested via a mocked SQLite database using custom SQLAlchemy TypeDecorators. The LangGraph Agent is tested *live* against the Gemini APIs to validate non-deterministic intent classification.
```bash
cd backend
pytest tests/ -v
```

### 4. Docker Deployment
To run the entire stack (PostgreSQL, FastAPI Backend, Next.js Frontend) in containerized mode:
```bash
docker-compose up -d --build
```

---

## Documentation
For a detailed chronological breakdown of the engineering process, architectural pivots, and decision rationales, refer to the [Build Journal](docs/BUILD_JOURNAL.md).