"""
Ledger and accounting module
"""
from datetime import datetime
from egg_farm_system.database.models import Ledger, Party
from egg_farm_system.database.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class LedgerManager:
    """Manage party ledger entries"""
    
    def post_entry(self, party_id, date, description, debit_afg=0, credit_afg=0, 
                   debit_usd=0, credit_usd=0, exchange_rate_used=78.0, 
                   reference_type=None, reference_id=None, session=None): # Added session parameter
        """Post a ledger entry"""
        # This method expects a session to be passed for transactional integrity.
        # It does not commit/rollback/close the session. The caller is responsible.
        if session is None:
            raise ValueError("A session must be provided to post_entry for transactional consistency.")
            
        party = session.query(Party).filter(Party.id == party_id).first()
        if not party:
            raise ValueError(f"Party {party_id} not found")
        
        entry = Ledger(
            party_id=party_id,
            date=date,
            description=description,
            debit_afg=debit_afg,
            credit_afg=credit_afg,
            debit_usd=debit_usd,
            credit_usd=credit_usd,
            exchange_rate_used=exchange_rate_used,
            reference_type=reference_type,
            reference_id=reference_id
        )
        session.add(entry)
        logger.info(f"Ledger entry posted for party {party_id}")
        return entry
    
    def get_party_ledger(self, party_id):
        """Get all ledger entries for a party"""
        session = DatabaseManager.get_session()
        try:
            return session.query(Ledger).filter(
                Ledger.party_id == party_id
            ).order_by(Ledger.date).all()
        except Exception as e:
            logger.error(f"Error getting party ledger: {e}")
            return []
        finally:
            session.close()
    
    def get_party_balance(self, party_id, currency="AFG"):
        """Calculate party balance"""
        # This method uses get_party_ledger, which manages its own session.
        try:
            entries = self.get_party_ledger(party_id)
            balance = 0
            
            for entry in entries:
                if currency == "AFG":
                    balance += (entry.debit_afg - entry.credit_afg)
                else:  # USD
                    balance += (entry.debit_usd - entry.credit_usd)
            
            return balance
        except Exception as e:
            logger.error(f"Error calculating balance: {e}")
            return 0
    
    def get_balance_with_running(self, party_id, currency="AFG"):
        """Get ledger with running balance"""
        # This method uses get_party_ledger, which manages its own session.
        try:
            entries = self.get_party_ledger(party_id)
            running_balance = 0
            result = []
            
            for entry in entries:
                if currency == "AFG":
                    change = entry.debit_afg - entry.credit_afg
                    debit = entry.debit_afg
                    credit = entry.credit_afg
                else:
                    change = entry.debit_usd - entry.credit_usd
                    debit = entry.debit_usd
                    credit = entry.credit_usd
                
                running_balance += change
                
                result.append({
                    'date': entry.date,
                    'description': entry.description,
                    'debit': debit,
                    'credit': credit,
                    'balance': running_balance,
                    'reference_type': entry.reference_type
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting balance with running total: {e}")
            return []
    
    def get_ledger_summary(self, party_id):
        """Get summary of party ledger"""
        # This method uses get_party_ledger, which manages its own session.
        try:
            entries = self.get_party_ledger(party_id)
            
            total_debit_afg = sum(e.debit_afg for e in entries)
            total_credit_afg = sum(e.credit_afg for e in entries)
            total_debit_usd = sum(e.debit_usd for e in entries)
            total_credit_usd = sum(e.credit_usd for e in entries)
            
            balance_afg = total_debit_afg - total_credit_afg
            balance_usd = total_debit_usd - total_credit_usd
            
            return {
                'party_id': party_id,
                'total_debit_afg': total_debit_afg,
                'total_credit_afg': total_credit_afg,
                'balance_afg': balance_afg,
                'total_debit_usd': total_debit_usd,
                'total_credit_usd': total_credit_usd,
                'balance_usd': balance_usd,
                'entry_count': len(entries),
                'last_entry_date': entries[-1].date if entries else None
            }
        except Exception as e:
            logger.error(f"Error getting ledger summary: {e}")
            return None
    
    def get_all_parties_outstanding(self):
        """Get outstanding balances for all parties"""
        session = DatabaseManager.get_session()
        try:
            parties = session.query(Party).all()
            outstanding = []
            
            for party in parties:
                balance_afg = self.get_party_balance(party.id, "AFG")
                balance_usd = self.get_party_balance(party.id, "USD")
                
                if balance_afg != 0 or balance_usd != 0:
                    outstanding.append({
                        'party': party,
                        'balance_afg': balance_afg,
                        'balance_usd': balance_usd,
                        'status': 'Owes us' if balance_afg > 0 else 'We owe'
                    })
            
            return outstanding
        except Exception as e:
            logger.error(f"Error getting outstanding balances: {e}")
            return []
        finally:
            session.close()