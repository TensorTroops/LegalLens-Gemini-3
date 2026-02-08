"""
Centralized Credentials Management for LegalLens
===============================================

Provides a single source of truth for Google Cloud service account credentials.
Prioritizes base64 encoded credentials over file paths for better security and deployment flexibility.
"""

import base64
import json
import os
import logging
from typing import Optional, Dict, Any
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class CredentialsManager:
 """Manages Google Cloud service account credentials with base64 priority."""
 
 _instance = None
 _credentials = None
 _service_account_info = None
 
 def __new__(cls):
 if cls._instance is None:
 cls._instance = super().__new__(cls)
 return cls._instance
 
 def __init__(self):
 if self._credentials is None:
 self._load_credentials()
 
 def _create_working_credentials(self, service_account_info: dict):
 """Create working service account credentials using single scope approach."""
 try:
 logger.info(" Creating credentials using single cloud-platform scope")
 
 # Use cloud-platform scope which covers all Google Cloud services
 # Multiple specific scopes cause id_token vs access_token issues
 scopes = ['https://www.googleapis.com/auth/cloud-platform']
 
 credentials = service_account.Credentials.from_service_account_info(
 service_account_info,
 scopes=scopes
 )
 
 # Force token refresh to ensure we have an access token
 import google.auth.transport.requests
 request = google.auth.transport.requests.Request()
 credentials.refresh(request)
 
 # Verify we got an access token (not id_token)
 if hasattr(credentials, 'token') and credentials.token and credentials.token.startswith('ya29.'):
 logger.info(f" Working access token generated: {credentials.token[:25]}...")
 return credentials
 else:
 logger.error(f" Invalid token type or missing token: {getattr(credentials, 'token', 'None')}")
 return None
 
 except Exception as e:
 logger.error(f" Failed to create working credentials: {e}")
 return None
 
 def _load_credentials(self):
 """Load service account credentials with base64 priority."""
 try:
 # Priority 1: Base64 encoded service account (RECOMMENDED)
 base64_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_B64')
 if base64_key:
 logger.info(" Loading credentials from base64 environment variable")
 decoded_json = base64.b64decode(base64_key).decode('utf-8')
 self._service_account_info = json.loads(decoded_json)
 
 logger.info(f" Service account info loaded: {self._service_account_info.get('client_email')}")
 logger.info(f" Project ID: {self._service_account_info.get('project_id')}")
 
 # Create credentials using the working method
 self._credentials = self._create_working_credentials(self._service_account_info)
 
 if self._credentials:
 logger.info(" Service account credentials created successfully")
 else:
 logger.error(" Failed to create service account credentials")
 
 return
 
 # Priority 2: File path (DEPRECATED - for backward compatibility only)
 file_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
 if file_path and os.path.exists(file_path):
 logger.warning(" Loading credentials from file path (deprecated). Consider using base64 encoding.")
 with open(file_path, 'r', encoding='utf-8') as file:
 self._service_account_info = json.load(file)
 
 # Use the same working method for file-based credentials
 self._credentials = self._create_working_credentials(self._service_account_info)
 
 if self._credentials:
 logger.info(f" Credentials loaded from file for: {self._service_account_info.get('client_email')}")
 else:
 logger.error(" Failed to create credentials from file")
 
 return
 
 # Priority 3: Default credentials (for local development)
 logger.warning(" No explicit service account found. Using default Google Cloud credentials.")
 from google.auth import default
 self._credentials, project = default(scopes=self._get_required_scopes())
 self._service_account_info = {"project_id": project}
 
 except Exception as e:
 logger.error(f" Failed to load credentials: {str(e)}")
 self._credentials = None
 self._service_account_info = None
 
 def _get_required_scopes(self) -> list:
 """Get the required OAuth 2.0 scopes for all Google Cloud services."""
 return [
 'https://www.googleapis.com/auth/cloud-platform',
 'https://www.googleapis.com/auth/cloudkms',
 'https://www.googleapis.com/auth/spanner.data',
 'https://www.googleapis.com/auth/datastore',
 'https://www.googleapis.com/auth/devstorage.full_control',
 'https://www.googleapis.com/auth/firebase.database',
 'https://www.googleapis.com/auth/firebase',
 'https://www.googleapis.com/auth/cloud-documents'
 ]
 
 def get_fresh_credentials(self) -> Optional[service_account.Credentials]:
 """Get fresh credentials with proper token generation."""
 if not self._service_account_info:
 logger.warning(" No service account info available for fresh credentials")
 return self._credentials
 
 logger.info(" Creating fresh credentials...")
 return self._create_working_credentials(self._service_account_info)
 
 @property
 def credentials(self) -> Optional[service_account.Credentials]:
 """Get the loaded service account credentials."""
 return self._credentials
 
 @property
 def service_account_info(self) -> Optional[Dict[str, Any]]:
 """Get the service account information dictionary."""
 return self._service_account_info
 
 @property
 def project_id(self) -> Optional[str]:
 """Get the project ID from credentials or environment."""
 if self._service_account_info:
 return self._service_account_info.get('project_id')
 return os.getenv('GCP_PROJECT_ID')
 
 @property
 def service_account_email(self) -> Optional[str]:
 """Get the service account email."""
 if self._service_account_info:
 return self._service_account_info.get('client_email')
 return None
 
 def is_available(self) -> bool:
 """Check if credentials are available."""
 return self._credentials is not None
 
 def refresh_credentials(self):
 """Force refresh of credentials (useful for testing)."""
 self._credentials = None
 self._service_account_info = None
 self._load_credentials()

# Singleton instance
_credentials_manager = CredentialsManager()

def get_credentials() -> Optional[service_account.Credentials]:
 """Get Google Cloud service account credentials."""
 return _credentials_manager.credentials

def get_fresh_credentials() -> Optional[service_account.Credentials]:
 """Get fresh Google Cloud service account credentials with token generation."""
 return _credentials_manager.get_fresh_credentials()

def get_service_account_info() -> Optional[Dict[str, Any]]:
 """Get service account information dictionary."""
 return _credentials_manager.service_account_info

def get_project_id() -> Optional[str]:
 """Get the project ID."""
 return _credentials_manager.project_id

def get_service_account_email() -> Optional[str]:
 """Get the service account email."""
 return _credentials_manager.service_account_email

def is_credentials_available() -> bool:
 """Check if credentials are available."""
 return _credentials_manager.is_available()

def refresh_credentials():
 """Force refresh of credentials."""
 _credentials_manager.refresh_credentials()