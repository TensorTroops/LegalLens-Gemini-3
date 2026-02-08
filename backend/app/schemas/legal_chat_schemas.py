"""
Schemas for Legal Chat API
==========================
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LegalTermSchema(BaseModel):
 """Schema for legal term with definition."""
 term: str
 definition: str
 source: str = Field(description="Source of definition: 'spanner' or 'gemini'")

class ProcessDocumentRequest(BaseModel):
 """Request schema for processing legal document text."""
 extracted_text: str = Field(description="Text extracted from legal document")
 user_email: str = Field(description="Email of the user")
 document_title: Optional[str] = Field(default=None, description="Optional title for the document")

class ProcessDocumentResponse(BaseModel):
 """Response schema for processed legal document."""
 original_text: str
 simplified_text: str
 extracted_terms: List[LegalTermSchema]
 processing_status: str
 terms_count: int
 spanner_matches: int
 gemini_fallbacks: int
 error_message: Optional[str] = None

class SaveSummaryRequest(BaseModel):
 """Request schema for saving document summary."""
 user_email: str
 summary_data: Dict[str, Any]
 document_title: Optional[str] = None

class SaveSummaryResponse(BaseModel):
 """Response schema for saved summary."""
 success: bool
 document_id: Optional[str] = None
 message: str

class SummarySchema(BaseModel):
 """Schema for user summary document."""
 id: str
 original_text: str
 simplified_text: str
 extracted_terms: List[LegalTermSchema]
 document_title: str
 processing_status: str
 terms_count: int
 spanner_matches: int
 gemini_fallbacks: int
 created_at: datetime
 updated_at: Optional[datetime] = None

class GetSummariesResponse(BaseModel):
 """Response schema for user summaries."""
 summaries: List[SummarySchema]
 total_count: int
 user_email: str

class ChatMessageSchema(BaseModel):
 """Schema for chat message."""
 id: str
 message: str
 timestamp: datetime
 is_user: bool
 message_type: str = Field(default="text", description="Type: text, document, summary")

class ChatSessionSchema(BaseModel):
 """Schema for chat session."""
 session_id: str
 user_email: str
 messages: List[ChatMessageSchema]
 created_at: datetime
 last_activity: datetime