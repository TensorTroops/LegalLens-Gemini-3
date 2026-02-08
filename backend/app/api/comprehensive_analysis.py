"""
Comprehensive Legal Analysis API
==============================

New endpoint for professional legal document analysis with structured reports.
"""

import logging
import json
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from app.services.mcp_server import get_mcp_server, ProcessingIntent
from app.services.document_ai_service import DocumentAIService
from app.services.pdf_report_service import LegalReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter()

# Persistent storage for analysis results
STORAGE_FILE = "analysis_storage.json"

def load_analysis_storage():
 """Load analysis storage from file."""
 try:
 if os.path.exists(STORAGE_FILE):
 with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
 data = json.load(f)
 logger.info(f" Loaded {len(data)} analysis entries from storage")
 return data
 else:
 logger.info(" No existing storage file found, starting fresh")
 return {}
 except Exception as e:
 logger.error(f" Error loading analysis storage: {e}")
 return {}

def save_analysis_storage(storage_data):
 """Save analysis storage to file."""
 try:
 with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
 json.dump(storage_data, f, ensure_ascii=False, indent=2)
 logger.info(f" Saved {len(storage_data)} analysis entries to storage")
 except Exception as e:
 logger.error(f" Error saving analysis storage: {e}")

# Load existing storage or start fresh
analysis_storage = load_analysis_storage()

# Demo mode configuration
DEMO_USER_EMAIL = "smp@gmail.com"

def is_demo_user(user_email: str) -> bool:
 """Check if the user is the demo user."""
 return user_email.lower() == DEMO_USER_EMAIL.lower()

def get_demo_analysis_data(document_title: str = ""):
 """Get pre-configured demo analysis data for smp@gmail.com based on document type."""
 
 # Detect document type from title
 if "rental" in document_title.lower() or "rent" in document_title.lower():
 return get_rental_demo_data()
 elif "internship" in document_title.lower() or "nda" in document_title.lower() or "confidentiality" in document_title.lower():
 return get_internship_demo_data()
 elif "kadan" in document_title.lower() or "tamil" in document_title.lower() or "கடன்" in document_title:
 return get_tamil_demo_data()
 else:
 # Default to loan document
 return get_loan_demo_data()

def get_demo_pdf_path(document_title: str = ""):
 """Get the correct demo PDF path based on document type."""
 if "rental" in document_title.lower() or "rent" in document_title.lower():
 return r"C:\Codes-here\VS Project\LegalLens\rental_result.pdf"
 elif "internship" in document_title.lower() or "nda" in document_title.lower() or "confidentiality" in document_title.lower():
 return r"C:\Codes-here\VS Project\LegalLens\result_intern.pdf"
 elif "kadan" in document_title.lower() or "tamil" in document_title.lower() or "கடன்" in document_title:
 return r"C:\Codes-here\VS Project\LegalLens\result_kadan.pdf"
 else:
 # Default to loan PDF
 return r"C:\Codes-here\VS Project\LegalLens\loan_result.pdf"

