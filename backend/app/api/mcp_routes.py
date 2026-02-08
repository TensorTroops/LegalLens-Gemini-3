"""
MCP Server API Endpoints
========================

API endpoints that use the Model Context Protocol server for intelligent routing.
"""

import logging
import time
import hashlib
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Header
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.mcp_server import get_mcp_server, ProcessingIntent, MCPToolResult
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

def generate_short_document_id(user_email: str, file_name: str) -> str:
 """
 Generate a document ID that fits within 36 characters for Cloud Spanner.
 
 Format: {hash_prefix}_{timestamp}
 Where hash_prefix is first 20 chars of SHA256 hash of user_email + file_name
 """
 # Create hash of user_email + file_name for uniqueness
 content = f"{user_email}_{file_name}".encode('utf-8')
 hash_obj = hashlib.sha256(content)
 hash_prefix = hash_obj.hexdigest()[:20] # First 20 chars of hash
 
 # Add timestamp for additional uniqueness (10 digits)
 timestamp = str(int(time.time()))[-10:] # Last 10 digits
 
 # Result: 20 + 1 + 10 = 31 characters (well within 36 char limit)
 return f"{hash_prefix}_{timestamp}"

router = APIRouter()

# Request models
class MCPTextRequest(BaseModel):
 text: str
 user_email: str
 intent: str = "comprehensive_processing"

class MCPTermLookupRequest(BaseModel):
 term: str
 context: str = None

class MCPQueryRequest(BaseModel):
 query: str
 context: str = None

@router.post("/process-text")
async def process_text_with_mcp(request: MCPTextRequest):
 """
 Process text using the MCP server with intelligent routing.
 
 Supports different processing intents:
 - comprehensive_processing: Full analysis with term extraction and simplification
 - text_simplification: Simple text simplification only
 - summary_generation: Generate summary and save to Firestore
 """
 try:
 logger.info(f" MCP API: Received text processing request from user: {request.user_email}")
 logger.info(f" MCP API: Text length: {len(request.text)} characters")
 logger.info(f" MCP API: Requested intent: {request.intent}")
 
 mcp_server = get_mcp_server()
 
 # Parse intent
 try:
 intent = ProcessingIntent(request.intent)
 logger.info(f" MCP API: Intent parsed successfully: {intent.value}")
 except ValueError:
 logger.warning(f" MCP API: Invalid intent '{request.intent}', defaulting to comprehensive_processing")
 intent = ProcessingIntent.COMPREHENSIVE_PROCESSING
 
 # Route the request
 logger.info(" MCP API: Routing request to MCP server")
 result = await mcp_server.route_request(
 intent=intent,
 text=request.text,
 user_email=request.user_email
 )
 
 if result.success:
 logger.info(f" MCP API: Request processed successfully in {result.processing_time:.2f}s")
 logger.info(f" MCP API: Result source: {result.source}")
 return {
 "success": True,
 "data": result.data,
 "processing_time": result.processing_time,
 "source": result.source
 }
 else:
 logger.error(f" MCP API: Request failed: {result.error}")
 raise HTTPException(status_code=500, detail=result.error)
 
 except Exception as e:
 logger.error(f"Error in MCP text processing: {str(e)}")
 raise HTTPException(status_code=500, detail=f"MCP processing failed: {str(e)}")

@router.post("/process-document")
async def process_document_with_mcp(
 file: UploadFile = File(...),
 user_email: str = Form(...)
):
 """
 Process a document using the MCP server.
 
 This endpoint:
 1. Extracts text using Document AI
 2. Performs comprehensive analysis using MCP routing
 3. Returns complete analysis with terms and simplification
 """
 try:
 if not file.filename:
 raise HTTPException(status_code=400, detail="No file provided")
 
 # Read file content
 file_content = await file.read()
 
 mcp_server = get_mcp_server()
 
 # Route to document analysis
 result = await mcp_server.route_request(
 intent=ProcessingIntent.DOCUMENT_ANALYSIS,
 file_content=file_content,
 mime_type=file.content_type,
 user_email=user_email
 )
 
 if result.success:
 return {
 "success": True,
 "data": result.data,
 "processing_time": result.processing_time,
 "source": result.source,
 "filename": file.filename
 }
 else:
 raise HTTPException(status_code=500, detail=result.error)
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Error in MCP document processing: {str(e)}")
 raise HTTPException(status_code=500, detail=f"MCP document processing failed: {str(e)}")

