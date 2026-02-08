"""
Files API endpoints for document management
==========================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from datetime import datetime
from pydantic import BaseModel

from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

# Pydantic models
class SavedDocumentResponse(BaseModel):
 id: str
 title: str
 fileName: str
 fileType: str
 fileSize: str
 createdAt: str
 documentType: str
 isBlockchainVerified: bool
 blockchainHash: Optional[str] = None
 thumbnailUrl: Optional[str] = None
 storageUrl: str
 userId: str

class DocumentListResponse(BaseModel):
 success: bool
 documents: List[SavedDocumentResponse]
 total_count: int
 message: Optional[str] = None

# Services will be initialized lazily
firestore_service = None

def get_firestore_service():
 """Get Firestore service instance (lazy initialization)."""
 global firestore_service
 if firestore_service is None:
 firestore_service = FirestoreService()
 return firestore_service

@router.get("/user/{user_email}", response_model=DocumentListResponse)
async def get_user_documents(
 user_email: str,
 limit: int = Query(default=50, ge=1, le=100),
 offset: int = Query(default=0, ge=0),
 document_type: Optional[str] = Query(default=None),
 search: Optional[str] = Query(default=None)
):
 """
 Get all documents for a specific user.
 
 Args:
 user_email: User's email address
 limit: Maximum number of documents to return
 offset: Number of documents to skip
 document_type: Filter by document type (Contract, Will, etc.)
 search: Search term for document titles/content
 """
 try:
 logger.info(f"Fetching documents for user: {user_email}")
 
 # Get real documents from Firestore instead of mock data
 firestore_service = get_firestore_service()
 
 # Get user documents from Firestore
 user_documents = await firestore_service.get_user_documents(
 user_email=user_email,
 limit=limit,
 offset=offset
 )
 
 if not user_documents:
 # Return empty list if no documents found
 return DocumentListResponse(
 success=True,
 documents=[],
 total_count=0,
 message=f"No documents found for user {user_email}"
 )
 
 # Convert Firestore documents to response format
 documents = []
 for doc_data in user_documents:
 # Apply filters first
 if document_type and doc_data.get('documentType', '').lower() != document_type.lower():
 continue
 
 if search:
 search_lower = search.lower()
 title = doc_data.get('title', '').lower()
 filename = doc_data.get('fileName', '').lower()
 if search_lower not in title and search_lower not in filename:
 continue
 
 doc_response = SavedDocumentResponse(
 id=doc_data.get('id', ''),
 title=doc_data.get('title', ''),
 fileName=doc_data.get('fileName', ''),
 fileType=doc_data.get('fileType', ''),
 fileSize=doc_data.get('fileSize', ''),
 createdAt=doc_data.get('createdAt', ''),
 documentType=doc_data.get('documentType', ''),
 isBlockchainVerified=doc_data.get('isBlockchainVerified', False),
 blockchainHash=doc_data.get('blockchainHash'),
 thumbnailUrl=doc_data.get('thumbnailUrl'),
 storageUrl=doc_data.get('storageUrl', ''),
 userId=doc_data.get('userId', user_email)
 )
 documents.append(doc_response)
 
 return DocumentListResponse(
 success=True,
 documents=documents,
 total_count=len(documents),
 message=f"Retrieved {len(documents)} documents for user {user_email}"
 )
 
 except Exception as e:
 logger.error(f"Error fetching documents for user {user_email}: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to fetch documents: {str(e)}"
 )

@router.delete("/document/{document_id}")
async def delete_document(document_id: str, user_email: str = Query(...)):
 """
 Delete a specific document.
 
 Args:
 document_id: ID of the document to delete
 user_email: User's email address for verification
 """
 try:
 logger.info(f"Deleting document {document_id} for user {user_email}")
 
 # TODO: Implement actual document deletion
 # This would involve:
 # 1. Verify user owns the document
 # 2. Delete from Cloud Storage
 # 3. Remove from Firestore
 # 4. Update blockchain record if applicable
 
 return {
 "success": True,
 "message": f"Document {document_id} deleted successfully"
 }
 
 except Exception as e:
 logger.error(f"Error deleting document {document_id}: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to delete document: {str(e)}"
 )

@router.get("/document/{document_id}/download")
async def download_document(document_id: str, user_email: str = Query(...)):
 """
 Get download URL for a specific document.
 
 Args:
 document_id: ID of the document to download
 user_email: User's email address for verification
 """
 try:
 logger.info(f"Generating download URL for document {document_id}")
 
 # TODO: Implement actual download URL generation
 # This would involve:
 # 1. Verify user owns the document
 # 2. Generate signed URL from Cloud Storage
 # 3. Return secure download link
 
 return {
 "success": True,
 "download_url": f"https://storage.googleapis.com/legallens/documents/{document_id}",
 "expires_at": datetime.utcnow().isoformat() + "Z"
 }
 
 except Exception as e:
 logger.error(f"Error generating download URL for document {document_id}: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to generate download URL: {str(e)}"
 )

@router.get("/health")
async def files_health_check():
 """
 Health check endpoint for files service.
 """
 return {
 "status": "healthy",
 "service": "files-api",
 "timestamp": datetime.utcnow().isoformat() + "Z",
 "endpoints": [
 "GET /files/user/{user_email}",
 "DELETE /files/document/{document_id}", 
 "GET /files/document/{document_id}/download"
 ]
 }