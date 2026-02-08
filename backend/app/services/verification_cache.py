"""
Simple in-memory caching service for verification results.
Reduces repeated Spanner queries and improves performance.
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
 data: Dict[str, Any]
 timestamp: float
 ttl: int # Time to live in seconds

class VerificationCache:
 """Simple in-memory cache for verification results."""
 
 def __init__(self):
 self._cache: Dict[str, CacheEntry] = {}
 self.default_ttl = 3600 # 1 hour
 self._request_timestamps: Dict[str, float] = {} # Track request times
 self.throttle_window = 60 # 60 seconds between requests
 
 def _generate_cache_key(self, document_id: str, content_hash: str = None) -> str:
 """Generate cache key for document verification."""
 if content_hash:
 return f"verify:{document_id}:{content_hash[:16]}"
 return f"verify:{document_id}"
 
 def get(self, document_id: str, content_hash: str = None) -> Optional[Dict[str, Any]]:
 """Get cached verification result."""
 try:
 cache_key = self._generate_cache_key(document_id, content_hash)
 
 if cache_key not in self._cache:
 logger.debug(f"Cache miss for key: {cache_key}")
 return None
 
 entry = self._cache[cache_key]
 current_time = time.time()
 
 # Check if entry has expired
 if current_time - entry.timestamp > entry.ttl:
 logger.debug(f"Cache entry expired for key: {cache_key}")
 del self._cache[cache_key]
 return None
 
 logger.info(f"Cache hit for verification: {document_id}")
 return entry.data
 
 except Exception as e:
 logger.error(f"Error getting from cache: {str(e)}")
 return None
 
 def is_throttled(self, document_id: str) -> bool:
 """Check if request should be throttled."""
 current_time = time.time()
 last_request = self._request_timestamps.get(document_id)
 
 if last_request and (current_time - last_request) < self.throttle_window:
 logger.warning(f"Request throttled for document: {document_id}")
 return True
 
 # Update timestamp
 self._request_timestamps[document_id] = current_time
 return False
 
 def set(self, document_id: str, verification_result: Dict[str, Any], 
 content_hash: str = None, ttl: int = None) -> None:
 """Set verification result in cache."""
 try:
 cache_key = self._generate_cache_key(document_id, content_hash)
 ttl = ttl or self.default_ttl
 
 entry = CacheEntry(
 data=verification_result,
 timestamp=time.time(),
 ttl=ttl
 )
 
 self._cache[cache_key] = entry
 logger.info(f"Cached verification result for: {document_id} (TTL: {ttl}s)")
 
 except Exception as e:
 logger.error(f"Error setting cache: {str(e)}")
 
 def invalidate(self, document_id: str) -> None:
 """Invalidate all cache entries for a document."""
 try:
 keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"verify:{document_id}")]
 
 for key in keys_to_remove:
 del self._cache[key]
 
 if keys_to_remove:
 logger.info(f"Invalidated {len(keys_to_remove)} cache entries for: {document_id}")
 
 except Exception as e:
 logger.error(f"Error invalidating cache: {str(e)}")
 
 def clear_expired(self) -> None:
 """Remove expired entries from cache."""
 try:
 current_time = time.time()
 expired_keys = []
 
 for key, entry in self._cache.items():
 if current_time - entry.timestamp > entry.ttl:
 expired_keys.append(key)
 
 for key in expired_keys:
 del self._cache[key]
 
 if expired_keys:
 logger.info(f"Cleared {len(expired_keys)} expired cache entries")
 
 except Exception as e:
 logger.error(f"Error clearing expired cache entries: {str(e)}")
 
 def get_stats(self) -> Dict[str, Any]:
 """Get cache statistics."""
 current_time = time.time()
 expired_count = 0
 
 for entry in self._cache.values():
 if current_time - entry.timestamp > entry.ttl:
 expired_count += 1
 
 return {
 'total_entries': len(self._cache),
 'expired_entries': expired_count,
 'active_entries': len(self._cache) - expired_count
 }

# Global cache instance
_verification_cache = VerificationCache()

def get_verification_cache() -> VerificationCache:
 """Get the global verification cache instance."""
 return _verification_cache