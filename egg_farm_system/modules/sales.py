"""
Sales module with auto ledger posting and performance optimizations
"""
from datetime import datetime
from egg_farm_system.database.models import Sale, EggProduction
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.utils.currency import CurrencyConverter
from egg_farm_system.utils.advanced_caching import CacheInvalidationManager
from egg_farm_system.utils.performance_monitoring import measure_time
from egg_farm_system.utils.audit_trail import get_audit_trail, ActionType
import logging
from egg_farm_system.modules.inventory import InventoryManager

logger = logging.getLogger(__name__)

class RawMaterialSaleManager:
    """
    Manage raw material sales
    
    Note: This manager uses an instance-level database session. The session is created
    in __init__ and should be closed by calling close_session() when done, or it will
    be closed when the manager instance is garbage collected.
    """
    
    def __init__(self, current_user=None):
        self.session = DatabaseManager.get_session()
        self.converter = CurrencyConverter()
        self.current_user = current_user

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()
    
    def record_raw_material_sale(self, party_id, material_id, quantity, rate_afg, rate_usd,
                                 exchange_rate_used=78.0, date=None, notes=None, payment_method="Cash"):
        """Record raw material sale and post to ledger"""
        try:
            with measure_time(f"record_raw_material_sale_party_{party_id}"):
                from egg_farm_system.database.models import RawMaterial, RawMaterialSale
                
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
                    raise ValueError(f"Raw Material {material_id} not found")
                
                if material.current_stock < quantity:
                    raise ValueError(f"Insufficient stock for {material.name}. Available: {material.current_stock}, Trying to sell: {quantity}")
                
                total_afg = quantity * rate_afg
                total_usd = quantity * rate_usd
                
                raw_material_sale = RawMaterialSale(
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
                self.session.add(raw_material_sale)
                
                # Deduct from material stock
                material.current_stock -= quantity
                self.session.add(material)
                
                self.session.flush() # Get sale ID for ledger posting
                
                # Post to ledger: Debit party, Credit Raw Material Sales
                ledger_manager = LedgerManager()
                ledger_manager.post_entry(
                    party_id=party_id,
                    date=date,
                    description=f"Raw Material Sale: {quantity}{material.unit} {material.name}",
                    debit_afg=total_afg,
                    debit_usd=total_usd,
                    exchange_rate_used=exchange_rate_used,
                    reference_type="RawMaterialSale",
                    reference_id=raw_material_sale.id,
                    session=self.session
                )
                
                # If payment method is Cash, create a payment record for cash flow tracking
                if payment_method == "Cash":
                    from egg_farm_system.database.models import Payment
                    cash_payment = Payment(
                        party_id=party_id,
                        date=date,
                        amount_afg=total_afg,
                        amount_usd=total_usd,
                        payment_type="Received",  # We received cash from customer
                        payment_method="Cash",
                        reference=f"Raw Material Sale #{raw_material_sale.id}",
                        exchange_rate_used=exchange_rate_used
                    )
                    self.session.add(cash_payment)
                
                self.session.commit()
                
                # Invalidate caches after successful save
                CacheInvalidationManager.on_raw_material_sale_created() # Assuming this cache key exists
                
                # Log audit
                user_id = self.current_user.id if self.current_user else None
                username = self.current_user.username if self.current_user else None
                get_audit_trail().log_action(
                    user_id=user_id,
                    username=username,
                    action_type=ActionType.CREATE,
                    entity_type="RawMaterialSale",
                    entity_id=raw_material_sale.id,
                    description=f"New raw material sale: {quantity}{material.unit} {material.name} to Party {party_id}"
                )
                
                logger.info(f"Raw material sale recorded: {quantity}{material.unit} {material.name} to party {party_id}")
                return raw_material_sale
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording raw material sale: {e}")
            raise
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()


class SalesManager:
    """
    Manage egg sales
    
    Note: This manager uses an instance-level database session. The session is created
    in __init__ and should be closed by calling close_session() when done, or it will
    be closed when the manager instance is garbage collected.
    """
    
    def __init__(self, current_user=None):
        self.session = DatabaseManager.get_session()
        self.converter = CurrencyConverter()
        self.current_user = current_user

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()
    
    def record_sale(self, party_id, quantity, rate_afg, rate_usd, 
                    exchange_rate_used=78.0, date=None, notes=None, payment_method="Cash"):
        """Record egg sale and post to ledger"""
        try:
            with measure_time(f"record_sale_party_{party_id}"):
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
                
                total_afg = quantity * rate_afg
                total_usd = quantity * rate_usd
                
                sale = Sale(
                    party_id=party_id,
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
                self.session.add(sale)
                self.session.flush()  # Get sale ID
                # Consume eggs from inventory
                inv_mgr = InventoryManager()
                inv_mgr.consume_eggs(self.session, quantity)
                # Post to ledger: Debit party, Credit sales
                ledger_manager = LedgerManager() # Instantiate LedgerManager
                ledger_manager.post_entry(
                    party_id=party_id,
                    date=date,
                    description=f"Egg sale: {quantity} units",
                    debit_afg=total_afg,
                    debit_usd=total_usd,
                    exchange_rate_used=exchange_rate_used,
                    reference_type="Sale",
                    reference_id=sale.id,
                    session=self.session # Pass the current session
                )
                
                self.session.commit()
                
                # Invalidate caches after successful save
                CacheInvalidationManager.on_sale_created()
                
                # Log audit
                user_id = self.current_user.id if self.current_user else None
                username = self.current_user.username if self.current_user else None
                get_audit_trail().log_action(
                    user_id=user_id,
                    username=username,
                    action_type=ActionType.CREATE,
                    entity_type="Sale",
                    entity_id=sale.id,
                    description=f"New sale: {quantity} eggs to Party {party_id}"
                )
                
                logger.info(f"Sale recorded: {quantity} eggs to party {party_id}")
                return sale
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording sale: {e}")
            raise
    
    def record_sale_advanced(self, party_id, cartons, eggs, grade, rate_afg, rate_usd,
                            tray_expense_afg=0, carton_expense_afg=0,
                            exchange_rate_used=78.0, date=None, notes=None, payment_method="Cash"):
        """Record advanced egg sale with carton and expense tracking"""
        try:
            # Input validation
            if eggs <= 0:
                raise ValueError("Egg quantity must be greater than 0")
            if cartons < 0:
                raise ValueError("Cartons cannot be negative")
            if rate_afg < 0:
                raise ValueError("Rate (AFG) cannot be negative")
            if rate_usd < 0:
                raise ValueError("Rate (USD) cannot be negative")
            if tray_expense_afg < 0:
                raise ValueError("Tray expense cannot be negative")
            if carton_expense_afg < 0:
                raise ValueError("Carton expense cannot be negative")
            if exchange_rate_used <= 0:
                raise ValueError("Exchange rate must be greater than 0")
            
            if date is None:
                date = datetime.utcnow()
            
            total_afg = eggs * rate_afg
            total_usd = eggs * rate_usd
            total_expense_afg = tray_expense_afg + carton_expense_afg
            
            sale = Sale(
                party_id=party_id,
                date=date,
                quantity=eggs,
                cartons=cartons,
                egg_grade=grade,
                rate_afg=rate_afg,
                rate_usd=rate_usd,
                total_afg=total_afg,
                total_usd=total_usd,
                exchange_rate_used=exchange_rate_used,
                tray_expense_afg=tray_expense_afg,
                carton_expense_afg=carton_expense_afg,
                total_expense_afg=total_expense_afg,
                payment_method=payment_method,
                notes=notes
            )
            self.session.add(sale)
            self.session.flush()  # Get sale ID

            # Consume eggs only (packaging was already consumed during production)
            inv_mgr = InventoryManager()
            inv_mgr.consume_eggs(self.session, eggs)
            # NOTE: Cartons/trays are NOT consumed here - they're consumed during egg production
            
            # Post to ledger: Debit party, Credit sales
            ledger_manager = LedgerManager()
            ledger_manager.post_entry(
                party_id=party_id,
                date=date,
                description=f"Egg sale: {cartons:.2f} cartons ({eggs} eggs) - {grade}",
                debit_afg=total_afg,
                debit_usd=total_usd,
                exchange_rate_used=exchange_rate_used,
                reference_type="Sale",
                reference_id=sale.id,
                session=self.session
            )
            
            # If payment method is Cash, create a payment record for cash flow tracking
            if payment_method == "Cash":
                from egg_farm_system.database.models import Payment
                cash_payment = Payment(
                    party_id=party_id,
                    date=date,
                    amount_afg=total_afg,
                    amount_usd=total_usd,
                    payment_type="Received",  # We received cash from customer
                    payment_method="Cash",
                    reference=f"Sale #{sale.id}",
                    exchange_rate_used=exchange_rate_used
                )
                self.session.add(cash_payment)
            
            self.session.commit()
            
            # Log audit
            user_id = self.current_user.id if self.current_user else None
            username = self.current_user.username if self.current_user else None
            get_audit_trail().log_action(
                user_id=user_id,
                username=username,
                action_type=ActionType.CREATE,
                entity_type="Sale",
                entity_id=sale.id,
                description=f"Advanced sale: {cartons} cartons to Party {party_id}"
            )
            
            logger.info(f"Advanced sale recorded: {cartons} cartons ({eggs} eggs) to party {party_id}")
            return sale
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording advanced sale: {e}")
            raise
    
    def get_sales(self, party_id=None, start_date=None, end_date=None):
        """Get sales records"""
        try:
            query = self.session.query(Sale)
            
            if party_id:
                query = query.filter(Sale.party_id == party_id)
            
            if start_date:
                query = query.filter(Sale.date >= start_date)
            
            if end_date:
                query = query.filter(Sale.date <= end_date)
            
            return query.order_by(Sale.date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting sales: {e}")
            return []
    
    def get_sales_summary(self, party_id=None, start_date=None, end_date=None):
        """Get sales summary"""
        try:
            sales = self.get_sales(party_id, start_date, end_date)
            
            total_quantity = sum(s.quantity for s in sales)
            total_afg = sum(s.total_afg for s in sales)
            total_usd = sum(s.total_usd for s in sales)
            
            return {
                'total_sales': len(sales),
                'total_quantity': total_quantity,
                'total_afg': total_afg,
                'total_usd': total_usd,
                'average_rate_afg': total_afg / total_quantity if total_quantity > 0 else 0,
                'average_rate_usd': total_usd / total_quantity if total_quantity > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting sales summary: {e}")
            return {
                'total_sales': 0,
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