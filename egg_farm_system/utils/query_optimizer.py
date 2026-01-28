"""
Query optimization utilities to prevent N+1 queries and improve database performance
"""
from egg_farm_system.utils.i18n import tr

from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy import func
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, List, Dict

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utility class for optimized database queries"""
    
    @staticmethod
    def get_farms_optimized(session):
        """Get all farms with related sheds eagerly loaded"""
        from egg_farm_system.database.models import Farm
        try:
            return session.query(Farm).options(
                selectinload(Farm.sheds)
            ).all()
        except Exception as e:
            logger.error(f"Error fetching farms: {e}")
            return []
    
    @staticmethod
    def get_sheds_by_farm_optimized(session, farm_id):
        """Get sheds for a farm with related flocks and egg productions"""
        from egg_farm_system.database.models import Shed
        try:
            return session.query(Shed).filter(Shed.farm_id == farm_id).options(
                selectinload(Shed.flocks),
                selectinload(Shed.egg_productions)
            ).all()
        except Exception as e:
            logger.error(f"Error fetching sheds: {e}")
            return []
    
    @staticmethod
    def get_flocks_with_mortalities_optimized(session, shed_id):
        """Get flocks with mortalities eagerly loaded"""
        from egg_farm_system.database.models import Flock
        try:
            return session.query(Flock).filter(Flock.shed_id == shed_id).options(
                selectinload(Flock.mortalities)
            ).all()
        except Exception as e:
            logger.error(f"Error fetching flocks: {e}")
            return []
    
    @staticmethod
    def get_parties_with_ledgers_optimized(session, limit=None):
        """Get parties with ledger entries eagerly loaded"""
        from egg_farm_system.database.models import Party
        try:
            query = session.query(Party).options(
                selectinload(Party.ledger_entries)
            ).order_by(Party.name)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching parties: {e}")
            return []
    
    @staticmethod
    def get_sales_with_parties_optimized(session, start_date=None, end_date=None, limit=None):
        """Get sales with party data eagerly loaded"""
        from egg_farm_system.database.models import Sale
        try:
            query = session.query(Sale)
            if start_date:
                query = query.filter(Sale.date >= start_date)
            if end_date:
                query = query.filter(Sale.date <= end_date)
            
            query = query.options(
                selectinload(Sale.party)
            ).order_by(Sale.date.desc())
            
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching sales: {e}")
            return []
    
    @staticmethod
    def get_purchases_optimized(session, start_date=None, end_date=None):
        """Get purchases with party and material data eagerly loaded"""
        from egg_farm_system.database.models import Purchase
        try:
            query = session.query(Purchase)
            if start_date:
                query = query.filter(Purchase.date >= start_date)
            if end_date:
                query = query.filter(Purchase.date <= end_date)
            
            query = query.options(
                selectinload(Purchase.party),
                selectinload(Purchase.material) if 'material' in Purchase.__dict__ else None
            ).order_by(Purchase.date.desc())
            
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching purchases: {e}")
            return []
    
    @staticmethod
    def get_expenses_optimized(session, farm_id=None, start_date=None, end_date=None):
        """Get expenses with party data eagerly loaded"""
        from egg_farm_system.database.models import Expense
        try:
            query = session.query(Expense)
            if farm_id:
                query = query.filter(Expense.farm_id == farm_id)
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)
            
            query = query.options(
                selectinload(Expense.party)
            ).order_by(Expense.date.desc())
            
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching expenses: {e}")
            return []


class CachedQueryResult:
    """Cache query results with TTL (Time To Live)"""
    
    def __init__(self, ttl_seconds=300):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time to live for cached results in seconds (default 5 minutes)
        """
        self.cache: Dict[str, tuple] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return "|".join(key_parts)
    
    def _is_expired(self, timestamp) -> bool:
        """Check if cached result has expired"""
        return datetime.utcnow() - timestamp > self.ttl
    
    def get(self, key: str):
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        self.cache[key] = (value, datetime.utcnow())
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]


# Global cache instance for frequently accessed data
query_cache = CachedQueryResult(ttl_seconds=300)


def cached_query(cache_key_prefix: str = "", ttl_seconds: int = 300):
    """
    Decorator to cache query results
    
    Args:
        cache_key_prefix: Prefix for cache key generation
        ttl_seconds: Time to live in seconds
    
    Example:
        @cached_query(cache_key_prefix="farms")
        def get_farms(session):
            return session.query(Farm).all()
    """
    def decorator(func):
        cache = CachedQueryResult(ttl_seconds=ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{cache_key_prefix}:{cache._get_cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cached result: {cache_key}")
            
            return result
        
        # Attach cache invalidation method
        wrapper.invalidate_cache = lambda pattern="": cache.invalidate_pattern(pattern or cache_key_prefix)
        
        return wrapper
    
    return decorator


class BulkQueryHelper:
    """Helper for batch operations to improve performance"""
    
    @staticmethod
    def bulk_insert(session, objects: List[Any], batch_size: int = 100):
        """Insert objects in batches"""
        try:
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                session.add_all(batch)
                session.commit()
            logger.info(f"Bulk insert completed: {len(objects)} objects")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    @staticmethod
    def bulk_update(session, objects: List[Any], batch_size: int = 100):
        """Update objects in batches"""
        try:
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                for obj in batch:
                    session.merge(obj)
                session.commit()
            logger.info(f"Bulk update completed: {len(objects)} objects")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk update failed: {e}")
            raise
    
    @staticmethod
    def bulk_delete(session, model, ids: List[int], batch_size: int = 100):
        """Delete objects by ID in batches"""
        try:
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                session.query(model).filter(model.id.in_(batch_ids)).delete()
                session.commit()
            logger.info(f"Bulk delete completed: {len(ids)} objects")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk delete failed: {e}")
            raise


class AggregationHelper:
    """Helper for database aggregation queries"""
    
    @staticmethod
    def get_daily_production_aggregate(session, farm_id, start_date, end_date):
        """Get aggregated daily production data"""
        from egg_farm_system.database.models import EggProduction, Shed
        try:
            results = session.query(
                EggProduction.date,
                func.sum(EggProduction.small_count).label('total_small'),
                func.sum(EggProduction.medium_count).label('total_medium'),
                func.sum(EggProduction.large_count).label('total_large'),
                func.sum(EggProduction.broken_count).label('total_broken')
            ).join(Shed).filter(
                Shed.farm_id == farm_id,
                EggProduction.date >= start_date,
                EggProduction.date <= end_date
            ).group_by(EggProduction.date).all()
            
            return results
        except Exception as e:
            logger.error(f"Error aggregating production: {e}")
            return []
    
    @staticmethod
    def get_sales_summary(session, start_date, end_date):
        """Get sales summary with aggregations"""
        from egg_farm_system.database.models import Sale
        try:
            result = session.query(
                func.count(Sale.id).label('total_sales'),
                func.sum(Sale.quantity).label('total_eggs'),
                func.sum(Sale.total_afg).label('total_afg'),
                func.sum(Sale.total_usd).label('total_usd'),
                func.avg(Sale.rate_afg).label('avg_rate_afg')
            ).filter(
                Sale.date >= start_date,
                Sale.date <= end_date
            ).first()
            
            return result
        except Exception as e:
            logger.error(f"Error getting sales summary: {e}")
            return None
