"""
LegalLens Document AI Backend
============================

FastAPI application for document processing with Google Document AI.
"""

import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

from app.api.documents import router as documents_router
from app.api.legal_chat import router as legal_chat_router
from app.api.dictionary import router as dictionary_router
from app.api.files import router as files_router
from app.api.mcp_routes import router as mcp_router
from app.api.comprehensive_analysis import router as comprehensive_router
from app.config.settings import get_settings

# Configure logging
logging.basicConfig(
 level=logging.INFO,
 format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
 title=settings.APP_NAME,
 description="Document AI processing service for LegalLens",
 version="1.0.0",
 debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
 CORSMiddleware,
 allow_origins=["*"], # Configure this properly for production
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)

# Include routers
app.include_router(
 files_router,
 prefix="/api/v1/files",
 tags=["files"]
)

app.include_router(
 documents_router,
 prefix="/api/v1/documents",
 tags=["documents"]
)

app.include_router(
 legal_chat_router,
 prefix="/api/v1/legal-chat",
 tags=["legal-chat"]
)

app.include_router(
 mcp_router,
 prefix="/api/v1/mcp",
 tags=["mcp"]
)

app.include_router(
 dictionary_router,
 prefix="/api/v1",
 tags=["dictionary"]
)

app.include_router(
 comprehensive_router,
 prefix="/api/v1/comprehensive",
 tags=["comprehensive-analysis"]
)

@app.get("/")
async def root():
 """Root endpoint."""
 return {
 "message": "LegalLens Document AI Service",
 "version": "1.0.0",
 "status": "running"
 }
from pydantic import BaseModel
class SignInRequest(BaseModel):
 email: str
 password: str
@app.get("/health")
async def health_check():
 """Health check endpoint."""
 return {
 "status": "healthy",
 "service": "legallens-document-ai"
 }
@app.post("/api/signin")
async def sign_in(request: SignInRequest):
 # Simulate checking credentials (you'll implement the actual logic here)
 return {"message": "Signed in successfully"}

if __name__ == "__main__":
 import uvicorn
 uvicorn.run(
 "app.main:app",
 host=settings.API_HOST,
 port=settings.API_PORT,
 reload=settings.DEBUG
 )