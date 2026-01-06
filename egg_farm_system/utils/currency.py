"""
Currency utilities and conversion functions
"""
from egg_farm_system.config import BASE_CURRENCY, SECONDARY_CURRENCY, DEFAULT_EXCHANGE_RATE
from egg_farm_system.modules.settings import SettingsManager

class CurrencyConverter:
    """Handle currency conversions"""
    
    def __init__(self, exchange_rate=None):
        """
        Initialize converter with exchange rate.
        Default: 1 USD = 78 AFG
        If exchange_rate is None, loads from settings or uses default.
        """
        if exchange_rate is None:
            self.exchange_rate = self.get_exchange_rate()
        else:
            self.exchange_rate = exchange_rate
    
    def get_exchange_rate(self):
        """Get exchange rate from settings or return default"""
        try:
            rate_str = SettingsManager.get_setting('exchange_rate_afg_usd')
            if rate_str:
                return float(rate_str)
        except (ValueError, TypeError):
            pass
        return DEFAULT_EXCHANGE_RATE
    
    def afg_to_usd(self, amount_afg):
        """Convert AFG to USD"""
        if self.exchange_rate == 0:
            return 0
        return amount_afg / self.exchange_rate
    
    def usd_to_afg(self, amount_usd):
        """Convert USD to AFG"""
        return amount_usd * self.exchange_rate
    
    def set_exchange_rate(self, rate):
        """Update exchange rate and save to settings"""
        if rate > 0:
            self.exchange_rate = rate
            SettingsManager.set_setting(
                'exchange_rate_afg_usd', 
                str(rate),
                'Exchange rate: AFG per USD'
            )
        else:
            raise ValueError("Exchange rate must be positive")
    
    def format_amount(self, amount, currency="AFG", decimal_places=2):
        """Format amount with currency"""
        formatted = f"{amount:,.{decimal_places}f}"
        symbol = "Afs" if currency == "AFG" else "$"
        return f"{symbol} {formatted}"

def calculate_weighted_average_cost(transactions):
    """
    Calculate weighted average cost from list of transactions.
    Each transaction should have 'quantity' and 'unit_cost' keys.
    """
    if not transactions:
        return 0
    
    total_qty = sum(t['quantity'] for t in transactions)
    if total_qty == 0:
        return 0
    
    total_value = sum(t['quantity'] * t['unit_cost'] for t in transactions)
    return total_value / total_qty
