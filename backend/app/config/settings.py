"""
Simple Configuration for Document AI
====================================
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
 """Simple settings for Document AI service."""
 
 # Application
 APP_NAME: str = "LegalLens Document AI"
 DEBUG: bool = False
 
 # API Configuration
 API_HOST: str = "0.0.0.0"
 API_PORT: int = 8080
 
 # Google Cloud - Updated to use base64 credentials only
 GCP_PROJECT_ID: str
 
 # Document AI
 DOCUMENT_AI_PROCESSOR_ID: str
 DOCUMENT_AI_LOCATION: str = "us"
 
 # Firebase - Base64 encoded service account (RECOMMENDED)
 FIREBASE_PROJECT_ID: Optional[str] = None
 FIREBASE_SERVICE_ACCOUNT_KEY_B64: Optional[str] = None
 
 # Spanner Configuration
 SPANNER_INSTANCE_ID: str
 SPANNER_DATABASE_ID: str
 
 # Gemini AI Configuration
 GEMINI_API_KEY: Optional[str] = None
 
 # Storage
 GCS_BUCKET_NAME: str
 
 # GCUL Blockchain Security Configuration
 GCP_KMS_PROJECT_ID: Optional[str] = None
 GCP_KMS_LOCATION: str = "global"
 GCP_KMS_KEYRING: str = "legallens-keyring"
 GCP_KMS_ENCRYPTION_KEY: str = "document-encryption-key"
 GCP_KMS_SIGNING_KEY: str = "hash-signing-key"
 GCP_SECURE_BUCKET: str = "legallens-secure-docs"
 
 @property
 def is_production(self) -> bool:
 """Check if running in production (Google Cloud App Engine)."""
 return os.getenv('GAE_ENV', '').startswith('standard')
 
 @property
 def firebase_credentials_available(self) -> bool:
 """Check if Firebase credentials are available via base64."""
 return bool(self.FIREBASE_SERVICE_ACCOUNT_KEY_B64)
 
 @property 
 def google_credentials(self) -> Optional[any]:
 """Get Google Cloud credentials from base64 environment variable."""
 from app.utils.credentials import get_credentials
 return get_credentials()
 
 model_config = SettingsConfigDict(
 env_file=".env",
 env_file_encoding="utf-8",
 extra="allow"
 )

def get_settings() -> Settings:
 """Get settings instance."""
 return Settings()