from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, RoleEnum
from app.services.knowledge_service import knowledge_service

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload a PDF document to the knowledge base.
    Only admins or placement officers can upload documents.
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to upload knowledge documents")
        
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        doc = await knowledge_service.process_and_store_document(
            db=db,
            file=file,
            uploader_id=current_user.id,
            description=description
        )
        return {
            "message": "Document processed and added to knowledge base successfully",
            "document_id": str(doc.id),
            "filename": doc.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
