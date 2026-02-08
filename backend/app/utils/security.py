"""
Security Utilities for LegalLens
===============================

DEPRECATED: This file is being phased out in favor of app.utils.credentials.
Use app.utils.credentials.get_credentials() instead of these functions.
"""

import base64
import json
import os
from typing import Dict, Any, Optional

def decode_base64_to_json(base64_string: str) -> Dict[Any, Any]:
 """
 DEPRECATED: Use app.utils.credentials instead.
 
 Decode a base64 string back to JSON.
 
 Args:
 base64_string: Base64 encoded string
 
 Returns:
 Decoded JSON as dictionary
 """
 try:
 # Decode from base64
 decoded_bytes = base64.b64decode(base64_string.encode('utf-8'))
 json_content = decoded_bytes.decode('utf-8')
 
 # Parse JSON
 return json.loads(json_content)
 
 except Exception as e:
 raise Exception(f"Error decoding base64 to JSON: {str(e)}")

def get_service_account_credentials() -> Optional[Dict[Any, Any]]:
 """
 DEPRECATED: Use app.utils.credentials.get_service_account_info() instead.
 
 Get service account credentials from environment variables.
 Now only supports base64 encoded credentials.
 
 Returns:
 Service account credentials as dictionary or None
 """
 try:
 # Only use base64 environment variable (file path support removed)
 base64_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_B64')
 if base64_key:
 return decode_base64_to_json(base64_key)
 
 return None
 
 except Exception as e:
 raise Exception(f"Error getting service account credentials: {str(e)}")

def is_running_in_docker() -> bool:
 """
 Check if the application is running inside a Docker container.
 
 Returns:
 True if running in Docker, False otherwise
 """
 return os.path.exists('/.dockerenv') or os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_B64') is not None