from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class DocumentUpload(BaseModel):
    """Schema for document upload response"""
    id: str
    filename: str
    size: int
    upload_time: datetime
    status: str

class QueryRequest(BaseModel):
    """Schema for query requests"""
    question: str
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    """Schema for query responses"""
    question: str
    answer: str
    sources: List[dict]
    processing_time: float

class DocumentInfo(BaseModel):
    """Schema for document information"""
    id: str
    filename: str
    size: int
    upload_time: datetime
    chunk_count: int
    status: str

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
