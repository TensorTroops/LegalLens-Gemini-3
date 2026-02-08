"""
Legal Text Simplification Service
=================================
"""

import logging
import re
from typing import Dict, List, Optional
from app.services.spanner_service import SpannerService
from app.services.gemini_service import GeminiService
from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

class LegalTextSimplificationService:
 """Main service for processing and simplifying legal text."""
 
 def __init__(self):
 self.spanner_service = SpannerService()
 self.gemini_service = GeminiService()
 self.firestore_service = FirestoreService()
 
 def format_response(self, response_text: str) -> str:
 """
 Format the response to remove unwanted characters and improve readability
 """
 # Remove all asterisks (*) completely
 formatted_text = re.sub(r'\*+', '', response_text)
 
 # Remove emojis (Unicode ranges for common emojis)
 emoji_pattern = re.compile("["
 u"\U0001F600-\U0001F64F" # emoticons
 u"\U0001F300-\U0001F5FF" # symbols & pictographs
 u"\U0001F680-\U0001F6FF" # transport & map symbols
 u"\U0001F1E0-\U0001F1FF" # flags (iOS)
 u"\U00002702-\U000027B0" # dingbats
 u"\U000024C2-\U0001F251"
 "]+", flags=re.UNICODE)
 formatted_text = emoji_pattern.sub('', formatted_text)
 
 # Remove "Analyze Summary" or similar phrases
 formatted_text = re.sub(r'analyze\s+summary:?\s*', '', formatted_text, flags=re.IGNORECASE)
 formatted_text = re.sub(r'summary\s+analysis:?\s*', '', formatted_text, flags=re.IGNORECASE)
 
 # Clean up extra whitespace and line breaks
 formatted_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_text) # Multiple line breaks to double
 formatted_text = re.sub(r'[ \t]+', ' ', formatted_text) # Multiple spaces to single
 formatted_text = re.sub(r'^\s+', '', formatted_text, flags=re.MULTILINE) # Leading spaces on lines
 
 return formatted_text.strip()
 
 async def process_legal_document(self, extracted_text: str, user_email: str) -> Dict:
 """
 Enhanced workflow for comprehensive legal document processing using Gemini AI.
 
 Args:
 extracted_text: Text extracted from the legal document
 user_email: Email of the user processing the document
 
 Returns:
 Dictionary containing simplified text and complex terms with definitions
 """
 try:
 logger.info(f"Processing legal document for user: {user_email}")
 
 # Use Gemini AI for comprehensive text simplification and term extraction
 logger.info("Using Gemini AI for comprehensive text simplification and term extraction...")
 
 # Use the comprehensive simplification method
 gemini_result = await self.gemini_service.comprehensive_simplification(extracted_text)
 
 # Format the response according to user requirements: {simplified text}\n[{term:meaning}]
 simplified_text = gemini_result['simplified_text']
 complex_terms = gemini_result['complex_terms']
 
 # Create the formatted response with simplified text and complex terms list
 if complex_terms:
 terms_list = []
 for term, meaning in complex_terms.items():
 terms_list.append(f"{term}: {meaning}")
 
 formatted_response = f"{simplified_text}COMPLEX TERMS--------------\n[{chr(10).join(terms_list)}]"
 else:
 formatted_response = simplified_text
 
 # Format the response to remove unwanted characters
 formatted_response = self.format_response(formatted_response)
 
 # Convert complex terms to the expected format for compatibility
 extracted_terms = []
 for term, definition in complex_terms.items():
 extracted_terms.append({
 'term': term,
 'definition': definition,
 'source': 'gemini_comprehensive',
 'confidence': 'high'
 })
 
 # Prepare comprehensive result
 result = {
 'original_text': extracted_text,
 'simplified_text': formatted_response,
 'extracted_terms': extracted_terms,
 'processing_status': 'success',
 'terms_count': len(complex_terms),
 'spanner_matches': 0, # Not using Spanner in new approach
 'gemini_matches': len(complex_terms),
 'original_word_count': gemini_result['original_word_count'],
 'simplified_word_count': gemini_result['simplified_word_count'],
 'reduction_percentage': gemini_result['reduction_percentage'],
 'processing_method': 'gemini_comprehensive_simplification'
 }
 
 logger.info(f"Successfully processed document with Gemini: {len(complex_terms)} terms extracted, "
 f"word count reduced from {gemini_result['original_word_count']} to {gemini_result['simplified_word_count']} "
 f"({gemini_result['reduction_percentage']}% reduction)")
 
 return result
 
 except Exception as e:
 logger.error(f"Error processing legal document: {str(e)}")
 return {
 'original_text': extracted_text,
 'simplified_text': extracted_text,
 'extracted_terms': [],
 'processing_status': 'error',
 'error_message': str(e)
 }
 
 async def _replace_terms_with_definitions(self, text: str, definitions: Dict[str, str]) -> str:
 """
 Replace complex legal terms with their definitions in the text.
 
 Args:
 text: Original text
 definitions: Dictionary mapping terms to definitions
 
 Returns:
 Text with terms replaced by definitions
 """
 try:
 simplified_text = text
 
 # Sort terms by length (longest first) to avoid partial replacements
 sorted_terms = sorted(definitions.keys(), key=len, reverse=True)
 
 for term in sorted_terms:
 definition = definitions[term]
 
 # Create regex pattern for case-insensitive whole word matching
 pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
 
 # Replace with definition in parentheses
 replacement = f"{term} ({definition})"
 simplified_text = pattern.sub(replacement, simplified_text)
 
 return simplified_text
 
 except Exception as e:
 logger.error(f"Error replacing terms with definitions: {str(e)}")
 return text
 
 async def save_summary(self, user_email: str, summary_data: Dict, document_title: str = None) -> Optional[str]:
 """
 Save the processed summary to Firestore.
 
 Args:
 user_email: User's email address
 summary_data: Processed document data
 document_title: Optional title for the document
 
 Returns:
 Document ID if successful, None otherwise
 """
 try:
 logger.info(f" LEGAL_SERVICE: Processing Firestore save for user: {user_email}")
 logger.info(f" LEGAL_SERVICE: Document title: {document_title}")
 logger.info(f" LEGAL_SERVICE: Summary data keys: {list(summary_data.keys())}")
 
 # Prepare data for Firestore
 firestore_data = {
 'original_text': summary_data.get('original_text', ''),
 'simplified_text': summary_data.get('simplified_text', ''),
 'extracted_terms': summary_data.get('extracted_terms', []),
 'document_title': document_title or 'Legal Document Summary',
 'processing_status': summary_data.get('processing_status', 'unknown'),
 'total_terms_found': summary_data.get('total_terms_found', 0),
 'spanner_terms': summary_data.get('spanner_terms', 0),
 'gemini_terms': summary_data.get('gemini_terms', 0),
 'processing_method': summary_data.get('processing_method', 'unknown')
 }
 
 logger.info(f" LEGAL_SERVICE: Prepared firestore_data with {len(firestore_data)} fields")
 logger.info(f" LEGAL_SERVICE: Calling Firestore save_user_summary for user: {user_email}")
 
 doc_id = await self.firestore_service.save_user_summary(user_email, firestore_data)
 
 if doc_id:
 logger.info(f" LEGAL_SERVICE: Summary saved successfully for user {user_email} with ID: {doc_id}")
 else:
 logger.warning(f" LEGAL_SERVICE: Firestore save returned None for user: {user_email}")
 
 return doc_id
 
 except Exception as e:
 logger.error(f" LEGAL_SERVICE: Error saving summary for user {user_email}: {str(e)}")
 return None
 
 async def get_user_summaries(self, user_email: str, limit: int = 10) -> List[Dict]:
 """
 Get user's saved summaries from Firestore.
 
 Args:
 user_email: User's email address
 limit: Maximum number of summaries to return
 
 Returns:
 List of summary documents
 """
 try:
 logger.info(f"Getting summaries from Firestore for user: {user_email}")
 return await self.firestore_service.get_user_summaries(user_email, limit)
 except Exception as e:
 logger.error(f"Error getting summaries for user {user_email}: {str(e)}")
 return []
 
 async def get_summary_by_id(self, user_email: str, summary_id: str) -> Optional[Dict]:
 """
 Get a specific summary by ID.
 
 Args:
 user_email: User's email address
 summary_id: Summary document ID
 
 Returns:
 Summary document if found, None otherwise
 """
 try:
 return await self.firestore_service.get_summary_by_id(user_email, summary_id)
 except Exception as e:
 logger.error(f"Error getting summary {summary_id} for user {user_email}: {str(e)}")
 return None