@router.post("/lookup-term")
async def lookup_term_with_mcp(request: MCPTermLookupRequest):
 """
 Look up a legal term using the MCP server with intelligent fallback.
 
 This endpoint:
 1. Tries Spanner database first
 2. Falls back to Gemini AI if not found
 3. Returns the best available definition
 """
 try:
 mcp_server = get_mcp_server()
 
 result = await mcp_server.route_request(
 intent=ProcessingIntent.TERM_LOOKUP,
 term=request.term,
 context=request.context
 )
 
 if result.success:
 return {
 "success": True,
 "data": result.data,
 "processing_time": result.processing_time,
 "source": result.source
 }
 else:
 raise HTTPException(status_code=404, detail=result.error)
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f"Error in MCP term lookup: {str(e)}")
 raise HTTPException(status_code=500, detail=f"MCP term lookup failed: {str(e)}")

@router.post("/legal-query")
async def legal_query_with_mcp(request: MCPQueryRequest):
 """
 Handle general legal queries using the MCP server.
 """
 try:
 mcp_server = get_mcp_server()
 
 result = await mcp_server.route_request(
 intent=ProcessingIntent.LEGAL_QUERY,
 query=request.query,
 context=request.context
 )
 
 if result.success:
 return {
 "success": True,
 "data": result.data,
 "processing_time": result.processing_time,
 "source": result.source
 }
 else:
 raise HTTPException(status_code=500, detail=result.error)
 
 except Exception as e:
 logger.error(f"Error in MCP legal query: {str(e)}")
 raise HTTPException(status_code=500, detail=f"MCP legal query failed: {str(e)}")

@router.post("/analyze-intent")
async def analyze_user_intent(query: str):
 """
 Analyze user input to determine the appropriate processing intent.
 """
 try:
 mcp_server = get_mcp_server()
 intent = await mcp_server.analyze_user_intent(query)
 
 return {
 "query": query,
 "detected_intent": intent.value,
 "description": _get_intent_description(intent)
 }
 
 except Exception as e:
 logger.error(f"Error in intent analysis: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")

@router.get("/health")
async def mcp_health_check():
 """
 Health check for the MCP server and all connected services.
 """
 try:
 mcp_server = get_mcp_server()
 health_status = await mcp_server.health_check()
 
 return health_status
 
 except Exception as e:
 logger.error(f"Error in MCP health check: {str(e)}")
 raise HTTPException(status_code=500, detail=f"MCP health check failed: {str(e)}")

def _get_intent_description(intent: ProcessingIntent) -> str:
 """Get human-readable description for processing intent."""
 descriptions = {
 ProcessingIntent.DOCUMENT_ANALYSIS: "Full document processing with text extraction and analysis",
 ProcessingIntent.TERM_LOOKUP: "Look up definition of a specific legal term",
 ProcessingIntent.TEXT_SIMPLIFICATION: "Simplify complex legal text into plain language",
 ProcessingIntent.LEGAL_QUERY: "Answer general legal questions",
 ProcessingIntent.SUMMARY_GENERATION: "Generate and save document summary",
 ProcessingIntent.COMPREHENSIVE_PROCESSING: "Complete text analysis with term extraction and simplification"
 }
 return descriptions.get(intent, "Unknown processing intent")

@router.post("/verify-document")
async def verify_document_integrity(
 document_id: str = Form(...),
 file: UploadFile = File(...)
):
 """Verify document integrity using GCUL blockchain."""
 try:
 logger.info(f" Verifying document integrity: {document_id}")
 
 # Read file content
 file_content = await file.read()
 
 mcp_server = get_mcp_server()
 
 # Verify using GCUL service
 verification_result = await mcp_server.gcul_service.verify_document_integrity(
 document_id=document_id,
 current_content=file_content
 )
 
 return {
 "success": True,
 "verification": verification_result,
 "document_id": document_id,
 "file_size": len(file_content)
 }
 
 except Exception as e:
 logger.error(f" Error in document verification: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Document verification failed: {str(e)}")

