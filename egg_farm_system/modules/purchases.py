"""
Purchase module with auto ledger posting and performance optimizations
"""
from datetime import datetime
from egg_farm_system.database.models import Purchase, RawMaterial
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.utils.currency import CurrencyConverter
from egg_farm_system.utils.advanced_caching import CacheInvalidationManager
from egg_farm_system.utils.performance_monitoring import measure_time
import logging

logger = logging.getLogger(__name__)

class PurchaseManager:
    """
    Manage material purchases
    
    Note: This manager uses an instance-level database session. The session is created
    in __init__ and should be closed by calling close_session() when done, or it will
    be closed when the manager instance is garbage collected.
    """
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.ledger_manager = LedgerManager()
        self.converter = CurrencyConverter()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()
    
    def record_purchase(self, party_id, material_id, quantity, rate_afg, rate_usd,
                       exchange_rate_used=78.0, date=None, notes=None, payment_method="Cash"):
        """Record material purchase and post to ledger"""
        try:
            with measure_time(f"record_purchase_party_{party_id}"):
                # Input validation
                if quantity <= 0:
                    raise ValueError("Quantity must be greater than 0")
                if rate_afg < 0:
                    raise ValueError("Rate (AFG) cannot be negative")
                if rate_usd < 0:
                    raise ValueError("Rate (USD) cannot be negative")
                if exchange_rate_used <= 0:
                    raise ValueError("Exchange rate must be greater than 0")
                
                if date is None:
                    date = datetime.utcnow()
                
                material = self.session.query(RawMaterial).filter(RawMaterial.id == material_id).first()
                if not material:
                    raise ValueError(f"Material {material_id} not found")
                
                total_afg = quantity * rate_afg
                total_usd = quantity * rate_usd
                
                purchase = Purchase(
                    party_id=party_id,
                    material_id=material_id,
                    date=date,
                    quantity=quantity,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    total_afg=total_afg,
                    total_usd=total_usd,
                    exchange_rate_used=exchange_rate_used,
                    payment_method=payment_method,
                    notes=notes
                )
                self.session.add(purchase)
                self.session.flush()  # Get purchase ID
                
                # Update material stock
                material.current_stock += quantity
                material.cost_afg = rate_afg  # Update cost
                material.cost_usd = rate_usd
                self.session.add(material)
                
                # Post to ledger: Credit party, Debit inventory
                self.ledger_manager.post_entry(
                    party_id=party_id,
                    date=date,
                    description=f"Purchase: {quantity}kg {material.name}",
                    credit_afg=total_afg,
                credit_usd=total_usd,
                exchange_rate_used=exchange_rate_used,
                reference_type="Purchase",
                reference_id=purchase.id,
                session=self.session  # Pass session for transactional consistency
            )
            
            self.session.commit()
            logger.info(f"Purchase recorded: {quantity}kg from party {party_id}")
            return purchase
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording purchase: {e}")
            raise
    
    def get_purchases(self, party_id=None, material_id=None, start_date=None, end_date=None):
        """Get purchase records"""
        try:
            query = self.session.query(Purchase)
            
            if party_id:
                query = query.filter(Purchase.party_id == party_id)
            
            if material_id:
                query = query.filter(Purchase.material_id == material_id)
            
            if start_date:
                query = query.filter(Purchase.date >= start_date)
            
            if end_date:
                query = query.filter(Purchase.date <= end_date)
            
            return query.order_by(Purchase.date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting purchases: {e}")
            return []
    
    def get_purchases_summary(self, party_id=None, material_id=None, start_date=None, end_date=None):
        """Get purchases summary"""
        try:
            purchases = self.get_purchases(party_id, material_id, start_date, end_date)
            
            total_quantity = sum(p.quantity for p in purchases)
            total_afg = sum(p.total_afg for p in purchases)
            total_usd = sum(p.total_usd for p in purchases)
            
            return {
                'total_purchases': len(purchases),
                'total_quantity': total_quantity,
                'total_afg': total_afg,
                'total_usd': total_usd,
                'average_rate_afg': total_afg / total_quantity if total_quantity > 0 else 0,
                'average_rate_usd': total_usd / total_quantity if total_quantity > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting purchases summary: {e}")
            return {
                'total_purchases': 0,
                'total_quantity': 0,
                'total_afg': 0,
                'total_usd': 0,
                'average_rate_afg': 0,
                'average_rate_usd': 0
            }
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()