"""
Advanced Egg Management System
Handles tray/carton conversion, expenses, and cost calculations
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import EggProduction
from egg_farm_system.modules.settings import SettingsManager

logger = logging.getLogger(__name__)


class EggManagementSystem:
    """Advanced egg management with tray/carton system"""
    
    # Constants
    EGGS_PER_TRAY = 15
    EGGS_PER_CARTON = 180
    TRAYS_PER_CARTON = 12  # 180 / 15
    TRAYS_EXPENSE_PER_CARTON = 7  # Packaging trays used per carton
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
    
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
            farm_id: Farm ID
            grade: Egg grade (small, medium, large, broken)
            
        Returns:
            Available count
        """
        try:
            from egg_farm_system.database.models import Shed, Sale
            from egg_farm_system.modules.sales import SalesManager
            
            # Get all sheds for farm
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            if not shed_ids:
                return 0
            
            # Get total production by grade
            grade_field_map = {
                'small': 'small_count',
                'medium': 'medium_count',
                'large': 'large_count',
                'broken': 'broken_count'
            }
            
            if grade not in grade_field_map:
                return 0
            
            # Sum production
            total_produced = 0
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids)
            ).all()
            
            for prod in productions:
                total_produced += getattr(prod, grade_field_map[grade])
            
            # Subtract sold eggs (simplified - would need to track by grade in sales)
            # For now, return total produced (sales don't track by grade currently)
            return total_produced
        
        except Exception as e:
            logger.error(f"Error getting available eggs: {e}")
            return 0
    
    def get_egg_stock_summary(self, farm_id: int) -> Dict[str, int]:
        """Get egg stock summary by grade"""
        try:
            from egg_farm_system.database.models import Shed
            
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            if not shed_ids:
                return {'small': 0, 'medium': 0, 'large': 0, 'broken': 0, 'total': 0}
            
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids)
            ).all()
            
            summary = {'small': 0, 'medium': 0, 'large': 0, 'broken': 0}
            
            for prod in productions:
                summary['small'] += prod.small_count
                summary['medium'] += prod.medium_count
                summary['large'] += prod.large_count
                summary['broken'] += prod.broken_count
            
            summary['total'] = sum(summary.values())
            summary['usable'] = summary['small'] + summary['medium'] + summary['large']
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting stock summary: {e}")
            return {'small': 0, 'medium': 0, 'large': 0, 'broken': 0, 'total': 0, 'usable': 0}
    
    def close(self):
        """Close session"""
        if self.session:
            self.session.close()

