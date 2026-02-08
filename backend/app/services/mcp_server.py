"""
Model Context Protocol (MCP) Server for LegalLens
=================================================

Intelligent routing layer powered by Gemini 3 that orchestrates between:
- Gemini 3 Pro/Flash AI for processing (thinking levels, search grounding)
- Cloud Spanner for term lookup
- Document AI for text extraction
- Vector embeddings for context
"""
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
from datetime import datetime

from app.services.gemini_service import GeminiService
from app.services.spanner_service import SpannerService
from app.services.document_ai_service import DocumentAIService
from app.services.firestore_service import FirestoreService
from app.services.gcul_blockchain_service import get_gcul_service
from app.services.comprehensive_legal_analyzer import ComprehensiveLegalAnalyzer

logger = logging.getLogger(__name__)

class ProcessingIntent(Enum):
 """Define different processing intents for routing decisions."""
 DOCUMENT_ANALYSIS = "document_analysis"
 TERM_LOOKUP = "term_lookup"
 TEXT_SIMPLIFICATION = "text_simplification"
 LEGAL_QUERY = "legal_query"
 SUMMARY_GENERATION = "summary_generation"
 COMPREHENSIVE_PROCESSING = "comprehensive_processing"
 COMPREHENSIVE_LEGAL_ANALYSIS = "comprehensive_legal_analysis" # New comprehensive analysis
 GENERAL_QUESTION = "general_question"
 DOCUMENT_QUESTION = "document_question"

class MCPToolResult:
 """Standardized result format for MCP tool responses."""
 
 def __init__(self, success: bool, data: Any = None, error: str = None, 
 source: str = None, processing_time: float = None):
 self.success = success
 self.data = data
 self.error = error
 self.source = source
 self.processing_time = processing_time
 self.timestamp = datetime.utcnow()
 
 def to_dict(self) -> Dict:
 return {
 'success': self.success,
 'data': self.data,
 'error': self.error,
 'source': self.source,
 'processing_time': self.processing_time,
 'timestamp': self.timestamp.isoformat()
 }

