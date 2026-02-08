"""
Gemini 3 AI Service for Legal Term Processing
==============================================

Upgraded to Gemini 3 SDK (google-genai) with support for:
- Gemini 3 Pro (complex reasoning) and Flash (fast tasks)
- Thinking Levels for controlled reasoning depth
- Google Search Grounding for real-time legal verification
- Structured Outputs for reliable JSON responses
- Media Resolution for better document OCR
- Image Generation for visual risk reports
- Code Execution for visual document analysis
"""

import logging
import re
import json
import base64
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


# --- Structured Output Schemas (Pydantic) ---

class LegalTermSchema(BaseModel):
 """Schema for a single legal term extraction."""
 term: str = Field(description="The legal term or phrase")
 definition: str = Field(description="Simple plain-language definition in 1-2 sentences")

class LegalTermsExtractionSchema(BaseModel):
 """Schema for extracting multiple legal terms."""
 terms: List[LegalTermSchema] = Field(description="List of extracted legal terms with definitions")

class RiskClauseSchema(BaseModel):
 """Schema for a single risk clause."""
 clause_reference: str = Field(description="Clause number or section reference")
 risk_level: str = Field(description="LOW, MODERATE, HIGH, or SEVERE")
 description: str = Field(description="What the risk is about")
 financial_impact: str = Field(description="Potential financial consequences")
 recommendation: str = Field(description="What to do about this risk")

class RiskAnalysisSchema(BaseModel):
 """Schema for comprehensive risk analysis."""
 overall_status: str = Field(description="SAFE, MODERATE, HIGH, or SEVERE")
 overall_summary: str = Field(description="Brief overall risk summary in 2-3 sentences")
 risk_clauses: List[RiskClauseSchema] = Field(description="List of identified risk clauses")
 financial_risk_summary: str = Field(description="Summary of financial risks")
 recommendations: List[str] = Field(description="Top recommendations for the user")

class ApplicableLawSchema(BaseModel):
 """Schema for an applicable law."""
 law_name: str = Field(description="Full name of the Act/Law with year")
 section: str = Field(description="Specific section numbers")
 relevance: str = Field(description="How this law applies to the document")
 compliance_note: str = Field(description="Key compliance requirement")

class ApplicableLawsSchema(BaseModel):
 """Schema for list of applicable laws."""
 laws: List[ApplicableLawSchema] = Field(description="List of applicable laws")


# --- Thinking Level Presets ---

class ThinkingPreset:
 """Predefined thinking configurations for different task complexities."""

 # For simple tasks: term definitions, basic lookups
 LOW = types.ThinkingConfig(thinking_level="low")

 # For moderate tasks: text simplification, summaries (Flash only)
 MEDIUM = types.ThinkingConfig(thinking_level="medium")

 # For complex tasks: risk analysis, law identification, comprehensive analysis
 HIGH = types.ThinkingConfig(thinking_level="high")