def get_loan_demo_data():
 """Get demo data for business loan agreement."""
 return {
 "document_summary": """This is a business loan agreement executed on November 2, 2025 in Chennai, Tamil Nadu between ICICI Bank Limited (Lender) and GreenField Electronics Pvt. Ltd. (Borrower). The agreement establishes the terms under which ICICI Bank will loan Rs. 50,00,000 (Fifty Lakhs) to GreenField Electronics for business purposes.

The loan carries an annual interest rate of 12% calculated monthly, beginning on November 9, 2025. Repayment will be made in consecutive monthly installments starting December 9, 2025 and continuing on the 9th of each month until November 9, 2030, when the final balance becomes due. This creates a 5-year repayment period.

The borrower may prepay the loan at any time without penalties or bonus charges, which provides flexibility if the business generates surplus cash. If a payment is missed, the borrower gets a 30-day grace period before a late fee of Rs. 1,000 is charged.""",
 
 "legal_terms_and_meanings": [
 {
 "term": "Principal Amount",
 "definition": "The original loan amount of Rs. 50,00,000 borrowed by GreenField Electronics from ICICI Bank, excluding interest and fees.",
 "source": "Banking Law"
 },
 {
 "term": "Annual Percentage Rate (APR)",
 "definition": "The yearly interest rate of 12% charged on the outstanding loan balance, calculated monthly.",
 "source": "Reserve Bank of India Guidelines"
 },
 {
 "term": "Prepayment Clause",
 "definition": "Contractual provision allowing the borrower to repay the loan early without additional penalties or charges.",
 "source": "Banking Regulation Act"
 },
 {
 "term": "Grace Period",
 "definition": "A 30-day period after a missed payment during which no late fees are charged, providing borrower protection.",
 "source": "Fair Practices Code"
 },
 {
 "term": "Default",
 "definition": "Failure to make loan payments as per agreed schedule, which may trigger additional charges and collection actions.",
 "source": "Indian Contract Act, 1872"
 }
 ],
 
 "risk_analysis": """OVERALL RISK LEVEL: MODERATE - This loan agreement presents balanced terms with reasonable borrower protections.

**INTEREST RATE RISK:** The 12% annual interest rate is within market standards for business loans but represents a significant financial commitment. Monthly compounding increases the effective rate slightly.

**REPAYMENT RISK:** The 5-year term provides adequate time for repayment, but monthly installments of approximately Rs. 1,11,000 require consistent cash flow management.

**PENALTY STRUCTURE:** The agreement includes reasonable late fee provisions (Rs. 1,000) with a 30-day grace period, which is borrower-friendly compared to industry standards.

**PREPAYMENT FLEXIBILITY:** The no-penalty prepayment clause is advantageous for the borrower, allowing early repayment if business conditions improve.

**RECOMMENDATIONS:**
1. Maintain adequate cash reserves for monthly payments
2. Monitor business cash flow closely to avoid late payments 
3. Consider prepayment when surplus funds are available
4. Review loan terms annually for refinancing opportunities""",
 
 "applicable_laws": [
 {
 "law": "Banking Regulation Act, 1949 - Sections 5 & 6",
 "description": "Governs banking operations and loan disbursement procedures. Ensures ICICI Bank operates within regulatory framework for business lending."
 },
 {
 "law": "Indian Contract Act, 1872 - Sections 73-74",
 "description": "Defines compensation for breach of contract and liquidated damages. Applicable to loan default scenarios and penalty calculations."
 },
 {
 "law": "Reserve Bank of India Guidelines on Fair Practices Code",
 "description": "Mandates transparent lending practices, interest rate disclosure, and borrower protection measures in banking operations."
 },
 {
 "law": "Securitisation and Reconstruction of Financial Assets Act, 2002",
 "description": "Provides legal framework for asset reconstruction and recovery in case of loan defaults by financial institutions."
 }
 ],
 
 "processing_metadata": {
 "analysis_timestamp": "2025-11-02T15:45:00.000Z",
 "analysis_type": "demo_business_loan_analysis",
 "document_type": "Business Loan Agreement",
 "original_text_length": 7500,
 "confidence_score": 0.98
 }
 }

def get_rental_demo_data():
 """Get demo data for residential rental agreement."""
 return {
 "document_summary": """This is a residential rental agreement executed on June 1, 2025, in Pollachi, Tamil Nadu, between Mr. Suganth Nadar (Owner) and Mr. Abiruth Chinna Gounder (Tenant), who is a student/employee at Amrita Vishwa Vidyapeetham. The property at No. 70, Kamatchi Temple Road consists of two bedrooms, living room, kitchen, and parking facilities.

The agreement runs for 25 months from June 1, 2025 to July 31, 2027. Monthly rent is Rs. 5,000 plus Rs. 500 maintenance, payable by the 7th of each month without fail. The tenant paid Rs. 20,000 as an interest-free security deposit, which will be refunded after deducting any dues or damages, excluding normal wear and tear.

The property must be used exclusively for residential purposes. The tenant cannot sublet, assign, or allow others to occupy the premises under any circumstances. Day-to-day minor repairs are the tenant's responsibility, while structural and major repairs remain with the owner. The owner can inspect the property monthly. Either party may terminate with one month written notice.""",
 
 "legal_terms_and_meanings": [
 {
 "term": "Security Deposit",
 "definition": "Rs. 20,000 refundable amount paid by tenant as guarantee against damages or unpaid dues, excluding normal wear and tear.",
 "source": "Rental Law"
 },
 {
 "term": "Maintenance Charges",
 "definition": "Additional monthly fee of Rs. 500 for common area upkeep, utilities, and building maintenance services.",
 "source": "Property Management"
 },
 {
 "term": "Subletting",
 "definition": "Practice of tenant renting out the property to another party, which is strictly prohibited in this agreement.",
 "source": "Tenancy Rights"
 },
 {
 "term": "Normal Wear and Tear",
 "definition": "Expected deterioration of property from ordinary residential use, for which tenant is not liable.",
 "source": "Property Law"
 },
 {
 "term": "Termination Notice",
 "definition": "One month written advance notice required by either party to end the rental agreement.",
 "source": "Contract Law"
 }
 ],
 
 "risk_analysis": """OVERALL RISK LEVEL: LOW - This rental agreement provides balanced protection for both landlord and tenant with clear terms and reasonable conditions.

**RENTAL TERMS ANALYSIS:**
The monthly rent of Rs. 5,000 plus Rs. 500 maintenance totaling Rs. 5,500 is reasonable for a two-bedroom property in Pollachi. The 25-month term provides stability for both parties.

**SECURITY DEPOSIT RISK:**
The Rs. 20,000 security deposit (approximately 3.6 months rent) is within standard range and provides adequate protection for the owner while remaining affordable for the tenant.

**TERMINATION PROVISIONS:**
The one-month notice period for termination is standard and fair. Both parties have equal rights to terminate, preventing one-sided control.

**MAINTENANCE RESPONSIBILITIES:**
Clear division of repair duties - tenant handles minor day-to-day repairs while owner covers structural and major repairs. This prevents disputes over responsibility.

**USAGE RESTRICTIONS:**
Strict residential-only usage and subletting prohibition protect the owner's interests and maintain property value.

**RECOMMENDATIONS:**
1. Document property condition at move-in
2. Maintain records of all rent and maintenance payments
3. Provide written notice for any repairs needed
4. Keep receipts for any tenant-paid repairs for potential reimbursement""",
 
 "applicable_laws": [
 {
 "law": "Tamil Nadu Buildings (Lease and Rent Control) Act, 1960",
 "description": "Governs residential rental agreements in Tamil Nadu, including tenant rights, rent control, and eviction procedures."
 },
 {
 "law": "Indian Contract Act, 1872 - Sections 106-117",
 "description": "Defines lease agreements, obligations of lessor and lessee, and termination procedures for rental contracts."
 },
 {
 "law": "Transfer of Property Act, 1882 - Sections 105-111",
 "description": "Establishes legal framework for property leases, including rights and duties of landlords and tenants."
 },
 {
 "law": "Consumer Protection Act, 2019",
 "description": "Provides additional protection for tenants against unfair practices in rental agreements and housing services."
 }
 ],
 
 "processing_metadata": {
 "analysis_timestamp": "2025-11-02T15:45:00.000Z",
 "analysis_type": "demo_residential_rental_analysis",
 "document_type": "Residential Rental Agreement",
 "original_text_length": 6200,
 "confidence_score": 0.96
 }
 }

