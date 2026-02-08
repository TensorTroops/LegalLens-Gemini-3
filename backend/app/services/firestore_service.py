"""
Firestore Service for User Data Management
==========================================
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from google.cloud import firestore
from firebase_admin import credentials, firestore as admin_firestore, initialize_app
from app.config.settings import get_settings
from app.utils.credentials import get_service_account_info, is_credentials_available

logger = logging.getLogger(__name__)

class FirestoreService:
 """Service for interacting with Firestore database."""
 
 def __init__(self):
 self.settings = get_settings()
 self._initialize_firebase()
 
 # Only initialize Firestore client if Firebase was successfully initialized
 try:
 self.db = admin_firestore.client()
 except Exception as e:
 logger.warning(f"Could not initialize Firestore client: {str(e)}")
 self.db = None
 
 def _initialize_firebase(self):
 """Initialize Firebase Admin SDK with base64 credentials."""
 try:
 # Check if Firebase app is already initialized
 from firebase_admin import _apps
 if not _apps:
 if not is_credentials_available():
 logger.warning(" No Firebase credentials found. Firebase services will be unavailable.")
 return
 
 # Get credentials from centralized manager
 credentials_dict = get_service_account_info()
 if credentials_dict:
 # Use the decoded credentials dictionary
 cred = credentials.Certificate(credentials_dict)
 logger.info(" Using base64 encoded service account credentials for Firebase")
 else:
 logger.warning(" No Firebase credentials found. Firebase services will be unavailable.")
 return
 
 initialize_app(cred, {
 'projectId': self.settings.FIREBASE_PROJECT_ID or self.settings.GCP_PROJECT_ID
 })
 
 logger.info(" Firebase Admin SDK initialized successfully with base64 credentials")
 
 except Exception as e:
 logger.error(f"Error initializing Firebase: {str(e)}")
 logger.warning("Firebase services will be unavailable")
 # Don't raise the exception, let the app continue without Firebase
 
 async def save_user_summary(self, user_email: str, summary_data: Dict) -> Optional[str]:
 """
 Save user summary to Firestore with structure: users/{email}/summaries/{doc_id}
 Using email as the document ID for simpler access
 
 Args:
 user_email: User's email address
 summary_data: Dictionary containing summary information
 
 Returns:
 Document ID if successful, None otherwise
 """
 try:
 logger.info(f" Firestore: Starting save_user_summary for user: {user_email}")
 
 # Check if db is available
 if not hasattr(self, 'db') or self.db is None:
 logger.error(f" Firestore: Database not initialized for user: {user_email}")
 return None
 
 # Use the same email format as documents (keep original @ format)
 logger.info(f" Firestore: Using email format: {user_email}")
 
 # Prepare the summary document
 doc_data = {
 'original_text': summary_data.get('original_text', ''),
 'simplified_text': summary_data.get('simplified_text', ''),
 'extracted_terms': summary_data.get('extracted_terms', []),
 'document_title': summary_data.get('document_title', 'Untitled Document'),
 'created_at': datetime.utcnow(),
 'updated_at': datetime.utcnow(),
 'user_email': user_email,
 'processing_status': summary_data.get('processing_status', 'completed'),
 'terms_count': summary_data.get('terms_count', 0),
 'spanner_matches': summary_data.get('spanner_matches', 0),
 'gemini_fallbacks': summary_data.get('gemini_fallbacks', 0)
 }
 
 logger.info(f" Firestore: Prepared document data with {len(doc_data)} fields")
 
 # Save to Firestore: users/{user_email}/summaries/{auto_generated_id}
 logger.info(f" Firestore: Creating document reference for user: {user_email}")
 user_doc_ref = self.db.collection('users').document(user_email)
 summary_ref = user_doc_ref.collection('summaries').document()
 
 logger.info(" Firestore: Setting document data...")
 summary_ref.set(doc_data)
 
 logger.info(f" Firestore: Summary saved for user {user_email} with summary ID: {summary_ref.id}")
 return summary_ref.id
 
 except Exception as e:
 logger.error(f"Error saving summary for user {user_email}: {str(e)}")
 return None
 
 async def get_user_summaries(self, user_email: str, limit: int = 10) -> List[Dict]:
 """
 Get user's saved summaries using the new email-based structure.
 
 Args:
 user_email: User's email address
 limit: Maximum number of summaries to return
 
 Returns:
 List of summary documents
 """
 try:
 # Use the same email format as documents (keep original @ format)
 
 # Get summaries from user's subcollection
 user_doc_ref = self.db.collection('users').document(user_email)
 summaries_ref = user_doc_ref.collection('summaries')
 
 # Query summaries ordered by creation date (newest first)
 query = summaries_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
 docs = query.stream()
 
 summaries = []
 for doc in docs:
 summary_data = doc.to_dict()
 summary_data['id'] = doc.id
 summaries.append(summary_data)
 
 return summaries
 
 except Exception as e:
 logger.error(f"Error getting summaries for user {user_email}: {str(e)}")
 return []
 
 async def get_summary_by_id(self, user_email: str, summary_id: str) -> Optional[Dict]:
 """
 Get a specific summary by ID using the new email-based structure.
 
 Args:
 user_email: User's email address
 summary_id: Summary document ID
 
 Returns:
 Summary document if found, None otherwise
 """
 try:
 # Use the same email format as documents (keep original @ format)
 
 # Get specific summary
 user_doc_ref = self.db.collection('users').document(user_email)
 summary_ref = user_doc_ref.collection('summaries').document(summary_id)
 
 doc = summary_ref.get()
 if doc.exists:
 summary_data = doc.to_dict()
 summary_data['id'] = doc.id
 return summary_data
 
 return None
 
 except Exception as e:
 logger.error(f"Error getting summary {summary_id} for user {user_email}: {str(e)}")
 return None
 
 async def delete_summary(self, user_email: str, summary_id: str) -> bool:
 """
 Delete a user's summary using the new email-based structure.
 
 Args:
 user_email: User's email address
 summary_id: Summary document ID
 
 Returns:
 True if successful, False otherwise
 """
 try:
 # Use the same email format as documents (keep original @ format)
 
 # Delete the summary
 user_doc_ref = self.db.collection('users').document(user_email)
 summary_ref = user_doc_ref.collection('summaries').document(summary_id)
 
 summary_ref.delete()
 logger.info(f"Summary {summary_id} deleted for user {user_email}")
 return True
 
 except Exception as e:
 logger.error(f"Error deleting summary {summary_id} for user {user_email}: {str(e)}")
 return False
 
 async def update_user_profile(self, user_email: str, profile_data: Dict) -> bool:
 """
 Update user profile information.
 
 Args:
 user_email: User's email address
 profile_data: Dictionary containing profile information
 
 Returns:
 True if successful, False otherwise
 """
 try:
 user_doc_ref = self.db.collection('users').document(user_email)
 
 # Add updated timestamp
 profile_data['updated_at'] = datetime.utcnow()
 
 user_doc_ref.set(profile_data, merge=True)
 logger.info(f"Profile updated for user {user_email}")
 return True
 
 except Exception as e:
 logger.error(f"Error updating profile for user {user_email}: {str(e)}")
 return False

 async def store_document_metadata(self, user_email: str, document_id: str, metadata: Dict) -> bool:
 """
 Store document metadata in Firestore.
 
 Args:
 user_email: User's email address
 document_id: Document ID
 metadata: Document metadata
 
 Returns:
 True if successful, False otherwise
 """
 try:
 if self.db is None:
 logger.warning("Firestore not available, skipping metadata storage")
 return False
 
 # Store in users/{email}/documents/{doc_id}
 user_doc_ref = self.db.collection('users').document(user_email)
 doc_ref = user_doc_ref.collection('documents').document(document_id)
 
 # Add timestamps
 metadata['created_at'] = datetime.utcnow()
 metadata['updated_at'] = datetime.utcnow()
 
 doc_ref.set(metadata)
 logger.info(f"Document metadata stored for user {user_email}, doc: {document_id}")
 return True
 
 except Exception as e:
 logger.error(f"Error storing document metadata: {str(e)}")
 return False

 async def get_user_documents(self, user_email: str, limit: int = 50, offset: int = 0) -> List[Dict]:
 """
 Get all documents for a user with pagination support.
 
 Args:
 user_email: User's email address
 limit: Maximum number of documents to return
 offset: Number of documents to skip
 
 Returns:
 List of document metadata
 """
 try:
 if self.db is None:
 logger.warning("Firestore not available, returning empty document list")
 return []
 
 user_doc_ref = self.db.collection('users').document(user_email)
 docs_ref = user_doc_ref.collection('documents')
 
 # Query documents ordered by creation date (newest first) with pagination
 query = docs_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
 
 # Apply pagination
 if offset > 0:
 query = query.offset(offset)
 if limit > 0:
 query = query.limit(limit)
 
 docs = query.stream()
 
 documents = []
 for doc in docs:
 doc_data = doc.to_dict()
 doc_data['id'] = doc.id
 documents.append(doc_data)
 
 logger.info(f"Retrieved {len(documents)} documents for user {user_email} (limit={limit}, offset={offset})")
 return documents
 
 except Exception as e:
 logger.error(f"Error getting user documents: {str(e)}")
 return []

 async def get_document_metadata(self, user_email: str, document_id: str) -> Optional[Dict]:
 """
 Get document metadata by ID.
 
 Args:
 user_email: User's email address
 document_id: Document ID
 
 Returns:
 Document metadata if found, None otherwise
 """
 try:
 if self.db is None:
 logger.warning("Firestore not available, cannot get document metadata")
 return None
 
 user_doc_ref = self.db.collection('users').document(user_email)
 doc_ref = user_doc_ref.collection('documents').document(document_id)
 
 doc = doc_ref.get()
 if doc.exists:
 doc_data = doc.to_dict()
 doc_data['id'] = doc.id
 return doc_data
 
 return None
 
 except Exception as e:
 logger.error(f"Error getting document metadata: {str(e)}")
 return None

 async def delete_document(self, user_email: str, document_id: str) -> bool:
 """
 Delete document metadata from Firestore.
 
 Args:
 user_email: User's email address
 document_id: Document ID
 
 Returns:
 True if successful, False otherwise
 """
 try:
 if self.db is None:
 logger.warning("Firestore not available, cannot delete document metadata")
 return False
 
 user_doc_ref = self.db.collection('users').document(user_email)
 doc_ref = user_doc_ref.collection('documents').document(document_id)
 
 doc_ref.delete()
 logger.info(f"Document {document_id} deleted for user {user_email}")
 return True
 
 except Exception as e:
 logger.error(f"Error deleting document metadata: {str(e)}")
 return False


# Global service instance
_firestore_service = None

def get_firestore_service() -> FirestoreService:
 """
 Get or create a singleton instance of FirestoreService.
 
 Returns:
 FirestoreService instance
 """
 global _firestore_service
 if _firestore_service is None:
 _firestore_service = FirestoreService()
 return _firestore_service