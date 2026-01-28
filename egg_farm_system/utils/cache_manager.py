"""
Cache Manager for Performance Optimization
"""
from egg_farm_system.utils.i18n import tr

import logging
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with expiration"""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self.cache: dict = {}
        self.max_size = 1000  # Maximum number of cache entries
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                return default
            return entry.value
        return default
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache"""
        # Evict expired entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_expired()
        
        # If still full, remove oldest entry
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]
        
        self.cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str):
        """Delete a cache entry"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
    
    def _evict_expired(self):
        """Remove expired entries"""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        self._evict_expired()
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size * 100
        }


# Global cache instance
_cache_manager = CacheManager()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(hash(str(args))))
            if kwargs:
                key_parts.append(str(hash(json.dumps(kwargs, sort_keys=True))))
            
            cache_key = hashlib.md5('_'.join(key_parts).encode()).hexdigest()
            
            # Check cache
            cached_value = _cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache_manager.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    return _cache_manager