class MCPServer:
 """
 Model Context Protocol Server - Intelligent routing and orchestration layer.
 
 This server acts as the central intelligence that:
 1. Analyzes user requests to determine processing intent
 2. Routes requests to appropriate services
 3. Orchestrates multi-service workflows
 4. Manages tool arguments and context
 5. Provides intelligent fallbacks
 """
 
 def __init__(self):
 # Initialize all services
 self.gemini_service = GeminiService()
 self.spanner_service = SpannerService()
 self.document_ai_service = DocumentAIService()
 self.firestore_service = FirestoreService()
 self.gcul_service = get_gcul_service()
 self.comprehensive_analyzer = ComprehensiveLegalAnalyzer()
 
 # Service availability tracking
 self.service_status = {}
 
 logger.info(" MCP Server initialized with all services including GCUL blockchain security")
 
 async def route_request(self, intent: ProcessingIntent, **kwargs) -> MCPToolResult:
 """
 Main routing function that directs requests to appropriate handlers.
 
 Args:
 intent: The processing intent
 **kwargs: Arguments specific to the intent
 
 Returns:
 MCPToolResult with the processed response
 """
 start_time = datetime.utcnow()
 
 try:
 logger.info(f" MCP SERVER: Routing request with intent: {intent.value}")
 logger.info(f" MCP SERVER: Request arguments: {list(kwargs.keys())}")
 
 # Route based on intent
 if intent == ProcessingIntent.DOCUMENT_ANALYSIS:
 logger.info(" MCP SERVER: Handling DOCUMENT_ANALYSIS workflow")
 result = await self._handle_document_analysis(**kwargs)
 elif intent == ProcessingIntent.TERM_LOOKUP:
 logger.info(" MCP SERVER: Handling TERM_LOOKUP workflow")
 result = await self._handle_term_lookup(**kwargs)
 elif intent == ProcessingIntent.TEXT_SIMPLIFICATION:
 logger.info(" MCP SERVER: Handling TEXT_SIMPLIFICATION workflow")
 result = await self._handle_text_simplification(**kwargs)
 elif intent == ProcessingIntent.LEGAL_QUERY:
 logger.info(" MCP SERVER: Handling LEGAL_QUERY workflow")
 result = await self._handle_legal_query(**kwargs)
 elif intent == ProcessingIntent.SUMMARY_GENERATION:
 logger.info(" MCP SERVER: Handling SUMMARY_GENERATION workflow")
 result = await self._handle_summary_generation(**kwargs)
 elif intent == ProcessingIntent.COMPREHENSIVE_PROCESSING:
 logger.info(" MCP SERVER: Handling COMPREHENSIVE_PROCESSING workflow")
 result = await self._handle_comprehensive_processing(**kwargs)
 elif intent == ProcessingIntent.COMPREHENSIVE_LEGAL_ANALYSIS:
 logger.info(" MCP SERVER: Handling COMPREHENSIVE_LEGAL_ANALYSIS workflow")
 result = await self._handle_comprehensive_legal_analysis(**kwargs)
 elif intent == ProcessingIntent.GENERAL_QUESTION:
 logger.info(" MCP SERVER: Handling GENERAL_QUESTION workflow")
 result = await self._handle_general_question(**kwargs)
 elif intent == ProcessingIntent.DOCUMENT_QUESTION:
 logger.info(" MCP SERVER: Handling DOCUMENT_QUESTION workflow")
 result = await self._handle_document_question(**kwargs)
 else:
 logger.error(f" MCP SERVER: Unknown intent: {intent.value}")
 result = MCPToolResult(
 success=False,
 error=f"Unknown intent: {intent.value}",
 source="mcp_server"
 )
 
 # Calculate processing time
 processing_time = (datetime.utcnow() - start_time).total_seconds()
 result.processing_time = processing_time
 
 if result.success:
 logger.info(f" MCP SERVER: Request completed successfully in {processing_time:.2f}s")
 logger.info(f" MCP SERVER: Result source: {result.source}")
 else:
 logger.error(f" MCP SERVER: Request failed in {processing_time:.2f}s - {result.error}")
 
 return result
 
 except Exception as e:
 processing_time = (datetime.utcnow() - start_time).total_seconds()
 logger.error(f"Error in route_request: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"MCP routing error: {str(e)}",
 source="mcp_server",
 processing_time=processing_time
 )
 
 async def _handle_document_analysis(self, file_content: bytes, mime_type: str, 
 user_email: str = None) -> MCPToolResult:
 """Handle document analysis workflow with GCUL blockchain security."""
 try:
 logger.info(" MCP: Processing document analysis with blockchain security")
 document_id = f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_email or 'unknown'}"
 
 # Step 1: Extract text using Document AI
 extracted_data = await self.document_ai_service.process_document(
 file_content, mime_type
 )
 
 if not extracted_data or not extracted_data.get("text"):
 return MCPToolResult(
 success=False,
 error="Failed to extract text from document",
 source="document_ai"
 )
 
 # Step 2: GCUL Blockchain Security Integration
 logger.info(" MCP: Creating blockchain security records")
 try:
 # Encrypt document
 encryption_metadata = {
 'filename': f"{document_id}.{mime_type.split('/')[-1]}",
 'mime_type': mime_type,
 'user_id': user_email or 'unknown',
 'document_id': document_id
 }
 
 blob_name, enc_metadata = await self.gcul_service.encrypt_document(
 file_content, encryption_metadata
 )
 
 # Create hash record for blockchain
 hash_id = await self.gcul_service.create_document_hash_record(
 document_id=document_id,
 content=file_content,
 extracted_text=extracted_data["text"],
 user_id=user_email or 'unknown',
 metadata=encryption_metadata
 )
 
 logger.info(f" MCP: Document secured in blockchain - Hash ID: {hash_id}")
 
 except Exception as blockchain_error:
 logger.warning(f" MCP: Blockchain security failed, continuing without: {blockchain_error}")
 # Continue processing even if blockchain fails
 blob_name = None
 hash_id = None
 enc_metadata = {}
 
 # Step 3: Proceed with comprehensive processing
 comprehensive_result = await self._handle_comprehensive_processing(
 text=extracted_data["text"],
 user_email=user_email
 )
 
 # Step 4: Combine all results
 if comprehensive_result.success:
 combined_data = {
 'document_id': document_id,
 'document_extraction': extracted_data,
 'comprehensive_analysis': comprehensive_result.data,
 'blockchain_security': {
 'secured': blob_name is not None,
 'hash_id': hash_id,
 'encrypted_blob': blob_name,
 'encryption_metadata': enc_metadata
 },
 'workflow': 'secure_document_to_analysis'
 }
 
 return MCPToolResult(
 success=True,
 data=combined_data,
 source="mcp_secure_document_analysis"
 )
 else:
 # Return extraction + security info even if comprehensive processing failed
 return MCPToolResult(
 success=True,
 data={
 'document_id': document_id,
 'document_extraction': extracted_data,
 'blockchain_security': {
 'secured': blob_name is not None,
 'hash_id': hash_id,
 'encrypted_blob': blob_name
 },
 'comprehensive_analysis_error': comprehensive_result.error,
 'workflow': 'secure_document_extraction_only'
 },
 source="mcp_secure_document_analysis_partial"
 )
 
 except Exception as e:
 logger.error(f" MCP: Error in secure document analysis: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Secure document analysis failed: {str(e)}",
 source="mcp_secure_document_analysis"
 )
 
 async def _handle_term_lookup(self, term: str, context: str = None) -> MCPToolResult:
 """Handle term lookup with intelligent fallback."""
 try:
 logger.info(f"Looking up term: {term}")
 
 # Step 1: Try Spanner database first
 spanner_definition = await self.spanner_service.get_legal_term_definition(term)
 
 if spanner_definition:
 return MCPToolResult(
 success=True,
 data={
 'term': term,
 'definition': spanner_definition,
 'source': 'spanner_database',
 'context_used': context is not None
 },
 source="mcp_term_lookup"
 )
 
 # Step 2: Fallback to Gemini AI
 logger.info(f"Term '{term}' not found in Spanner, using Gemini fallback")
 
 if context:
 gemini_definition = await self.gemini_service.get_term_definition(term, context)
 else:
 gemini_definition = await self.gemini_service.get_standalone_legal_definition(term)
 
 if gemini_definition:
 return MCPToolResult(
 success=True,
 data={
 'term': term,
 'definition': gemini_definition,
 'source': 'gemini_ai_fallback',
 'context_used': context is not None
 },
 source="mcp_term_lookup"
 )
 
 # Step 3: No definition found
 return MCPToolResult(
 success=False,
 error=f"No definition found for term '{term}' in any source",
 source="mcp_term_lookup"
 )
 
 except Exception as e:
 logger.error(f"Error in term lookup: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Term lookup failed: {str(e)}",
 source="mcp_term_lookup"
 )
 
 async def _handle_text_simplification(self, text: str) -> MCPToolResult:
 """Handle text simplification using Gemini."""
 try:
 logger.info("Processing text simplification request")
 
 simplified_text = await self.gemini_service.simplify_legal_text(text)
 
 if simplified_text:
 return MCPToolResult(
 success=True,
 data={
 'original_text': text,
 'simplified_text': simplified_text,
 'word_count_reduction': len(text.split()) - len(simplified_text.split())
 },
 source="mcp_text_simplification"
 )
 else:
 return MCPToolResult(
 success=False,
 error="Failed to simplify text",
 source="gemini_service"
 )
 
 except Exception as e:
 logger.error(f"Error in text simplification: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Text simplification failed: {str(e)}",
 source="mcp_text_simplification"
 )
 
 async def _handle_legal_query(self, text: str, user_email: str = None, context: str = None) -> MCPToolResult:
 """Handle general legal queries."""
 try:
 logger.info(f" MCP LEGAL QUERY: Processing query from user: {user_email}")
 logger.info(f" MCP LEGAL QUERY: Query: {text[:100]}...")
 
 # For now, use Gemini for general legal questions
 # This could be enhanced with RAG using vector embeddings
 
 response = await self.gemini_service.get_standalone_legal_definition(text)
 
 if response:
 logger.info(" MCP LEGAL QUERY: Response generated successfully")
 return MCPToolResult(
 success=True,
 data={
 'query': text,
 'response': response,
 'context_used': context is not None,
 'user_email': user_email
 },
 source="mcp_legal_query"
 )
 else:
 logger.warning(" MCP LEGAL QUERY: Failed to generate response")
 return MCPToolResult(
 success=False,
 error="Failed to process legal query",
 source="gemini_service"
 )
 
 except Exception as e:
 logger.error(f"Error in legal query: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Legal query failed: {str(e)}",
 source="mcp_legal_query"
 )
 
 async def _handle_summary_generation(self, text: str, user_email: str = None) -> MCPToolResult:
 """Handle summary generation workflow."""
 try:
 logger.info("Processing summary generation request")
 
 # Use comprehensive simplification for summary
 summary_data = await self.gemini_service.comprehensive_simplification(text)
 
 # Optionally save to Firestore if user_email provided
 document_id = None
 if user_email and summary_data:
 try:
 document_id = await self.firestore_service.save_user_summary(
 user_email,
 {
 'original_text': text,
 'simplified_text': summary_data.get('simplified_text', ''),
 'extracted_terms': [
 {'term': term, 'definition': definition}
 for term, definition in summary_data.get('complex_terms', {}).items()
 ],
 'processing_method': 'mcp_summary_generation'
 }
 )
 except Exception as save_error:
 logger.warning(f"Failed to save summary: {save_error}")
 
 return MCPToolResult(
 success=True,
 data={
 **summary_data,
 'document_id': document_id,
 'saved_to_firestore': document_id is not None
 },
 source="mcp_summary_generation"
 )
 
 except Exception as e:
 logger.error(f"Error in summary generation: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Summary generation failed: {str(e)}",
 source="mcp_summary_generation"
 )
 
 async def _handle_comprehensive_processing(self, text: str, user_email: str = None) -> MCPToolResult:
 """
 Handle comprehensive document processing workflow.
 
 This is the main processing pipeline that:
 1. Simplifies text using Gemini
 2. Extracts complex terms
 3. Looks up terms in Spanner
 4. Uses Gemini fallback for missing terms
 5. Combines everything into a comprehensive result
 """
 try:
 logger.info(" MCP COMPREHENSIVE: Starting comprehensive document analysis")
 logger.info(f" MCP COMPREHENSIVE: Text length: {len(text)} characters")
 if user_email:
 logger.info(f" MCP COMPREHENSIVE: Processing for user: {user_email}")
 
 # Step 1: Get comprehensive simplification from Gemini
 logger.info(" MCP COMPREHENSIVE: Step 1 - Getting Gemini simplification")
 gemini_result = await self.gemini_service.comprehensive_simplification(text)
 
 if not gemini_result:
 return MCPToolResult(
 success=False,
 error="Failed to get comprehensive analysis from Gemini",
 source="gemini_service"
 )
 
 # Step 2: Process complex terms through Spanner lookup
 complex_terms = gemini_result.get('complex_terms', {})
 logger.info(f" MCP COMPREHENSIVE: Step 2 - Processing {len(complex_terms)} complex terms")
 enhanced_terms = []
 spanner_matches = 0
 gemini_matches = len(complex_terms)
 
 for term, gemini_definition in complex_terms.items():
 # Try to get more authoritative definition from Spanner
 logger.info(f" MCP COMPREHENSIVE: Looking up term '{term}' in Spanner database")
 spanner_definition = await self.spanner_service.get_legal_term_definition(term)
 
 if spanner_definition:
 logger.info(f" MCP COMPREHENSIVE: Found '{term}' in Spanner database")
 enhanced_terms.append({
 'term': term,
 'definition': spanner_definition,
 'source': 'spanner_database',
 'gemini_definition': gemini_definition
 })
 spanner_matches += 1
 else:
 logger.info(f" MCP COMPREHENSIVE: Term '{term}' not in Spanner, using Gemini definition")
 enhanced_terms.append({
 'term': term,
 'definition': gemini_definition,
 'source': 'gemini_ai',
 'spanner_checked': True
 })
 
 # Step 3: Scan text for additional Spanner terms not caught by Gemini
 logger.info(" MCP COMPREHENSIVE: Step 3 - Scanning for additional Spanner terms")
 additional_spanner_terms = await self.spanner_service.find_terms_in_text(text)
 
 # Add terms that Gemini missed but exist in Spanner
 for term, definition in additional_spanner_terms.items():
 # Check if we already have this term
 if not any(t['term'].lower() == term.lower() for t in enhanced_terms):
 enhanced_terms.append({
 'term': term,
 'definition': definition,
 'source': 'spanner_additional',
 'found_by_scan': True
 })
 spanner_matches += 1
 
 # Step 4: Compile comprehensive result
 comprehensive_data = {
 'original_text': text,
 'simplified_text': gemini_result.get('simplified_text', text),
 'enhanced_terms': enhanced_terms,
 'processing_stats': {
 'original_word_count': gemini_result.get('original_word_count', 0),
 'simplified_word_count': gemini_result.get('simplified_word_count', 0),
 'reduction_percentage': gemini_result.get('reduction_percentage', 0),
 'total_terms': len(enhanced_terms),
 'spanner_matches': spanner_matches,
 'gemini_matches': gemini_matches,
 'additional_spanner_terms': len(additional_spanner_terms)
 },
 'processing_workflow': 'mcp_comprehensive'
 }
 
 logger.info(f" MCP COMPREHENSIVE: Processing completed successfully!")
 logger.info(f" MCP COMPREHENSIVE: {len(enhanced_terms)} total terms identified")
 logger.info(f" MCP COMPREHENSIVE: {spanner_matches} terms from Spanner database")
 logger.info(f" MCP COMPREHENSIVE: {gemini_matches} terms from Gemini AI")
 logger.info(f" MCP COMPREHENSIVE: Text reduced by {comprehensive_data['processing_stats']['reduction_percentage']}%")
 
 return MCPToolResult(
 success=True,
 data=comprehensive_data,
 source="mcp_comprehensive_processing"
 )
 
 except Exception as e:
 logger.error(f"Error in comprehensive processing: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Comprehensive processing failed: {str(e)}",
 source="mcp_comprehensive_processing"
 )
 
 async def _handle_comprehensive_legal_analysis(self, text: str, user_email: str = None) -> MCPToolResult:
 """
 Handle comprehensive legal analysis for professional legal reports.
 
 This uses the new ComprehensiveLegalAnalyzer to generate:
 1. Document Summary (for chat display)
 2. Legal Terms and Meanings (for PDF report)
 3. Risk Analysis (for PDF report) 
 4. Applicable Laws (for PDF report)
 """
 try:
 logger.info(" MCP LEGAL ANALYSIS: Starting comprehensive legal document analysis")
 
 # Use the comprehensive analyzer
 analysis_result = await self.comprehensive_analyzer.analyze_document(text, user_email)
 
 logger.info(" MCP LEGAL ANALYSIS: Analysis completed successfully")
 return MCPToolResult(
 success=True,
 data=analysis_result,
 source="comprehensive_legal_analyzer"
 )
 
 except Exception as e:
 logger.error(f" MCP LEGAL ANALYSIS: Analysis failed: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Comprehensive legal analysis failed: {str(e)}",
 source="comprehensive_legal_analyzer"
 )
 
 async def analyze_user_intent(self, user_input: str, context: Dict = None) -> ProcessingIntent:
 """
 Analyze user input to determine the appropriate processing intent.
 
 This could be enhanced with ML models, but for now uses rule-based logic.
 """
 user_input_lower = user_input.lower()
 
 # Document-related keywords
 if any(keyword in user_input_lower for keyword in 
 ['upload', 'document', 'pdf', 'analyze document', 'process file']):
 return ProcessingIntent.DOCUMENT_ANALYSIS
 
 # Term lookup keywords
 if any(keyword in user_input_lower for keyword in 
 ['what is', 'define', 'meaning of', 'explain', 'what does', 'means']):
 return ProcessingIntent.TERM_LOOKUP
 
 # Simplification keywords
 if any(keyword in user_input_lower for keyword in 
 ['simplify', 'make simple', 'explain simply', 'break down']):
 return ProcessingIntent.TEXT_SIMPLIFICATION
 
 # Summary keywords
 if any(keyword in user_input_lower for keyword in 
 ['summarize', 'summary', 'key points', 'overview']):
 return ProcessingIntent.SUMMARY_GENERATION
 
 # Comprehensive processing keywords
 if any(keyword in user_input_lower for keyword in 
 ['comprehensive', 'full analysis', 'complete analysis']):
 return ProcessingIntent.COMPREHENSIVE_PROCESSING
 
 # Default to legal query for other inputs
 return ProcessingIntent.LEGAL_QUERY
 
 async def health_check(self) -> Dict[str, Any]:
 """Check health of all connected services."""
 health_status = {
 'mcp_server': 'healthy',
 'timestamp': datetime.utcnow().isoformat(),
 'services': {}
 }
 
 # Check each service
 try:
 gemini_health = await self._check_gemini_health()
 health_status['services']['gemini'] = gemini_health
 except Exception as e:
 health_status['services']['gemini'] = {'status': 'error', 'error': str(e)}
 
 try:
 spanner_health = self.spanner_service.database is not None
 health_status['services']['spanner'] = {
 'status': 'healthy' if spanner_health else 'unavailable',
 'database_connected': spanner_health
 }
 except Exception as e:
 health_status['services']['spanner'] = {'status': 'error', 'error': str(e)}
 
 try:
 doc_ai_health = self.document_ai_service.health_check()
 health_status['services']['document_ai'] = doc_ai_health
 except Exception as e:
 health_status['services']['document_ai'] = {'status': 'error', 'error': str(e)}
 
 return health_status
 
 async def _handle_general_question(self, text: str = None, user_question: str = None, 
 user_email: str = None) -> MCPToolResult:
 """
 Handle general legal questions without document context.
 Uses Gemini to provide informative responses to legal queries.
 """
 try:
 question = user_question or text
 logger.info(f" MCP GENERAL: Processing general question: {question[:50]}...")
 
 # Use Gemini to answer general legal questions
 prompt = f"""
 You are a helpful legal assistant. Answer this legal question in a clear, informative way:
 
 Question: {question}
 
 Provide a helpful response that:
 - Explains legal concepts clearly
 - Uses simple language
 - Includes relevant legal terms with definitions
 - Reminds that this is informational, not legal advice
 
 Format your response naturally for a chat conversation.
 """
 
 # Get response from Gemini 3 with Google Search grounding for accurate legal info
 response = await self.gemini_service.generate_grounded_response(prompt)
 
 if response:
 cleaned_response = response.strip()
 
 return MCPToolResult(
 success=True,
 data={
 'response': cleaned_response,
 'simplified_text': cleaned_response,
 'question': question,
 'response_type': 'general_legal_question',
 'gemini_3_features': ['google_search_grounding']
 },
 source="mcp_general_question"
 )
 else:
 raise Exception("No response from Gemini")
 
 except Exception as e:
 logger.error(f" MCP GENERAL: Error processing question: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"General question processing error: {str(e)}",
 source="mcp_general_question"
 )
 
 async def _handle_document_question(self, text: str = None, user_question: str = None, 
 user_email: str = None) -> MCPToolResult:
 """
 Handle questions about an uploaded document.
 Uses document context to provide specific answers.
 """
 try:
 # Split text to get document content and question
 if '\n\nUser Question:' in text:
 document_content, question = text.split('\n\nUser Question:', 1)
 else:
 document_content = text
 question = user_question or "What is this document about?"
 
 logger.info(f" MCP DOCUMENT Q: Document length: {len(document_content)} chars")
 logger.info(f" MCP DOCUMENT Q: Question: {question[:50]}...")
 
 # Use Gemini to analyze document and answer question
 prompt = f"""
 Based on this legal document, answer the user's question:
 
 DOCUMENT:
 {document_content}
 
 USER QUESTION: {question}
 
 Provide a helpful response that:
 - Directly answers their question based on the document
 - References specific parts of the document when relevant
 - Explains any legal terms mentioned
 - Uses clear, understandable language
 
 Format your response naturally for a chat conversation.
 """
 
 # Get response from Gemini 3 Pro with high thinking for document analysis
 response = await self.gemini_service.generate_response(
 prompt,
 use_pro=True,
 thinking="high"
 )
 
 if response:
 cleaned_response = response.strip()
 
 return MCPToolResult(
 success=True,
 data={
 'response': cleaned_response,
 'simplified_text': cleaned_response,
 'question': question,
 'document_length': len(document_content),
 'response_type': 'document_specific_answer',
 'gemini_3_features': ['thinking_high', 'pro_model']
 },
 source="mcp_document_question"
 )
 else:
 raise Exception("No response from Gemini")
 
 except Exception as e:
 logger.error(f" MCP DOCUMENT Q: Error processing question: {str(e)}")
 return MCPToolResult(
 success=False,
 error=f"Document question processing error: {str(e)}",
 source="mcp_document_question"
 )
 
 async def _check_gemini_health(self) -> Dict[str, Any]:
 """Check if Gemini service is responsive."""
 try:
 # Simple test with Gemini
 test_result = await self.gemini_service.get_standalone_legal_definition("contract")
 return {
 'status': 'healthy' if test_result else 'degraded',
 'responsive': test_result is not None
 }
 except Exception as e:
 return {'status': 'error', 'error': str(e)}

# Global MCP Server instance
mcp_server = MCPServer()

def get_mcp_server() -> MCPServer:
 """Get the global MCP server instance."""
 return mcp_server