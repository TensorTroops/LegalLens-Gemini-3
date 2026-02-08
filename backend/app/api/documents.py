"""
Document API Routes
==================

Handles document upload, processing, and analysis.
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form

from app.services.document_ai_service import get_document_ai_service
from app.schemas.document import (
 DocumentUploadResponse, 
 DocumentProcessResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
 file: UploadFile = File(...),
 user_id: str = Form(default="anonymous")
):
 """
 Upload a document for processing.
 
 Args:
 file: The uploaded file
 user_id: User ID (optional, defaults to 'anonymous' for testing)
 
 Returns:
 Document upload response with file details
 """
 try:
 # Validate file
 if not file.filename:
 raise HTTPException(
 status_code=status.HTTP_400_BAD_REQUEST,
 detail="No file provided"
 )
 
 # Get Document AI service
 doc_service = get_document_ai_service()
 
 # Check if file type is supported
 if file.content_type not in doc_service.get_supported_mime_types():
 raise HTTPException(
 status_code=status.HTTP_400_BAD_REQUEST,
 detail=f"Unsupported file type: {file.content_type}"
 )
 
 # Read file content
 file_content = await file.read()
 file_size = len(file_content)
 
 # Validate file size (max 10MB)
 max_size = 10 * 1024 * 1024 # 10MB
 if file_size > max_size:
 raise HTTPException(
 status_code=status.HTTP_400_BAD_REQUEST,
 detail="File size too large. Maximum size is 10MB"
 )
 
 # Generate unique document ID
 document_id = str(uuid.uuid4())
 
 # Upload to storage
 storage_url = await doc_service.upload_to_storage(
 file_content, 
 f"{document_id}_{file.filename}",
 user_id
 )
 
 logger.info(f"Document uploaded successfully: {document_id}")
 
 return DocumentUploadResponse(
 document_id=document_id,
 filename=file.filename,
 file_size=file_size,
 mime_type=file.content_type,
 storage_url=storage_url,
 created_at=datetime.utcnow()
 )
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Document upload failed: {e}")
 raise HTTPException(
 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 detail="Document upload failed"
 )

@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
 file: UploadFile = File(...),
 user_id: str = Form(default="anonymous")
):
 """
 Process a document using Document AI.
 
 Args:
 file: The uploaded file to process
 user_id: User ID (optional)
 
 Returns:
 Processed document data with extracted text and entities
 """
 try:
 start_time = datetime.utcnow()
 
 # Validate file
 if not file.filename:
 raise HTTPException(
 status_code=status.HTTP_400_BAD_REQUEST,
 detail="No file provided"
 )
 
 # Get Document AI service
 doc_service = get_document_ai_service()
 
 # Check if file type is supported
 if file.content_type not in doc_service.get_supported_mime_types():
 raise HTTPException(
 status_code=status.HTTP_400_BAD_REQUEST,
 detail=f"Unsupported file type: {file.content_type}"
 )
 
 # Read file content
 file_content = await file.read()
 
 # Generate document ID
 document_id = str(uuid.uuid4())
 
 # Process document with Document AI
 extracted_data = await doc_service.process_document(
 file_content, 
 file.content_type
 )
 
 # Calculate processing time
 processing_time = (datetime.utcnow() - start_time).total_seconds()
 
 logger.info(f"Document processed successfully: {document_id}")
 
 return DocumentProcessResponse(
 document_id=document_id,
 text=extracted_data["text"],
 pages=extracted_data["pages"],
 entities=extracted_data["entities"],
 tables=extracted_data["tables"],
 confidence=extracted_data["confidence"],
 processing_time=processing_time
 )
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Document processing failed: {e}")
 raise HTTPException(
 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 detail=f"Document processing failed: {str(e)}"
 )

@router.get("/supported-types")
async def get_supported_file_types():
 """Get list of supported file types for document processing."""
 try:
 doc_service = get_document_ai_service()
 supported_types = doc_service.get_supported_mime_types()
 
 return {
 "supported_mime_types": supported_types,
 "description": "List of MIME types supported by Document AI"
 }
 
 except Exception as e:
 logger.error(f"Failed to get supported types: {e}")
 raise HTTPException(
 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 detail="Failed to retrieve supported file types"
 )

@router.get("/health")
async def health_check():
 """Health check endpoint for document processing service."""
 try:
 # Basic health check
 return {
 "status": "healthy",
 "service": "document-ai",
 "timestamp": datetime.utcnow().isoformat()
 }
 except Exception as e:
 logger.error(f"Health check failed: {e}")
 raise HTTPException(
 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 detail="Service unhealthy"
 )