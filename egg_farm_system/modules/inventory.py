"""
Inventory management module
"""
from egg_farm_system.database.models import RawMaterial, FinishedFeed, EggInventory, EggGrade
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.utils.advanced_caching import dashboard_cache, CacheInvalidationManager
from egg_farm_system.utils.performance_monitoring import measure_time
import logging
import math

logger = logging.getLogger(__name__)

class InventoryManager:
    """Manage inventory operations"""

    @staticmethod
    def _cache_farm_id(farm_id):
        """Map optional farm_id to a stable cache key id."""
        return farm_id if farm_id is not None else 0
    
    def get_raw_materials_inventory(self, farm_id=None):
        """Get all raw materials with inventory (cached for 5 minutes)"""
        with measure_time("get_raw_materials_inventory"):
            # Check cache first
            cache_farm_id = self._cache_farm_id(farm_id)
            cached = dashboard_cache.get_daily_metrics(farm_id=cache_farm_id)
            if cached and 'raw_materials' in cached:
                logger.info("Raw materials inventory cache hit")
                return cached['raw_materials']
            
            session = DatabaseManager.get_session()
            try:
                query = session.query(RawMaterial)
                if farm_id is not None:
                    query = query.filter(RawMaterial.farm_id == farm_id)
                materials = query.all()
                inventory = []
                
                for material in materials:
                    # Get cost safely - handle case where no purchases yet
                    try:
                        cost_afg = material.cost_afg if material.total_quantity_purchased > 0 else 0.0
                        cost_usd = material.cost_usd if material.total_quantity_purchased > 0 else 0.0
                    except Exception as e:
                        logger.warning(f"Error calculating cost for material {material.id}: {e}")
                        cost_afg = 0.0
                        cost_usd = 0.0
                    
                    inventory_value_afg = material.current_stock * cost_afg
                    inventory_value_usd = material.current_stock * cost_usd
                    is_low = material.current_stock <= material.low_stock_alert
                    
                    inventory.append({
                        'id': material.id,
                        'name': material.name,
                        'stock': material.current_stock,
                        'unit': material.unit,
                        'cost_afg': cost_afg,
                        'cost_usd': cost_usd,
                        'inventory_value_afg': inventory_value_afg,
                        'inventory_value_usd': inventory_value_usd,
                        'low_stock_alert': material.low_stock_alert,
                        'is_low': is_low,
                        'supplier_id': material.supplier_id
                    })
                
                # Cache for 5 minutes
                dashboard_cache.set_daily_metrics(farm_id=cache_farm_id, data={'raw_materials': inventory})
                return inventory
            except Exception as e:
                logger.error(f"Error getting raw materials inventory: {e}")
                return []
            finally:
                session.close()
    
    def get_finished_feed_inventory(self, farm_id=None):
        """Get finished feed inventory (cached for 5 minutes)"""
        with measure_time("get_finished_feed_inventory"):
            # Check cache first
            cache_farm_id = self._cache_farm_id(farm_id)
            cached = dashboard_cache.get_daily_metrics(farm_id=cache_farm_id)
            if cached and 'finished_feed' in cached:
                logger.info("Finished feed inventory cache hit")
                return cached['finished_feed']
            
            session = DatabaseManager.get_session()
            try:
                query = session.query(FinishedFeed)
                if farm_id is not None:
                    query = query.filter(FinishedFeed.farm_id == farm_id)
                feeds = query.all()
                inventory = []
                
                for feed in feeds:
                    inventory_value_afg = feed.current_stock * feed.cost_per_kg_afg
                    inventory_value_usd = feed.current_stock * feed.cost_per_kg_usd
                    is_low = feed.current_stock <= feed.low_stock_alert
                    
                    inventory.append({
                        'id': feed.id,
                        'feed_type': feed.feed_type.value,
                        'stock_kg': feed.current_stock,
                        'cost_per_kg_afg': feed.cost_per_kg_afg,
                        'cost_per_kg_usd': feed.cost_per_kg_usd,
                        'inventory_value_afg': inventory_value_afg,
                        'inventory_value_usd': inventory_value_usd,
                        'low_stock_alert': feed.low_stock_alert,
                        'is_low': is_low
                    })
                
                # Cache for 5 minutes
                dashboard_cache.set_daily_metrics(farm_id=cache_farm_id, data={'finished_feed': inventory})
                return inventory
            except Exception as e:
                logger.error(f"Error getting finished feed inventory: {e}")
                return []
            finally:
                session.close()
    
    def get_total_inventory_value(self, farm_id=None):
        """Get total inventory value"""
        session = DatabaseManager.get_session()
        try:
            total_afg = 0
            total_usd = 0
            
            # Raw materials
            materials_query = session.query(RawMaterial)
            if farm_id is not None:
                materials_query = materials_query.filter(RawMaterial.farm_id == farm_id)
            materials = materials_query.all()
            for material in materials:
                total_afg += material.current_stock * material.cost_afg
                total_usd += material.current_stock * material.cost_usd
            
            # Finished feed
            feeds_query = session.query(FinishedFeed)
            if farm_id is not None:
                feeds_query = feeds_query.filter(FinishedFeed.farm_id == farm_id)
            feeds = feeds_query.all()
            for feed in feeds:
                total_afg += feed.current_stock * feed.cost_per_kg_afg
                total_usd += feed.current_stock * feed.cost_per_kg_usd
            
            return {
                'total_afg': total_afg,
                'total_usd': total_usd
            }
        except Exception as e:
            logger.error(f"Error calculating inventory value: {e}")
            return {'total_afg': 0, 'total_usd': 0}
        finally:
            session.close()
    
    def get_low_stock_alerts(self, farm_id=None):
        """Get all low stock alerts"""
        session = DatabaseManager.get_session()
        try:
            alerts = []
            
            # Raw materials
            low_materials_query = session.query(RawMaterial).filter(
                RawMaterial.current_stock <= RawMaterial.low_stock_alert
            )
            if farm_id is not None:
                low_materials_query = low_materials_query.filter(RawMaterial.farm_id == farm_id)
            low_materials = low_materials_query.all()
            
            for material in low_materials:
                alerts.append({
                    'type': 'Raw Material',
                    'name': material.name,
                    'farm_id': material.farm_id,
                    'farm_name': material.farm.name if material.farm else 'Unknown Farm',
                    'stock': material.current_stock,
                    'alert_level': material.low_stock_alert,
                    'unit': material.unit
                })
            
            # Finished feed
            low_feeds_query = session.query(FinishedFeed).filter(
                FinishedFeed.current_stock <= FinishedFeed.low_stock_alert
            )
            if farm_id is not None:
                low_feeds_query = low_feeds_query.filter(FinishedFeed.farm_id == farm_id)
            low_feeds = low_feeds_query.all()
            
            for feed in low_feeds:
                alerts.append({
                    'type': 'Finished Feed',
                    'name': feed.feed_type.value,
                    'farm_id': feed.farm_id,
                    'farm_name': feed.farm.name if feed.farm else 'Unknown Farm',
                    'stock': feed.current_stock,
                    'alert_level': feed.low_stock_alert,
                    'unit': 'kg'
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error getting low stock alerts: {e}")
            return []
        finally:
            session.close()

    # --- Egg inventory and packaging helpers ---
    def ensure_packaging_materials(self, session, farm_id):
        """Ensure RawMaterial entries for Carton and Tray exist."""
        carton = session.query(RawMaterial).filter(
            RawMaterial.farm_id == farm_id,
            RawMaterial.name == 'Carton'
        ).first()
        tray = session.query(RawMaterial).filter(
            RawMaterial.farm_id == farm_id,
            RawMaterial.name == 'Tray'
        ).first()
        created = False
        if not carton:
            carton = RawMaterial(farm_id=farm_id, name='Carton', unit='pcs', current_stock=0)
            session.add(carton)
            created = True
        if not tray:
            tray = RawMaterial(farm_id=farm_id, name='Tray', unit='pcs', current_stock=0)
            session.add(tray)
            created = True
        if created:
            session.flush()
        return carton, tray

    def add_eggs(self, session, farm_id, small=0, medium=0, large=0):
        """Add eggs produced to `egg_inventory` by grade."""
        for grade_name, count in (('SMALL', small), ('MEDIUM', medium), ('LARGE', large)):
            if count <= 0:
                continue
            grade_enum = EggGrade[grade_name]
            inv = session.query(EggInventory).filter(
                EggInventory.farm_id == farm_id,
                EggInventory.grade == grade_enum
            ).first()
            if not inv:
                inv = EggInventory(farm_id=farm_id, grade=grade_enum, current_stock=0)
                session.add(inv)
                session.flush()
            inv.current_stock = (inv.current_stock or 0) + int(count)
            session.add(inv)

    def total_usable_eggs(self, session, farm_id):
        rows = session.query(EggInventory).filter(EggInventory.farm_id == farm_id).all()
        return sum(r.current_stock for r in rows)

    def consume_eggs(self, session, quantity, farm_id, grade=None):
        """Consume eggs from inventory.

        - If `grade` is one of small/medium/large/broken, deduct only that grade.
        - Otherwise (None/mixed), deduct from Large -> Medium -> Small.

        Raises ValueError if insufficient stock.
        Returns breakdown consumed per grade.
        """
        if quantity <= 0:
            return {'small':0,'medium':0,'large':0}

        remaining = int(quantity)
        consumed = {'large':0,'medium':0,'small':0,'broken':0}

        normalized_grade = (grade or '').strip().lower() if isinstance(grade, str) else None
        single_grade_map = {
            'small': EggGrade.SMALL,
            'medium': EggGrade.MEDIUM,
            'large': EggGrade.LARGE,
            'broken': EggGrade.BROKEN,
        }
        if normalized_grade in single_grade_map:
            grade_enum = single_grade_map[normalized_grade]
            inv = session.query(EggInventory).filter(
                EggInventory.farm_id == farm_id,
                EggInventory.grade == grade_enum
            ).first()
            available = int(inv.current_stock or 0) if inv else 0
            if available < remaining:
                raise ValueError(
                    f"Insufficient {normalized_grade} egg stock. Available: {available}, requested: {remaining}"
                )
            inv.current_stock = available - remaining
            session.add(inv)
            consumed[normalized_grade] = remaining
            return consumed

        if normalized_grade not in (None, '', 'mixed'):
            raise ValueError(f"Unsupported egg grade: {grade}")

        order = [('LARGE','large'), ('MEDIUM','medium'), ('SMALL','small')]
        total_usable = 0
        for enum_name, _key in order:
            grade_enum = EggGrade[enum_name]
            inv = session.query(EggInventory).filter(
                EggInventory.farm_id == farm_id,
                EggInventory.grade == grade_enum
            ).first()
            total_usable += int(inv.current_stock or 0) if inv else 0
        if total_usable < remaining:
            raise ValueError(f"Insufficient egg stock. Available: {total_usable}, requested: {remaining}")

        for enum_name, key in order:
            if remaining <= 0:
                break
            grade_enum = EggGrade[enum_name]
            inv = session.query(EggInventory).filter(
                EggInventory.farm_id == farm_id,
                EggInventory.grade == grade_enum
            ).first()
            avail = inv.current_stock if inv else 0
            take = min(avail, remaining)
            if take > 0:
                inv.current_stock = avail - take
                session.add(inv)
                consumed[key] = take
                remaining -= take
        if remaining != 0:
            raise ValueError("Failed to consume required eggs; inventory mismatch")
        return consumed

    def consume_packaging(self, session, cartons_needed, trays_needed, farm_id):
        """Consume integer cartons and trays from RawMaterial entries.
        Raises ValueError if insufficient packaging stock.
        """
        cartons_needed = int(math.ceil(cartons_needed)) if cartons_needed else 0
        trays_needed = int(math.ceil(trays_needed)) if trays_needed else 0
        carton, tray = self.ensure_packaging_materials(session, farm_id)

        if carton.current_stock < cartons_needed:
            raise ValueError(f"Insufficient Carton stock. Available: {carton.current_stock}, required: {cartons_needed}")
        if tray.current_stock < trays_needed:
            raise ValueError(f"Insufficient Tray stock. Available: {tray.current_stock}, required: {trays_needed}")

        carton.current_stock -= cartons_needed
        tray.current_stock -= trays_needed
        session.add(carton)
        session.add(tray)
        return {'cartons_consumed':cartons_needed, 'trays_consumed':trays_needed}
    

