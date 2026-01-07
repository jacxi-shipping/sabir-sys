"""
Sales module with auto ledger posting
"""
from datetime import datetime
from egg_farm_system.database.models import Sale, EggProduction
from egg_farm_system.database.db import DatabaseManager
from modules.ledger import LedgerManager
from utils.currency import CurrencyConverter
import logging

logger = logging.getLogger(__name__)

class SalesManager:
    """Manage egg sales"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.converter = CurrencyConverter()
    
    def record_sale(self, party_id, quantity, rate_afg, rate_usd, 
                    exchange_rate_used=78.0, date=None, notes=None, payment_method="Cash"):
        """Record egg sale and post to ledger"""
        try:
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
            
            self.session.commit()
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
            return None
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()