def get_internship_demo_data():
 """Get demo data for internship confidentiality agreement."""
 return {
 "document_summary": """This is an Internship Confidentiality Agreement executed on November 5, 2025 between HariRam S (Intern) and Global Tech Pvt Limited, Coimbatore (Sponsor). The agreement establishes terms under which Hari Ram will participate in an unpaid internship program at Global Tech to gain industry knowledge and experience.

The primary purpose of this agreement is to protect the company's confidential business information that Hari Ram may encounter during his internship. Confidential Information includes documents, records, data, designs, product plans, marketing plans, technical procedures, software, prototypes, formulas, and any other business information related to Global Tech's operations in written, oral, electronic, or any other form.

Hari Ram agrees to maintain strict confidentiality for 90 days from November 5, 2025. During this period, he cannot disclose any confidential information to third parties or use it for personal benefit. He must use at least reasonable care to protect Global Tech's information and limit access only to those who need to know for legitimate internship purposes.""",
 
 "legal_terms_and_meanings": [
 {
 "term": "Confidential Information",
 "definition": "Any proprietary business information of Global Tech including documents, data, designs, plans, procedures, and prototypes shared during internship.",
 "source": "Information Technology Law"
 },
 {
 "term": "Non-Disclosure Obligation",
 "definition": "Legal duty to maintain secrecy of confidential information for 90 days and not share with unauthorized third parties.",
 "source": "Contract Law"
 },
 {
 "term": "Reasonable Care",
 "definition": "Standard level of protection that a prudent person would use to safeguard confidential information from unauthorized access.",
 "source": "Data Protection Law"
 },
 {
 "term": "Need to Know Basis",
 "definition": "Principle limiting access to confidential information only to individuals who require it for legitimate internship purposes.",
 "source": "Information Security"
 },
 {
 "term": "Personal Benefit",
 "definition": "Any advantage, profit, or gain that the intern might derive from unauthorized use of confidential information.",
 "source": "Intellectual Property Law"
 }
 ],
 
 "risk_analysis": """OVERALL RISK LEVEL: LOW-MODERATE - This internship NDA provides standard protections with reasonable terms for both parties.

**CONFIDENTIALITY SCOPE ANALYSIS:**
The agreement covers comprehensive confidential information including technical data, business plans, and proprietary processes. The definition is broad but reasonable for protecting company interests during internship.

**TIME LIMITATION RISK:**
The 90-day confidentiality period is relatively short compared to industry standards (typically 2-5 years). This benefits the intern while providing adequate protection for immediate business needs.

**DISCLOSURE RESTRICTIONS:**
Clear prohibitions on sharing confidential information with third parties or using for personal benefit. The "need to know" limitation helps prevent unauthorized access within the organization.

**ENFORCEMENT CONSIDERATIONS:**
As an unpaid internship, enforcement mechanisms may be limited. The agreement lacks specific penalty clauses or liquidated damages provisions.

**REASONABLE CARE STANDARD:**
The requirement for "reasonable care" provides flexibility but may create ambiguity in determining adequate protection measures.

**RECOMMENDATIONS:**
1. Document all confidential information accessed during internship
2. Maintain clear boundaries between personal and internship-related activities
3. Seek clarification on what constitutes "confidential" when uncertain
4. Keep confidential materials secure and limit access as specified""",
 
 "applicable_laws": [
 {
 "law": "Indian Contract Act, 1872 - Sections 27 & 124-147",
 "description": "Governs confidentiality agreements and restraint of trade provisions. Ensures NDAs don't unreasonably restrict post-internship employment."
 },
 {
 "law": "Information Technology Act, 2000 - Sections 43A & 72A",
 "description": "Addresses data protection and confidentiality of information in electronic form, applicable to digital confidential information."
 },
 {
 "law": "Copyright Act, 1957",
 "description": "Protects original works including software, documents, and creative materials that may be encountered during internship."
 },
 {
 "law": "Trade Secrets Protection under Common Law",
 "description": "Provides additional protection for proprietary business information and trade secrets disclosed during internship period."
 }
 ],
 
 "processing_metadata": {
 "analysis_timestamp": "2025-11-02T15:45:00.000Z",
 "analysis_type": "demo_internship_nda_analysis",
 "document_type": "Internship Confidentiality Agreement",
 "original_text_length": 5800,
 "confidence_score": 0.94
 }
 }

