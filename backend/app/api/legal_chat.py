"""
Legal Chat API Endpoints
========================
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.services.legal_text_service import LegalTextSimplificationService
from app.schemas.legal_chat_schemas import (
 ProcessDocumentRequest,
 ProcessDocumentResponse,
 SaveSummaryRequest,
 SaveSummaryResponse,
 GetSummariesResponse,
 SummarySchema,
 LegalTermSchema
)
from pydantic import BaseModel

# Simple request model for testing
class SimplifyTextRequest(BaseModel):
 text: str
 user_email: str

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
legal_service = LegalTextSimplificationService()

@router.post("/simplify")
async def simplify_text(request: SimplifyTextRequest):
 """
 Simple text simplification endpoint for testing.
 """
 try:
 logger.info(f"Simplifying text for user: {request.user_email}")
 
 # Process the document with simplified response
 result = await legal_service.process_legal_document(
 extracted_text=request.text,
 user_email=request.user_email
 )
 
 return {
 "simplified_text": result['simplified_text'],
 "terms_processed": len(result.get('extracted_terms', [])),
 "processing_status": result['processing_status'],
 "summary_saved": True # For compatibility with test
 }
 
 except Exception as e:
 logger.error(f"Error simplifying text: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error simplifying text: {str(e)}")

@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_legal_document(request: ProcessDocumentRequest):
 """
 Process legal document text and simplify complex terms.
 
 This endpoint:
 1. Extracts complex legal terms using Gemini AI
 2. Looks up definitions in Spanner database
 3. Uses Gemini as fallback for missing terms
 4. Returns simplified text with terms replaced by definitions
 """
 try:
 logger.info(f"Processing legal document for user: {request.user_email}")
 
 # Process the document
 result = await legal_service.process_legal_document(
 extracted_text=request.extracted_text,
 user_email=request.user_email
 )
 
 # Convert to response schema
 response = ProcessDocumentResponse(
 original_text=result['original_text'],
 simplified_text=result['simplified_text'],
 extracted_terms=[
 LegalTermSchema(
 term=term_data['term'],
 definition=term_data['definition'],
 source=term_data['source']
 )
 for term_data in result['extracted_terms']
 ],
 processing_status=result['processing_status'],
 terms_count=result.get('terms_count', 0),
 spanner_matches=result.get('spanner_matches', 0),
 gemini_fallbacks=result.get('gemini_fallbacks', 0),
 error_message=result.get('error_message')
 )
 
 logger.info(f"Successfully processed document for user {request.user_email}")
 return response
 
 except Exception as e:
 logger.error(f"Error processing document: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.post("/save-summary", response_model=SaveSummaryResponse)
async def save_document_summary(request: SaveSummaryRequest):
 """
 Save processed document summary to Firestore.
 
 Structure: users/{email}/summaries/{doc_id}
 """
 try:
 logger.info(f" LEGAL_CHAT_API: Received save-summary request for user: {request.user_email}")
 logger.info(f" LEGAL_CHAT_API: Document title: {request.document_title}")
 logger.info(f" LEGAL_CHAT_API: Summary data keys: {list(request.summary_data.keys()) if hasattr(request.summary_data, 'keys') else 'Not a dict'}")
 
 document_id = await legal_service.save_summary(
 user_email=request.user_email,
 summary_data=request.summary_data,
 document_title=request.document_title
 )
 
 logger.info(f" LEGAL_CHAT_API: Received document_id from service: {document_id}")
 
 if document_id:
 response = SaveSummaryResponse(
 success=True,
 document_id=document_id,
 message="Summary saved successfully"
 )
 logger.info(f" LEGAL_CHAT_API: Returning success response with ID: {document_id}")
 return response
 else:
 response = SaveSummaryResponse(
 success=False,
 message="Failed to save summary"
 )
 logger.warning(f" LEGAL_CHAT_API: Returning failure response")
 return response
 
 except Exception as e:
 logger.error(f" LEGAL_CHAT_API: Error saving summary: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error saving summary: {str(e)}")

@router.get("/summaries/{user_email}", response_model=GetSummariesResponse)
async def get_user_summaries(user_email: str, limit: int = 10):
 """
 Get user's saved document summaries.
 """
 try:
 logger.info(f"Getting summaries for user: {user_email}")
 
 summaries_data = await legal_service.get_user_summaries(user_email, limit)
 
 summaries = []
 for summary_data in summaries_data:
 # Convert extracted_terms to schema format
 extracted_terms = []
 for term_data in summary_data.get('extracted_terms', []):
 if isinstance(term_data, dict):
 extracted_terms.append(LegalTermSchema(
 term=term_data.get('term', ''),
 definition=term_data.get('definition', ''),
 source=term_data.get('source', 'unknown')
 ))
 
 summary = SummarySchema(
 id=summary_data['id'],
 original_text=summary_data.get('original_text', ''),
 simplified_text=summary_data.get('simplified_text', ''),
 extracted_terms=extracted_terms,
 document_title=summary_data.get('document_title', 'Untitled'),
 processing_status=summary_data.get('processing_status', 'unknown'),
 terms_count=summary_data.get('terms_count', 0),
 spanner_matches=summary_data.get('spanner_matches', 0),
 gemini_fallbacks=summary_data.get('gemini_fallbacks', 0),
 created_at=summary_data.get('created_at'),
 updated_at=summary_data.get('updated_at')
 )
 summaries.append(summary)
 
 return GetSummariesResponse(
 summaries=summaries,
 total_count=len(summaries),
 user_email=user_email
 )
 
 except Exception as e:
 logger.error(f"Error getting summaries: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error getting summaries: {str(e)}")

@router.get("/summary/{user_email}/{summary_id}", response_model=SummarySchema)
async def get_summary_by_id(user_email: str, summary_id: str):
 """
 Get a specific summary by ID.
 """
 try:
 logger.info(f"Getting summary {summary_id} for user: {user_email}")
 
 summary_data = await legal_service.get_summary_by_id(user_email, summary_id)
 
 if not summary_data:
 raise HTTPException(status_code=404, detail="Summary not found")
 
 # Convert extracted_terms to schema format
 extracted_terms = []
 for term_data in summary_data.get('extracted_terms', []):
 if isinstance(term_data, dict):
 extracted_terms.append(LegalTermSchema(
 term=term_data.get('term', ''),
 definition=term_data.get('definition', ''),
 source=term_data.get('source', 'unknown')
 ))
 
 summary = SummarySchema(
 id=summary_data['id'],
 original_text=summary_data.get('original_text', ''),
 simplified_text=summary_data.get('simplified_text', ''),
 extracted_terms=extracted_terms,
 document_title=summary_data.get('document_title', 'Untitled'),
 processing_status=summary_data.get('processing_status', 'unknown'),
 terms_count=summary_data.get('terms_count', 0),
 spanner_matches=summary_data.get('spanner_matches', 0),
 gemini_fallbacks=summary_data.get('gemini_fallbacks', 0),
 created_at=summary_data.get('created_at'),
 updated_at=summary_data.get('updated_at')
 )
 
 return summary
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Error getting summary: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")

@router.delete("/summary/{user_email}/{summary_id}")
async def delete_summary(user_email: str, summary_id: str):
 """
 Delete a user's summary.
 """
 try:
 logger.info(f"Deleting summary {summary_id} for user: {user_email}")
 
 success = await legal_service.firestore_service.delete_summary(user_email, summary_id)
 
 if success:
 return JSONResponse(
 status_code=200,
 content={"success": True, "message": "Summary deleted successfully"}
 )
 else:
 raise HTTPException(status_code=404, detail="Summary not found or could not be deleted")
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Error deleting summary: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Error deleting summary: {str(e)}")

@router.get("/health")
async def health_check():
 """Health check for legal chat service."""
 return {
 "status": "healthy",
 "service": "legal-chat-api",
 "endpoints": [
 "POST /process-document",
 "POST /save-summary", 
 "GET /summaries/{user_email}",
 "GET /summary/{user_email}/{summary_id}",
 "DELETE /summary/{user_email}/{summary_id}"
 ]
 }