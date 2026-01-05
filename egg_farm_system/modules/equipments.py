"""
Equipment Management Module
"""
import logging
from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Equipment, EquipmentStatus

logger = logging.getLogger(__name__)

class EquipmentManager:
    """Manages CRUD operations for Equipment."""

    def __init__(self):
        self.session = DatabaseManager.get_session()

    def create_equipment(self, farm_id, name, description=None, purchase_date=None, purchase_price=None, status=EquipmentStatus.OPERATIONAL):
        """Creates a new piece of equipment."""
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
        """Retrieves all equipment, optionally filtered by farm."""
        try:
            query = self.session.query(Equipment)
            if farm_id:
                query = query.filter(Equipment.farm_id == farm_id)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all equipment: {e}")
            return []

    def get_equipment_by_id(self, equipment_id):
        """Retrieves a single piece of equipment by its ID."""
        try:
            return self.session.query(Equipment).filter(Equipment.id == equipment_id).first()
        except Exception as e:
            logger.error(f"Error getting equipment by ID: {e}")
            return None

    def update_equipment(self, equipment_id, **data):
        """Updates a piece of equipment's details."""
        try:
            equipment = self.get_equipment_by_id(equipment_id)
            if not equipment:
                raise ValueError("Equipment not found.")
            for key, value in data.items():
                setattr(equipment, key, value)
            self.session.commit()
            logger.info(f"Equipment {equipment_id} updated.")
            return equipment
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating equipment: {e}")
            raise

    def delete_equipment(self, equipment_id):
        """Deletes a piece of equipment."""
        try:
            equipment = self.get_equipment_by_id(equipment_id)
            if not equipment:
                raise ValueError("Equipment not found.")
            self.session.delete(equipment)
            self.session.commit()
            logger.info(f"Equipment {equipment_id} deleted.")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting equipment: {e}")
            raise

