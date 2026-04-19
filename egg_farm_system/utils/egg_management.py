"""
Advanced Egg Management System
Handles tray/carton conversion, expenses, and cost calculations
"""
from egg_farm_system.utils.i18n import tr

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy import func

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import EggProduction, Sale, Shed
from egg_farm_system.modules.settings import SettingsManager

logger = logging.getLogger(__name__)


class EggManagementSystem:
    """Advanced egg management with tray/carton system"""
    
    # Constants
    EGGS_PER_TRAY = 30
    EGGS_PER_CARTON = 180
    TRAYS_PER_CARTON = 6  # 180 / 30
    TRAYS_EXPENSE_PER_CARTON = 7  # Packaging trays used per carton
    
    def __init__(self):
        self.session = None
    
    @staticmethod
    def eggs_to_trays(eggs: int) -> float:
        """Convert eggs to trays"""
        return eggs / EggManagementSystem.EGGS_PER_TRAY
    
    @staticmethod
    def eggs_to_cartons(eggs: int) -> float:
        """Convert eggs to cartons"""
        return eggs / EggManagementSystem.EGGS_PER_CARTON
    
    @staticmethod
    def trays_to_eggs(trays: float) -> int:
        """Convert trays to eggs"""
        return int(trays * EggManagementSystem.EGGS_PER_TRAY)
    
    @staticmethod
    def cartons_to_eggs(cartons: float) -> int:
        """Convert cartons to eggs"""
        return int(cartons * EggManagementSystem.EGGS_PER_CARTON)
    
    @staticmethod
    def get_tray_expense() -> float:
        """Get tray expense per tray"""
        return float(SettingsManager.get_setting('tray_expense_afg', '0') or 0)
    
    @staticmethod
    def get_carton_expense() -> float:
        """Get carton expense per carton"""
        return float(SettingsManager.get_setting('carton_expense_afg', '0') or 0)
    
    @staticmethod
    def set_tray_expense(expense_afg: float):
        """Set tray expense"""
        SettingsManager.set_setting('tray_expense_afg', str(expense_afg))
    
    @staticmethod
    def set_carton_expense(expense_afg: float):
        """Set carton expense"""
        SettingsManager.set_setting('carton_expense_afg', str(expense_afg))
    
    def calculate_carton_cost(self, cartons: float, egg_price_per_egg: float, 
                            grade: str = "mixed") -> Dict[str, float]:
        """
        Calculate total cost for cartons including eggs and expenses
        
        Args:
            cartons: Number of cartons
            egg_price_per_egg: Price per egg in AFG
            grade: Egg grade (small, medium, large, broken, mixed)
            
        Returns:
            Dictionary with cost breakdown
        """
        total_eggs = self.cartons_to_eggs(cartons)
        
        # Egg cost
        egg_cost = total_eggs * egg_price_per_egg
        
        # Tray expense (7 trays per carton for packaging)
        trays_needed = cartons * self.TRAYS_EXPENSE_PER_CARTON
        tray_expense = trays_needed * self.get_tray_expense()
        
        # Carton expense
        carton_expense = cartons * self.get_carton_expense()
        
        # Total cost
        total_cost = egg_cost + tray_expense + carton_expense
        
        return {
            'cartons': cartons,
            'eggs': total_eggs,
            'egg_cost': egg_cost,
            'tray_expense': tray_expense,
            'carton_expense': carton_expense,
            'total_cost': total_cost,
            'cost_per_carton': total_cost / cartons if cartons > 0 else 0,
            'cost_per_egg': total_cost / total_eggs if total_eggs > 0 else 0
        }
    
    def get_available_eggs_by_grade(self, farm_id: int, grade: str) -> int:
        """
        Get available eggs by grade (not yet sold)
        
        Args:
            farm_id: Farm ID (Note: EggInventory is currently global, so farm_id is unused but kept for API compatibility)
            grade: Egg grade (small, medium, large, broken)
            
        Returns:
            Available count
        """
        try:
            summary = self.get_egg_stock_summary(farm_id)
            return int(summary.get(grade.lower(), 0))
        except Exception as e:
            logger.error(f"Error getting available eggs: {e}")
            return 0
    
    def get_egg_stock_summary(self, farm_id: int) -> Dict[str, int]:
        """Get egg stock summary by grade"""
        try:
            session = DatabaseManager.get_session()
            try:
                summary = {'small': 0, 'medium': 0, 'large': 0, 'broken': 0}

                if farm_id is None:
                    # Backward compatibility fallback when no farm is selected.
                    from egg_farm_system.database.models import EggInventory, EggGrade
                    inventories = session.query(EggInventory).all()
                    for inv in inventories:
                        if inv.grade == EggGrade.SMALL:
                            summary['small'] = inv.current_stock
                        elif inv.grade == EggGrade.MEDIUM:
                            summary['medium'] = inv.current_stock
                        elif inv.grade == EggGrade.LARGE:
                            summary['large'] = inv.current_stock
                        elif inv.grade == EggGrade.BROKEN:
                            summary['broken'] = inv.current_stock
                else:
                    produced = (
                        session.query(
                            func.coalesce(func.sum(EggProduction.small_count), 0),
                            func.coalesce(func.sum(EggProduction.medium_count), 0),
                            func.coalesce(func.sum(EggProduction.large_count), 0),
                            func.coalesce(func.sum(EggProduction.broken_count), 0),
                        )
                        .join(Shed, EggProduction.shed_id == Shed.id)
                        .filter(Shed.farm_id == farm_id)
                        .one()
                    )
                    summary['small'] = int(produced[0] or 0)
                    summary['medium'] = int(produced[1] or 0)
                    summary['large'] = int(produced[2] or 0)
                    summary['broken'] = int(produced[3] or 0)

                    sold_usable = int(
                        session.query(func.coalesce(func.sum(Sale.quantity), 0))
                        .filter(Sale.farm_id == farm_id)
                        .scalar()
                        or 0
                    )

                    # Mirror inventory consumption order used during sales.
                    remaining = sold_usable
                    for key in ('large', 'medium', 'small'):
                        if remaining <= 0:
                            break
                        take = min(summary[key], remaining)
                        summary[key] -= take
                        remaining -= take

                    summary['small'] = max(summary['small'], 0)
                    summary['medium'] = max(summary['medium'], 0)
                    summary['large'] = max(summary['large'], 0)
                    summary['broken'] = max(summary['broken'], 0)

            finally:
                session.close()

            summary['total'] = sum(summary.values())
            summary['usable'] = summary['small'] + summary['medium'] + summary['large']
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting stock summary: {e}")
            return {'small': 0, 'medium': 0, 'large': 0, 'broken': 0, 'total': 0, 'usable': 0}
    
    def close(self):
        """Close session"""
        return None

