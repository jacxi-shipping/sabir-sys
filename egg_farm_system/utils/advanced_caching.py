"""
Advanced caching system for application performance optimization
Includes request-scoped cache, result cache, and invalidation strategies
"""
from egg_farm_system.utils.i18n import tr

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class MemoryCache:
    """In-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.cache: Dict[str, tuple] = {}
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl)
        self.hits = 0
        self.misses = 0
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            k for k, (_, timestamp) in self.cache.items()
            if now - timestamp > self.default_ttl
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """Remove least recently used item when cache is full"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self._cleanup_expired()
        
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.utcnow() - timestamp <= self.default_ttl:
                self.hits += 1
                return value
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        self._cleanup_expired()
        self._evict_lru()
        
        self.cache[key] = (value, datetime.utcnow())
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }


class DashboardCache:
    """Specialized cache for dashboard data"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = MemoryCache(max_size=500, default_ttl=300)
        return cls._instance
    
    def get_daily_metrics(self, farm_id: int) -> Optional[Dict]:
        """Get cached daily metrics"""
        return self.cache.get(f"daily_metrics:{farm_id}")
    
    def set_daily_metrics(self, farm_id: int, data: Dict):
        """Cache daily metrics"""
        self.cache.set(f"daily_metrics:{farm_id}", data)
    
    def get_production_summary(self, farm_id: int, date_str: str) -> Optional[Dict]:
        """Get cached production summary"""
        return self.cache.get(f"prod_summary:{farm_id}:{date_str}")
    
    def set_production_summary(self, farm_id: int, date_str: str, data: Dict):
        """Cache production summary"""
        self.cache.set(f"prod_summary:{farm_id}:{date_str}", data)
    
    def invalidate_farm(self, farm_id: int):
        """Invalidate all cache for a farm"""
        self.cache.invalidate_pattern(f":{farm_id}:")
    
    def invalidate_all(self):
        """Clear entire cache"""
        self.cache.clear()


class ReportCache:
    """Specialized cache for report generation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = MemoryCache(max_size=200, default_ttl=600)
        return cls._instance
    
    def get_report(self, report_type: str, params: Dict) -> Optional[Any]:
        """Get cached report"""
        cache_key = self._generate_key(report_type, params)
        return self.cache.get(cache_key)
    
    def set_report(self, report_type: str, params: Dict, data: Any):
        """Cache report"""
        cache_key = self._generate_key(report_type, params)
        self.cache.set(cache_key, data)
    
    def _generate_key(self, report_type: str, params: Dict) -> str:
        """Generate deterministic cache key from parameters"""
        param_str = "|".join([f"{k}={v}" for k, v in sorted(params.items())])
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"report:{report_type}:{param_hash}"
    
    def invalidate_report_type(self, report_type: str):
        """Invalidate all reports of a type"""
        self.cache.invalidate_pattern(f"report:{report_type}:")
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()


class QueryCache:
    """Specialized cache for database queries"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = MemoryCache(max_size=300, default_ttl=900)
        return cls._instance
    
    def get_parties_list(self) -> Optional[list]:
        """Get cached parties list"""
        return self.cache.get("parties_list")
    
    def set_parties_list(self, data: list):
        """Cache parties list"""
        self.cache.set("parties_list", data)
    
    def get_farm_summary(self, farm_id: int) -> Optional[Dict]:
        """Get cached farm summary"""
        return self.cache.get(f"farm_summary:{farm_id}")
    
    def set_farm_summary(self, farm_id: int, data: Dict):
        """Cache farm summary"""
        self.cache.set(f"farm_summary:{farm_id}", data)
    
    def invalidate_parties(self):
        """Invalidate parties cache"""
        self.cache.delete("parties_list")
    
    def invalidate_farm(self, farm_id: int):
        """Invalidate farm cache"""
        self.cache.invalidate_pattern(f"farm_summary:{farm_id}")


def cache_result(ttl_seconds: int = 300, cache_type: str = "memory"):
    """
    Decorator to cache function results
    
    Args:
        ttl_seconds: Time to live in seconds
        cache_type: Type of cache (memory, dashboard, report, query)
    """
    def decorator(func: Callable) -> Callable:
        cache = MemoryCache(default_ttl=ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Check cache
            cached_result = cache.get(cache_key_hash)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key_hash, result)
            return result
        
        # Attach cache control methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_invalidate = cache.invalidate_pattern
        
        return wrapper
    
    return decorator


class CacheInvalidationManager:
    """Manager for cache invalidation across the application"""
    
    @staticmethod
    def on_farm_created():
        """Invalidate caches when farm is created"""
        DashboardCache().invalidate_all()
        QueryCache().invalidate_parties()
    
    @staticmethod
    def on_farm_updated(farm_id: int):
        """Invalidate caches when farm is updated"""
        DashboardCache().invalidate_farm(farm_id)
        QueryCache().invalidate_farm(farm_id)
    
    @staticmethod
    def on_sale_created():
        """Invalidate caches when sale is recorded"""
        DashboardCache().invalidate_all()
        ReportCache().invalidate_report_type("sales")
        ReportCache().invalidate_report_type("financial")
    
    @staticmethod
    def on_purchase_created():
        """Invalidate caches when purchase is recorded"""
        ReportCache().invalidate_report_type("purchases")
        ReportCache().invalidate_report_type("inventory")
    
    @staticmethod
    def on_raw_material_sale_created():
        """Invalidate caches when raw material sale is recorded"""
        ReportCache().invalidate_report_type("inventory")
        ReportCache().invalidate_report_type("financial")
    
    @staticmethod
    def on_expense_created():
        """Invalidate caches when expense is recorded"""
        DashboardCache().invalidate_all()
        ReportCache().invalidate_report_type("expenses")
        ReportCache().invalidate_report_type("financial")
    
    @staticmethod
    def on_production_recorded():
        """Invalidate caches when egg production is recorded"""
        DashboardCache().invalidate_all()
        ReportCache().invalidate_report_type("production")


# Global cache instances
dashboard_cache = DashboardCache()
report_cache = ReportCache()
query_cache = QueryCache()