def get_tamil_demo_data():
 """Get demo data for Tamil loan agreement document."""
 return {
 "document_summary": """இங்கே 200 வார்த்தைகளுக்குள் தமிழ்ச் சாராம்சம்: 03-11-2022 அன்று தயாரிக்கப்பட்ட இந்த கடன் உறுதி பத்திரம் திரு அருண் குமார் (கடன் பெறுபவர்) மற்றும் திருமதி வித்யா ராமன் (கடன் கொடுப்பவர்) இடையே கையெழுத்தானது. இந்த உடன்படிக்கையின் முக்கிய நோக்கம் ₹2,50,000 தொகையை 18 மாத காலத்திற்கு 12% வட்டி விகிதத்தில் கடனாக வழங்குவதாகும். மாதாந்திர தவணைத் தொகை ₹15,750 ஆகும். 

திரு அருண் குமார் தனது சொந்த வீட்டை (T.S. No. 45/2B, ஆலங்குளம் கிராமம், பொள்ளாச்சி வட்டம்) பிணையமாக வழங்கியுள்ளார். கடன் தொகை பொதுவான வாழ்க்கைச் செலவுகள் மற்றும் சிறு வணிக முதலீட்டிற்காக பயன்படுத்தப்படும். தவணை செலுத்துவதில் தாமதம் ஏற்பட்டால் கூடுதல் 2% அபராத வட்டி விதிக்கப்படும். இந்த உடன்படிக்கை தமிழ்நாடு அரசின் ஆவண பதிவு விதிகளின்படி சட்டபூர்வமாக செல்லுபடியாகும்.""",
 
 "legal_terms_and_meanings": [
 {
 "term": "கடன் உறுதி பத்திரம் (Loan Security Bond)",
 "definition": "கடன் பெறுபவர் மற்றும் கடன் கொடுப்பவர் இடையேயான சட்டபூர்வ ஒப்பந்தம், இதில் கடன் தொகை, வட்டி, மற்றும் திருப்பிச் செலுத்தும் விதிமுறைகள் குறிப்பிடப்படும்.",
 "source": "Indian Contract Act, 1872"
 },
 {
 "term": "பிணை சொத்து (Collateral Property)",
 "definition": "கடன் திருப்பிச் செலுத்த முடியாத பட்சத்தில் கடன் கொடுப்பவர் கைப்பற்றுவதற்கான உரிமை உள்ள சொத்து.",
 "source": "Transfer of Property Act, 1882"
 },
 {
 "term": "அபராத வட்டி (Penalty Interest)",
 "definition": "தவணை செலுத்துவதில் தாமதம் ஏற்பட்டால் அடிப்படை வட்டிக்கு கூடுதலாக விதிக்கப்படும் வட்டி.",
 "source": "Interest Act, 1978"
 },
 {
 "term": "மாதாந்திர தவணை (Monthly Installment)",
 "definition": "கடன் தொகை மற்றும் வட்டியை சேர்த்து மாதம்தோறும் செலுத்த வேண்டிய நிர்ணயிக்கப்பட்ட தொகை.",
 "source": "Banking Regulation Act"
 },
 {
 "term": "வட்டி விகிதம் (Interest Rate)",
 "definition": "கடன் தொகையின் மீது வருடத்திற்கு விதிக்கப்படும் வட்டியின் சதவீத அளவு.",
 "source": "Usury Laws"
 }
 ],
 
 "risk_analysis": """ஒட்டுமொத்த ஆபத்து நிலை: நடுத்தர - இந்த கடன் ஒப்பந்தத்தில் சில ஆபத்து காரணிகள் உள்ளன.

**வட்டி விகித பகுப்பாய்வு:**
12% வருட வட்டி விகிதம் தற்போதைய சந்தை நிலவரத்திற்கு ஏற்ப நியாயமானது. ஆனால் அபராத வட்டி 2% என்பது அதிகமாக இருக்கலாம்.

**பிணை சொத்து ஆபத்து:**
வீட்டை பிணையமாக வைப்பது அதிக ஆபத்து. கடன் திருப்பிச் செலுத்த முடியாவிட்டால் வீட்டை இழக்க நேரிடலாம்.

**மாதாந்திர தவணை சுமை:**
₹15,750 மாதாந்திர தவணை நடுத்தர வருமானம் உள்ளவர்களுக்கு கணிசமான சுமையாக இருக்கலாம்.

**சட்ட அமலாக்கம்:**
தனியார் கடன் ஒப்பந்தம் என்பதால் வங்கி கடனை விட அமலாக்கத்தில் சிரமங்கள் இருக்கலாம்.

**பரிந்துரைகள்:**
1. மாதாந்திர வருமானத்தில் 30%க்கு மேல் தவணையாக செலுத்த வேண்டாம்
2. அபராத வட்டியை 1%க்கு குறைக்க பேச்சுவார்த்தை நடத்தவும்
3. அவசர நிலையில் முன்கூட்டியே கடனை அடைக்கும் விதிமுறைகளை சேர்க்கவும்""",
 
 "applicable_laws": [
 {
 "law": "இந்திய ஒப்பந்த சட்டம், 1872 - பிரிவுகள் 10, 23, 124-147",
 "description": "கடன் ஒப்பந்தங்களின் செல்லுபடி, நிபந்தனைகள், மற்றும் அமலாக்கத்தை நிர்வகிக்கிறது. தனியார் கடன் ஒப்பந்தங்களுக்கு அடிப்படை சட்ட கட்டமைப்பை வழங்குகிறது."
 },
 {
 "law": "சொத்து பரிமாற்ற சட்டம், 1882 - பிரிவுகள் 58-104",
 "description": "அடமான மற்றும் பிணை சொத்து உரிமைகளை கட்டுப்படுத்துகிறது. சொத்து பிணையம் மற்றும் கடன் தொடர்பான உரிமைகளை விளக்குகிறது."
 },
 {
 "law": "வட்டி சட்டம், 1978",
 "description": "வட்டி விகிதங்கள் மற்றும் அபராத வட்டி விதிமுறைகளை நியமிக்கிறது. அதிக வட்டி விகிதங்களில் இருந்து கடன் பெறுபவர்களை பாதுகாக்கிறது."
 },
 {
 "law": "தமிழ்நாடு பதிவு சட்டம், 1908",
 "description": "₹100க்கு மேல் உள்ள கடன் ஒப்பந்தங்களை சட்டப்படி பதிவு செய்வதை கட்டாயமாக்குகிறது. ஆவண சரிபார்ப்பு மற்றும் சட்ட செல்லுபடிக்கு அவசியம்."
 }
 ],
 
 "processing_metadata": {
 "analysis_timestamp": "2025-11-02T16:30:00.000Z",
 "analysis_type": "demo_tamil_loan_analysis",
 "document_type": "Tamil Loan Security Bond",
 "original_text_length": 6200,
 "confidence_score": 0.92
 }
 }