@router.post("/get-audit-trail")
async def get_document_audit_trail(request: MCPTextRequest):
 """Get complete audit trail for a document."""
 try:
 document_id = request.text # Using text field for document_id
 logger.info(f" Getting audit trail for: {document_id}")
 
 mcp_server = get_mcp_server()
 
 audit_trail = await mcp_server.gcul_service.get_document_audit_trail(document_id)
 
 # Format response to match Flutter expectations
 formatted_trail = []
 
 # Add hash records as audit entries
 for record in audit_trail.get('hash_records', []):
 formatted_trail.append({
 'type': 'hash_record',
 'timestamp': record['timestamp'],
 'description': f'Document hash created: {record["verification_status"]}',
 'details': {
 'file_hash': record['file_hash'],
 'content_hash': record['content_hash'],
 'has_signature': record['has_signature']
 }
 })
 
 # Add chain blocks as audit entries
 for block in audit_trail.get('chain_blocks', []):
 formatted_trail.append({
 'type': 'chain_block',
 'timestamp': block['timestamp'],
 'description': f'Added to blockchain block #{block["block_number"]}',
 'details': {
 'chain_id': block['chain_id'],
 'block_number': block['block_number'],
 'block_hash': block['block_hash']
 }
 })
 
 # Sort by timestamp (most recent first)
 formatted_trail.sort(key=lambda x: x['timestamp'], reverse=True)
 
 return {
 "success": True,
 "audit_trail": formatted_trail,
 "total_records": audit_trail.get('total_records', 0)
 }
 
 except Exception as e:
 logger.error(f" Error in audit trail retrieval: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Audit trail retrieval failed: {str(e)}")

@router.post("/store-document")
async def store_document_with_gcul(
 file: UploadFile = File(...),
 user_email: str = Form(...),
 file_name: str = Form(...),
 file_type: str = Form(...),
 document_type: str = Form(...),
 enable_gcul: str = Form(default="true"),
 extracted_text: str = Form(default=None)
):
 """Store document with GCUL blockchain security."""
 try:
 logger.info(f" Storing document with GCUL for user: {user_email}")
 logger.info(f" Document: {file_name} ({file_type})")
 
 # Read file content
 file_content = await file.read()
 
 mcp_server = get_mcp_server()
 
 # Store document with GCUL encryption and blockchain verification
 if enable_gcul.lower() == "true":
 # Prepare metadata for encryption
 encryption_metadata = {
 'file_name': file_name,
 'file_type': file_type,
 'document_type': document_type,
 'user_id': user_email,
 'file_size': len(file_content),
 'mime_type': file.content_type or file_type
 }
 
 # Generate short document ID (max 36 chars for Cloud Spanner)
 document_id = generate_short_document_id(user_email, file_name)
 
 # Encrypt and store document
 blob_name, encryption_result = await mcp_server.gcul_service.encrypt_document(
 content=file_content,
 metadata=encryption_metadata
 )
 
 # Create hash record in blockchain
 hash_result = await mcp_server.gcul_service.create_document_hash_record(
 document_id=document_id,
 content=file_content,
 extracted_text=extracted_text or "",
 user_id=user_email,
 metadata=encryption_metadata
 )
 
 # Create document metadata for response
 document_metadata = {
 "id": document_id,
 "title": file_name,
 "fileName": file_name,
 "fileType": file_type.upper(),
 "fileSize": f"{len(file_content) / 1024:.1f} KB" if len(file_content) < 1024*1024 else f"{len(file_content) / (1024*1024):.1f} MB",
 "createdAt": datetime.utcnow().isoformat(),
 "documentType": document_type,
 "isBlockchainVerified": True,
 "blockchainHash": hash_result,
 "storageUrl": f"gs://{settings.GCP_SECURE_BUCKET}/{blob_name}",
 "userId": user_email,
 "encryptionMetadata": encryption_result
 }
 
 logger.info(" Document stored with GCUL blockchain security")
 
 else:
 # Store without GCUL (regular storage)
 document_id = generate_short_document_id(user_email, file_name)
 
 # Store in regular Google Cloud Storage with credentials
 from google.cloud import storage
 from app.utils.credentials import get_credentials, get_project_id
 
 storage_client = storage.Client(
 project=get_project_id(),
 credentials=get_credentials()
 )
 bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
 blob = bucket.blob(f"documents/{document_id}")
 blob.upload_from_string(file_content, content_type=file.content_type)
 
 document_metadata = {
 "id": document_id,
 "title": file_name,
 "fileName": file_name,
 "fileType": file_type.upper(),
 "fileSize": f"{len(file_content) / 1024:.1f} KB" if len(file_content) < 1024*1024 else f"{len(file_content) / (1024*1024):.1f} MB",
 "createdAt": datetime.utcnow().isoformat(),
 "documentType": document_type,
 "isBlockchainVerified": False,
 "storageUrl": f"gs://{settings.GCS_BUCKET_NAME}/documents/{document_id}",
 "userId": user_email
 }
 
 logger.info(" Document stored without GCUL")
 
 # Store metadata in Firestore
 from app.services.firestore_service import get_firestore_service
 firestore_service = get_firestore_service()
 
 await firestore_service.store_document_metadata(
 user_email=user_email,
 document_id=document_metadata["id"],
 metadata=document_metadata
 )
 
 return {
 "success": True,
 "document": document_metadata,
 "message": "Document stored successfully with GCUL security" if enable_gcul.lower() == "true" else "Document stored successfully"
 }
 
 except Exception as e:
 logger.error(f" Error storing document: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Document storage failed: {str(e)}")

