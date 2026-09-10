"""
API v1 router aggregator.

As we build features, each feature gets its own router module
(e.g., students.py, companies.py, chat.py). They all get included here,
and this single v1_router gets mounted in main.py.

This keeps main.py clean and lets us version our API easily.
"""

from fastapi import APIRouter

v1_router = APIRouter()

# Future routers will be included here like:
# from app.api.v1.endpoints import students, companies, chat
# v1_router.include_router(students.router, prefix="/students", tags=["Students"])
# v1_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
