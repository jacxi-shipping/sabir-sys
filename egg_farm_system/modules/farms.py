"""
Farm management module
"""
from egg_farm_system.database.models import Farm
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.utils.cache_manager import cached, get_cache_manager
import logging

logger = logging.getLogger(__name__)

class FarmManager:
    """
    Manage farm operations
    
    Supports the context manager protocol for safe session handling:
    with FarmManager() as fm:
        fm.get_all_farms()
    """
    
    def __init__(self, session=None):
        self._owned_session = False
        if session:
            self.session = session
        else:
            self.session = DatabaseManager.get_session()
            self._owned_session = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()

    def close_session(self):
        """Close database session if it was created by this instance."""
        if self._owned_session and self.session:
            self.session.close()
            self.session = None
    
    def create_farm(self, name, location=None):
        """Create a new farm"""
        try:
            farm = Farm(name=name, location=location)
            self.session.add(farm)
            self.session.commit()
            
            # Invalidate cache
            get_cache_manager().delete("farms_all")
            
            logger.info(f"Farm created: {name}")
            return farm
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating farm: {e}")
            raise
    
    def get_all_farms(self):
        """Get all farms (eagerly load related sheds to avoid DetachedInstance errors).

        Note: avoid caching raw ORM instances across sessions; load related
        collections while the session is open and then expunge instances so
        callers can safely access loaded attributes after the manager closes.
        """
        try:
            from sqlalchemy.orm import selectinload

            # Eagerly load sheds to avoid lazy loading after session close
            farms = self.session.query(Farm).options(selectinload(Farm.sheds)).all()

            # Force evaluation of the relationship collections while session is open
            for f in farms:
                _ = f.sheds

            # Detach instances from session so they remain usable after close
            self.session.expunge_all()

            return farms
        except Exception as e:
            logger.error(f"Error getting farms: {e}")
            return []
    
    def get_farm_by_id(self, farm_id):
        """Get farm by ID"""
        try:
            return self.session.query(Farm).filter(Farm.id == farm_id).first()
        except Exception as e:
            logger.error(f"Error getting farm: {e}")
            return None
    
    def get_farm_by_name(self, name):
        """Get farm by name"""
        try:
            return self.session.query(Farm).filter(Farm.name == name).first()
        except Exception as e:
            logger.error(f"Error getting farm: {e}")
            return None
    
    def update_farm(self, farm_id, name=None, location=None):
        """Update farm details"""
        try:
            farm = self.get_farm_by_id(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            if name:
                farm.name = name
            if location:
                farm.location = location
            
            self.session.commit()
            
            # Invalidate cache
            get_cache_manager().delete("farms_all")
            
            logger.info(f"Farm updated: {farm_id}")
            return farm
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating farm: {e}")
            raise
    
    def delete_farm(self, farm_id):
        """Delete farm and related data"""
        try:
            farm = self.get_farm_by_id(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            self.session.delete(farm)
            self.session.commit()
            
            # Invalidate cache
            get_cache_manager().delete("farms_all")
            
            logger.info(f"Farm deleted: {farm_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting farm: {e}")
            raise
    
    def get_farm_summary(self, farm_id):
        """Get farm summary with stats"""
        try:
            farm = self.get_farm_by_id(farm_id)
            if not farm:
                return None
            
            total_sheds = len(farm.sheds)
            total_capacity = sum(shed.capacity for shed in farm.sheds)
            total_expenses = sum(exp.amount_afg for exp in farm.expenses)
            
            return {
                'farm': farm,
                'total_sheds': total_sheds,
                'total_capacity': total_capacity,
                'total_expenses': total_expenses,
                'sheds': farm.sheds,
                'expenses': farm.expenses
            }
        except Exception as e:
            logger.error(f"Error getting farm summary: {e}")
            return None
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
    

