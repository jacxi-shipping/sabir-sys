"""
Module for generating financial reports.
"""
from datetime import datetime, time
from sqlalchemy import func
from egg_farm_system.database.models import (
    Sale, Expense, FeedIssue, Payment, Purchase, Shed, RawMaterial, FinishedFeed, FeedFormula
)
from egg_farm_system.utils.advanced_caching import report_cache, CacheInvalidationManager
from egg_farm_system.utils.query_optimizer import AggregationHelper
from egg_farm_system.utils.performance_monitoring import measure_time
from egg_farm_system.utils.currency import CurrencyConverter
import logging

logger = logging.getLogger(__name__)

class FinancialReportGenerator:
    """
    Generates financial reports (P&L, Cash Flow).
    
    Note: This class does NOT manage the session lifecycle. The caller is responsible
    for creating and closing the session. The session should remain open for the
    lifetime of this generator instance.
    
    Example:
        session = DatabaseManager.get_session()
        try:
            generator = FinancialReportGenerator(session)
            pnl = generator.generate_pnl_statement(start_date, end_date)
        finally:
            session.close()
    """

    def __init__(self, session):
        """
        Initialize the report generator with a database session.
        
        Args:
            session: SQLAlchemy database session (caller must close it)
        """
        self.session = session
        self.currency_converter = CurrencyConverter()

    def _ensure_end_of_day(self, date_obj):
        """Helper to ensure end date includes the whole day"""
        if isinstance(date_obj, datetime):
            return date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        return datetime.combine(date_obj, time.max)

    def generate_pnl_statement(self, start_date, end_date, farm_id=None):
        """
        Generates a Profit and Loss (P&L) statement for a given period.
        Uses caching for financial reports (30-minute TTL).
        """
        # Ensure end_date includes the full day
        query_end_date = self._ensure_end_of_day(end_date)
        
        with measure_time(f"pnl_statement_{farm_id}_{start_date}_{end_date}"):
            # Check cache first
            cache_key = f"pnl_{farm_id}_{start_date}_{end_date}"
            cached = report_cache.get_report("pnl", {'farm_id': farm_id, 'start': start_date, 'end': end_date})
            if cached is not None:
                logger.info(f"PnL report cache hit for farm {farm_id}")
                return cached
            
            # 1. Calculate Total Revenue from Sales
            revenue_query = self.session.query(func.sum(Sale.total_afg)).filter(
                Sale.date >= start_date,
                Sale.date <= query_end_date
            )
            # Note: Sales are currently global and linked to Parties, not specific Farms/Sheds.
            # Farm-specific revenue filtering is not possible without schema changes.
            total_revenue = revenue_query.scalar() or 0

            # 2. Calculate Cost of Goods Sold (COGS) - primarily feed cost for now
            cogs_query = self.session.query(func.sum(FeedIssue.cost_afg)).join(FeedIssue.shed).filter(
                FeedIssue.date >= start_date,
                FeedIssue.date <= query_end_date
            )
            if farm_id:
                cogs_query = cogs_query.filter(Shed.farm_id == farm_id)
            total_cogs = cogs_query.scalar() or 0
            
            # 3. Calculate Gross Profit
            gross_profit = total_revenue - total_cogs

            # 4. Calculate Operating Expenses
            expenses_query = self.session.query(func.sum(Expense.amount_afg)).filter(
                Expense.date >= start_date,
                Expense.date <= query_end_date
            )
            if farm_id:
                expenses_query = expenses_query.filter(Expense.farm_id == farm_id)
            total_expenses = expenses_query.scalar() or 0

            # 5. Calculate Net Profit
            net_profit = gross_profit - total_expenses

            # Convert all amounts to USD
            total_revenue_usd = self.currency_converter.afg_to_usd(total_revenue)
            total_cogs_usd = self.currency_converter.afg_to_usd(total_cogs)
            gross_profit_usd = self.currency_converter.afg_to_usd(gross_profit)
            total_expenses_usd = self.currency_converter.afg_to_usd(total_expenses)
            net_profit_usd = self.currency_converter.afg_to_usd(net_profit)

            pnl_data = {
                "start_date": start_date,
                "end_date": end_date,
                "farm_id": farm_id,
                "total_revenue": total_revenue,
                "total_revenue_usd": total_revenue_usd,
                "total_cogs": total_cogs,
                "total_cogs_usd": total_cogs_usd,
                "gross_profit": gross_profit,
                "gross_profit_usd": gross_profit_usd,
                "total_expenses": total_expenses,
                "total_expenses_usd": total_expenses_usd,
                "net_profit": net_profit,
                "net_profit_usd": net_profit_usd
            }
            
            # Cache the report for 30 minutes
            report_cache.set_report("pnl", {'farm_id': farm_id, 'start': start_date, 'end': end_date}, pnl_data, ttl=1800)
            return pnl_data

    def generate_cash_flow_statement(self, start_date, end_date, farm_id=None):
        """
        Generates a Cash Flow statement for a given period.
        Note: This statement focuses on actual cash movements (Payments and Direct Expenses).
        Sales and Purchases are treated as Accrual (Ledger) events and are NOT included in cash flow
        until a Payment is recorded.
        """
        # Ensure end_date includes the full day
        query_end_date = self._ensure_end_of_day(end_date)

        # --- Cash Inflows ---
        # Only Payments Received (Cash Sales should have a corresponding Payment record)
        # Sales records themselves are Accrual (AR).
        payments_received = self.session.query(func.sum(Payment.amount_afg)).filter(
            Payment.date >= start_date, Payment.date <= query_end_date,
            Payment.payment_type == 'Received'
        ).scalar() or 0

        total_inflows = payments_received

        # --- Cash Outflows ---
        # 1. Payments Paid (for Credit Purchases/Expenses)
        payments_paid = self.session.query(func.sum(Payment.amount_afg)).filter(
            Payment.date >= start_date, Payment.date <= query_end_date,
            Payment.payment_type == 'Paid'
        ).scalar() or 0
        
        # 2. Direct Cash Expenses (Expenses without a Party linked)
        # If an Expense has a Party, it's a Credit Expense (Liability) -> Paid via Payment later.
        # If an Expense has NO Party, it's assumed to be paid Cash immediately.
        direct_cash_expenses_query = self.session.query(func.sum(Expense.amount_afg)).filter(
            Expense.date >= start_date, 
            Expense.date <= query_end_date,
            Expense.party_id == None 
        )
        if farm_id:
            direct_cash_expenses_query = direct_cash_expenses_query.filter(Expense.farm_id == farm_id)
        direct_cash_expenses = direct_cash_expenses_query.scalar() or 0
        
        total_outflows = payments_paid + direct_cash_expenses

        # --- Net Cash Flow ---
        net_cash_flow = total_inflows - total_outflows

        # Convert all amounts to USD
        total_inflows_usd = self.currency_converter.afg_to_usd(total_inflows)
        payments_received_usd = self.currency_converter.afg_to_usd(payments_received)
        total_outflows_usd = self.currency_converter.afg_to_usd(total_outflows)
        direct_cash_expenses_usd = self.currency_converter.afg_to_usd(direct_cash_expenses)
        payments_paid_usd = self.currency_converter.afg_to_usd(payments_paid)
        net_cash_flow_usd = self.currency_converter.afg_to_usd(net_cash_flow)

        cash_flow_data = {
            "start_date": start_date,
            "end_date": end_date,
            "farm_id": farm_id,
            "total_inflows": total_inflows,
            "total_inflows_usd": total_inflows_usd,
            "inflows_from_sales": 0, # Removed as sales are accrual
            "inflows_from_payments": payments_received,
            "inflows_from_payments_usd": payments_received_usd,
            "total_outflows": total_outflows,
            "total_outflows_usd": total_outflows_usd,
            "outflows_for_purchases": 0, # Removed as purchases are accrual
            "outflows_for_expenses": direct_cash_expenses,
            "outflows_for_expenses_usd": direct_cash_expenses_usd,
            "outflows_for_payments": payments_paid,
            "outflows_for_payments_usd": payments_paid_usd,
            "net_cash_flow": net_cash_flow,
            "net_cash_flow_usd": net_cash_flow_usd
        }
        return cash_flow_data
