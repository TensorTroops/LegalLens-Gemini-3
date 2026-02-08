"""
Dictionary API endpoints for legal terms
========================================
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from pydantic import BaseModel

from app.services.spanner_service import SpannerService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

# Pydantic models
class LegalTermResponse(BaseModel):
 term_id: str
 term: str
 original_meaning: str
 simplified_meaning: Optional[str] = None
 pronunciation: Optional[str] = None
 related_terms: Optional[List[str]] = None

class DictionarySearchResponse(BaseModel):
 success: bool
 data: Optional[LegalTermResponse] = None
 message: Optional[str] = None

class MultipleTermsResponse(BaseModel):
 success: bool
 data: Optional[List[LegalTermResponse]] = None
 message: Optional[str] = None

# Services will be initialized lazily
spanner_service = None
gemini_service = None

def get_spanner_service():
 """Get Spanner service instance (lazy initialization)."""
 global spanner_service
 if spanner_service is None:
 spanner_service = SpannerService()
 return spanner_service

def get_gemini_service():
 """Get Gemini service instance (lazy initialization)."""
 global gemini_service
 if gemini_service is None:
 gemini_service = GeminiService()
 return gemini_service

@router.get("/search", response_model=DictionarySearchResponse)
async def search_legal_term(
 term: str = Query(..., description="Legal term to search for")
):
 """
 Search for a specific legal term in Spanner database and return simplified meaning.
 
 This endpoint:
 1. Searches the Spanner database for the exact term
 2. If found, uses Gemini AI to simplify the meaning
 3. Returns both original and simplified meanings
 """
 try:
 logger.info(f"Searching for legal term: '{term}'")
 
 # Search in Spanner database first
 spanner_svc = get_spanner_service()
 original_meaning = await spanner_svc.get_legal_term_definition(term)
 simplified_meaning = None
 
 if original_meaning:
 logger.info(f"Found term '{term}' in Spanner database")
 # Use Gemini to simplify the meaning from Spanner
 try:
 gemini_svc = get_gemini_service()
 simplified_meaning = await gemini_svc.get_term_definition(term, original_meaning)
 logger.info(f"Generated simplified meaning for '{term}' using Gemini")
 except Exception as e:
 logger.warning(f"Failed to generate simplified meaning for '{term}': {str(e)}")
 else:
 logger.info(f"Term '{term}' not found in Spanner database, trying Gemini fallback")
 # Use Gemini as fallback to get definition
 try:
 gemini_svc = get_gemini_service()
 gemini_definition = await gemini_svc.get_term_definition(term, f"Please provide a clear legal definition for the term '{term}'")
 if gemini_definition:
 original_meaning = gemini_definition
 simplified_meaning = gemini_definition # Gemini already provides simplified meaning
 logger.info(f"Generated definition for '{term}' using Gemini fallback")
 else:
 logger.warning(f"Failed to get definition from Gemini for '{term}'")
 return DictionarySearchResponse(
 success=False,
 message=f"Term '{term}' not found in dictionary and could not generate definition"
 )
 except Exception as e:
 logger.error(f"Gemini fallback failed for '{term}': {str(e)}")
 return DictionarySearchResponse(
 success=False,
 message=f"Term '{term}' not found in dictionary and could not generate definition"
 )
 
 # Generate term ID
 term_id = term.lower().replace(' ', '_').replace('-', '_')
 
 # Generate pronunciation (basic version)
 pronunciation = f"[{term.lower()}]"
 
 term_response = LegalTermResponse(
 term_id=term_id,
 term=term,
 original_meaning=original_meaning,
 simplified_meaning=simplified_meaning,
 pronunciation=pronunciation,
 related_terms=[] # Could be enhanced to find related terms
 )
 
 return DictionarySearchResponse(
 success=True,
 data=term_response,
 message=f"Found definition for '{term}'"
 )
 
 except Exception as e:
 logger.error(f"Error searching for term '{term}': {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to search for term: {str(e)}"
 )

@router.get("/autocomplete", response_model=MultipleTermsResponse)
async def autocomplete_terms(
 q: str = Query(..., description="Query string for autocomplete")
):
 """
 Get autocomplete suggestions for legal terms.
 
 This is a simplified implementation that returns popular terms matching the query.
 In a full implementation, this would search the Spanner database for partial matches.
 """
 try:
 logger.info(f"Autocomplete search for: '{q}'")
 
 # For now, return a simple list of popular terms that match
 popular_terms = [
 "Subrogation",
 "Res Judicata", 
 "Affidavit",
 "Jurisdiction",
 "Indemnity",
 "Force Majeure",
 "Voir Dire",
 "Habeas Corpus",
 "Subpoena",
 "Warrant"
 ]
 
 # Filter terms that contain the query (case-insensitive)
 matching_terms = [
 term for term in popular_terms 
 if q.lower() in term.lower()
 ]
 
 # Limit to first 5 matches
 matching_terms = matching_terms[:5]
 
 # Create response objects
 results = []
 for term in matching_terms:
 term_id = term.lower().replace(' ', '_')
 
 # Try to get meaning from Spanner
 spanner_svc = get_spanner_service()
 meaning = await spanner_svc.get_legal_term_definition(term)
 if not meaning:
 meaning = f"Legal definition for {term}"
 
 results.append(LegalTermResponse(
 term_id=term_id,
 term=term,
 original_meaning=meaning,
 pronunciation=f"[{term.lower()}]"
 ))
 
 return MultipleTermsResponse(
 success=True,
 data=results,
 message=f"Found {len(results)} matching terms"
 )
 
 except Exception as e:
 logger.error(f"Error in autocomplete for '{q}': {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to get autocomplete suggestions: {str(e)}"
 )

@router.get("/popular", response_model=MultipleTermsResponse)
async def get_popular_terms():
 """
 Get a list of popular legal terms from Spanner database.
 """
 try:
 logger.info("Fetching popular legal terms from Spanner database")
 
 # Try to get terms from Spanner database
 popular_terms = []
 spanner_svc = get_spanner_service()
 
 if spanner_svc.database:
 try:
 with spanner_svc.database.snapshot() as snapshot:
 # Get a sample of terms from the database
 query = """
 SELECT term, meaning 
 FROM LegalTerm 
 ORDER BY term
 LIMIT 10
 """
 results = snapshot.execute_sql(query)
 
 for row in results:
 term_name, meaning = row
 popular_terms.append({
 'term': term_name,
 'meaning': meaning
 })
 
 logger.info(f"Retrieved {len(popular_terms)} terms from Spanner database")
 except Exception as e:
 logger.warning(f"Failed to get terms from Spanner: {str(e)}")
 popular_terms = []
 
 # If no terms from Spanner, use fallback terms
 if not popular_terms:
 logger.info("Using fallback popular terms")
 fallback_terms = [
 {"term": "Subrogation", "meaning": "The legal right of an insurer to pursue a third party responsible for an insurance loss to the insured, allowing the insurer to recover the amount paid to the policyholder."},
 {"term": "Res Judicata", "meaning": "A legal doctrine that bars continued litigation of a case that has already been conclusively decided by a competent court."},
 {"term": "Affidavit", "meaning": "A written statement confirmed by oath or affirmation, for use as evidence in court."},
 {"term": "Jurisdiction", "meaning": "The authority given to a legal body, such as a court, to administer justice within a defined field of responsibility."},
 {"term": "Indemnity", "meaning": "A contractual obligation of one party to compensate the loss incurred by another party due to acts of the indemnifier or any other party."}
 ]
 popular_terms = fallback_terms
 
 # Build response objects
 results = []
 for term_data in popular_terms:
 term_id = term_data['term'].lower().replace(' ', '_')
 term_name = term_data['term']
 meaning = term_data['meaning']
 
 # Try to get simplified meaning from Gemini
 simplified_meaning = None
 try:
 gemini_svc = get_gemini_service()
 simplified_meaning = await gemini_svc.get_term_definition(term_name, meaning)
 except Exception as e:
 logger.warning(f"Failed to simplify meaning for '{term_name}': {str(e)}")
 
 results.append(LegalTermResponse(
 term_id=term_id,
 term=term_name,
 original_meaning=meaning,
 simplified_meaning=simplified_meaning,
 pronunciation=f"[{term_name.lower()}]"
 ))
 
 return MultipleTermsResponse(
 success=True,
 data=results,
 message=f"Retrieved {len(results)} popular terms"
 )
 
 except Exception as e:
 logger.error(f"Error fetching popular terms: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to get popular terms: {str(e)}"
 )

@router.get("/health")
async def dictionary_health_check():
 """
 Health check endpoint for dictionary service.
 """
 spanner_svc = get_spanner_service()
 gemini_svc = get_gemini_service()
 
 spanner_status = "connected" if spanner_svc.database else "disconnected"
 gemini_status = "available" if gemini_svc.model else "unavailable"
 
 return {
 "status": "healthy",
 "spanner_database": spanner_status,
 "gemini_service": gemini_status,
 "timestamp": "2024-01-01T00:00:00Z"
 }