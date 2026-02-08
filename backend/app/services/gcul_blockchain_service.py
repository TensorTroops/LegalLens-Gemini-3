"""
GCUL Blockchain Security Service
===============================

Implements blockchain-like security using Google Cloud KMS and Cloud Spanner.
Provides document encryption, hash verification, and tamper-proof audit trails.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging
from google.cloud import kms
from google.cloud import storage
from google.cloud import spanner
import base64
import os

from app.services.verification_cache import get_verification_cache
from app.utils.credentials import get_credentials, get_project_id

def _get_working_storage_credentials():
 """Get working credentials for all Google Cloud operations."""
 import base64
 import json
 import os
 from google.oauth2 import service_account
 
 base64_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_B64')
 if not base64_key:
 return None, None
 
 try:
 decoded_json = base64.b64decode(base64_key).decode('utf-8')
 service_account_info = json.loads(decoded_json)
 project_id = service_account_info.get('project_id')
 
 # Use all required scopes for GCUL operations
 scopes = [
 'https://www.googleapis.com/auth/cloud-platform',
 'https://www.googleapis.com/auth/cloudkms',
 'https://www.googleapis.com/auth/spanner.data',
 'https://www.googleapis.com/auth/devstorage.full_control'
 ]
 
 credentials = service_account.Credentials.from_service_account_info(
 service_account_info,
 scopes=scopes
 )
 
 # Generate access token
 import google.auth.transport.requests
 request = google.auth.transport.requests.Request()
 credentials.refresh(request)
 
 if credentials.token:
 return credentials, project_id
 else:
 return None, None
 
 except Exception:
 return None, None

logger = logging.getLogger(__name__)

class GCULBlockchainService:
 """
 Google Cloud Universal Ledger (GCUL) simulation using:
 - Cloud KMS for encryption/signing
 - Cloud Spanner for hash storage
 - Cloud Storage for encrypted documents
 """
 
 def __init__(self):
 # Use working credentials approach for all services
 storage_credentials, storage_project = _get_working_storage_credentials()
 if not storage_credentials:
 raise ValueError(" No working Google Cloud credentials available for GCUL service")
 
 # Use the working credentials for all services
 logger.info(" Using working credentials for all GCUL services")
 self.project_id = storage_project
 self.location = os.getenv('GCP_KMS_LOCATION', 'global')
 self.keyring = os.getenv('GCP_KMS_KEYRING', 'legallens-keyring')
 self.encryption_key = os.getenv('GCP_KMS_ENCRYPTION_KEY', 'document-encryption-key')
 self.signing_key = os.getenv('GCP_KMS_SIGNING_KEY', 'hash-signing-key')
 self.secure_bucket = os.getenv('GCP_SECURE_BUCKET', 'legallens-secure-docs')
 
 # Initialize all clients with working credentials
 self.kms_client = kms.KeyManagementServiceClient(credentials=storage_credentials)
 self.storage_client = storage.Client(project=storage_project, credentials=storage_credentials)
 self.spanner_client = spanner.Client(project=storage_project, credentials=storage_credentials)
 
 self.instance_id = os.getenv('SPANNER_INSTANCE_ID', 'legallens-instance')
 self.database_id = os.getenv('SPANNER_DATABASE_ID', 'legallens-db')
 self.database = self.spanner_client.instance(self.instance_id).database(self.database_id)
 
 logger.info(" GCUL Blockchain Service initialized with working credentials for all services")
 
 def _get_encryption_key_name(self) -> str:
 """Get the full KMS encryption key name."""
 return self.kms_client.crypto_key_path(
 self.project_id, self.location, self.keyring, self.encryption_key
 )
 
 def _get_signing_key_name(self) -> str:
 """Get the full KMS signing key name."""
 return self.kms_client.crypto_key_path(
 self.project_id, self.location, self.keyring, self.signing_key
 )
 
 def _calculate_file_hash(self, content: bytes) -> str:
 """Calculate SHA-256 hash of file content."""
 return hashlib.sha256(content).hexdigest()
 
 def _calculate_content_hash(self, text: str) -> str:
 """Calculate SHA-256 hash of extracted text content."""
 return hashlib.sha256(text.encode('utf-8')).hexdigest()
 
 async def encrypt_document(self, content: bytes, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
 """
 Encrypt document content using envelope encryption with Cloud KMS.
 
 For large files (>64KB), we use envelope encryption:
 1. Generate a random Data Encryption Key (DEK)
 2. Encrypt the file content with the DEK using AES
 3. Encrypt the DEK with Cloud KMS
 4. Store both encrypted content and encrypted DEK
 
 Args:
 content: Raw document bytes
 metadata: Document metadata
 
 Returns:
 Tuple of (encrypted_blob_name, encryption_metadata)
 """
 try:
 logger.info(" GCUL: Starting document encryption")
 logger.info(f" File size: {len(content)} bytes")
 
 # Generate a random 256-bit AES key for data encryption
 from cryptography.fernet import Fernet
 import base64
 
 # Generate random DEK (Data Encryption Key)
 dek = Fernet.generate_key()
 logger.info(" Generated Data Encryption Key (DEK)")
 
 # Encrypt the large file content with the DEK
 fernet = Fernet(dek)
 encrypted_content = fernet.encrypt(content)
 logger.info(f" File encrypted with DEK, size: {len(encrypted_content)} bytes")
 
 # Encrypt the small DEK with Cloud KMS
 encryption_key_name = self._get_encryption_key_name()
 encrypt_response = self.kms_client.encrypt(
 request={
 'name': encryption_key_name,
 'plaintext': dek # Only encrypt the small DEK (32 bytes)
 }
 )
 
 encrypted_dek = encrypt_response.ciphertext
 logger.info(" DEK encrypted with Cloud KMS")
 
 # Generate unique blob name
 blob_name = f"encrypted/{uuid.uuid4()}.enc"
 
 # Create envelope encryption metadata
 envelope_metadata = {
 'encrypted_dek': base64.b64encode(encrypted_dek).decode('utf-8'),
 'kms_key_name': encryption_key_name,
 'encryption_algorithm': 'AES-256 + KMS',
 'envelope_encryption': True
 }
 
 # Upload encrypted content to secure bucket
 bucket = self.storage_client.bucket(self.secure_bucket)
 blob = bucket.blob(blob_name)
 
 # Set metadata for the blob
 blob.metadata = {
 'original_filename': metadata.get('file_name', 'unknown'),
 'file_type': metadata.get('file_type', 'unknown'),
 'user_id': metadata.get('user_id', 'unknown'),
 'encrypted_with': 'GCUL_envelope_encryption',
 'kms_key_name': encryption_key_name,
 'original_size': str(len(content)),
 'encrypted_size': str(len(encrypted_content)),
 'envelope_metadata': base64.b64encode(encrypted_dek).decode('utf-8')
 }
 
 # Upload the encrypted file content with retry logic
 try:
 logger.info(f" Uploading encrypted content to bucket: {self.secure_bucket}")
 blob.upload_from_string(
 encrypted_content,
 content_type='application/octet-stream'
 )
 logger.info(f" Successfully uploaded blob: {blob_name}")
 except Exception as upload_error:
 logger.error(f" Upload failed: {upload_error}")
 # Try to refresh credentials and retry once
 try:
 logger.info(" Refreshing credentials and retrying upload...")
 storage_credentials, storage_project = _get_working_storage_credentials()
 if not storage_credentials:
 raise Exception("Could not get working credentials")
 
 # Recreate storage client with fresh working credentials
 self.storage_client = storage.Client(project=storage_project, credentials=storage_credentials)
 bucket = self.storage_client.bucket(self.secure_bucket)
 blob = bucket.blob(blob_name)
 blob.metadata = {
 'original_filename': metadata.get('file_name', 'unknown'),
 'file_type': metadata.get('file_type', 'unknown'),
 'user_id': metadata.get('user_id', 'unknown'),
 'encrypted_with': 'GCUL_envelope_encryption',
 'kms_key_name': encryption_key_name,
 'original_size': str(len(content)),
 'encrypted_size': str(len(encrypted_content)),
 'envelope_metadata': base64.b64encode(encrypted_dek).decode('utf-8')
 }
 
 blob.upload_from_string(
 encrypted_content,
 content_type='application/octet-stream'
 )
 logger.info(f" Upload successful on retry: {blob_name}")
 except Exception as retry_error:
 logger.error(f" Retry upload failed: {retry_error}")
 raise upload_error # Raise the original error
 
 encryption_metadata = {
 'blob_name': blob_name,
 'bucket': self.secure_bucket,
 'kms_key': encryption_key_name,
 'encrypted_at': datetime.utcnow().isoformat(),
 'file_size': len(content),
 'encryption_algorithm': 'AES-256 + KMS envelope encryption',
 'envelope_metadata': envelope_metadata,
 'original_size': len(content),
 'encrypted_size': len(encrypted_content)
 }
 
 logger.info(f" GCUL: Document encrypted successfully using envelope encryption: {blob_name}")
 logger.info(f" Original: {len(content)} bytes → Encrypted: {len(encrypted_content)} bytes")
 
 return blob_name, encryption_metadata
 
 except Exception as e:
 logger.error(f" GCUL: Encryption failed: {str(e)}")
 raise
 
 async def decrypt_document(self, blob_name: str) -> bytes:
 """
 Decrypt document content using envelope decryption with Cloud KMS.
 
 This method handles both envelope encryption and legacy direct encryption.
 
 Args:
 blob_name: Name of encrypted blob in storage
 
 Returns:
 Decrypted document content
 """
 try:
 logger.info(f" GCUL: Starting document decryption: {blob_name}")
 
 # Download encrypted content and metadata
 bucket = self.storage_client.bucket(self.secure_bucket)
 blob = bucket.blob(blob_name)
 
 if not blob.exists():
 raise Exception(f"Encrypted blob not found: {blob_name}")
 
 # Reload blob to get metadata
 blob.reload()
 encrypted_content = blob.download_as_bytes()
 
 # Check if this is envelope encryption
 if blob.metadata and blob.metadata.get('encrypted_with') == 'GCUL_envelope_encryption':
 logger.info(" Detected envelope encryption")
 
 # Get the encrypted DEK from metadata
 encrypted_dek_b64 = blob.metadata.get('envelope_metadata')
 if not encrypted_dek_b64:
 raise Exception("Envelope metadata not found in blob")
 
 import base64
 from cryptography.fernet import Fernet
 
 # Decode the encrypted DEK
 encrypted_dek = base64.b64decode(encrypted_dek_b64)
 
 # Decrypt the DEK using KMS
 encryption_key_name = self._get_encryption_key_name()
 decrypt_response = self.kms_client.decrypt(
 request={
 'name': encryption_key_name,
 'ciphertext': encrypted_dek
 }
 )
 
 dek = decrypt_response.plaintext
 logger.info(" DEK decrypted with Cloud KMS")
 
 # Decrypt the file content with the DEK
 fernet = Fernet(dek)
 decrypted_content = fernet.decrypt(encrypted_content)
 logger.info(" File content decrypted with DEK")
 
 logger.info(" GCUL: Document decrypted successfully using envelope decryption")
 return decrypted_content
 
 else:
 # Legacy direct KMS decryption (for older files)
 logger.info(" Using legacy direct KMS decryption")
 encryption_key_name = self._get_encryption_key_name()
 decrypt_response = self.kms_client.decrypt(
 request={
 'name': encryption_key_name,
 'ciphertext': encrypted_content
 }
 )
 
 logger.info(" GCUL: Document decrypted successfully using direct KMS")
 return decrypt_response.plaintext
 
 except Exception as e:
 logger.error(f" GCUL: Decryption failed: {str(e)}")
 raise
 
 async def create_document_hash_record(
 self, 
 document_id: str, 
 content: bytes, 
 extracted_text: str,
 user_id: str,
 metadata: Dict[str, Any]
 ) -> str:
 """
 Create a blockchain-like hash record for a document.
 
 Args:
 document_id: Unique document identifier
 content: Raw document content
 extracted_text: Extracted text content
 user_id: User who uploaded the document
 metadata: Additional metadata
 
 Returns:
 Hash record ID
 """
 try:
 logger.info(f" GCUL: Creating hash record for document: {document_id}")
 
 # Calculate hashes
 file_hash = self._calculate_file_hash(content)
 content_hash = self._calculate_content_hash(extracted_text)
 
 # Create hash record
 hash_id = str(uuid.uuid4())
 
 # Get current KMS key version
 key_name = self._get_encryption_key_name()
 
 # Create signature of the hash
 signing_key_name = self._get_signing_key_name()
 hash_to_sign = f"{file_hash}:{content_hash}:{document_id}".encode('utf-8')
 
 sign_response = self.kms_client.asymmetric_sign(
 request={
 'name': f"{signing_key_name}/cryptoKeyVersions/1",
 'digest': {
 'sha256': hashlib.sha256(hash_to_sign).digest()
 }
 }
 )
 
 signature = base64.b64encode(sign_response.signature).decode('utf-8')
 
 # Store in Spanner 
 with self.database.batch() as batch:
 batch.insert(
 table='DocumentHashes',
 columns=[
 'hash_id', 'document_id', 'file_hash', 'content_hash',
 'kms_key_version', 'signature', 'timestamp', 'user_id', 'file_size',
 'mime_type', 'encryption_metadata', 'verification_status'
 ],
 values=[
 (
 hash_id,
 document_id,
 file_hash,
 content_hash,
 f"{key_name}/cryptoKeyVersions/1",
 signature,
 datetime.utcnow(),
 user_id,
 len(content),
 metadata.get('mime_type', 'application/octet-stream'),
 json.dumps(metadata),
 'VERIFIED'
 )
 ]
 )
 
 # Add to hash chain
 await self._add_to_hash_chain([hash_id])
 
 logger.info(f" GCUL: Hash record created successfully: {hash_id}")
 return hash_id
 
 except Exception as e:
 logger.error(f" GCUL: Hash record creation failed: {str(e)}")
 raise
 
 async def verify_document_integrity(self, document_id: str, current_content: bytes) -> Dict[str, Any]:
 """
 Verify document integrity against blockchain record with caching and throttling.
 
 Args:
 document_id: Document to verify
 current_content: Current content to check against
 
 Returns:
 Verification result with status and details
 """
 try:
 logger.info(f" GCUL: Verifying document integrity: {document_id}")
 
 # Check if request is throttled
 cache = get_verification_cache()
 if cache.is_throttled(document_id):
 # Return cached result or basic response if throttled
 cached_result = cache.get(document_id)
 if cached_result:
 logger.info(f" GCUL: Using cached result due to throttling: {document_id}")
 return cached_result
 else:
 return {
 'verified': False,
 'is_valid': False,
 'status': 'THROTTLED',
 'message': 'Request throttled - please wait before retrying',
 'throttled': True
 }
 
 # Calculate current hash for cache key
 current_hash = self._calculate_file_hash(current_content)
 
 # Check cache first
 cache = get_verification_cache()
 cached_result = cache.get(document_id, current_hash)
 
 if cached_result:
 logger.info(f" GCUL: Using cached verification result for: {document_id}")
 return cached_result
 
 # Get stored hash record from Spanner
 with self.database.snapshot() as snapshot:
 results = snapshot.execute_sql(
 "SELECT hash_id, file_hash, content_hash, signature, verification_status "
 "FROM DocumentHashes WHERE document_id = @document_id "
 "ORDER BY timestamp DESC LIMIT 1",
 params={'document_id': document_id},
 param_types={'document_id': spanner.param_types.STRING}
 )
 
 rows = list(results)
 if not rows:
 verification_result = {
 'verified': False,
 'is_valid': False,
 'status': 'NOT_FOUND',
 'expected_hash': 'N/A',
 'actual_hash': current_hash,
 'algorithm': 'SHA-256',
 'blockchain_record': 'Not Found',
 'message': 'No hash record found for document'
 }
 # Cache the result even if not found (shorter TTL)
 cache.set(document_id, verification_result, current_hash, ttl=300) # 5 minutes
 return verification_result
 
 stored_record = rows[0]
 
 # Compare hashes
 integrity_verified = (current_hash == stored_record[1]) # file_hash
 
 verification_result = {
 'verified': integrity_verified,
 'is_valid': integrity_verified, # Frontend compatibility
 'status': 'VERIFIED' if integrity_verified else 'TAMPERED',
 'hash_id': stored_record[0],
 'stored_hash': stored_record[1],
 'expected_hash': stored_record[1], # Frontend compatibility
 'current_hash': current_hash,
 'actual_hash': current_hash, # Frontend compatibility
 'signature_valid': stored_record[3] is not None, # Basic signature check
 'verification_status': stored_record[4],
 'algorithm': 'SHA-256', # Frontend expects this
 'blockchain_record': 'Found' if stored_record else 'Not Found' # Frontend expects this
 }
 
 # Cache the verification result
 cache_ttl = 3600 if integrity_verified else 1800 # 1 hour if valid, 30 min if tampered
 cache.set(document_id, verification_result, current_hash, ttl=cache_ttl)
 
 if integrity_verified:
 logger.info(f" GCUL: Document integrity verified: {document_id}")
 else:
 logger.warning(f" GCUL: Document integrity FAILED: {document_id}")
 
 return verification_result
 
 except Exception as e:
 logger.error(f" GCUL: Integrity verification failed: {str(e)}")
 error_result = {
 'verified': False,
 'is_valid': False,
 'status': 'ERROR',
 'expected_hash': 'N/A',
 'actual_hash': 'N/A',
 'algorithm': 'SHA-256',
 'blockchain_record': 'Error',
 'message': f'Verification failed: {str(e)}'
 }
 return error_result
 
 async def _add_to_hash_chain(self, document_hashes: List[str]) -> str:
 """
 Add document hashes to the blockchain-like hash chain.
 
 Args:
 document_hashes: List of document hash IDs to add to chain
 
 Returns:
 Chain block ID
 """
 try:
 # Get latest block
 with self.database.snapshot() as snapshot:
 results = snapshot.execute_sql(
 "SELECT chain_id, block_number, current_hash "
 "FROM HashChain ORDER BY block_number DESC LIMIT 1"
 )
 
 rows = list(results)
 if rows:
 last_block = rows[0]
 previous_hash = last_block[2]
 block_number = last_block[1] + 1
 else:
 # Genesis block
 previous_hash = None
 block_number = 0
 
 # Create new block
 chain_id = str(uuid.uuid4())
 
 # Calculate Merkle root (simplified)
 merkle_root = hashlib.sha256(
 ''.join(document_hashes).encode('utf-8')
 ).hexdigest()
 
 # Calculate current block hash
 block_data = f"{block_number}:{previous_hash}:{merkle_root}"
 current_hash = hashlib.sha256(block_data.encode('utf-8')).hexdigest()
 
 # Sign the block
 signing_key_name = self._get_signing_key_name()
 sign_response = self.kms_client.asymmetric_sign(
 request={
 'name': f"{signing_key_name}/cryptoKeyVersions/1",
 'digest': {
 'sha256': hashlib.sha256(current_hash.encode('utf-8')).digest()
 }
 }
 )
 
 signature = base64.b64encode(sign_response.signature).decode('utf-8')
 
 # Store in Spanner 
 with self.database.batch() as batch:
 batch.insert(
 table='HashChain',
 columns=[
 'chain_id', 'block_number', 'previous_hash', 'current_hash',
 'document_hashes', 'merkle_root', 'signature', 'timestamp'
 ],
 values=[
 (
 chain_id,
 block_number,
 previous_hash,
 current_hash,
 document_hashes,
 merkle_root,
 signature,
 datetime.utcnow()
 )
 ]
 )
 
 logger.info(f" GCUL: Block added to hash chain: {chain_id}")
 return chain_id
 
 except Exception as e:
 logger.error(f" GCUL: Hash chain addition failed: {str(e)}")
 raise
 
 async def get_document_audit_trail(self, document_id: str) -> List[Dict[str, Any]]:
 """
 Get complete audit trail for a document with optimized single-snapshot queries.
 
 Args:
 document_id: Document to get audit trail for
 
 Returns:
 List of audit trail entries
 """
 try:
 # Use single snapshot for both queries to reduce costs
 with self.database.snapshot() as snapshot:
 # Get document hash records
 hash_results = snapshot.execute_sql(
 "SELECT hash_id, file_hash, content_hash, timestamp, "
 "verification_status, signature FROM DocumentHashes "
 "WHERE document_id = @document_id ORDER BY timestamp",
 params={'document_id': document_id},
 param_types={'document_id': spanner.param_types.STRING}
 )
 
 hash_records = []
 for row in hash_results:
 hash_records.append({
 'hash_id': row[0],
 'file_hash': row[1],
 'content_hash': row[2],
 'timestamp': row[3].isoformat(),
 'verification_status': row[4],
 'has_signature': row[5] is not None
 })
 
 # Get latest hash chain entries in same snapshot (limit to reduce costs)
 chain_results = snapshot.execute_sql(
 "SELECT chain_id, block_number, current_hash, timestamp "
 "FROM HashChain ORDER BY block_number DESC LIMIT 5", # Reduced from 10 to 5
 params={},
 param_types={}
 )
 
 chain_blocks = []
 for row in chain_results:
 chain_blocks.append({
 'chain_id': row[0],
 'block_number': row[1],
 'block_hash': row[2],
 'timestamp': row[3].isoformat()
 })
 
 return {
 'document_id': document_id,
 'hash_records': hash_records,
 'chain_blocks': chain_blocks,
 'total_records': len(hash_records)
 }
 
 except Exception as e:
 logger.error(f" GCUL: Audit trail retrieval failed: {str(e)}")
 return {
 'document_id': document_id,
 'hash_records': [],
 'chain_blocks': [],
 'error': str(e)
 }

# Initialize global GCUL service
gcul_service = None

def get_gcul_service() -> GCULBlockchainService:
 """Get the global GCUL blockchain service instance."""
 global gcul_service
 if gcul_service is None:
 gcul_service = GCULBlockchainService()
 return gcul_service