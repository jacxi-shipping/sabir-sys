"""
Expenses and payments module with performance optimizations
"""
from datetime import datetime
from egg_farm_system.database.models import Expense, Payment
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.utils.advanced_caching import CacheInvalidationManager
from egg_farm_system.utils.performance_monitoring import measure_time
import logging

logger = logging.getLogger(__name__)

class ExpenseManager:
    """
    Manage farm expenses
    
    Note: This manager uses an instance-level database session. The session is created
    in __init__ and should be closed by calling close_session() when done, or it will
    be closed when the manager instance is garbage collected.
    """
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
    
    def record_expense(self, farm_id, category, amount_afg, amount_usd, 
                      party_id=None, exchange_rate_used=78.0, date=None, description=None, payment_method="Cash"):
        """Record farm expense"""
        try:
            with measure_time(f"record_expense_farm_{farm_id}"):
                # Input validation
                if amount_afg < 0:
                    raise ValueError("Amount (AFG) cannot be negative")
                if amount_usd < 0:
                    raise ValueError("Amount (USD) cannot be negative")
                if exchange_rate_used <= 0:
                    raise ValueError("Exchange rate must be greater than 0")
                if not category or not category.strip():
                    raise ValueError("Category is required")
                
                if date is None:
                    date = datetime.utcnow()
                
                expense = Expense(
                    farm_id=farm_id,
                    party_id=party_id,
                    date=date,
                    category=category,
                    description=description,
                    amount_afg=amount_afg,
                    amount_usd=amount_usd,
                    exchange_rate_used=exchange_rate_used,
                    payment_method=payment_method
                )
                self.session.add(expense)
                self.session.flush()
                
                # Post to ledger if party is linked
                if party_id:
                    ledger_manager = LedgerManager() # Instantiate LedgerManager
                    ledger_manager.post_entry(
                        party_id=party_id,
                        date=date,
                        description=f"Expense: {category} - {description or ''}",
                        credit_afg=amount_afg,
                        credit_usd=amount_usd,
                        exchange_rate_used=exchange_rate_used,
                        reference_type="Expense",
                        reference_id=expense.id,
                        session=self.session # Pass the current session
                    )
                
                self.session.commit()
                
                # Invalidate caches after successful save
                CacheInvalidationManager.on_expense_created()
                
                logger.info(f"Expense recorded: {category} - Afs {amount_afg}")
                return expense
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording expense: {e}")
            raise
    
    def get_expenses(self, farm_id=None, start_date=None, end_date=None, category=None):
        """Get expense records"""
        try:
            query = self.session.query(Expense)
            
            if farm_id:
                query = query.filter(Expense.farm_id == farm_id)
            
            if start_date:
                query = query.filter(Expense.date >= start_date)
            
            if end_date:
                query = query.filter(Expense.date <= end_date)
            
            if category:
                query = query.filter(Expense.category == category)
            
            return query.order_by(Expense.date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting expenses: {e}")
            return []
    
    def get_expenses_summary(self, farm_id=None, start_date=None, end_date=None):
        """Get expenses summary"""
        try:
            expenses = self.get_expenses(farm_id, start_date, end_date)
            
            total_afg = sum(e.amount_afg for e in expenses)
            total_usd = sum(e.amount_usd for e in expenses)
            
            by_category = {}
            for expense in expenses:
                if expense.category not in by_category:
                    by_category[expense.category] = {'count': 0, 'afg': 0, 'usd': 0}
                
                by_category[expense.category]['count'] += 1
                by_category[expense.category]['afg'] += expense.amount_afg
                by_category[expense.category]['usd'] += expense.amount_usd
            
            return {
                'total_expenses': len(expenses),
                'total_afg': total_afg,
                'total_usd': total_usd,
                'by_category': by_category
            }
        except Exception as e:
            logger.error(f"Error getting expenses summary: {e}")
            return {
                'total_expenses': 0,
                'total_afg': 0,
                'total_usd': 0,
                'by_category': {}
            }


class PaymentManager:
    """
    Manage payments to/from parties
    
    Note: This manager uses an instance-level database session. The session is created
    in __init__ and should be closed by calling close_session() when done, or it will
    be closed when the manager instance is garbage collected.
    """
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
    
    def record_payment(self, party_id, amount_afg, amount_usd, payment_type,
                      payment_method="Cash", reference=None, exchange_rate_used=78.0, 
                      date=None, notes=None):
        """Record payment and post to ledger"""
        try:
            # Input validation
            if amount_afg < 0:
                raise ValueError("Amount (AFG) cannot be negative")
            if amount_usd < 0:
                raise ValueError("Amount (USD) cannot be negative")
            if exchange_rate_used <= 0:
                raise ValueError("Exchange rate must be greater than 0")
            if payment_type not in ["Received", "Paid"]:
                raise ValueError("Payment type must be 'Received' or 'Paid'")
            
            if date is None:
                date = datetime.utcnow()
            
            payment = Payment(
                party_id=party_id,
                date=date,
                amount_afg=amount_afg,
                amount_usd=amount_usd,
                payment_type=payment_type,
                payment_method=payment_method,
                reference=reference,
                exchange_rate_used=exchange_rate_used,
                notes=notes
            )
            self.session.add(payment)
            self.session.flush()
            
            # Post to ledger
            ledger_manager = LedgerManager() # Instantiate LedgerManager
            if payment_type == "Received":
                # Debit cash, Credit party
                ledger_manager.post_entry(
                    party_id=party_id,
                    date=date,
                    description=f"Payment received: {reference or 'Cash'}",
                    credit_afg=amount_afg,
                    credit_usd=amount_usd,
                    exchange_rate_used=exchange_rate_used,
                    reference_type="Payment",
                    reference_id=payment.id,
                    session=self.session # Pass the current session
                )
            else:  # Paid
                # Debit party, Credit cash
                ledger_manager.post_entry(
                    party_id=party_id,
                    date=date,
                    description=f"Payment paid: {reference or 'Cash'}",
                    debit_afg=amount_afg,
                    debit_usd=amount_usd,
                    exchange_rate_used=exchange_rate_used,
                    reference_type="Payment",
                    reference_id=payment.id,
                    session=self.session # Pass the current session
                )
            
            self.session.commit()
            logger.info(f"Payment recorded: {payment_type} Afs {amount_afg} from/to party {party_id}")
            return payment
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording payment: {e}")
            raise
    
    def get_payments(self, party_id=None, start_date=None, end_date=None):
        """Get payment records"""
        try:
            query = self.session.query(Payment)
            
            if party_id:
                query = query.filter(Payment.party_id == party_id)
            
            if start_date:
                query = query.filter(Payment.date >= start_date)
            
            if end_date:
                query = query.filter(Payment.date <= end_date)
            
            return query.order_by(Payment.date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting payments: {e}")
            return []
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
