"""
Document Schemas
===============

Pydantic models for document API.
"""

from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class DocumentUploadResponse(BaseModel):
 """Response model for document upload."""
 document_id: str
 filename: str
 file_size: int
 mime_type: str
 storage_url: str
 status: str = "uploaded"
 created_at: datetime

class DocumentProcessResponse(BaseModel):
 """Response model for document processing."""
 document_id: str
 text: str
 pages: int
 entities: List[Dict[str, Any]]
 tables: List[Dict[str, Any]]
 confidence: float
 processing_time: float
 status: str = "processed"

class DocumentSummaryResponse(BaseModel):
 """Response model for document summary."""
 document_id: str
 summary: str
 key_points: List[str]
 document_type: str
 confidence: float
 status: str = "summarized"

class DocumentListResponse(BaseModel):
 """Response model for listing documents."""
 documents: List[Dict[str, Any]]
 total: int
 page: int
 limit: int

class ErrorResponse(BaseModel):
 """Error response model."""
 error: str
 detail: str
 status_code: int