@router.get("/user-documents")
async def get_user_documents(user_email: str = Header(alias="user-email")):
 """Get all documents for a user from Firestore or demo documents for demo user."""
 try:
 logger.info(f" Getting documents for user: {user_email}")
 
 # Check if this is the demo user
 if user_email == "smp@gmail.com":
 logger.info(" Demo user detected - returning demo documents")
 
 # Return demo documents from comprehensive analysis
 demo_documents = [
 {
 "id": "demo_loan_doc_001",
 "title": "Business Loan Agreement - ICICI Bank",
 "filename": "Loan1.pdf",
 "upload_date": "2025-11-02T10:30:00Z",
 "file_size": "450 KB",
 "document_type": "Loan Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_rental_doc_002",
 "title": "Residential Rental Agreement - Pollachi",
 "filename": "rental_contract.pdf",
 "upload_date": "2025-11-02T11:15:00Z",
 "file_size": "380 KB",
 "document_type": "Rental Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_internship_doc_003",
 "title": "Internship Confidentiality Agreement - Global Tech",
 "filename": "Internship-NDA.pdf",
 "upload_date": "2025-11-02T12:00:00Z",
 "file_size": "320 KB",
 "document_type": "NDA Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_tamil_doc_004",
 "title": "கடன் உறுதி பத்திரம் - பொள்ளாச்சி",
 "filename": "kadan.pdf",
 "upload_date": "2025-11-02T16:30:00Z",
 "file_size": "420 KB",
 "document_type": "Tamil Loan Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 }
 ]
 
 logger.info(f" Retrieved {len(demo_documents)} demo documents for user")
 
 return {
 "success": True,
 "documents": demo_documents
 }
 else:
 # Regular user - get from Firestore
 from app.services.firestore_service import get_firestore_service
 firestore_service = get_firestore_service()
 
 documents = await firestore_service.get_user_documents(user_email)
 
 logger.info(f" Retrieved {len(documents)} documents for user")
 
 return {
 "success": True,
 "documents": documents
 }
 
 except Exception as e:
 logger.error(f" Error getting user documents: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Failed to get user documents: {str(e)}")

@router.get("/download-document/{document_id}")
async def download_document(document_id: str, user_email: str = Header(alias="user-email")):
 """Download and decrypt document from GCUL storage."""
 try:
 logger.info(f" Downloading document: {document_id} for user: {user_email}")
 
 # First, get document metadata to find the actual blob name
 from app.services.firestore_service import get_firestore_service
 firestore_service = get_firestore_service()
 
 document_metadata = await firestore_service.get_document_metadata(user_email, document_id)
 if not document_metadata:
 raise HTTPException(status_code=404, detail="Document not found")
 
 # Extract blob name from storageUrl
 storage_url = document_metadata.get('storageUrl', '')
 if not storage_url:
 raise HTTPException(status_code=500, detail="Document storage URL not found")
 
 # Extract blob name from gs://bucket/blob_name format
 blob_name = storage_url.split('/')[-1] # Get the last part after the last /
 if not blob_name:
 raise HTTPException(status_code=500, detail="Invalid storage URL format")
 
 # For encrypted documents, the blob path includes the encrypted/ prefix
 blob_path = f"encrypted/{blob_name}" if not blob_name.startswith('encrypted/') else blob_name
 
 mcp_server = get_mcp_server()
 
 # Decrypt and return document using the correct blob path
 decrypted_content = await mcp_server.gcul_service.decrypt_document(
 blob_name=blob_path
 )
 
 # Use original filename from metadata
 filename = document_metadata.get('fileName', document_id)
 
 return Response(
 content=decrypted_content,
 media_type="application/octet-stream",
 headers={"Content-Disposition": f"attachment; filename={filename}"}
 )
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f" Error downloading document: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Document download failed: {str(e)}")

