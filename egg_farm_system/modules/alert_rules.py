"""
Alert Rules Engine for Smart Notifications
"""
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, Shed, EggProduction, Mortality, Flock,
    RawMaterial, FinishedFeed, Party, Sale, Purchase
)

logger = logging.getLogger(__name__)


class AlertRule:
    """Base class for alert rules"""
    
    def __init__(self, rule_id: str, name: str, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.enabled = enabled
        self.settings = {}
    
    def check(self, session) -> list:
        """Check if alert should be triggered - returns list of alerts"""
        raise NotImplementedError
    
    def get_settings(self) -> dict:
        """Get rule settings"""
        return self.settings
    
    def set_settings(self, settings: dict):
        """Set rule settings"""
        self.settings.update(settings)


class ProductionDropAlert(AlertRule):
    """Alert when production drops significantly"""
    
    def __init__(self):
        super().__init__(
            'production_drop',
            'Production Drop Alert',
            enabled=True
        )
        self.settings = {
            'threshold_percent': 20,  # 20% drop
            'days_to_compare': 7
        }
    
    def check(self, session) -> list:
        """Check for production drops"""
        alerts = []
        
        try:
            threshold = self.settings.get('threshold_percent', 20)
            days = self.settings.get('days_to_compare', 7)
            
            # Get all farms
            farms = session.query(Farm).all()
            
            for farm in farms:
                # Get recent production (last N days)
                recent_avg = self._get_avg_production(session, farm.id, days=days)
                
                # Get previous period (days N+1 to 2N)
                previous_avg = self._get_avg_production(
                    session, farm.id, days=days, offset=days
                )
                
                if previous_avg > 0:
                    drop_pct = ((previous_avg - recent_avg) / previous_avg) * 100
                    
                    if drop_pct >= threshold:
                        alerts.append({
                            'type': 'production_drop',
                            'severity': 'warning',
                            'title': f'Production Drop at {farm.name}',
                            'message': f'Production has dropped {drop_pct:.1f}% in the last {days} days (was {previous_avg:.0f}, now {recent_avg:.0f})',
                            'farm_id': farm.id,
                            'data': {
                                'recent_avg': recent_avg,
                                'previous_avg': previous_avg,
                                'drop_percentage': drop_pct,
                                'threshold': threshold
                            }
                        })
        except Exception as e:
            logger.error(f"Error checking production drop: {e}")
        
        return alerts
    
    def _get_avg_production(self, session, farm_id: int, days: int, offset: int = 0):
        """Get average daily production"""
        end_date = datetime.now().date() - timedelta(days=offset)
        start_date = end_date - timedelta(days=days - 1)
        
        total = session.query(func.sum(
            EggProduction.small_count + EggProduction.medium_count + EggProduction.large_count
        )).join(Shed).filter(
            Shed.farm_id == farm_id,
            EggProduction.date >= start_date,
            EggProduction.date <= end_date
        ).scalar() or 0
        
        return total / days if days > 0 else 0


class HighMortalityAlert(AlertRule):
    """Alert when mortality rate is high"""
    
    def __init__(self):
        super().__init__(
            'high_mortality',
            'High Mortality Alert',
            enabled=True
        )
        self.settings = {
            'threshold_percent': 5,  # 5% mortality in a week
            'days_to_check': 7
        }
    
    def check(self, session) -> list:
        """Check for high mortality"""
        alerts = []
        
        try:
            threshold = self.settings.get('threshold_percent', 5)
            days = self.settings.get('days_to_check', 7)
            
            # Get all active flocks
            flocks = session.query(Flock).all()
            
            for flock in flocks:
                mortality_rate = self._get_mortality_rate(session, flock.id, days)
                
                if mortality_rate >= threshold:
                    alerts.append({
                        'type': 'high_mortality',
                        'severity': 'critical',
                        'title': f'High Mortality in {flock.name}',
                        'message': f'Mortality rate is {mortality_rate:.1f}% over the last {days} days (threshold: {threshold}%)',
                        'flock_id': flock.id,
                        'data': {
                            'mortality_rate': mortality_rate,
                            'threshold': threshold,
                            'days': days
                        }
                    })
        except Exception as e:
            logger.error(f"Error checking high mortality: {e}")
        
        return alerts
    
    def _get_mortality_rate(self, session, flock_id: int, days: int) -> float:
        """Calculate mortality rate over period"""
        try:
            flock = session.query(Flock).filter(Flock.id == flock_id).first()
            if not flock:
                return 0
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
            
            total_deaths = session.query(func.sum(Mortality.count)).filter(
                Mortality.flock_id == flock_id,
                Mortality.date >= start_date,
                Mortality.date <= end_date
            ).scalar() or 0
            
            live_count = flock.get_live_count()
            if live_count > 0:
                return (total_deaths / (live_count + total_deaths)) * 100
            
            return 0
        except Exception as e:
            logger.error(f"Error calculating mortality rate: {e}")
            return 0


class LowStockAlert(AlertRule):
    """Alert when stock is low"""
    
    def __init__(self):
        super().__init__(
            'low_stock',
            'Low Stock Alert',
            enabled=True
        )
        self.settings = {}
    
    def check(self, session) -> list:
        """Check for low stock"""
        alerts = []
        
        try:
            # Check raw materials
            low_materials = session.query(RawMaterial).filter(
                RawMaterial.current_stock <= RawMaterial.low_stock_alert
            ).all()
            
            for material in low_materials:
                severity = 'critical' if material.current_stock == 0 else 'warning'
                alerts.append({
                    'type': 'low_stock',
                    'severity': severity,
                    'title': f'Low Stock: {material.name}',
                    'message': f'Current stock: {material.current_stock:.1f} {material.unit} (alert level: {material.low_stock_alert:.1f})',
                    'material_id': material.id,
                    'data': {
                        'material_name': material.name,
                        'current_stock': material.current_stock,
                        'alert_level': material.low_stock_alert,
                        'unit': material.unit
                    }
                })
            
            # Check finished feed
            low_feed = session.query(FinishedFeed).filter(
                FinishedFeed.current_stock <= FinishedFeed.low_stock_alert
            ).all()
            
            for feed in low_feed:
                severity = 'critical' if feed.current_stock == 0 else 'warning'
                alerts.append({
                    'type': 'low_stock',
                    'severity': severity,
                    'title': f'Low Stock: {feed.feed_type.value} Feed',
                    'message': f'Current stock: {feed.current_stock:.1f} kg (alert level: {feed.low_stock_alert:.1f})',
                    'feed_id': feed.id,
                    'data': {
                        'feed_type': feed.feed_type.value,
                        'current_stock': feed.current_stock,
                        'alert_level': feed.low_stock_alert
                    }
                })
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")
        
        return alerts


class OverduePaymentAlert(AlertRule):
    """Alert when payments are overdue"""
    
    def __init__(self):
        super().__init__(
            'overdue_payment',
            'Overdue Payment Alert',
            enabled=True
        )
        self.settings = {
            'days_overdue': 30
        }
    
    def check(self, session) -> list:
        """Check for overdue payments"""
        alerts = []
        
        try:
            days_overdue = self.settings.get('days_overdue', 30)
            cutoff_date = datetime.now().date() - timedelta(days=days_overdue)
            
            # Get parties with positive balance (they owe us)
            parties = session.query(Party).all()
            
            for party in parties:
                balance_afg = party.get_balance("AFG")
                
                if balance_afg > 0:
                    # Check if there are old unpaid sales
                    old_sales = session.query(Sale).filter(
                        Sale.party_id == party.id,
                        Sale.date <= cutoff_date,
                        Sale.payment_method == 'Credit'
                    ).count()
                    
                    if old_sales > 0:
                        alerts.append({
                            'type': 'overdue_payment',
                            'severity': 'warning',
                            'title': f'Overdue Payment: {party.name}',
                            'message': f'Outstanding balance: {balance_afg:,.0f} AFG with {old_sales} sales older than {days_overdue} days',
                            'party_id': party.id,
                            'data': {
                                'party_name': party.name,
                                'balance_afg': balance_afg,
                                'old_sales_count': old_sales,
                                'days_overdue': days_overdue
                            }
                        })
        except Exception as e:
            logger.error(f"Error checking overdue payments: {e}")
        
        return alerts


class FlockAgeAlert(AlertRule):
    """Alert when flock reaches certain age (feed change time)"""
    
    def __init__(self):
        super().__init__(
            'flock_age',
            'Flock Age Milestone Alert',
            enabled=True
        )
        self.settings = {
            'starter_to_grower_weeks': 6,
            'grower_to_layer_weeks': 16
        }
    
    def check(self, session) -> list:
        """Check for flock age milestones"""
        alerts = []
        
        try:
            starter_weeks = self.settings.get('starter_to_grower_weeks', 6)
            grower_weeks = self.settings.get('grower_to_layer_weeks', 16)
            
            flocks = session.query(Flock).all()
            
            for flock in flocks:
                # Handle potential mixed date/datetime from SQLAlchemy
                start_date = flock.start_date
                if isinstance(start_date, datetime):
                    start_date = start_date.date()
                
                age_days = (datetime.now().date() - start_date).days
                age_weeks = age_days / 7
                
                # Check for feed change milestones (within 1 week)
                if abs(age_weeks - starter_weeks) <= 1:
                    alerts.append({
                        'type': 'flock_age',
                        'severity': 'info',
                        'title': f'Feed Change Due: {flock.name}',
                        'message': f'Flock is {age_weeks:.1f} weeks old - time to switch from Starter to Grower feed',
                        'flock_id': flock.id,
                        'data': {
                            'flock_name': flock.name,
                            'age_weeks': age_weeks,
                            'milestone': 'starter_to_grower'
                        }
                    })
                elif abs(age_weeks - grower_weeks) <= 1:
                    alerts.append({
                        'type': 'flock_age',
                        'severity': 'info',
                        'title': f'Feed Change Due: {flock.name}',
                        'message': f'Flock is {age_weeks:.1f} weeks old - time to switch from Grower to Layer feed',
                        'flock_id': flock.id,
                        'data': {
                            'flock_name': flock.name,
                            'age_weeks': age_weeks,
                            'milestone': 'grower_to_layer'
                        }
                    })
        except Exception as e:
            logger.error(f"Error checking flock age: {e}")
        
        return alerts


class AlertEngine:
    """Manages all alert rules"""
    
    RULES = [
        ProductionDropAlert,
        HighMortalityAlert,
        LowStockAlert,
        OverduePaymentAlert,
        FlockAgeAlert,
    ]
    
    def __init__(self):
        self.rules = [rule_class() for rule_class in self.RULES]
    
    def check_all_rules(self) -> list:
        """Check all rules and return combined alerts"""
        all_alerts = []
        session = DatabaseManager.get_session()
        
        try:
            for rule in self.rules:
                if rule.enabled:
                    try:
                        alerts = rule.check(session)
                        all_alerts.extend(alerts)
                    except Exception as e:
                        logger.error(f"Error checking rule {rule.rule_id}: {e}")
        finally:
            session.close()
        
        return all_alerts
    
    def trigger_alerts(self):
        """Check rules and send notifications"""
        alerts = self.check_all_rules()
        
        for alert in alerts:
            self._send_alert(alert)
        
        return alerts
    
    def _send_alert(self, alert: dict):
        """Send alert via notification system"""
        try:
            from egg_farm_system.utils.notification_manager import get_notification_manager
            
            notification_manager = get_notification_manager()
            notification_manager.add_notification(
                title=alert['title'],
                message=alert['message'],
                severity=alert['severity'],
                data=alert.get('data', {})
            )
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def get_rule_by_id(self, rule_id: str):
        """Get rule by ID"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def enable_rule(self, rule_id: str):
        """Enable a rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = True
    
    def disable_rule(self, rule_id: str):
        """Disable a rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = False
