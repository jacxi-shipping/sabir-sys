"""
Equipment Management Module
"""
from egg_farm_system.utils.i18n import tr

import logging
from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Equipment, EquipmentStatus

logger = logging.getLogger(__name__)

class EquipmentManager:
    """
    Manages CRUD operations for Equipment.
    
    Supports the context manager protocol for safe session handling:
    with EquipmentManager() as em:
        em.create_equipment(...)
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

    def create_equipment(self, farm_id, name, description=None, purchase_date=None, purchase_price=0, status=EquipmentStatus.OPERATIONAL):
        """Create new equipment record"""
        try:
            equipment = Equipment(
                farm_id=farm_id,
                name=name,
                description=description,
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                status=status
            )
            self.session.add(equipment)
            self.session.commit()
            logger.info(f"Equipment created: {name}")
            return equipment
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating equipment: {e}")
            raise

    def get_all_equipment(self, farm_id=None):
        """Get all equipment, optionally filtered by farm"""
        try:
            query = self.session.query(Equipment)
            if farm_id:
                query = query.filter(Equipment.farm_id == farm_id)
            return query.order_by(Equipment.purchase_date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting equipment: {e}")
            return []

    def get_equipment_by_id(self, equipment_id):
        """Get equipment by ID"""
        try:
            return self.session.query(Equipment).filter(Equipment.id == equipment_id).first()
        except Exception as e:
            logger.error(f"Error getting equipment: {e}")
            return None

    def update_equipment(self, equipment_id, name=None, description=None, purchase_date=None, purchase_price=None, status=None):
        """Update equipment details"""
        try:
            equipment = self.get_equipment_by_id(equipment_id)
            if not equipment:
                raise ValueError(f"Equipment {equipment_id} not found")
            
            if name is not None:
                equipment.name = name
            if description is not None:
                equipment.description = description
            if purchase_date is not None:
                equipment.purchase_date = purchase_date
            if purchase_price is not None:
                equipment.purchase_price = purchase_price
            if status is not None:
                equipment.status = status
            
            self.session.commit()
            logger.info(f"Equipment updated: {equipment_id}")
            return equipment
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating equipment: {e}")
            raise

    def delete_equipment(self, equipment_id):
        """Delete equipment record"""
        try:
            equipment = self.get_equipment_by_id(equipment_id)
            if not equipment:
                raise ValueError(f"Equipment {equipment_id} not found")
            
            self.session.delete(equipment)
            self.session.commit()
            logger.info(f"Equipment deleted: {equipment_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting equipment: {e}")
            raise

