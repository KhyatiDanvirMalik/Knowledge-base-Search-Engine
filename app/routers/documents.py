from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import os
import shutil
import logging
from datetime import datetime

from ..models.schemas import DocumentUpload, DocumentInfo, ErrorResponse
from ..services.document_processor import DocumentProcessor
from ..services.vector_store import VectorStore
from ..utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances (in production, use dependency injection)
document_processor = DocumentProcessor()
vector_store = VectorStore()

# In-memory storage for document metadata (use database in production)
documents_db = {}

@router.post("/upload", response_model=DocumentUpload)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document
    """
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes")
        
        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        
        # Handle duplicate filenames
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate PDF
        if not document_processor.validate_pdf_file(file_path):
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")
        
        # Process document
        document_info = document_processor.process_document(file_path, file.filename)
        
        # Add to vector store
        success = vector_store.add_documents(document_info['chunks'], document_info['id'])
        if not success:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to index document")
        
        # Store document metadata
        documents_db[document_info['id']] = document_info
        
        # Return response
        return DocumentUpload(
            id=document_info['id'],
            filename=document_info['filename'],
            size=document_info['size'],
            upload_time=document_info['upload_time'],
            status=document_info['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        # Cleanup on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all uploaded documents
    """
    try:
        documents = []
        for doc_id, doc_info in documents_db.items():
            documents.append(DocumentInfo(
                id=doc_info['id'],
                filename=doc_info['filename'],
                size=doc_info['size'],
                upload_time=doc_info['upload_time'],
                chunk_count=doc_info['chunk_count'],
                status=doc_info['status']
            ))
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """
    Get information about a specific document
    """
    try:
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = documents_db[document_id]
        return DocumentInfo(
            id=doc_info['id'],
            filename=doc_info['filename'],
            size=doc_info['size'],
            upload_time=doc_info['upload_time'],
            chunk_count=doc_info['chunk_count'],
            status=doc_info['status']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document information")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and remove it from the vector store
    """
    try:
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = documents_db[document_id]
        
        # Remove from vector store
        vector_store.delete_document(document_id)
        
        # Remove file from filesystem
        if os.path.exists(doc_info['file_path']):
            os.remove(doc_info['file_path'])
        
        # Remove from memory
        del documents_db[document_id]
        
        return {"message": f"Document {doc_info['filename']} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.get("/stats/collection")
async def get_collection_stats():
    """
    Get vector store collection statistics
    """
    try:
        stats = vector_store.get_collection_stats()
        stats['total_documents'] = len(documents_db)
        return stats
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get collection statistics")
