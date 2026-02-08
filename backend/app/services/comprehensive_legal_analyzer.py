"""
Comprehensive Legal Document Analyzer
====================================

Enhanced service for professional legal document analysis with structured output.
Integrates Gemini 3 features:
- Thinking Levels: High reasoning for risk analysis, low for term extraction
- Structured Outputs: Guaranteed JSON for terms, risks, and laws
- Google Search Grounding: Real-time legal citation verification
- Gemini 3 Pro: Complex reasoning for risk and law analysis
- Gemini 3 Flash: Fast operations for summaries and terms
"""

import logging
import re
from typing import Dict, List, Any
from datetime import datetime
import asyncio

from .gemini_service import GeminiService
from .spanner_service import SpannerService

logger = logging.getLogger(__name__)

class ComprehensiveLegalAnalyzer:
 """
 Enhanced legal document analyzer that produces professional legal reports
 with comprehensive analysis including summary, terms, risks, and applicable laws.
 """
 
 def __init__(self):
 self.gemini_service = GeminiService()
 self.spanner_service = SpannerService()
 
 def _clean_markdown_formatting(self, text: str) -> str:
 """
 Remove markdown formatting from text for clean chat display.
 Removes ** bold, * italic, ` code, and other markdown syntax.
 """
 if not text:
 return text
 
 # Remove ** bold formatting (most important for clean chat display)
 cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
 
 # Remove ` code formatting
 cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)
 
 # Remove markdown headers but keep the text
 cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
 
 # Remove markdown links but keep the text [text](url) -> text
 cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
 
 # Clean up multiple newlines
 cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
 
 # Clean up extra whitespace
 cleaned = cleaned.strip()
 
 return cleaned
 
 async def analyze_document(self, extracted_text: str, user_email: str = None) -> Dict[str, Any]:
 """
 Perform comprehensive legal document analysis.
 
 Returns structured data with:
 1. Document Summary (for chat display) - 200 words
 2. Detailed Document Summary (for PDF) - comprehensive
 3. Legal Terms and Meanings (from Spanner + Gemini)
 4. Risk Analysis (comprehensive Gemini analysis)
 5. Applicable Laws (detailed Indian laws)
 6. Related Links (relevant resources)
 """
 try:
 logger.info("COMPREHENSIVE ANALYZER: Starting comprehensive legal analysis")
 logger.info(f"Text length: {len(extracted_text)} characters")
 
 # Run all analysis tasks concurrently for better performance
 summary_task = self._generate_document_summary(extracted_text)
 detailed_summary_task = self._generate_detailed_document_summary(extracted_text)
 terms_task = self._extract_legal_terms_and_meanings(extracted_text)
 risk_task = self._perform_risk_analysis(extracted_text)
 laws_task = self._identify_applicable_laws(extracted_text)
 links_task = self._generate_related_links(extracted_text)
 
 # Wait for all tasks to complete
 summary_result, detailed_summary_result, terms_result, risk_result, laws_result, links_result = await asyncio.gather(
 summary_task, detailed_summary_task, terms_task, risk_task, laws_task, links_task,
 return_exceptions=True
 )
 
 # Handle any exceptions and set default values
 if isinstance(summary_result, Exception):
 logger.error(f"Summary analysis failed: {summary_result}")
 summary_result = "Summary analysis failed"
 
 if isinstance(detailed_summary_result, Exception):
 logger.error(f"Detailed summary analysis failed: {detailed_summary_result}")
 detailed_summary_result = "Detailed summary analysis failed"
 
 if isinstance(terms_result, Exception):
 logger.error(f"Terms extraction failed: {terms_result}")
 terms_result = []
 
 if isinstance(risk_result, Exception):
 logger.error(f"Risk analysis failed: {risk_result}")
 risk_result = "Risk analysis failed"
 
 if isinstance(laws_result, Exception):
 logger.error(f"Laws identification failed: {laws_result}")
 laws_result = []
 
 if isinstance(links_result, Exception):
 logger.error(f"Related links generation failed: {links_result}")
 links_result = []
 
 # Build structured risk analysis string for backward compatibility
 risk_text = risk_result
 risk_structured = None
 if isinstance(risk_result, dict):
 risk_structured = risk_result
 risk_text = self._format_risk_to_text(risk_result)

 # Build laws list for backward compatibility
 laws_formatted = laws_result
 if laws_result and isinstance(laws_result, list) and len(laws_result) > 0:
 if isinstance(laws_result[0], dict) and 'law_name' in laws_result[0]:
 laws_formatted = [
 {
 "law": f"{l.get('law_name', '')} - {l.get('section', '')}",
 "description": f"{l.get('relevance', '')} {l.get('compliance_note', '')}"
 }
 for l in laws_result
 ]

 # Compile comprehensive analysis
 analysis_result = {
 "document_summary": summary_result,
 "detailed_document_summary": detailed_summary_result,
 "legal_terms_and_meanings": terms_result,
 "risk_analysis": risk_text,
 "risk_analysis_structured": risk_structured,
 "applicable_laws": laws_formatted,
 "related_links": links_result,
 "processing_metadata": {
 "analysis_timestamp": datetime.utcnow().isoformat(),
 "user_email": user_email,
 "original_text_length": len(extracted_text),
 "analysis_type": "comprehensive_legal_analysis",
 "gemini_3_features_used": [
 "thinking_level_high (risk analysis, law identification)",
 "thinking_level_medium (summaries, simplification)",
 "thinking_level_low (term extraction, definitions)",
 "structured_outputs (terms, risk, laws)",
 "google_search_grounding (law verification)",
 "gemini_3_pro (complex reasoning)",
 "gemini_3_flash (fast operations)"
 ]
 }
 }
 
 logger.info("COMPREHENSIVE ANALYZER: Analysis completed successfully")
 return analysis_result
 
 except Exception as e:
 logger.error(f"COMPREHENSIVE ANALYZER: Analysis failed: {e}")
 raise Exception(f"Comprehensive legal analysis failed: {str(e)}")

 def _format_risk_to_text(self, risk_data: dict) -> str:
 """Convert structured risk analysis dict to readable text for display."""
 lines = []
 lines.append(f"OVERALL STATUS: {risk_data.get('overall_status', 'UNKNOWN')}")
 lines.append(f"\n{risk_data.get('overall_summary', '')}")
 
 clauses = risk_data.get('risk_clauses', [])
 if clauses:
 lines.append("\nRISK CLAUSES:")
 for i, c in enumerate(clauses, 1):
 lines.append(f"\n{i}. {c.get('clause_reference', 'N/A')} [{c.get('risk_level', '')}]")
 lines.append(f" {c.get('description', '')}")
 lines.append(f" Financial Impact: {c.get('financial_impact', 'N/A')}")
 lines.append(f" Recommendation: {c.get('recommendation', 'N/A')}")
 
 if risk_data.get('financial_risk_summary'):
 lines.append(f"\nFINANCIAL RISK SUMMARY:\n{risk_data['financial_risk_summary']}")
 
 recs = risk_data.get('recommendations', [])
 if recs:
 lines.append("\nRECOMMENDATIONS:")
 for r in recs:
 lines.append(f" - {r}")
 
 return "\n".join(lines)
 
 async def _generate_document_summary(self, text: str) -> str:
 """Generate user-friendly document summary using Gemini 3 Flash + medium thinking.
 
 Gemini 3 Feature: thinking_level=medium
 - Balanced reasoning for summary generation
 - Faster than high thinking but better than low for comprehension tasks
 """
 
 prompt = """You are a professional legal document analyzer specializing in Indian law. 

Analyze the following legal document and provide ONLY a DOCUMENT SUMMARY in EXACTLY 200 WORDS that includes:

- Document type, execution date, location, and parties involved
- Key financial terms (amounts, fees, deposits)
- Main obligations of each party
- Duration and termination conditions
- Critical rights and restrictions

Write in simple language suitable for non-lawyers. Keep it concise and focused on the most important points.

IMPORTANT: Your response must be EXACTLY 200 words - no more, no less.

Document to analyze:
{text}

Provide only the 200-word summary, no other sections."""

 try:
 response = await self.gemini_service.generate_response(
 prompt.format(text=text)
 )
 # Clean markdown formatting for chat display
 cleaned_response = self._clean_markdown_formatting(response.strip())
 return cleaned_response
 except Exception as e:
 logger.error(f"Summary generation failed: {e}")
 return f"Document summary generation failed: {str(e)}"

 async def _generate_detailed_document_summary(self, text: str) -> str:
 """Generate comprehensive document summary using Gemini 3 Pro + high thinking.
 
 Gemini 3 Feature: thinking_level=high, model=Pro
 - Maximum reasoning depth for comprehensive legal analysis
 - Pro model handles complex multi-section document understanding
 """
 
 prompt = """You are a professional legal document analyzer specializing in Indian law. 

Analyze the following legal document and provide a COMPREHENSIVE DOCUMENT SUMMARY (800-1200 words) that includes:

**DOCUMENT OVERVIEW:**
- Document type and legal nature
- Execution date, location, and jurisdiction
- All parties involved with their complete roles and responsibilities
- Property/subject matter details with complete addresses and descriptions

**FINANCIAL TERMS & OBLIGATIONS:**
- Complete breakdown of all amounts: rent, deposits, fees, penalties
- Payment schedules, due dates, and payment methods
- Late payment consequences and penalty structures
- Security deposits and refund conditions
- Any escalation clauses or rent increases

**RIGHTS & RESPONSIBILITIES:**
- Detailed obligations of each party
- Maintenance and repair responsibilities
- Usage restrictions and permitted activities
- Insurance requirements and liability coverage

**DURATION & TERMINATION:**
- Contract duration and renewal terms
- Termination conditions and notice requirements
- Early termination penalties and procedures
- Handover conditions and requirements

**SPECIAL CLAUSES & CONDITIONS:**
- Any unique or unusual provisions
- Inspection rights and procedures
- Dispute resolution mechanisms
- Registration requirements

**COMPLIANCE & LEGAL ASPECTS:**
- Legal compliance requirements
- Documentation needed
- Registration obligations

Write in clear, professional language explaining each aspect thoroughly with reference to specific clauses.

Document to analyze:
{text}

Provide the comprehensive summary covering all above aspects."""

 try:
 response = await self.gemini_service.generate_response(
 prompt.format(text=text),
 use_pro=True, # Gemini 3 Pro for deep analysis
 thinking="high" # Gemini 3: maximum reasoning depth
 )
 return response.strip()
 except Exception as e:
 logger.error(f"Detailed summary generation failed: {e}")
 return f"Detailed document summary generation failed: {str(e)}"
 
 async def _extract_legal_terms_and_meanings(self, text: str) -> List[Dict[str, str]]:
 """Extract legal terms using Gemini 3 Structured Outputs + Spanner.
 
 Gemini 3 Feature: Structured Outputs
 - Returns guaranteed JSON with {term, definition} objects
 - No parsing errors - schema is enforced by the model
 - Falls back to Spanner database for authoritative definitions
 """
 
 try:
 # Step 1: Find terms in Spanner database
 spanner_terms = await self.spanner_service.find_terms_in_text(text)
 logger.info(f" Found {len(spanner_terms)} terms in Spanner database")
 
 terms_list = []
 
 # Add Spanner terms
 for term, definition in spanner_terms.items():
 terms_list.append({
 "term": term,
 "definition": definition,
 "source": "spanner_database"
 })
 
 # Step 2: Get additional terms from Gemini 3 with Structured Output
 try:
 gemini_terms = await self.gemini_service.extract_terms_structured(
 text[:3000], max_terms=12
 )
 
 for term_data in gemini_terms:
 if not any(t["term"].lower() == term_data["term"].lower() for t in terms_list):
 terms_list.append({
 "term": term_data["term"],
 "definition": term_data["definition"],
 "source": "gemini_3_structured"
 })
 
 except Exception as e:
 logger.warning(f"Gemini 3 structured term extraction failed, using fallback: {e}")
 # Fallback to regular extraction
 try:
 gemini_prompt = f"""Extract 8-12 key legal terms from this document that are critical to understanding obligations. For each term, provide a one-line simple definition in maximum 15 words.

Document: {text[:3000]}

Format each as:
Term Name: Plain language explanation"""
 gemini_response = await self.gemini_service.generate_response(gemini_prompt)
 gemini_terms = self._parse_gemini_terms(gemini_response)
 for term_data in gemini_terms:
 if not any(t["term"].lower() == term_data["term"].lower() for t in terms_list):
 term_data["source"] = "gemini_3_fallback"
 terms_list.append(term_data)
 except Exception as fallback_error:
 logger.warning(f"Gemini fallback also failed: {fallback_error}")
 
 logger.info(f"Total terms extracted: {len(terms_list)}")
 return terms_list[:12] # Limit to 12 terms max
 
 except Exception as e:
 logger.error(f"Terms extraction failed: {e}")
 return []
 
 async def _perform_risk_analysis(self, text: str) -> Any:
 """Perform risk analysis using Gemini 3 Pro + High Thinking + Structured Output.
 
 Gemini 3 Features:
 - thinking_level=high: Deep reasoning for clause-by-clause risk evaluation
 - Structured Output: Guaranteed JSON with risk levels, clauses, recommendations
 - Pro model: Best reasoning for complex legal risk assessment
 
 Returns structured dict on success, text string on fallback.
 """
 
 risk_prompt = """You are a professional legal document analyzer specializing in Indian law. Analyze this document for risks and provide a COMPREHENSIVE RISK ANALYSIS (800-1000 words).

STRUCTURE YOUR ANALYSIS AS FOLLOWS:

**OVERALL RISK ASSESSMENT:**
Begin with one of these exact phrases:
- "OVERALL STATUS: This document is SAFE TO SIGN with standard terms and balanced protections."
- "OVERALL STATUS: This document contains MODERATE RISKS that should be negotiated before signing." 
- "OVERALL STATUS: This document is HIGH RISK with unfavorable terms that could cause financial harm."
- "OVERALL STATUS: This document presents SEVERE FINANCIAL RISK and should not be signed without major modifications."

**CLAUSE-BY-CLAUSE RISK ANALYSIS:**
Analyze each problematic clause with:
- Clause number and exact text reference
- Specific risk explanation with financial impact
- Comparison with standard market practices
- Recommendations for mitigation

**FINANCIAL RISK ASSESSMENT:**
- Penalty structures and their enforceability
- Security deposit analysis (amount vs market standards)
- Payment terms and default consequences
- Hidden costs and additional charges
- Escalation clauses and future financial obligations

**LEGAL COMPLIANCE RISKS:**
- Registration requirements and penalties for non-compliance
- Tax implications and responsibilities
- Insurance and liability coverage gaps
- Dispute resolution limitations

**TENANT/PARTY PROTECTION ANALYSIS:**
- Rights protection level
- Termination flexibility
- Notice period adequacy
- Deposit refund protections

**ENFORCEABILITY CONCERNS:**
- Clauses that may be legally unenforceable
- Excessive penalties that courts might reduce
- Terms that violate consumer protection laws

**RECOMMENDATIONS:**
- Specific clauses to negotiate
- Alternative terms to propose
- Legal documentation needed
- Professional consultation requirements

Reference specific clause numbers and text from the document. Quantify financial risks where possible.

Document: {text}

Provide comprehensive risk analysis covering all above aspects."""

 try:
 # Primary: Gemini 3 Pro with structured output
 structured_result = await self.gemini_service.analyze_risk_structured(text)
 if structured_result and structured_result.get('overall_status'):
 logger.info(f"Risk analysis completed via Gemini 3 Pro structured output: {structured_result.get('overall_status')}")
 return structured_result
 except Exception as e:
 logger.warning(f"Structured risk analysis failed, using text fallback: {e}")

 # Fallback: text-based risk analysis
 risk_prompt = """You are a professional legal document analyzer specializing in Indian law. Analyze this document for risks and provide a COMPREHENSIVE RISK ANALYSIS (800-1000 words).

STRUCTURE YOUR ANALYSIS AS FOLLOWS:

OVERALL RISK ASSESSMENT:
Begin with one of these exact phrases:
- "OVERALL STATUS: This document is SAFE TO SIGN with standard terms and balanced protections."
- "OVERALL STATUS: This document contains MODERATE RISKS that should be negotiated before signing."
- "OVERALL STATUS: This document is HIGH RISK with unfavorable terms that could cause financial harm."
- "OVERALL STATUS: This document presents SEVERE FINANCIAL RISK and should not be signed without major modifications."

CLAUSE-BY-CLAUSE RISK ANALYSIS:
Analyze each problematic clause with:
- Clause number and exact text reference
- Specific risk explanation with financial impact
- Comparison with standard market practices
- Recommendations for mitigation

FINANCIAL RISK ASSESSMENT:
- Penalty structures and their enforceability
- Security deposit analysis
- Payment terms and default consequences

RECOMMENDATIONS:
- Specific clauses to negotiate
- Alternative terms to propose
- Professional consultation requirements

Document: {text}

Provide comprehensive risk analysis."""

 try:
 response = await self.gemini_service.generate_response(
 risk_prompt.format(text=text),
 use_pro=True, # Gemini 3 Pro for complex reasoning
 thinking="high" # Maximum reasoning depth
 )
 cleaned_response = self._clean_markdown_formatting(response.strip())
 return cleaned_response
 except Exception as e:
 logger.error(f"Risk analysis failed: {e}")
 return f"Risk analysis failed: {str(e)}"
 
 async def _identify_applicable_laws(self, text: str) -> List[Dict[str, str]]:
 """Identify applicable Indian laws using Gemini 3 Pro + Google Search Grounding.
 
 Gemini 3 Features:
 - Google Search Grounding: Real-time verification of law citations
 - thinking_level=high: Deep reasoning for accurate legal analysis
 - Structured Output: Guaranteed JSON with law_name, section, relevance
 - Pro model: Best for legal knowledge synthesis
 
 The model cross-references its legal knowledge with live search results
 to ensure cited laws are current and section numbers are accurate.
 """
 
 laws_prompt = """Identify 8-12 relevant Indian laws for this legal document. For each law, provide:

**Format for each law:**
*Act Name, Year, Section Number:* Detailed explanation covering:
- What this legal provision specifically governs
- How it applies to clauses in this document 
- Compliance requirements and penalties for violation
- Practical implications for the parties involved
- Recent amendments or judicial interpretations if relevant

**Focus on these areas based on document type:**

For Rental Agreements:
- Transfer of Property Act, 1882 (Sections 105-117)
- Registration Act, 1908 (Section 17)
- Indian Contract Act, 1872 (Sections 73-74 for damages)
- Model Tenancy Act, 2021 provisions
- State Rent Control Acts
- Consumer Protection Act, 2019
- Constitution of India (Article 21 - Right to Privacy)

For Employment Contracts:
- Contract Labour Act, 1970
- Minimum Wages Act, 1948
- Payment of Wages Act, 1936
- Industrial Disputes Act, 1947

For Service Agreements:
- Indian Contract Act, 1872
- Consumer Protection Act, 2019
- Information Technology Act, 2000 (if applicable)

For each law, explain:
1. Specific sections applicable to this document
2. How violations would be handled
3. Compliance requirements
4. Recent legal precedents if any
5. Practical impact on the agreement

Document type analysis: {text[:2000]}

Provide 8-12 comprehensive law explanations following the format above."""

 try:
 # Primary: Gemini 3 Pro with Google Search grounding + structured output
 grounded_laws = await self.gemini_service.identify_laws_grounded(text[:2000])
 if grounded_laws:
 logger.info(f"Identified {len(grounded_laws)} laws via Gemini 3 Pro + Google Search grounding")
 return grounded_laws
 except Exception as e:
 logger.warning(f"Grounded law identification failed, using fallback: {e}")

 # Fallback: regular text-based law identification
 laws_prompt = """Identify 8-12 relevant Indian laws for this legal document. For each law, provide:

*Act Name, Year, Section Number:* Detailed explanation covering:
- What this legal provision specifically governs
- How it applies to clauses in this document
- Compliance requirements and penalties for violation
- Practical implications for the parties involved

Document type analysis: {text}

Provide 8-12 comprehensive law explanations."""

 try:
 response = await self.gemini_service.generate_response(
 laws_prompt.format(text=text[:2000]),
 use_pro=True,
 thinking="high"
 )
 laws_list = self._parse_detailed_applicable_laws(response)
 return laws_list
 except Exception as e:
 logger.error(f"Applicable laws identification failed: {e}")
 return []
 
 def _parse_gemini_terms(self, gemini_response: str) -> List[Dict[str, str]]:
 """Parse Gemini terms response into structured format."""
 terms = []
 lines = gemini_response.strip().split('\n')
 
 for line in lines:
 line = line.strip()
 if ':' in line and len(line) > 10:
 parts = line.split(':', 1)
 if len(parts) == 2:
 term = parts[0].strip('*').strip()
 definition = parts[1].strip()
 
 # Clean markdown formatting from both term and definition
 term = self._clean_markdown_formatting(term)
 definition = self._clean_markdown_formatting(definition)
 
 if term and definition and len(definition) <= 100: # Reasonable definition length
 terms.append({
 "term": term,
 "definition": definition
 })
 
 return terms
 
 def _parse_detailed_applicable_laws(self, laws_response: str) -> List[Dict[str, str]]:
 """Parse detailed applicable laws response into structured format."""
 laws = []
 lines = laws_response.strip().split('\n')
 current_law = None
 current_description = []
 
 for line in lines:
 line = line.strip()
 if line.startswith('*') and ':' in line:
 # Save previous law if exists
 if current_law and current_description:
 law_name = self._clean_markdown_formatting(current_law)
 description = self._clean_markdown_formatting(' '.join(current_description))
 laws.append({
 "law": law_name,
 "description": description
 })
 
 # Start new law
 line = line.strip('*')
 parts = line.split(':', 1)
 if len(parts) == 2:
 current_law = parts[0].strip()
 current_description = [parts[1].strip()]
 else:
 current_law = None
 current_description = []
 elif current_law and line:
 # Continue description for current law
 current_description.append(line)
 
 # Don't forget the last law
 if current_law and current_description:
 law_name = self._clean_markdown_formatting(current_law)
 description = self._clean_markdown_formatting(' '.join(current_description))
 laws.append({
 "law": law_name,
 "description": description
 })
 
 return laws

 async def _generate_related_links(self, text: str, document_type: str = "legal") -> List[Dict[str, str]]:
 """Generate related links using Gemini 3 Pro with Google Search grounding.
 
 Gemini 3 Feature: Google Search Grounding
 - Real-time search ensures URLs are valid and current
 - Grounded generation produces factual resource recommendations
 """
 
 # Simplified prompt to avoid timeouts
 links_prompt = """Based on this legal document text, suggest 5 relevant Indian legal resources.

Document: {text}

For each resource, provide exactly this format:
Title: Resource title
URL: https://website.com
Description: Brief description

Provide exactly 5 resources."""

 try:
 logger.info("Starting related links generation with Google Search grounding")
 # Use Google Search grounded response for real URLs
 response = await self.gemini_service.generate_grounded_response(
 links_prompt.format(text=text[:500])
 )
 
 logger.info(f"Gemini response type: {type(response)}")
 logger.info(f"Gemini response preview: {str(response)[:300] if response else 'None'}...")
 
 # Ensure response is a string
 if not isinstance(response, str):
 logger.error(f"Gemini returned non-string response: {type(response)}")
 return []
 
 parsed_links = self._parse_related_links(response)
 logger.info(f"Successfully parsed {len(parsed_links)} related links")
 return parsed_links
 
 except Exception as e:
 logger.error(f"Related links generation failed: {e}")
 logger.error(f"Error type: {type(e)}")
 import traceback
 logger.error(f"Full traceback: {traceback.format_exc()}")
 return []

 def _parse_related_links(self, links_response: str) -> List[Dict[str, str]]:
 """Parse related links response into structured format."""
 try:
 logger.info(f"Parsing related links response, type: {type(links_response)}")
 
 if not isinstance(links_response, str):
 logger.error(f"Expected string response, got {type(links_response)}: {links_response}")
 return []
 
 logger.info(f"Response preview: {links_response[:300]}...")
 
 links = []
 lines = links_response.strip().split('\n')
 current_link = {}
 
 for i, line in enumerate(lines):
 line = line.strip()
 logger.debug(f"Processing line {i}: {line[:50]}...")
 
 if line.startswith('Title:'):
 # Save previous link if complete
 if isinstance(current_link, dict) and current_link.get('title') and current_link.get('url'):
 links.append(current_link.copy())
 # Start new link
 current_link = {'title': line.replace('Title:', '').strip()}
 elif line.startswith('URL:'):
 if isinstance(current_link, dict): # Ensure it's a dict
 current_link['url'] = line.replace('URL:', '').strip()
 else:
 logger.error(f"current_link is not a dict: {type(current_link)} = {current_link}")
 elif line.startswith('Description:'):
 if isinstance(current_link, dict): # Ensure it's a dict
 current_link['description'] = line.replace('Description:', '').strip()
 else:
 logger.error(f"current_link is not a dict: {type(current_link)} = {current_link}")
 
 # Don't forget the last link
 if isinstance(current_link, dict) and current_link.get('title') and current_link.get('url'):
 links.append(current_link.copy())
 
 logger.info(f"Successfully parsed {len(links)} related links")
 return links
 
 except Exception as e:
 logger.error(f"Error parsing related links: {e}")
 logger.error(f"Response type: {type(links_response)}")
 logger.error(f"Response preview: {str(links_response)[:200] if links_response else 'None'}")
 import traceback
 logger.error(f"Traceback: {traceback.format_exc()}")
 return []