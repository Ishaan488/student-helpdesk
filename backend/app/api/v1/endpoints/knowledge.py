from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, RoleEnum
from app.services.knowledge_service import knowledge_service

router = APIRouter()

@router.post("/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    description: str = Form(""),
    access_level: str = Form("ALL"),
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
            description=description,
            access_level=access_level
        )
        return {
            "message": "Document processed and added to knowledge base successfully",
            "document_id": str(doc.id),
            "filename": doc.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

from pydantic import BaseModel
from uuid import UUID

class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    filename: str
    description: str | None
    uploader_id: UUID
    created_at: str

    class Config:
        from_attributes = True

@router.get("", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all uploaded documents in the knowledge base.
    Only admins or placement officers can view the list of documents.
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to view knowledge documents")
        
    from sqlalchemy import select
    from app.models.document import KnowledgeDocument
    
    result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
    docs = result.scalars().all()
    
    return [
        KnowledgeDocumentResponse(
            id=d.id,
            filename=d.filename,
            description=d.description,
            uploader_id=d.uploader_id,
            created_at=d.created_at.isoformat()
        ) for d in docs
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document from the knowledge base (DB and FAISS).
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to delete knowledge documents")
        
    from app.models.document import KnowledgeDocument
    doc = await db.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from FAISS vector store
    try:
        await knowledge_service.delete_document(db, document_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document from vector store: {str(e)}")
        
    return {"message": "Document deleted successfully"}