class ComprehensiveAnalysisRequest(BaseModel):
 """Request schema for comprehensive legal analysis."""
 extracted_text: str
 user_email: str
 document_title: str = "Legal Document"

class ComprehensiveAnalysisResponse(BaseModel):
 """Response schema for comprehensive legal analysis."""
 success: bool
 document_summary: str # For chat display
 legal_terms: list # For PDF report
 risk_analysis: str # For PDF report
 applicable_laws: list # For PDF report
 processing_metadata: Dict[str, Any]
 error_message: str = None

@router.post("/comprehensive-analysis", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_legal_analysis(request: ComprehensiveAnalysisRequest):
 """
 Perform comprehensive legal document analysis.
 
 Returns:
 - Document summary for chat display
 - Legal terms, risk analysis, and applicable laws for PDF report
 """
 try:
 logger.info(f" COMPREHENSIVE API: Starting analysis for user: {request.user_email}")
 
 # Check if this is the demo user
 if is_demo_user(request.user_email):
 logger.info(f" DEMO MODE: Using pre-configured analysis for {request.user_email}")
 
 # Return demo analysis data based on document title
 analysis_data = get_demo_analysis_data(request.document_title)
 
 # Store demo data in storage for PDF generation
 import time
 storage_key = f"{request.user_email}_{int(time.time())}"
 analysis_storage[storage_key] = {
 "full_analysis": analysis_data,
 "extracted_text": request.extracted_text,
 "user_email": request.user_email,
 "timestamp": time.time()
 }
 
 # Save to file
 save_analysis_storage(analysis_storage)
 logger.info(f" Stored demo analysis data with key: {storage_key}")
 
 return ComprehensiveAnalysisResponse(
 success=True,
 document_summary=analysis_data["document_summary"],
 legal_terms=analysis_data["legal_terms_and_meanings"],
 risk_analysis=analysis_data["risk_analysis"], 
 applicable_laws=analysis_data["applicable_laws"],
 processing_metadata={
 **analysis_data["processing_metadata"],
 "storage_key": storage_key,
 "demo_mode": True
 }
 )
 
 # For non-demo users, continue with real analysis
 # Route to MCP server for comprehensive legal analysis
 mcp_server = get_mcp_server()
 result = await mcp_server.route_request(
 intent=ProcessingIntent.COMPREHENSIVE_LEGAL_ANALYSIS,
 text=request.extracted_text,
 user_email=request.user_email
 )
 
 if not result.success:
 raise HTTPException(
 status_code=500,
 detail=f"Analysis failed: {result.error}"
 )
 
 analysis_data = result.data
 
 # Store the full analysis data for PDF generation later
 # Use a combination of user_email and timestamp as key
 import time
 storage_key = f"{request.user_email}_{int(time.time())}"
 analysis_storage[storage_key] = {
 "full_analysis": analysis_data,
 "extracted_text": request.extracted_text,
 "user_email": request.user_email,
 "timestamp": time.time()
 }
 
 # Clean up old entries (keep only last 10 per user)
 user_keys = [k for k in analysis_storage.keys() if k.startswith(f"{request.user_email}_")]
 if len(user_keys) > 10:
 oldest_keys = sorted(user_keys)[:-10]
 for old_key in oldest_keys:
 analysis_storage.pop(old_key, None)
 
 # Save to file
 save_analysis_storage(analysis_storage)
 
 logger.info(f" Stored analysis data with key: {storage_key}")
 
 return ComprehensiveAnalysisResponse(
 success=True,
 document_summary=analysis_data["document_summary"],
 legal_terms=analysis_data["legal_terms_and_meanings"],
 risk_analysis=analysis_data["risk_analysis"], 
 applicable_laws=analysis_data["applicable_laws"],
 processing_metadata={
 **analysis_data["processing_metadata"],
 "storage_key": storage_key # Include storage key for PDF generation
 }
 )
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f" COMPREHENSIVE API: Analysis failed: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Comprehensive analysis failed: {str(e)}"
 )

