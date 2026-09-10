# Backend — College Placement Intelligence Platform

Python + FastAPI backend for the placement intelligence platform.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Edit .env with your database credentials

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /docs` | Swagger UI (interactive API docs) |
| `GET /redoc` | ReDoc (alternative API docs) |

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Settings (pydantic-settings)
├── api/v1/              # Route handlers (versioned)
├── core/                # Database, auth, dependencies
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
└── services/            # Business logic
```
