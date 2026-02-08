"""
Google Cloud Spanner Service for Legal Terms
============================================
"""

import logging
from typing import Dict, List, Optional
from google.cloud import spanner
from app.config.settings import get_settings
from app.utils.credentials import get_credentials, get_project_id, is_credentials_available

logger = logging.getLogger(__name__)

class SpannerService:
 """Service for interacting with Google Cloud Spanner database."""
 
 def __init__(self):
 self.settings = get_settings()
 
 # Check if credentials are available
 if not is_credentials_available():
 logger.warning(" No service account credentials found. Spanner services will be unavailable.")
 self.client = None
 self.instance = None
 self.database = None
 return

 try:
 # Initialize client with credentials from base64
 credentials = get_credentials()
 project_id = get_project_id() or self.settings.GCP_PROJECT_ID
 
 self.client = spanner.Client(
 project=project_id,
 credentials=credentials
 )
 self.instance = self.client.instance(self.settings.SPANNER_INSTANCE_ID)
 self.database = self.instance.database(self.settings.SPANNER_DATABASE_ID)
 logger.info(" Spanner client initialized successfully with base64 credentials")
 except Exception as e:
 logger.error(f" Failed to initialize Spanner client: {str(e)}")
 self.client = None
 self.instance = None
 self.database = None
 self.client = None
 self.instance = None
 self.database = None
 
 async def get_legal_term_definition(self, term: str) -> Optional[str]:
 """
 Get definition for a single legal term from Spanner database.
 
 Args:
 term: The legal term to look up
 
 Returns:
 Definition string if found, None otherwise
 """
 if not self.database:
 logger.warning("Spanner database not available")
 return None
 
 try:
 with self.database.snapshot() as snapshot:
 logger.info(f"Searching Spanner for term: '{term}'")
 
 # First try exact match (case-insensitive)
 query = """
 SELECT term, meaning 
 FROM LegalTerm 
 WHERE LOWER(term) = LOWER(@term)
 LIMIT 1
 """
 results = snapshot.execute_sql(
 query,
 params={"term": term},
 param_types={"term": spanner.param_types.STRING}
 )
 
 for row in results:
 found_term, meaning = row
 logger.info(f"Found exact match for term '{term}' -> '{found_term}': {meaning}")
 return meaning
 
 # If no exact match, try partial matching
 logger.info(f"No exact match for '{term}', trying partial match")
 partial_query = """
 SELECT term, meaning 
 FROM LegalTerm 
 WHERE LOWER(term) LIKE LOWER(@term_pattern)
 ORDER BY 
 CASE 
 WHEN LOWER(term) = LOWER(@exact_term) THEN 1
 WHEN LOWER(term) LIKE LOWER(@term_start) THEN 2
 ELSE 3
 END
 LIMIT 5
 """
 term_pattern = f"%{term}%"
 term_start = f"{term}%"
 partial_results = snapshot.execute_sql(
 partial_query,
 params={
 "term_pattern": term_pattern,
 "exact_term": term,
 "term_start": term_start
 },
 param_types={
 "term_pattern": spanner.param_types.STRING,
 "exact_term": spanner.param_types.STRING,
 "term_start": spanner.param_types.STRING
 }
 )
 
 for row in partial_results:
 found_term, meaning = row
 logger.info(f"Found partial match: '{found_term}' for search term '{term}': {meaning}")
 # Return the first partial match
 return meaning
 
 # Let's also try a broader search to see what terms exist
 logger.info(f"No matches found for '{term}', checking if any terms exist in database")
 check_query = "SELECT COUNT(*) FROM LegalTerm"
 count_results = snapshot.execute_sql(check_query)
 for row in count_results:
 total_terms = row[0]
 logger.info(f"Total terms in database: {total_terms}")
 break
 
 # Show a few sample terms for debugging
 sample_query = "SELECT term FROM LegalTerm LIMIT 5"
 sample_results = snapshot.execute_sql(sample_query)
 sample_terms = []
 for row in sample_results:
 sample_terms.append(row[0])
 logger.info(f"Sample terms in database: {sample_terms}")
 
 return None
 
 except Exception as e:
 logger.error(f"Error querying Spanner for term '{term}': {str(e)}")
 return None
 
 except Exception as e:
 logger.error(f"Error querying Spanner for term '{term}': {str(e)}")
 return None
 
 async def find_terms_in_text(self, text: str) -> Dict[str, str]:
 """
 Scan ALL Spanner terms against the provided text and return matches.
 
 Args:
 text: The text to scan for legal terms
 
 Returns:
 Dictionary mapping found terms to their definitions
 """
 if not self.database:
 logger.warning("Spanner database not available")
 return {}
 
 if not text:
 return {}
 
 try:
 import re
 
 # Get all terms from the database
 with self.database.snapshot() as snapshot:
 query = "SELECT term, meaning FROM LegalTerm"
 results = snapshot.execute_sql(query)
 
 found_terms = {}
 text_lower = text.lower()
 
 for row in results:
 term, meaning = row
 
 # Create regex pattern for case-insensitive whole word matching
 pattern = re.compile(rf'\b{re.escape(term.lower())}\b', re.IGNORECASE)
 
 # Check if term exists in text
 if pattern.search(text_lower):
 found_terms[term] = meaning
 logger.debug(f"Found Spanner term in text: '{term}'")
 
 logger.info(f"Found {len(found_terms)} Spanner terms in provided text")
 return found_terms
 
 except Exception as e:
 logger.error(f"Error scanning text for Spanner terms: {str(e)}")
 return {}

 async def get_multiple_terms_definitions(self, terms: List[str]) -> Dict[str, str]:
 """
 Get definitions for multiple legal terms in a single query.
 
 Args:
 terms: List of legal terms to look up
 
 Returns:
 Dictionary mapping terms to their definitions
 """
 if not self.database:
 logger.warning("Spanner database not available")
 return {}
 
 if not terms:
 return {}
 
 try:
 with self.database.snapshot() as snapshot:
 # Create parameterized query for multiple terms
 # Use LOWER() to make case-insensitive comparison
 placeholders = []
 params = {}
 param_types = {}
 
 for i, term in enumerate(terms):
 param_name = f"term_{i}"
 placeholders.append(f"LOWER(@{param_name})")
 params[param_name] = term.lower()
 param_types[param_name] = spanner.param_types.STRING
 
 placeholders_str = ", ".join(placeholders)
 
 query = f"""
 SELECT term, meaning 
 FROM LegalTerm 
 WHERE LOWER(term) IN ({placeholders_str})
 """
 
 results = snapshot.execute_sql(query, params=params, param_types=param_types)
 
 # Build result dictionary
 definitions = {}
 for row in results:
 term, meaning = row
 # Use the original case from database, but key with lowercase for matching
 for original_term in terms:
 if term.lower() == original_term.lower():
 definitions[original_term.lower()] = meaning
 break
 
 return definitions
 
 except Exception as e:
 logger.error(f"Error querying Spanner for multiple terms: {str(e)}")
 return {}
 
 async def add_legal_term(self, term_id: str, term: str, meaning: str) -> bool:
 """
 Add a new legal term to the database.
 
 Args:
 term_id: Unique identifier for the term
 term: The legal term
 meaning: Definition of the term
 
 Returns:
 True if successful, False otherwise
 """
 if not self.database:
 logger.warning("Spanner database not available")
 return False
 
 try:
 with self.database.batch() as batch:
 batch.insert(
 table="LegalTerm",
 columns=("term_id", "term", "meaning"),
 values=[(term_id, term, meaning)]
 )
 return True
 
 except Exception as e:
 logger.error(f"Error adding term to Spanner: {str(e)}")
 return False