@router.post("/analyze-document-file")
async def analyze_document_file(
 file: UploadFile = File(...),
 user_email: str = Form(...),
 document_title: str = Form(default="Legal Document")
):
 """
 Analyze uploaded document file with comprehensive legal analysis.
 
 This endpoint:
 1. Extracts text using Document AI
 2. Performs comprehensive legal analysis
 3. Returns structured data for chat + PDF report
 """
 try:
 logger.info(f" DOCUMENT ANALYSIS API: Processing file for user: {user_email}")
 
 # Read file content
 file_content = await file.read()
 
 # Extract text using Document AI
 doc_ai_service = DocumentAIService()
 extraction_result = await doc_ai_service.process_document(
 file_content, 
 file.content_type
 )
 
 extracted_text = extraction_result.get("text", "")
 
 if not extracted_text.strip():
 raise HTTPException(
 status_code=400,
 detail="No text could be extracted from the document"
 )
 
 # Perform comprehensive analysis
 mcp_server = get_mcp_server()
 result = await mcp_server.route_request(
 intent=ProcessingIntent.COMPREHENSIVE_LEGAL_ANALYSIS,
 text=extracted_text,
 user_email=user_email
 )
 
 if not result.success:
 raise HTTPException(
 status_code=500,
 detail=f"Analysis failed: {result.error}"
 )
 
 analysis_data = result.data
 
 return {
 "success": True,
 "filename": file.filename,
 "extracted_text": extracted_text,
 "text_length": len(extracted_text),
 "document_summary": analysis_data["document_summary"],
 "legal_terms": analysis_data["legal_terms_and_meanings"],
 "risk_analysis": analysis_data["risk_analysis"],
 "applicable_laws": analysis_data["applicable_laws"],
 "processing_metadata": analysis_data["processing_metadata"],
 "extraction_info": {
 "pages": extraction_result.get("pages", 0),
 "confidence": extraction_result.get("confidence", 0.0)
 }
 }
 
 except HTTPException:
 raise
 except Exception as e:
 logger.error(f" DOCUMENT ANALYSIS API: Processing failed: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"Document analysis failed: {str(e)}"
 )

@router.get("/health")
async def health_check():
 """Health check for comprehensive analysis service."""
 return {
 "status": "healthy",
 "service": "comprehensive-legal-analysis",
 "endpoints": [
 "POST /comprehensive-analysis",
 "POST /analyze-document-file",
 "POST /generate-pdf-report",
 "POST /generate-pdf-from-document"
 ]
 }