class GeminiService:
 """
 Service for interacting with Gemini 3 AI for legal processing.

 Uses three model tiers:
 - gemini-3-pro-preview: Complex reasoning (risk analysis, law identification)
 - gemini-3-flash-preview: Fast tasks (definitions, term extraction, simplification)
 - gemini-3-pro-image-preview: Visual report generation
 """

 # Model identifiers
 MODEL_PRO = "gemini-3-pro-preview"
 MODEL_FLASH = "gemini-3-flash-preview"
 MODEL_IMAGE = "gemini-3-pro-image-preview"

 def __init__(self):
 self.settings = get_settings()
 api_key = self.settings.GEMINI_API_KEY

 if not api_key:
 logger.warning("GEMINI_API_KEY not set - Gemini service will not function")
 self.client = None
 self.client_alpha = None
 return

 # Standard client for most operations
 self.client = genai.Client(api_key=api_key)

 # Alpha client for media_resolution support (currently v1alpha only)
 self.client_alpha = genai.Client(
 api_key=api_key,
 http_options={"api_version": "v1alpha"}
 )

 logger.info("Gemini 3 service initialized with Pro, Flash, and Image models")

 # ------------------------------------------------------------------
 # FEATURE: Thinking Levels
 # ------------------------------------------------------------------

 def _make_config(
 self,
 thinking: types.ThinkingConfig = None,
 temperature: float = 1.0,
 tools: list = None,
 response_mime_type: str = None,
 response_schema: Any = None,
 ) -> types.GenerateContentConfig:
 """
 Build a GenerateContentConfig with Gemini 3 parameters.
 Temperature is kept at 1.0 (Gemini 3 recommended default).
 """
 kwargs: Dict[str, Any] = {"temperature": temperature}

 if thinking:
 kwargs["thinking_config"] = thinking
 if tools:
 kwargs["tools"] = tools
 if response_mime_type:
 kwargs["response_mime_type"] = response_mime_type
 if response_schema:
 kwargs["response_json_schema"] = response_schema

 return types.GenerateContentConfig(**kwargs)

 # ------------------------------------------------------------------
 # Term Extraction (Flash + Low Thinking)
 # ------------------------------------------------------------------

 async def extract_complex_legal_terms(self, text: str) -> List[str]:
 """
 Extract complex legal terms using Gemini 3 Flash with low thinking.
 Fast extraction for UI responsiveness.
 """
 if not self.client:
 return []

 try:
 prompt = f"""Analyze the following legal text and identify complex legal terms, jargon, and phrases that would be difficult for a layperson to understand.

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

Complex legal terms:"""

 config = self._make_config(thinking=ThinkingPreset.LOW)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 terms_text = response.text.strip()
 terms = [term.strip() for term in terms_text.split(',') if term.strip()]
 cleaned_terms = []
 for term in terms:
 cleaned_term = term.strip('"\'.,;')
 if cleaned_term and len(cleaned_term) > 1:
 cleaned_terms.append(cleaned_term)

 logger.info(f"Extracted {len(cleaned_terms)} complex legal terms via Gemini 3 Flash")
 return cleaned_terms

 return []

 except Exception as e:
 logger.error(f"Error extracting legal terms: {str(e)}")
 return []

 # ------------------------------------------------------------------
 # Term Definitions (Flash + Low Thinking)
 # ------------------------------------------------------------------

 async def get_term_definition(self, term: str, context: str) -> Optional[str]:
 """Get definition for a legal term using Gemini 3 Flash with context."""
 if not self.client:
 return None

 try:
 if "Please provide a clear legal definition" in context:
 return await self.get_standalone_legal_definition(term)

 prompt = f"""Provide a clear, simple definition for the legal term "{term}" in the context of the following text.

The definition should be:
- Easy to understand for a layperson
- Concise (1-2 sentences maximum)
- Relevant to the specific context provided
- Written in plain English

Context:
{context}

Term to define: {term}

Definition:"""

 config = self._make_config(thinking=ThinkingPreset.LOW)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 definition = response.text.strip()
 definition = re.sub(r'^(Definition:|Term:|Answer:)\s*', '', definition, flags=re.IGNORECASE)
 return definition.strip()

 return None

 except Exception as e:
 logger.error(f"Error getting definition for term '{term}': {str(e)}")
 return None

 async def get_standalone_legal_definition(self, term: str) -> Optional[str]:
 """Get a standalone legal definition using Gemini 3 Flash."""
 if not self.client:
 return None

 try:
 prompt = f"""You are a legal expert. Provide a clear, accurate definition for the legal term "{term}".

Requirements for the definition:
- Must be legally accurate and authoritative
- Written in clear, simple language that non-lawyers can understand
- Include the main legal meaning and practical application
- 2-3 sentences maximum
- Focus on the most common legal usage

Legal term: {term}

Definition:"""

 config = self._make_config(thinking=ThinkingPreset.LOW)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 definition = response.text.strip()
 definition = re.sub(r'^(Definition:|Legal term:|Answer:)\s*', '', definition, flags=re.IGNORECASE)
 return definition.strip()

 return None

 except Exception as e:
 logger.error(f"Error getting standalone definition for '{term}': {str(e)}")
 return None

 async def get_multiple_terms_definitions(self, terms: List[str], context: str) -> Dict[str, str]:
 """Get definitions for multiple terms in a single API call using Flash."""
 if not self.client or not terms:
 return {}

 try:
 terms_list = "\n".join([f"- {term}" for term in terms])

 prompt = f"""Provide clear, simple definitions for the following legal terms in the context of the provided text.

For each term, provide:
- A definition that is easy to understand for a layperson
- Concise explanation (1-2 sentences maximum)
- Relevant to the specific context provided
- Written in plain English

Format your response as:
Term1: Definition1
Term2: Definition2

Context:
{context}

Legal terms to define:
{terms_list}

Definitions:"""

 config = self._make_config(thinking=ThinkingPreset.LOW)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 definitions = {}
 lines = response.text.strip().split('\n')
 for line in lines:
 if ':' in line:
 parts = line.split(':', 1)
 if len(parts) == 2:
 term = parts[0].strip().strip('-').strip()
 definition = parts[1].strip()
 for original_term in terms:
 if term.lower() == original_term.lower():
 definitions[original_term] = definition
 break
 return definitions

 return {}

 except Exception as e:
 logger.error(f"Error getting multiple definitions: {str(e)}")
 return {}

 # ------------------------------------------------------------------
 # FEATURE: Structured Term Extraction (Flash + Structured Output)
 # ------------------------------------------------------------------

 async def extract_terms_structured(self, text: str, max_terms: int = 12) -> List[Dict[str, str]]:
 """
 Extract legal terms with guaranteed JSON structure using Gemini 3 Structured Outputs.
 Returns a list of {term, definition} dicts - no parsing errors possible.
 """
 if not self.client:
 return []

 try:
 prompt = f"""Extract {max_terms} key legal terms from this document that are critical to understanding obligations. For each term, provide a one-line simple definition in maximum 15 words.

Document:
{text[:4000]}

Focus on terms that appear in the document and are critical to understanding obligations."""

 config = self._make_config(
 thinking=ThinkingPreset.LOW,
 response_mime_type="application/json",
 response_schema=LegalTermsExtractionSchema.model_json_schema(),
 )

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 result = LegalTermsExtractionSchema.model_validate_json(response.text)
 return [{"term": t.term, "definition": t.definition} for t in result.terms]

 return []

 except Exception as e:
 logger.error(f"Structured term extraction failed: {str(e)}")
 return []

 # ------------------------------------------------------------------
 # FEATURE: Risk Analysis (Pro + High Thinking + Structured Output)
 # ------------------------------------------------------------------

 async def analyze_risk_structured(self, text: str) -> Dict[str, Any]:
 """
 Perform risk analysis using Gemini 3 Pro with high thinking level
 and structured JSON output. Returns guaranteed structured data.
 """
 if not self.client:
 return {}

 try:
 prompt = f"""You are a professional legal document analyzer specializing in Indian law. Analyze this document for risks.

For each risky clause, identify:
- The clause reference
- Risk level (LOW, MODERATE, HIGH, or SEVERE)
- Description of the risk
- Financial impact
- Recommendation

Also provide an overall risk status (SAFE, MODERATE, HIGH, or SEVERE), a brief summary,
a financial risk summary, and top recommendations.

Document:
{text}"""

 config = self._make_config(
 thinking=ThinkingPreset.HIGH,
 response_mime_type="application/json",
 response_schema=RiskAnalysisSchema.model_json_schema(),
 )

 response = self.client.models.generate_content(
 model=self.MODEL_PRO,
 contents=prompt,
 config=config,
 )

 if response.text:
 result = RiskAnalysisSchema.model_validate_json(response.text)
 return result.model_dump()

 return {}

 except Exception as e:
 logger.error(f"Structured risk analysis failed: {str(e)}")
 return {}

 # ------------------------------------------------------------------
 # FEATURE: Law Identification (Pro + High Thinking + Google Search)
 # ------------------------------------------------------------------

 async def identify_laws_grounded(self, text: str) -> List[Dict[str, str]]:
 """
 Identify applicable laws using Gemini 3 Pro with Google Search grounding.
 The model verifies law citations against real-time search results.
 """
 if not self.client:
 return []

 try:
 prompt = f"""Identify 8-12 relevant Indian laws for this legal document. For each law provide the full Act name with year, specific section numbers, how it applies to this document, and key compliance requirements.

Focus on current Indian laws including BNS, BNSS, BSA, Consumer Protection Act 2019, Transfer of Property Act 1882, Registration Act 1908, Indian Contract Act 1872, and any other relevant legislation.

Document:
{text[:3000]}"""

 config = self._make_config(
 thinking=ThinkingPreset.HIGH,
 tools=[{"google_search": {}}],
 response_mime_type="application/json",
 response_schema=ApplicableLawsSchema.model_json_schema(),
 )

 response = self.client.models.generate_content(
 model=self.MODEL_PRO,
 contents=prompt,
 config=config,
 )

 if response.text:
 result = ApplicableLawsSchema.model_validate_json(response.text)
 return [law.model_dump() for law in result.laws]

 return []

 except Exception as e:
 logger.error(f"Grounded law identification failed: {str(e)}")
 return []

 # ------------------------------------------------------------------
 # Text Simplification (Flash + Medium Thinking)
 # ------------------------------------------------------------------

 async def simplify_legal_text(self, text: str) -> Optional[str]:
 """Simplify complex legal text using Gemini 3 Flash with medium thinking."""
 if not self.client:
 return None

 try:
 prompt = f"""Rewrite the following legal text in simple, clear language that anyone can understand.

Guidelines:
- Use everyday language instead of legal jargon
- Break down complex sentences into shorter ones
- Explain legal concepts in plain terms
- Maintain the original meaning and intent
- Make it accessible to someone without legal background

Original legal text:
{text}

Simplified version:"""

 config = self._make_config(thinking=ThinkingPreset.MEDIUM)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 return response.text.strip()
 return None

 except Exception as e:
 logger.error(f"Error simplifying legal text: {str(e)}")
 return None

 async def comprehensive_simplification(self, text: str) -> Dict[str, Any]:
 """
 Perform comprehensive text simplification with reduced word count and term extraction.
 Uses Gemini 3 Flash with medium thinking for balanced speed and quality.
 """
 if not self.client:
 return {
 'simplified_text': text,
 'complex_terms': {},
 'original_word_count': len(text.split()) if text else 0,
 'simplified_word_count': len(text.split()) if text else 0,
 'reduction_percentage': 0
 }

 try:
 original_word_count = len(text.split())

 prompt = f"""Analyze and simplify the following legal document. Your task has two parts:

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
[term1: simple explanation of term1
term2: simple explanation of term2
term3: simple explanation of term3]"""

 config = self._make_config(thinking=ThinkingPreset.MEDIUM)

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=prompt,
 config=config,
 )

 if response.text:
 response_text = response.text.strip()
 simplified_text = ""
 complex_terms = {}

 if "SIMPLIFIED TEXT:" in response_text and "COMPLEX TERMS:" in response_text:
 parts = response_text.split("COMPLEX TERMS:")
 simplified_part = parts[0].replace("SIMPLIFIED TEXT:", "").strip()
 terms_part = parts[1].strip()
 simplified_text = simplified_part

 term_lines = terms_part.split('\n')
 for line in term_lines:
 if ':' in line and line.strip():
 term_parts = line.split(':', 1)
 if len(term_parts) == 2:
 term = term_parts[0].strip().strip('[]-')
 definition = term_parts[1].strip()
 complex_terms[term] = definition

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
 logger.error(f"Error in comprehensive simplification: {str(e)}")
 return {
 'simplified_text': text,
 'complex_terms': {},
 'original_word_count': len(text.split()) if text else 0,
 'simplified_word_count': len(text.split()) if text else 0,
 'reduction_percentage': 0
 }

 # ------------------------------------------------------------------
 # General Response Generation (Flash + configurable thinking)
 # ------------------------------------------------------------------

 async def generate_response(self, prompt: str, use_pro: bool = False, thinking: str = "low") -> str:
 """
 Generate a response using Gemini 3.

 Args:
 prompt: The prompt to send
 use_pro: If True, use Pro model for complex reasoning
 thinking: Thinking level - "low", "medium", or "high"
 """
 if not self.client:
 return ""

 try:
 logger.info(f"GEMINI 3: Generating response ({len(prompt)} chars, model={'Pro' if use_pro else 'Flash'}, thinking={thinking})")

 thinking_config = {
 "low": ThinkingPreset.LOW,
 "medium": ThinkingPreset.MEDIUM,
 "high": ThinkingPreset.HIGH,
 }.get(thinking, ThinkingPreset.LOW)

 config = self._make_config(thinking=thinking_config)
 model = self.MODEL_PRO if use_pro else self.MODEL_FLASH

 response = self.client.models.generate_content(
 model=model,
 contents=prompt,
 config=config,
 )

 if response and response.text:
 cleaned = self._clean_gemini_response(response.text)
 logger.info(f"GEMINI 3: Response generated ({len(cleaned)} chars)")
 return cleaned
 else:
 logger.warning("GEMINI 3: Empty response received")
 return ""

 except Exception as e:
 logger.error(f"GEMINI 3: Response generation failed: {e}")
 return ""

 # ------------------------------------------------------------------
 # FEATURE: Google Search Grounded Response
 # ------------------------------------------------------------------

 async def generate_grounded_response(self, prompt: str) -> str:
 """
 Generate a response grounded with Google Search for factual accuracy.
 Uses Gemini 3 Pro for maximum reasoning with real-time data.
 """
 if not self.client:
 return ""

 try:
 config = self._make_config(
 thinking=ThinkingPreset.HIGH,
 tools=[{"google_search": {}}],
 )

 response = self.client.models.generate_content(
 model=self.MODEL_PRO,
 contents=prompt,
 config=config,
 )

 if response and response.text:
 return self._clean_gemini_response(response.text)
 return ""

 except Exception as e:
 logger.error(f"GEMINI 3: Grounded response failed: {e}")
 return ""

 # ------------------------------------------------------------------
 # FEATURE: Image OCR with Media Resolution (Flash + v1alpha)
 # ------------------------------------------------------------------

 async def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
 """
 Extract text from an image using Gemini 3 Flash with media_resolution_high.
 Uses v1alpha API for media resolution support - captures fine legal text.
 """
 if not self.client_alpha:
 return "Gemini API not configured"

 try:
 contents = [
 types.Content(
 parts=[
 types.Part(text="""Extract all text content from this image. The image contains a legal document.

Instructions:
1. Extract ALL visible text exactly as it appears
2. Maintain the original formatting and structure
3. Include headers, footers, and any marginal text
4. If there are multiple columns, read from left to right, top to bottom
5. Preserve line breaks and paragraph structure
6. Include any table content in a readable format
7. If text is partially obscured or unclear, indicate with [unclear]

Provide only the extracted text without any additional commentary."""),
 types.Part(
 inline_data=types.Blob(
 mime_type=mime_type,
 data=image_bytes,
 ),
 media_resolution={"level": "media_resolution_high"}
 )
 ]
 )
 ]

 config = self._make_config(thinking=ThinkingPreset.LOW)

 response = self.client_alpha.models.generate_content(
 model=self.MODEL_FLASH,
 contents=contents,
 config=config,
 )

 if response.text:
 logger.info(f"Gemini 3 extracted {len(response.text)} chars with media_resolution_high")
 return response.text.strip()

 return "No text could be extracted from this image."

 except Exception as e:
 logger.error(f"Gemini 3 image extraction failed: {e}")
 return f"Error extracting text: {str(e)}"

 # ------------------------------------------------------------------
 # FEATURE: Image Generation (Pro Image model)
 # ------------------------------------------------------------------

 async def generate_risk_infographic(self, risk_data: Dict[str, Any], document_title: str = "Legal Document") -> Optional[bytes]:
 """
 Generate a visual risk assessment infographic using Gemini 3 Pro Image.
 Returns image bytes (PNG) or None on failure.
 """
 if not self.client:
 return None

 try:
 overall = risk_data.get('overall_status', 'UNKNOWN')
 clauses = risk_data.get('risk_clauses', [])
 recommendations = risk_data.get('recommendations', [])

 clause_text = ""
 for i, c in enumerate(clauses[:5], 1):
 clause_text += f" {i}. {c.get('clause_reference', 'N/A')} - {c.get('risk_level', 'N/A')}: {c.get('description', '')}\n"

 rec_text = "\n".join([f" - {r}" for r in recommendations[:4]])

 prompt = f"""Create a clean, professional legal risk assessment infographic with the following data:

Title: Risk Analysis - {document_title}
Overall Risk Level: {overall}
Key Risk Clauses:
{clause_text}
Recommendations:
{rec_text}

Design requirements:
- Professional color scheme (green for safe, yellow for moderate, red for high risk)
- Clear section headers
- Risk level indicators with color coding
- Clean typography, no decorative elements
- Aspect ratio 16:9, suitable for a report"""

 config = types.GenerateContentConfig(
 image_config=types.ImageConfig(
 aspect_ratio="16:9",
 )
 )

 response = self.client.models.generate_content(
 model=self.MODEL_IMAGE,
 contents=prompt,
 config=config,
 )

 # Extract image from response
 if response.candidates and response.candidates[0].content.parts:
 for part in response.candidates[0].content.parts:
 if part.inline_data:
 logger.info("Gemini 3 Pro Image generated risk infographic")
 return part.inline_data.data

 return None

 except Exception as e:
 logger.error(f"Risk infographic generation failed: {e}")
 return None

 # ------------------------------------------------------------------
 # FEATURE: Code Execution with Images (Flash + visual analysis)
 # ------------------------------------------------------------------

 async def analyze_document_visual(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
 """
 Analyze a document image using Gemini 3 Flash with code execution.
 The model can zoom, crop, and annotate to extract detailed information.
 """
 if not self.client:
 return {"error": "Gemini API not configured"}

 try:
 image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

 config = self._make_config(
 thinking=ThinkingPreset.HIGH,
 tools=[types.Tool(code_execution=types.ToolCodeExecution)],
 )

 response = self.client.models.generate_content(
 model=self.MODEL_FLASH,
 contents=[
 image_part,
 "Analyze this legal document image. Extract all text, identify key sections, and highlight any areas that need attention. Use code execution to zoom into small text areas if needed."
 ],
 config=config,
 )

 result = {"text_parts": [], "code_parts": [], "images": []}

 if response.candidates and response.candidates[0].content.parts:
 for part in response.candidates[0].content.parts:
 if part.text is not None:
 result["text_parts"].append(part.text)
 if hasattr(part, 'executable_code') and part.executable_code is not None:
 result["code_parts"].append(part.executable_code.code)
 if hasattr(part, 'code_execution_result') and part.code_execution_result is not None:
 result["code_parts"].append(part.code_execution_result.output)
 if part.inline_data is not None:
 result["images"].append(base64.b64encode(part.inline_data.data).decode())

 return result

 except Exception as e:
 logger.error(f"Visual document analysis failed: {e}")
 return {"error": str(e)}

 # ------------------------------------------------------------------
 # Utility
 # ------------------------------------------------------------------

 def _clean_gemini_response(self, response_text: str) -> str:
 """Clean up Gemini response text by removing markdown formatting."""
 if not response_text:
 return ""

 cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)
 cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
 cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)
 cleaned = re.sub(r'#{1,6}\s*(.*)', r'\1', cleaned)
 cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
 cleaned = cleaned.strip()

 return cleaned
