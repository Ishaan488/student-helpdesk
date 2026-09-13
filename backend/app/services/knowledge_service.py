import os
from typing import List
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

from app.models.document import KnowledgeDocument
from app.config import settings

FAISS_INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index")

class KnowledgeService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )

    async def process_and_store_document(
        self, db: AsyncSession, file: UploadFile, uploader_id: UUID, description: str = "", access_level: str = "ALL"
    ) -> KnowledgeDocument:
        """
        Saves the file temporarily, extracts text, creates chunks, 
        generates embeddings, and saves them to the local FAISS index.
        """
        # 1. Save file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        try:
            # 2. Extract text from PDF
            loader = PyPDFLoader(temp_file_path)
            pages = loader.load()

            # 3. Split into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            chunks = text_splitter.split_documents(pages)

            # 4. Create metadata record in Postgres
            doc_record = KnowledgeDocument(
                filename=file.filename,
                description=description,
                uploader_id=uploader_id
            )
            db.add(doc_record)
            await db.commit()
            await db.refresh(doc_record)

            # 5. Add document metadata to chunks
            for chunk in chunks:
                chunk.metadata["document_id"] = str(doc_record.id)
                chunk.metadata["filename"] = file.filename
                chunk.metadata["access_level"] = access_level

            # 6. Generate Embeddings and Store in FAISS
            if os.path.exists(FAISS_INDEX_PATH):
                # Load existing index and add to it
                vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                vectorstore.add_documents(chunks)
            else:
                # Create a new index
                vectorstore = FAISS.from_documents(chunks, self.embeddings)
            
            # Save the index back to disk
            vectorstore.save_local(FAISS_INDEX_PATH)

            return doc_record

        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def search_knowledge_base(self, query: str, user_role: str = "ALL", k: int = 3) -> str:
        """
        Searches the FAISS index for the most relevant chunks, filtering by user_role.
        """
        if not os.path.exists(FAISS_INDEX_PATH):
            return "No knowledge base documents have been uploaded yet."

        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        def role_filter(metadata: dict) -> bool:
            doc_level = metadata.get("access_level", "ALL")
            if user_role == "STUDENT":
                return doc_level in ["ALL", "STUDENT"]
            elif user_role == "TPO":
                return doc_level in ["ALL", "STUDENT", "TPO"]
            return True # Admin can see all

        results = vectorstore.similarity_search_with_score(query, k=k, filter=role_filter)
        
        if not results:
            return "No relevant information found in the knowledge base."
            
        formatted_results = []
        for res, score in results:
            source = res.metadata.get('filename', 'Unknown Document')
            page = res.metadata.get('page', 'Unknown Page')
            # L2 distance (lower is closer)
            formatted_results.append(f"Source: {source} (Page {page}) [FAISS L2 Score: {score:.4f}]\nContent: {res.page_content}")
            
        return "\n\n---\n\n".join(formatted_results)

    async def delete_document(self, db: AsyncSession, document_id: UUID) -> None:
        """
        Deletes a document from the Postgres database and its chunks from the FAISS vector store.
        """
        # 1. Delete from Postgres
        doc_record = await db.get(KnowledgeDocument, document_id)
        if doc_record:
            await db.delete(doc_record)
            await db.commit()

        # 2. Delete from FAISS
        if os.path.exists(FAISS_INDEX_PATH):
            vectorstore = FAISS.load_local(
                FAISS_INDEX_PATH, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            
            # Find the internal FAISS IDs of chunks that belong to this document
            ids_to_delete = []
            if hasattr(vectorstore, 'docstore') and hasattr(vectorstore.docstore, '_dict'):
                for chunk_id, document in vectorstore.docstore._dict.items():
                    if document.metadata.get("document_id") == str(document_id):
                        ids_to_delete.append(chunk_id)
                        
            if ids_to_delete:
                vectorstore.delete(ids_to_delete)
                vectorstore.save_local(FAISS_INDEX_PATH)

knowledge_service = KnowledgeService()
