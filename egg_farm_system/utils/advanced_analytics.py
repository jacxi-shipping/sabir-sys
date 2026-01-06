"""
Advanced Analytics Module for Egg Farm Management System
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    EggProduction, Shed, Flock, Sale, Purchase, Expense, FeedIssue,
    RawMaterial, FinishedFeed
)

logger = logging.getLogger(__name__)


class ProductionAnalytics:
    """Advanced production analytics"""
    
    def __init__(self, session=None):
        self.session = session or DatabaseManager.get_session()
    
    def detect_anomalies(self, farm_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Detect production anomalies (unusual drops or spikes)
        
        Returns list of anomalies with details
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            if not shed_ids:
                return []
            
            # Get daily production data
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids),
                EggProduction.date >= datetime.combine(start_date, datetime.min.time()),
                EggProduction.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            ).order_by(EggProduction.date).all()
            
            # Group by date
            daily_totals = defaultdict(int)
            for prod in productions:
                date_key = prod.date.date() if hasattr(prod.date, 'date') else prod.date
                total = prod.small_count + prod.medium_count + prod.large_count + prod.broken_count
                daily_totals[date_key] += total
            
            if len(daily_totals) < 7:
                return []
            
            # Calculate statistics
            values = list(daily_totals.values())
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            # Detect anomalies (values outside 2 standard deviations)
            anomalies = []
            threshold = 2 * std_dev
            
            for date, value in sorted(daily_totals.items()):
                deviation = abs(value - mean)
                if deviation > threshold and std_dev > 0:
                    anomaly_type = "spike" if value > mean else "drop"
                    severity = "high" if deviation > 3 * std_dev else "medium"
                    
                    anomalies.append({
                        'date': date,
                        'value': value,
                        'expected': round(mean, 2),
                        'deviation': round(deviation, 2),
                        'type': anomaly_type,
                        'severity': severity,
                        'percentage_change': round(((value - mean) / mean * 100) if mean > 0 else 0, 2)
                    })
            
            return sorted(anomalies, key=lambda x: x['deviation'], reverse=True)
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def seasonal_trend_analysis(self, farm_id: int, years: int = 2) -> Dict[str, Any]:
        """
        Analyze seasonal trends in production
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=years * 365)
            
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            if not shed_ids:
                return {}
            
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids),
                EggProduction.date >= datetime.combine(start_date, datetime.min.time())
            ).all()
            
            # Group by month
            monthly_totals = defaultdict(int)
            for prod in productions:
                date = prod.date.date() if hasattr(prod.date, 'date') else prod.date
                month_key = f"{date.year}-{date.month:02d}"
                total = prod.small_count + prod.medium_count + prod.large_count + prod.broken_count
                monthly_totals[month_key] += total
            
            # Calculate average per month
            month_averages = defaultdict(list)
            for month_key, total in monthly_totals.items():
                month_num = int(month_key.split('-')[1])
                month_averages[month_num].append(total)
            
            result = {}
            for month in range(1, 13):
                if month in month_averages:
                    result[month] = {
                        'average': statistics.mean(month_averages[month]),
                        'count': len(month_averages[month]),
                        'min': min(month_averages[month]),
                        'max': max(month_averages[month])
                    }
            
            return result
        
        except Exception as e:
            logger.error(f"Error in seasonal analysis: {e}")
            return {}
    
    def shed_performance_comparison(self, farm_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Compare performance across sheds
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            
            comparison = []
            for shed in sheds:
                productions = self.session.query(EggProduction).filter(
                    EggProduction.shed_id == shed.id,
                    EggProduction.date >= datetime.combine(start_date, datetime.min.time()),
                    EggProduction.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
                ).all()
                
                total_eggs = sum(
                    p.small_count + p.medium_count + p.large_count + p.broken_count
                    for p in productions
                )
                
                usable_eggs = sum(
                    p.small_count + p.medium_count + p.large_count
                    for p in productions
                )
                
                production_days = len(set(p.date.date() if hasattr(p.date, 'date') else p.date for p in productions))
                avg_daily = total_eggs / production_days if production_days > 0 else 0
                
                # Get flock info
                flocks = self.session.query(Flock).filter(Flock.shed_id == shed.id).all()
                total_birds = sum(f.get_live_count() for f in flocks)
                eggs_per_bird = (total_eggs / total_birds) if total_birds > 0 else 0
                
                comparison.append({
                    'shed_id': shed.id,
                    'shed_name': shed.name,
                    'total_eggs': total_eggs,
                    'usable_eggs': usable_eggs,
                    'avg_daily': round(avg_daily, 2),
                    'total_birds': total_birds,
                    'eggs_per_bird': round(eggs_per_bird, 2),
                    'production_days': production_days,
                    'utilization': round((total_birds / shed.capacity * 100) if shed.capacity > 0 else 0, 2)
                })
            
            # Sort by total eggs
            comparison.sort(key=lambda x: x['total_eggs'], reverse=True)
            
            return comparison
        
        except Exception as e:
            logger.error(f"Error in shed comparison: {e}")
            return []


class FinancialAnalytics:
    """Advanced financial analytics"""
    
    def __init__(self, session=None):
        self.session = session or DatabaseManager.get_session()
    
    def profit_loss_analysis(self, farm_id: int, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """
        Calculate profit and loss for a period
        """
        try:
            # Revenue from sales
            sales = self.session.query(Sale).filter(
                Sale.date >= datetime.combine(start_date, datetime.min.time()),
                Sale.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            ).all()
            
            total_revenue_afg = sum(s.total_afg for s in sales)
            total_revenue_usd = sum(s.total_usd for s in sales)
            
            # Costs
            # Feed costs
            sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            feed_costs_afg = 0
            feed_costs_usd = 0
            if shed_ids:
                feed_issues = self.session.query(FeedIssue).filter(
                    FeedIssue.shed_id.in_(shed_ids),
                    FeedIssue.date >= datetime.combine(start_date, datetime.min.time()),
                    FeedIssue.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
                ).all()
                
                for issue in feed_issues:
                    # Estimate cost based on feed type
                    feed = self.session.query(FinishedFeed).filter_by(feed_type=issue.feed_type).first()
                    if feed:
                        cost_per_kg = feed.cost_per_kg_afg
                        feed_costs_afg += issue.quantity_kg * cost_per_kg
                        feed_costs_usd += issue.quantity_kg * (feed.cost_per_kg_afg / 78.0)  # Approximate
            
            # Expenses
            expenses = self.session.query(Expense).filter(
                Expense.farm_id == farm_id,
                Expense.date >= datetime.combine(start_date, datetime.min.time()),
                Expense.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            ).all()
            
            total_expenses_afg = sum(e.amount_afg for e in expenses)
            total_expenses_usd = sum(e.amount_usd for e in expenses)
            
            # Total costs
            total_costs_afg = feed_costs_afg + total_expenses_afg
            total_costs_usd = feed_costs_usd + total_expenses_usd
            
            # Profit/Loss
            profit_afg = total_revenue_afg - total_costs_afg
            profit_usd = total_revenue_usd - total_costs_usd
            
            # Profit margin
            profit_margin = (profit_afg / total_revenue_afg * 100) if total_revenue_afg > 0 else 0
            
            return {
                'revenue_afg': total_revenue_afg,
                'revenue_usd': total_revenue_usd,
                'feed_costs_afg': feed_costs_afg,
                'feed_costs_usd': feed_costs_usd,
                'expenses_afg': total_expenses_afg,
                'expenses_usd': total_expenses_usd,
                'total_costs_afg': total_costs_afg,
                'total_costs_usd': total_costs_usd,
                'profit_afg': profit_afg,
                'profit_usd': profit_usd,
                'profit_margin': round(profit_margin, 2),
                'period': f"{start_date} to {end_date}"
            }
        
        except Exception as e:
            logger.error(f"Error in P&L analysis: {e}")
            return {}
    
    def cost_breakdown(self, farm_id: int, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """Break down costs by category"""
        try:
            expenses = self.session.query(Expense).filter(
                Expense.farm_id == farm_id,
                Expense.date >= datetime.combine(start_date, datetime.min.time()),
                Expense.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            ).all()
            
            breakdown = defaultdict(lambda: {'afg': 0, 'usd': 0, 'count': 0})
            
            for expense in expenses:
                category = expense.category
                breakdown[category]['afg'] += expense.amount_afg
                breakdown[category]['usd'] += expense.amount_usd
                breakdown[category]['count'] += 1
            
            return dict(breakdown)
        
        except Exception as e:
            logger.error(f"Error in cost breakdown: {e}")
            return {}
    
    def calculate_roi(self, farm_id: int, period_days: int = 365) -> Dict[str, Any]:
        """
        Calculate Return on Investment
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=period_days)
            
            pnl = self.profit_loss_analysis(farm_id, start_date, end_date)
            
            # Estimate investment (inventory value + equipment)
            from egg_farm_system.modules.inventory import InventoryManager
            inventory_manager = InventoryManager()
            inventory_value = inventory_manager.get_total_inventory_value()
            
            total_investment_afg = inventory_value.get('total_afg', 0)
            
            # ROI = (Profit / Investment) * 100
            roi = (pnl.get('profit_afg', 0) / total_investment_afg * 100) if total_investment_afg > 0 else 0
            
            return {
                'investment_afg': total_investment_afg,
                'profit_afg': pnl.get('profit_afg', 0),
                'roi_percentage': round(roi, 2),
                'period_days': period_days
            }
        
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return {}


class InventoryAnalytics:
    """Advanced inventory analytics"""
    
    def __init__(self, session=None):
        self.session = session or DatabaseManager.get_session()
    
    def consumption_rate_analysis(self, material_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze consumption rate for a material
        """
        try:
            material = self.session.query(RawMaterial).filter_by(id=material_id).first()
            if not material:
                return {}
            
            # Get purchase history
            purchases = self.session.query(Purchase).filter(
                Purchase.material_name == material.name
            ).order_by(Purchase.date.desc()).limit(10).all()
            
            if not purchases:
                return {}
            
            # Calculate average consumption
            # This is simplified - in reality would track actual usage from feed production
            current_stock = material.current_stock
            avg_purchase_quantity = statistics.mean([p.quantity for p in purchases]) if purchases else 0
            
            # Estimate daily consumption (simplified)
            days_since_last_purchase = (datetime.utcnow().date() - purchases[0].date.date()).days if purchases else 30
            estimated_daily_consumption = (avg_purchase_quantity - current_stock) / days_since_last_purchase if days_since_last_purchase > 0 else 0
            
            # Calculate days until stockout
            days_until_stockout = current_stock / estimated_daily_consumption if estimated_daily_consumption > 0 else 999
            
            return {
                'material_name': material.name,
                'current_stock': current_stock,
                'estimated_daily_consumption': round(estimated_daily_consumption, 2),
                'days_until_stockout': round(days_until_stockout, 2),
                'reorder_point': material.low_stock_alert,
                'needs_reorder': days_until_stockout < 7
            }
        
        except Exception as e:
            logger.error(f"Error in consumption analysis: {e}")
            return {}
    
    def inventory_turnover_ratio(self, days: int = 365) -> Dict[str, Any]:
        """
        Calculate inventory turnover ratio
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get purchases in period
            purchases = self.session.query(Purchase).filter(
                Purchase.date >= datetime.combine(start_date, datetime.min.time()),
                Purchase.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            ).all()
            
            total_purchases_afg = sum(p.total_afg for p in purchases)
            
            # Get current inventory value
            from egg_farm_system.modules.inventory import InventoryManager
            inventory_manager = InventoryManager()
            inventory_value = inventory_manager.get_total_inventory_value()
            avg_inventory_afg = inventory_value.get('total_afg', 0)
            
            # Turnover ratio = Cost of Goods Sold / Average Inventory
            turnover_ratio = (total_purchases_afg / avg_inventory_afg) if avg_inventory_afg > 0 else 0
            
            return {
                'total_purchases_afg': total_purchases_afg,
                'avg_inventory_afg': avg_inventory_afg,
                'turnover_ratio': round(turnover_ratio, 2),
                'days_to_turnover': round(days / turnover_ratio, 2) if turnover_ratio > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error calculating turnover: {e}")
            return {}
    
    def abc_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        ABC analysis - categorize items by value
        A: High value (80% of total)
        B: Medium value (15% of total)
        C: Low value (5% of total)
        """
        try:
            materials = self.session.query(RawMaterial).all()
            
            # Calculate total value
            items = []
            for material in materials:
                value = material.current_stock * material.cost_per_unit_afg
                items.append({
                    'name': material.name,
                    'value': value,
                    'type': 'raw_material',
                    'id': material.id
                })
            
            # Sort by value
            items.sort(key=lambda x: x['value'], reverse=True)
            
            total_value = sum(item['value'] for item in items)
            
            # Categorize
            category_a = []
            category_b = []
            category_c = []
            
            cumulative_value = 0
            for item in items:
                cumulative_value += item['value']
                percentage = (cumulative_value / total_value * 100) if total_value > 0 else 0
                
                if percentage <= 80:
                    category_a.append(item)
                elif percentage <= 95:
                    category_b.append(item)
                else:
                    category_c.append(item)
            
            return {
                'A': category_a,
                'B': category_b,
                'C': category_c,
                'total_value': total_value
            }
        
        except Exception as e:
            logger.error(f"Error in ABC analysis: {e}")
            return {'A': [], 'B': [], 'C': [], 'total_value': 0}

