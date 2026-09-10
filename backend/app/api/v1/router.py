"""
API v1 router aggregator.

Mounts all v1 feature routers under their respective paths and OpenAPI tags.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, drives, students, chat

v1_router = APIRouter()

v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
v1_router.include_router(drives.router, prefix="/drives", tags=["Placement Drives"])
v1_router.include_router(students.router, prefix="/students", tags=["Students"])
v1_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
v1_router.include_router(chat.router, prefix="/chat", tags=["Chat Intelligence"])
