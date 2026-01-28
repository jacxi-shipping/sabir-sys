"""
Egg production tracking module
"""
from datetime import datetime
from egg_farm_system.database.models import EggProduction
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Shed
import logging

logger = logging.getLogger(__name__)

class EggProductionManager:
    """Manage egg production records"""
    
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
    
    def record_production(self, shed_id, date, small=0, medium=0, large=0, broken=0, cartons_used=0, trays_used=0, notes=None):
        """Record daily egg production"""
        try:
            production = EggProduction(
                shed_id=shed_id,
                date=date,
                small_count=small,
                medium_count=medium,
                large_count=large,
                broken_count=broken,
                cartons_used=cartons_used,
                trays_used=trays_used,
                notes=notes
            )
            # Add production record and update inventory/packaging atomically
            from egg_farm_system.modules.inventory import InventoryManager

            self.session.add(production)
            self.session.flush()

            inv_mgr = InventoryManager()
            # Add eggs to inventory (only usable eggs)
            inv_mgr.add_eggs(self.session, small=small, medium=medium, large=large)

            # Consume packaging if provided
            if cartons_used or trays_used:
                inv_mgr.consume_packaging(self.session, cartons_used, trays_used)

            self.session.commit()
            logger.info(f"Egg production recorded for shed {shed_id} on {date}")
            return production
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording egg production: {e}")
            raise
    
    def get_production_by_date(self, shed_id, date):
        """Get production record for a specific date"""
        try:
            return self.session.query(EggProduction).filter(
                EggProduction.shed_id == shed_id,
                EggProduction.date == date
            ).first()
        except Exception as e:
            logger.error(f"Error getting production: {e}")
            return None
    
    def get_daily_production(self, shed_id, start_date, end_date):
        """Get production records for a date range"""
        try:
            return self.session.query(EggProduction).filter(
                EggProduction.shed_id == shed_id,
                EggProduction.date >= start_date,
                EggProduction.date <= end_date
            ).all()
        except Exception as e:
            logger.error(f"Error getting production records: {e}")
            return []
    
    def get_farm_production(self, farm_id, start_date, end_date):
        """Get production for entire farm"""
        try:
            from egg_farm_system.database.models import Shed
            
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            productions = []
            
            for shed in sheds:
                prods = self.session.query(EggProduction).filter(
                    EggProduction.shed_id == shed.id,
                    EggProduction.date >= start_date,
                    EggProduction.date <= end_date
                ).all()
                productions.extend(prods)
            
            return productions
        except Exception as e:
            logger.error(f"Error getting farm production: {e}")
            return []
    
    def get_production_summary(self, shed_id, start_date, end_date):
        """Get production summary for date range"""
        try:
            productions = self.get_daily_production(shed_id, start_date, end_date)
            
            total_small = sum(p.small_count for p in productions)
            total_medium = sum(p.medium_count for p in productions)
            total_large = sum(p.large_count for p in productions)
            total_broken = sum(p.broken_count for p in productions)
            total_eggs = sum(p.total_eggs for p in productions)
            usable_eggs = sum(p.usable_eggs for p in productions)
            
            return {
                'shed_id': shed_id,
                'start_date': start_date,
                'end_date': end_date,
                'days_count': len(productions),
                'small': total_small,
                'medium': total_medium,
                'large': total_large,
                'broken': total_broken,
                'total_eggs': total_eggs,
                'usable_eggs': usable_eggs,
                'broken_percentage': (total_broken / total_eggs * 100) if total_eggs > 0 else 0,
                'daily_average': total_eggs / len(productions) if productions else 0
            }
        except Exception as e:
            logger.error(f"Error getting production summary: {e}")
            return None
    
    def update_production(self, production_id, small=None, medium=None, large=None, broken=None, cartons_used=None, trays_used=None, notes=None):
        """Update egg production record"""
        try:
            production = self.session.query(EggProduction).filter(EggProduction.id == production_id).first()
            if not production:
                raise ValueError(f"Production record {production_id} not found")
            
            if small is not None:
                production.small_count = small
            if medium is not None:
                production.medium_count = medium
            if large is not None:
                production.large_count = large
            if broken is not None:
                production.broken_count = broken
            if cartons_used is not None and hasattr(production, 'cartons_used'):
                production.cartons_used = int(cartons_used)
            if trays_used is not None and hasattr(production, 'trays_used'):
                production.trays_used = int(trays_used)
            # Notes
            if notes is not None:
                production.notes = notes
            
            self.session.commit()
            logger.info(f"Production record updated: {production_id}")
            return production
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating production: {e}")
            raise
    
    def delete_production(self, production_id):
        """Delete production record"""
        try:
            production = self.session.query(EggProduction).filter(EggProduction.id == production_id).first()
            if not production:
                raise ValueError(f"Production record {production_id} not found")
            
            self.session.delete(production)
            self.session.commit()
            logger.info(f"Production record deleted: {production_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting production: {e}")
            raise
    

    

