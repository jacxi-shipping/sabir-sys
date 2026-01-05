"""
Flock management module
"""
from datetime import datetime
from egg_farm_system.database.models import Flock, Mortality
from egg_farm_system.database.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class FlockManager:
    """Manage flock operations"""
    
    def create_flock(self, shed_id, name, start_date, initial_count):
        """Create a new flock"""
        with DatabaseManager.get_session() as session:
            try:
                flock = Flock(
                    shed_id=shed_id,
                    name=name,
                    start_date=start_date,
                    initial_count=initial_count
                )
                session.add(flock)
                # session.commit() is handled by the context manager
                logger.info(f"Flock created: {name} in shed {shed_id}")
                return flock
            except Exception as e:
                # session.rollback() is handled by the context manager
                logger.error(f"Error creating flock: {e}")
                raise
    
    def get_flocks_by_shed(self, shed_id):
        """Get all flocks for a shed"""
        with DatabaseManager.get_session() as session:
            try:
                return session.query(Flock).filter(Flock.shed_id == shed_id).all()
            except Exception as e:
                logger.error(f"Error getting flocks: {e}")
                return []
    
    def get_flock_by_id(self, flock_id):
        """Get flock by ID"""
        with DatabaseManager.get_session() as session:
            try:
                return session.query(Flock).filter(Flock.id == flock_id).first()
            except Exception as e:
                logger.error(f"Error getting flock: {e}")
                return None
    
    def add_mortality(self, flock_id, date, count, notes=None):
        """Record mortality for a flock"""
        with DatabaseManager.get_session() as session:
            try:
                mortality = Mortality(
                    flock_id=flock_id,
                    date=date,
                    count=count,
                    notes=notes
                )
                session.add(mortality)
                # session.commit() is handled by the context manager
                logger.info(f"Mortality recorded: {count} birds in flock {flock_id}")
                return mortality
            except Exception as e:
                # session.rollback() is handled by the context manager
                logger.error(f"Error recording mortality: {e}")
                raise
    
    def get_mortalities(self, flock_id):
        """Get mortality records for a flock"""
        with DatabaseManager.get_session() as session:
            try:
                return session.query(Mortality).filter(Mortality.flock_id == flock_id).all()
            except Exception as e:
                logger.error(f"Error getting mortalities: {e}")
                return []
    
    def get_flock_stats(self, flock_id, as_of_date=None):
        """Get comprehensive flock statistics"""
        with DatabaseManager.get_session() as session:
            try:
                flock = session.query(Flock).filter(Flock.id == flock_id).first()
                if not flock:
                    return None
                
                if as_of_date is None:
                    as_of_date = datetime.utcnow()
                
                live_count = flock.get_live_count(as_of_date)
                age_days = flock.get_age_days(as_of_date)
                mortality_pct = flock.get_mortality_percentage(as_of_date)
                
                return {
                    'flock': flock,
                    'initial_count': flock.initial_count,
                    'live_count': live_count,
                    'dead_count': flock.initial_count - live_count,
                    'age_days': age_days,
                    'age_weeks': age_days / 7,
                    'mortality_percentage': mortality_pct,
                    'mortalities': session.query(Mortality).filter(Mortality.flock_id == flock_id).all()
                }
            except Exception as e:
                logger.error(f"Error getting flock stats: {e}")
                return None
    
    def update_flock(self, flock_id, name=None, start_date=None, initial_count=None):
        """Update flock details"""
        with DatabaseManager.get_session() as session:
            try:
                flock = session.query(Flock).filter(Flock.id == flock_id).first()
                if not flock:
                    raise ValueError(f"Flock {flock_id} not found")
                
                if name:
                    flock.name = name
                if start_date:
                    flock.start_date = start_date
                if initial_count:
                    flock.initial_count = initial_count
                
                # session.commit() is handled by the context manager
                logger.info(f"Flock updated: {flock_id}")
                return flock
            except Exception as e:
                # session.rollback() is handled by the context manager
                logger.error(f"Error updating flock: {e}")
                raise
    
    def delete_flock(self, flock_id):
        """Delete flock and related data"""
        with DatabaseManager.get_session() as session:
            try:
                flock = session.query(Flock).filter(Flock.id == flock_id).first()
                if not flock:
                    raise ValueError(f"Flock {flock_id} not found")
                
                session.delete(flock)
                # session.commit() is handled by the context manager
                logger.info(f"Flock deleted: {flock_id}")
            except Exception as e:
                # session.rollback() is handled by the context manager
                logger.error(f"Error deleting flock: {e}")
                raise
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