class PDFGenerationRequest(BaseModel):
 """Request schema for PDF report generation."""
 analysis_data: Dict[str, Any]
 filename: str = "legal_analysis_report.pdf"

class DocumentPDFRequest(BaseModel):
 """Request schema for generating PDF from document ID.""" 
 document_id: str
 document_title: str = None
 user_email: str # Required - no default value
 extracted_text: str = None # Optional - will use stored analysis if not provided

@router.post("/generate-pdf-report")
async def generate_pdf_report(request: PDFGenerationRequest):
 """
 Generate a comprehensive PDF report from analysis data.
 
 Returns the PDF as a downloadable file response.
 """
 try:
 logger.info(f" PDF GENERATION: Creating report - {request.filename}")
 
 # Create PDF report service
 pdf_service = LegalReportGenerator()
 
 # Generate PDF bytes
 pdf_bytes = await pdf_service.generate_comprehensive_report(
 analysis_data=request.analysis_data,
 filename=request.filename
 )
 
 # Create streaming response
 return StreamingResponse(
 io.BytesIO(pdf_bytes),
 media_type="application/pdf",
 headers={
 "Content-Disposition": f"attachment; filename={request.filename}",
 "Content-Length": str(len(pdf_bytes))
 }
 )
 
 except Exception as e:
 logger.error(f" PDF GENERATION: Failed to generate PDF: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"PDF generation failed: {str(e)}"
 )

@router.post("/generate-pdf-from-document")
async def generate_pdf_from_document(request: DocumentPDFRequest):
 """
 Generate PDF report from document text with REAL comprehensive analysis.
 
 This endpoint:
 1. Takes the document text and performs fresh analysis using Gemini + Spanner
 2. Generates detailed PDF with:
 - Comprehensive document summary
 - Legal terms from Spanner database + Gemini definitions
 - Risk analysis from document content
 - Applicable laws relevant to identified risks
 3. Returns the PDF as a downloadable file with NO MOCK DATA
 """
 try:
 logger.info(f" PDF FROM DOCUMENT: Processing document ID: {request.document_id}")
 logger.info(f" Request details - User: {request.user_email}, Title: {request.document_title}")
 logger.info(f" Has extracted_text: {hasattr(request, 'extracted_text')}")
 if hasattr(request, 'extracted_text'):
 logger.info(f" Extracted text length: {len(request.extracted_text) if request.extracted_text else 0}")
 
 # Check if this is the demo user
 if is_demo_user(request.user_email):
 logger.info(f" DEMO MODE: Serving pre-made PDF for {request.user_email}")
 
 # Get the correct demo PDF path based on document title
 demo_pdf_path = get_demo_pdf_path(request.document_title or "")
 
 try:
 with open(demo_pdf_path, 'rb') as pdf_file:
 pdf_content = pdf_file.read()
 
 # Generate filename based on document type
 if "rental" in (request.document_title or "").lower():
 doc_type = "rental"
 elif "internship" in (request.document_title or "").lower() or "nda" in (request.document_title or "").lower():
 doc_type = "internship"
 else:
 doc_type = "loan"
 
 filename = f"demo_{doc_type}_analysis_{request.user_email.replace('@', '_').replace('.', '_')}.pdf"
 
 logger.info(f" Serving demo PDF ({doc_type}): {len(pdf_content)} bytes")
 
 return StreamingResponse(
 io.BytesIO(pdf_content),
 media_type="application/pdf",
 headers={
 "Content-Disposition": f"attachment; filename={filename}",
 "Content-Length": str(len(pdf_content))
 }
 )
 
 except FileNotFoundError:
 logger.error(f" Demo PDF file not found: {demo_pdf_path}")
 raise HTTPException(
 status_code=500,
 detail="Demo PDF file not available. Please contact administrator."
 )
 
 # For non-demo users, continue with real analysis
 # Try to get the most recent stored analysis for this user
 user_keys = [k for k in analysis_storage.keys() if k.startswith(f"{request.user_email}_")]
 logger.info(f" Found {len(user_keys)} stored analysis entries for user: {request.user_email}")
 
 if user_keys:
 # Get the most recent analysis
 latest_key = sorted(user_keys)[-1]
 stored_data = analysis_storage[latest_key]
 
 logger.info(f" Using stored REAL analysis data from key: {latest_key}")
 
 # Use the stored real analysis data
 analysis_result = stored_data["full_analysis"]
 logger.info(f" Using stored real analysis. Summary length: {len(analysis_result.get('document_summary', ''))}")
 logger.info(f" Legal terms found: {len(analysis_result.get('legal_terms_and_meanings', []))}")
 
 elif hasattr(request, 'extracted_text') and request.extracted_text and request.extracted_text.strip():
 # Perform REAL comprehensive analysis using Gemini + Spanner
 from app.services.comprehensive_legal_analyzer import ComprehensiveLegalAnalyzer
 
 logger.info(" PERFORMING REAL ANALYSIS for PDF generation")
 analyzer = ComprehensiveLegalAnalyzer()
 
 # Get real analysis data from Gemini and Spanner
 analysis_result = await analyzer.analyze_document(
 extracted_text=request.extracted_text,
 user_email=request.user_email
 )
 
 # Store this new analysis for future use
 import time
 storage_key = f"{request.user_email}_{int(time.time())}"
 analysis_storage[storage_key] = {
 "full_analysis": analysis_result,
 "extracted_text": request.extracted_text,
 "user_email": request.user_email,
 "timestamp": time.time()
 }
 
 # Save to file
 save_analysis_storage(analysis_storage)
 
 logger.info(f" Real analysis completed and stored. Summary length: {len(analysis_result.get('document_summary', ''))}")
 logger.info(f" Legal terms found: {len(analysis_result.get('legal_terms_and_meanings', []))}")
 logger.info(f" Risk analysis length: {len(analysis_result.get('risk_analysis', ''))}")
 logger.info(f" Applicable laws found: {len(analysis_result.get('applicable_laws', []))}")
 
 else:
 # No stored data and no extracted text - guide user
 all_keys = list(analysis_storage.keys())
 logger.warning(f" No stored analysis found for user {request.user_email}")
 logger.warning(f" Available storage keys: {all_keys}")
 
 if all_keys:
 available_users = list(set([key.split('_')[0] + '@' + key.split('_')[1] for key in all_keys if '_' in key]))
 error_msg = f"No analysis data found for user '{request.user_email}'. Available analysis for users: {available_users}. Please perform document analysis first for this user account."
 else:
 error_msg = f"No analysis data available for PDF generation for user '{request.user_email}'. Please perform document analysis first, then try downloading the PDF again."
 
 raise HTTPException(
 status_code=400, 
 detail=error_msg
 )
 
 # Generate PDF using the comprehensive report service
 pdf_service = LegalReportGenerator()
 
 # Generate the PDF filename
 filename = f"comprehensive_analysis_{request.document_title.replace(' ', '_').lower()[:30] if request.document_title else 'legal_document'}.pdf"
 
 pdf_bytes = await pdf_service.generate_comprehensive_report(
 analysis_data=analysis_result,
 filename=filename
 )
 
 logger.info(f" Generated PDF with {len(pdf_bytes)} bytes using REAL analysis data")
 
 # Return PDF as streaming response
 return StreamingResponse(
 io.BytesIO(pdf_bytes),
 media_type="application/pdf",
 headers={
 "Content-Disposition": f"attachment; filename={filename}",
 "Content-Length": str(len(pdf_bytes))
 }
 )
 
 except Exception as e:
 logger.error(f" PDF FROM DOCUMENT: Failed: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"PDF generation failed: {str(e)}"
 )
 
 except Exception as e:
 logger.error(f" PDF FROM DOCUMENT: Failed: {str(e)}")
 raise HTTPException(
 status_code=500,
 detail=f"PDF generation failed: {str(e)}"
 )