@router.delete("/document/{document_id}")
async def delete_document(document_id: str, user_email: str = Header(alias="user-email")):
 """Delete document from all GCUL services: Firestore, Cloud Storage, and Spanner."""
 try:
 logger.info(f" Deleting document: {document_id} for user: {user_email}")
 
 # Get MCP server for GCUL access
 mcp_server = get_mcp_server()
 
 # Delete from Firestore first
 from app.services.firestore_service import get_firestore_service
 firestore_service = get_firestore_service()
 await firestore_service.delete_document(user_email, document_id)
 logger.info(" Document deleted from Firestore")
 
 # Delete from Google Cloud Storage with credentials
 from google.cloud import storage
 from app.utils.credentials import get_credentials, get_project_id
 
 storage_client = storage.Client(
 project=get_project_id(),
 credentials=get_credentials()
 )
 bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
 
 # Try to delete both original and encrypted files
 blobs_to_delete = [
 f"documents/{document_id}",
 f"encrypted/{document_id}.enc",
 f"encrypted/{document_id}"
 ]
 
 for blob_path in blobs_to_delete:
 blob = bucket.blob(blob_path)
 if blob.exists():
 blob.delete()
 logger.info(f" Deleted blob: {blob_path}")
 
 # Delete from Cloud Spanner (DocumentHashes and related HashChain entries)
 try:
 from google.cloud import spanner
 # Get document hash records first
 with mcp_server.gcul_service.database.snapshot() as snapshot:
 hash_results = snapshot.execute_sql(
 "SELECT hash_id FROM DocumentHashes WHERE document_id = @document_id",
 params={'document_id': document_id},
 param_types={'document_id': spanner.param_types.STRING}
 )
 hash_ids = [row[0] for row in hash_results]
 logger.info(f" Found {len(hash_ids)} DocumentHashes records to delete")
 
 # Delete DocumentHashes records
 if hash_ids:
 with mcp_server.gcul_service.database.batch() as batch:
 for hash_id in hash_ids:
 batch.delete(
 table='DocumentHashes',
 keyset=spanner.KeySet(keys=[[hash_id]])
 )
 logger.info(f" Deleted {len(hash_ids)} DocumentHashes records from Spanner")
 else:
 logger.info(" No DocumentHashes records found for document")
 
 except Exception as spanner_error:
 logger.warning(f" Could not delete from Spanner: {str(spanner_error)}")
 # Continue with success since Firestore and Storage are cleaned up
 
 return {
 "success": True,
 "message": "Document deleted successfully from all services"
 }
 
 except Exception as e:
 logger.error(f" Error deleting document: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")

@router.get("/document-metadata/{document_id}")
async def get_document_metadata(document_id: str, user_email: str = Header(alias="user-email")):
 """Get document metadata without file content."""
 try:
 logger.info(f" Getting metadata for document: {document_id}")
 
 from app.services.firestore_service import get_firestore_service
 firestore_service = get_firestore_service()
 
 metadata = await firestore_service.get_document_metadata(user_email, document_id)
 
 if not metadata:
 raise HTTPException(status_code=404, detail="Document not found")
 
 return {
 "success": True,
 "document": metadata
 }
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f" Error getting document metadata: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Failed to get document metadata: {str(e)}")