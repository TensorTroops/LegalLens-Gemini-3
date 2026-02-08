"""
Professional PDF Report Generator
================================

Service for generating professional legal analysis reports in PDF format.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

logger = logging.getLogger(__name__)

class LegalReportGenerator:
 """
 Professional PDF report generator for legal document analysis.
 """
 
 def __init__(self):
 self.styles = getSampleStyleSheet()
 self._setup_custom_styles()
 
 def _setup_custom_styles(self):
 """Set up custom styles for professional legal reports."""
 
 # Title style
 self.title_style = ParagraphStyle(
 'CustomTitle',
 parent=self.styles['Heading1'],
 fontSize=20,
 spaceAfter=30,
 alignment=TA_CENTER,
 textColor=colors.Color(0.2, 0.2, 0.2)
 )
 
 # Section header style
 self.section_style = ParagraphStyle(
 'SectionHeader',
 parent=self.styles['Heading2'],
 fontSize=14,
 spaceBefore=20,
 spaceAfter=12,
 textColor=colors.Color(0.1, 0.1, 0.4),
 borderWidth=2,
 borderColor=colors.Color(0.8, 0.8, 0.8),
 borderPadding=5
 )
 
 # Body text style
 self.body_style = ParagraphStyle(
 'CustomBody',
 parent=self.styles['Normal'],
 fontSize=11,
 spaceAfter=12,
 alignment=TA_JUSTIFY,
 leftIndent=0,
 rightIndent=0
 )
 
 # Term definition style
 self.term_style = ParagraphStyle(
 'TermStyle',
 parent=self.styles['Normal'],
 fontSize=10,
 spaceAfter=8,
 leftIndent=20,
 bulletIndent=15
 )
 
 # Risk analysis style
 self.risk_style = ParagraphStyle(
 'RiskStyle',
 parent=self.styles['Normal'],
 fontSize=11,
 spaceAfter=10,
 alignment=TA_JUSTIFY,
 borderWidth=1,
 borderColor=colors.Color(0.9, 0.9, 0.9),
 borderPadding=10
 )
 
 async def generate_comprehensive_report(
 self, 
 analysis_data: Dict[str, Any],
 filename: str = None
 ) -> bytes:
 """
 Generate comprehensive legal analysis PDF report with detailed content.
 
 Args:
 analysis_data: Analysis results from comprehensive analyzer
 filename: Optional filename for the document
 
 Returns:
 PDF bytes
 """
 try:
 logger.info(" PDF GENERATOR: Starting comprehensive report generation")
 
 # Create PDF buffer
 buffer = io.BytesIO()
 
 # Create document with larger page size for more content
 doc = SimpleDocTemplate(
 buffer,
 pagesize=A4,
 rightMargin=50,
 leftMargin=50,
 topMargin=50,
 bottomMargin=50
 )
 
 # Build content
 story = []
 
 # Title page
 story.append(Paragraph("LEGAL DOCUMENT ANALYSIS REPORT", self.title_style))
 story.append(Spacer(1, 0.3*inch))
 
 # Document info
 if filename:
 story.append(Paragraph(f"<b>Document:</b> {filename}", self.body_style))
 
 timestamp = analysis_data.get("processing_metadata", {}).get("analysis_timestamp", "")
 if timestamp:
 try:
 formatted_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%B %d, %Y at %I:%M %p")
 story.append(Paragraph(f"<b>Analysis Date:</b> {formatted_time}", self.body_style))
 except Exception:
 story.append(Paragraph(f"<b>Analysis Date:</b> {timestamp}", self.body_style))
 
 story.append(Paragraph("<b>Report Type:</b> Comprehensive Legal Analysis", self.body_style))
 story.append(Spacer(1, 0.4*inch))
 
 # Section 1: Comprehensive Document Summary
 story.append(Paragraph("DOCUMENT SUMMARY", self.section_style))
 
 # Use detailed summary if available, fallback to regular summary
 detailed_summary = analysis_data.get("detailed_document_summary", "")
 regular_summary = analysis_data.get("document_summary", "")
 summary_to_use = detailed_summary if detailed_summary and len(detailed_summary) > len(regular_summary) else regular_summary
 
 if summary_to_use:
 story.append(Paragraph(summary_to_use, self.body_style))
 else:
 story.append(Paragraph("No summary available for this document.", self.body_style))
 
 story.append(Spacer(1, 0.3*inch))
 
 # Section 2: Legal Terms and Meanings
 story.append(Paragraph("LEGAL TERMS AND MEANINGS", self.section_style))
 
 legal_terms = analysis_data.get("legal_terms_and_meanings", [])
 if legal_terms:
 story.append(Paragraph("The following legal terms are identified and explained:", self.body_style))
 story.append(Spacer(1, 0.1*inch))
 
 for i, term_data in enumerate(legal_terms, 1):
 term_name = term_data.get("term", "")
 definition = term_data.get("definition", "")
 source = term_data.get("source", "")
 
 if term_name and definition:
 term_text = f"<b>{i}. {term_name}:</b> {definition}"
 if source:
 term_text += f" <i>(Source: {source})</i>"
 story.append(Paragraph(term_text, self.term_style))
 story.append(Spacer(1, 0.1*inch))
 else:
 story.append(Paragraph("No specific legal terms were identified in this document.", self.body_style))
 
 story.append(Spacer(1, 0.3*inch))
 
 # Section 3: Risk Analysis
 story.append(Paragraph("RISK ANALYSIS", self.section_style))
 risk_analysis = analysis_data.get("risk_analysis", "No risk analysis available")
 if risk_analysis:
 story.append(Paragraph(risk_analysis, self.body_style))
 story.append(Spacer(1, 0.3*inch))
 
 # Section 4: Applicable Laws
 story.append(Paragraph("APPLICABLE LAWS", self.section_style))
 
 applicable_laws = analysis_data.get("applicable_laws", [])
 if applicable_laws:
 story.append(Paragraph("The following Indian laws are applicable to this document:", self.body_style))
 story.append(Spacer(1, 0.1*inch))
 
 for i, law_data in enumerate(applicable_laws, 1):
 law_name = law_data.get("law", "")
 description = law_data.get("description", "")
 
 if law_name and description:
 law_text = f"<b>{i}. {law_name}:</b><br/>{description}"
 story.append(Paragraph(law_text, self.body_style))
 story.append(Spacer(1, 0.15*inch))
 else:
 story.append(Paragraph("No specific applicable laws were identified for this document.", self.body_style))
 
 # Section 5: Related Links and Resources
 related_links = analysis_data.get("related_links", [])
 if related_links:
 story.append(Spacer(1, 0.3*inch))
 story.append(Paragraph("RELATED LINKS AND RESOURCES", self.section_style))
 story.append(Paragraph("Additional resources for understanding legal aspects:", self.body_style))
 story.append(Spacer(1, 0.1*inch))
 
 for i, link_data in enumerate(related_links, 1):
 title = link_data.get("title", "")
 url = link_data.get("url", "")
 description = link_data.get("description", "")
 
 if title and url:
 link_text = f"<b>{i}. {title}</b><br/>"
 if description:
 link_text += f"{description}<br/>"
 link_text += f"<i>URL: {url}</i>"
 story.append(Paragraph(link_text, self.term_style))
 story.append(Spacer(1, 0.1*inch))
 
 # Footer and Disclaimer
 story.append(Spacer(1, 0.4*inch))
 
 disclaimer_style = ParagraphStyle(
 'Disclaimer',
 parent=self.styles['Normal'],
 fontSize=10,
 alignment=TA_JUSTIFY,
 textColor=colors.Color(0.4, 0.4, 0.4),
 borderWidth=1,
 borderColor=colors.Color(0.8, 0.8, 0.8),
 borderPadding=10
 )
 
 disclaimer_text = """
 <b>LEGAL DISCLAIMER:</b><br/><br/>
 This analysis is generated by LegalLens AI for informational purposes only. 
 The content provided should not be considered as legal advice, and should not be 
 relied upon as a substitute for consultation with qualified legal professionals. 
 <br/><br/>
 The accuracy and completeness of this analysis cannot be guaranteed, and LegalLens 
 disclaims any liability for actions taken based on this information. For specific 
 legal guidance related to your situation, please consult with a licensed attorney 
 familiar with the relevant jurisdiction and area of law.
 <br/><br/>
 Generated by LegalLens AI Legal Assistant | www.legallens.ai
 """
 story.append(Paragraph(disclaimer_text, disclaimer_style))
 
 # Build PDF
 doc.build(story)
 
 # Get PDF bytes
 pdf_bytes = buffer.getvalue()
 buffer.close()
 
 logger.info(f" PDF GENERATOR: Report generated successfully ({len(pdf_bytes)} bytes)")
 return pdf_bytes
 
 except Exception as e:
 logger.error(f" PDF GENERATOR: Report generation failed: {str(e)}")
 raise Exception(f"PDF report generation failed: {str(e)}")
 
 def _format_text_with_bullets(self, text: str) -> str:
 """Format text with bullet points for better readability."""
 lines = text.split('\n')
 formatted_lines = []
 
 for line in lines:
 line = line.strip()
 if line.startswith('•') or line.startswith('-'):
 formatted_lines.append(f"&bull; {line[1:].strip()}")
 elif line:
 formatted_lines.append(line)
 
 return '<br/>'.join(formatted_lines)

# Service instance
legal_report_generator = LegalReportGenerator()

async def generate_legal_analysis_pdf(analysis_data: Dict[str, Any], filename: str = None) -> bytes:
 """
 Generate PDF report for legal analysis.
 
 Args:
 analysis_data: Comprehensive analysis results
 filename: Optional document filename
 
 Returns:
 PDF bytes
 """
 return await legal_report_generator.generate_comprehensive_report(analysis_data, filename)