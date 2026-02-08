"""
Gemini AI Service for Legal Term Processing
==========================================
"""

import logging
import re
from typing import List, Dict, Optional
import google.generativeai as genai
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Gemini AI for legal term processing."""
    
    def __init__(self):
        self.settings = get_settings()
        if self.settings.GEMINI_API_KEY:
            genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def extract_complex_legal_terms(self, text: str) -> List[str]:
        """
        Extract complex legal terms from the given text using Gemini AI.
        
        Args:
            text: The legal text to analyze
            
        Returns:
            List of complex legal terms found in the text
        """
        try:
            prompt = f"""
            Analyze the following legal text and identify complex legal terms, jargon, and phrases that would be difficult for a layperson to understand. 

            Focus on:
            - Legal terminology and jargon
            - Latin phrases commonly used in law
            - Technical legal concepts
            - Complex procedural terms
            - Legal obligations and conditions
            - Formal legal language that could be simplified

            Return only the complex terms as a comma-separated list, without any explanations or additional text.

            Text to analyze:
            {text}

            Complex legal terms:
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Parse the response to extract terms
                terms_text = response.text.strip()
                terms = [term.strip() for term in terms_text.split(',') if term.strip()]
                
                # Clean up terms (remove quotes, extra spaces, etc.)
                cleaned_terms = []
                for term in terms:
                    cleaned_term = term.strip('"\'.,;')
                    if cleaned_term and len(cleaned_term) > 1:
                        cleaned_terms.append(cleaned_term)
                
                logger.info(f"Extracted {len(cleaned_terms)} complex legal terms")
                return cleaned_terms
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting legal terms with Gemini: {str(e)}")
            return []
    
    async def get_term_definition(self, term: str, context: str) -> Optional[str]:
        """
        Get definition for a legal term using Gemini AI with context.
        
        Args:
            term: The legal term to define
            context: The surrounding text for context
            
        Returns:
            Definition of the term if successful, None otherwise
        """
        try:
            # Check if context is just a request for definition (fallback case)
            if "Please provide a clear legal definition" in context:
                return await self.get_standalone_legal_definition(term)
            
            prompt = f"""
            Provide a clear, simple definition for the legal term "{term}" in the context of the following text. 

            The definition should be:
            - Easy to understand for a layperson
            - Concise (1-2 sentences maximum)
            - Relevant to the specific context provided
            - Written in plain English

            Context:
            {context}

            Term to define: {term}

            Definition:
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                definition = response.text.strip()
                # Remove any unwanted prefixes or formatting
                definition = re.sub(r'^(Definition:|Term:|Answer:)\s*', '', definition, flags=re.IGNORECASE)
                return definition.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting definition for term '{term}' with Gemini: {str(e)}")
            return None

    async def get_standalone_legal_definition(self, term: str) -> Optional[str]:
        """
        Get a standalone legal definition for a term when it's not found in the database.
        
        Args:
            term: The legal term to define
            
        Returns:
            Definition of the term if successful, None otherwise
        """
        try:
            prompt = f"""
            You are a legal expert. Provide a clear, accurate definition for the legal term "{term}".

            Requirements for the definition:
            - Must be legally accurate and authoritative
            - Written in clear, simple language that non-lawyers can understand
            - Include the main legal meaning and practical application
            - 2-3 sentences maximum
            - Focus on the most common legal usage

            Legal term: {term}

            Definition:
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                definition = response.text.strip()
                # Remove any unwanted prefixes or formatting
                definition = re.sub(r'^(Definition:|Legal term:|Answer:)\s*', '', definition, flags=re.IGNORECASE)
                return definition.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting standalone definition for term '{term}' with Gemini: {str(e)}")
            return None
    
    async def get_multiple_terms_definitions(self, terms: List[str], context: str) -> Dict[str, str]:
        """
        Get definitions for multiple terms in a single API call.
        
        Args:
            terms: List of legal terms to define
            context: The surrounding text for context
            
        Returns:
            Dictionary mapping terms to their definitions
        """
        if not terms:
            return {}
            
        try:
            terms_list = "\n".join([f"- {term}" for term in terms])
            
            prompt = f"""
            Provide clear, simple definitions for the following legal terms in the context of the provided text. 

            For each term, provide:
            - A definition that's easy to understand for a layperson
            - Concise explanation (1-2 sentences maximum)
            - Relevant to the specific context provided
            - Written in plain English

            Format your response as:
            Term1: Definition1
            Term2: Definition2
            ...

            Context:
            {context}

            Legal terms to define:
            {terms_list}

            Definitions:
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                definitions = {}
                lines = response.text.strip().split('\n')
                
                for line in lines:
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            term = parts[0].strip().strip('-').strip()
                            definition = parts[1].strip()
                            
                            # Match the term with original terms (case-insensitive)
                            for original_term in terms:
                                if term.lower() == original_term.lower():
                                    definitions[original_term] = definition
                                    break
                
                return definitions
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting multiple definitions with Gemini: {str(e)}")
            return {}
    
    async def simplify_legal_text(self, text: str) -> Optional[str]:
        """
        Simplify complex legal text using Gemini AI.
        
        Args:
            text: The legal text to simplify
            
        Returns:
            Simplified version of the text if successful, None otherwise
        """
        try:
            prompt = f"""
            Rewrite the following legal text in simple, clear language that anyone can understand. 

            Guidelines:
            - Use everyday language instead of legal jargon
            - Break down complex sentences into shorter ones
            - Explain legal concepts in plain terms
            - Maintain the original meaning and intent
            - Make it accessible to someone without legal background

            Original legal text:
            {text}

            Simplified version:
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error simplifying legal text with Gemini: {str(e)}")
            return None

    async def comprehensive_simplification(self, text: str) -> Dict[str, any]:
        """
        Perform comprehensive text simplification with reduced word count and term extraction.
        
        Args:
            text: The legal text to analyze and simplify
            
        Returns:
            Dictionary containing simplified text and extracted complex terms with definitions
        """
        try:
            # Count original words
            original_word_count = len(text.split())
            
            prompt = f"""
            Analyze and simplify the following legal document. Your task has two parts:

            PART 1 - SIMPLIFIED TEXT:
            Rewrite the text in simple, clear language that:
            - Uses significantly FEWER words than the original (aim for 40-60% of original length)
            - Uses everyday language instead of legal jargon
            - Breaks down complex sentences into shorter ones
            - Maintains all essential meaning and key information
            - Is accessible to someone without legal background
            - Summarizes efficiently while preserving important details

            PART 2 - COMPLEX TERMS:
            Identify the most complex legal terms, jargon, and phrases from the ORIGINAL text that would be difficult for a layperson to understand. For each term, provide a simple explanation and go for new line for each term, bold the term.

            Original text (approximately {original_word_count} words):
            {text}

            Please format your response EXACTLY as follows:

            SIMPLIFIED TEXT:
            [Your simplified text here - should be significantly shorter than original]

            ----COMPLEX TERMS:----
            [term1: simple explanation of term1\n
            term2: simple explanation of term2\n
            term3: simple explanation of term3]
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                response_text = response.text.strip()
                
                # Parse the response
                simplified_text = ""
                complex_terms = {}
                
                # Split by sections
                if "SIMPLIFIED TEXT:" in response_text and "COMPLEX TERMS:" in response_text:
                    parts = response_text.split("COMPLEX TERMS:")
                    simplified_part = parts[0].replace("SIMPLIFIED TEXT:", "").strip()
                    terms_part = parts[1].strip()
                    
                    simplified_text = simplified_part
                    
                    # Parse complex terms
                    term_lines = terms_part.split('\n')
                    for line in term_lines:
                        if ':' in line and line.strip():
                            term_parts = line.split(':', 1)
                            if len(term_parts) == 2:
                                term = term_parts[0].strip().strip('[]-')
                                definition = term_parts[1].strip()
                                complex_terms[term] = definition
                
                # Count simplified words
                simplified_word_count = len(simplified_text.split()) if simplified_text else original_word_count
                
                return {
                    'simplified_text': simplified_text,
                    'complex_terms': complex_terms,
                    'original_word_count': original_word_count,
                    'simplified_word_count': simplified_word_count,
                    'reduction_percentage': round((1 - simplified_word_count / original_word_count) * 100, 1) if original_word_count > 0 else 0
                }
            
            return {
                'simplified_text': text,
                'complex_terms': {},
                'original_word_count': original_word_count,
                'simplified_word_count': original_word_count,
                'reduction_percentage': 0
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive simplification with Gemini: {str(e)}")
            return {
                'simplified_text': text,
                'complex_terms': {},
                'original_word_count': len(text.split()) if text else 0,
                'simplified_word_count': len(text.split()) if text else 0,
                'reduction_percentage': 0
            }

    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response using Gemini AI for any prompt.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Generated response text
        """
        try:
            logger.info(f"🤖 GEMINI: Generating response for prompt ({len(prompt)} chars)")
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                cleaned_response = self._clean_gemini_response(response.text)
                logger.info(f"✅ GEMINI: Response generated ({len(cleaned_response)} chars)")
                return cleaned_response
            else:
                logger.warning("⚠️ GEMINI: Empty response received")
                return ""
                
        except Exception as e:
            logger.error(f"❌ GEMINI: Response generation failed: {e}")
            return ""   

    def _clean_gemini_response(self, response_text: str) -> str:
        """Clean up Gemini response text by removing markdown formatting."""
        if not response_text:
            return ""
        
        # Remove markdown formatting but preserve structure
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)  # Remove ** bold **
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)  # Remove * italic *
        cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)  # Remove ` code `
        cleaned = re.sub(r'#{1,6}\s*(.*)', r'\1', cleaned)  # Remove # headers
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Multiple newlines to double
        cleaned = cleaned.strip()
        
        return cleaned