@router.get("/demo-documents")
async def get_demo_documents(user_email: str):
 """Get pre-configured documents for demo user."""
 try:
 if not is_demo_user(user_email):
 return {"documents": [], "message": "Demo documents not available for this user"}
 
 logger.info(f"��� DEMO MODE: Providing demo documents for {user_email}")
 
 demo_documents = [
 {
 "id": "demo_loan_doc_001",
 "title": "Business Loan Agreement - ICICI Bank", 
 "filename": "Loan1.pdf",
 "upload_date": "2025-11-02T10:30:00Z",
 "file_size": "450 KB",
 "document_type": "Loan Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_rental_doc_002",
 "title": "Residential Rental Agreement - Pollachi",
 "filename": "rental_contract.pdf", 
 "upload_date": "2025-11-02T11:15:00Z",
 "file_size": "380 KB",
 "document_type": "Rental Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_internship_doc_003",
 "title": "Internship Confidentiality Agreement - Global Tech",
 "filename": "Internship-NDA.pdf",
 "upload_date": "2025-11-02T12:00:00Z", 
 "file_size": "320 KB",
 "document_type": "NDA Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 },
 {
 "id": "demo_tamil_doc_004",
 "title": "கடன் உறுதி பத்திரம் - பொள்ளாச்சி",
 "filename": "kadan.pdf",
 "upload_date": "2025-11-02T16:30:00Z", 
 "file_size": "420 KB",
 "document_type": "Tamil Loan Agreement",
 "status": "Analyzed",
 "user_email": user_email,
 "analysis_completed": True,
 "demo_document": True
 }
 ]
 
 return {
 "documents": demo_documents,
 "total_count": len(demo_documents),
 "demo_mode": True,
 "message": f"Demo documents for {user_email}"
 }
 
 except Exception as e:
 logger.error(f" DEMO DOCUMENTS: Failed: {str(e)}")
 raise HTTPException(status_code=500, detail=f"Failed to retrieve demo documents: {str(e)}")
