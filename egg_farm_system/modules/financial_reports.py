"""
Module for generating financial reports.
"""
from sqlalchemy import func
from egg_farm_system.database.models import (
    Sale, Expense, FeedIssue, Payment, Purchase, Shed, RawMaterial, FinishedFeed, FeedFormula
)
from egg_farm_system.utils.advanced_caching import report_cache, CacheInvalidationManager
from egg_farm_system.utils.query_optimizer import AggregationHelper
from egg_farm_system.utils.performance_monitoring import measure_time
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

    def generate_pnl_statement(self, start_date, end_date, farm_id=None):
        """
        Generates a Profit and Loss (P&L) statement for a given period.
        Uses caching for financial reports (30-minute TTL).
        """
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
                Sale.date <= end_date
            )
            # TODO: Add farm_id filtering for sales if possible
            total_revenue = revenue_query.scalar() or 0

            # 2. Calculate Cost of Goods Sold (COGS) - primarily feed cost for now
            cogs_query = self.session.query(func.sum(FeedIssue.cost_afg)).join(FeedIssue.shed).filter(
                FeedIssue.date >= start_date,
                FeedIssue.date <= end_date
            )
            if farm_id:
                cogs_query = cogs_query.filter(Shed.farm_id == farm_id)
            total_cogs = cogs_query.scalar() or 0
            
            # 3. Calculate Gross Profit
            gross_profit = total_revenue - total_cogs

            # 4. Calculate Operating Expenses
            expenses_query = self.session.query(func.sum(Expense.amount_afg)).filter(
                Expense.date >= start_date,
                Expense.date <= end_date
            )
            if farm_id:
                expenses_query = expenses_query.filter(Expense.farm_id == farm_id)
            total_expenses = expenses_query.scalar() or 0

            # 5. Calculate Net Profit
            net_profit = gross_profit - total_expenses

            pnl_data = {
                "start_date": start_date,
                "end_date": end_date,
                "farm_id": farm_id,
                "total_revenue": total_revenue,
                "total_cogs": total_cogs,
                "gross_profit": gross_profit,
                "total_expenses": total_expenses,
                "net_profit": net_profit
            }
            
            # Cache the report for 30 minutes
            report_cache.set_report("pnl", {'farm_id': farm_id, 'start': start_date, 'end': end_date}, pnl_data, ttl=1800)
            return pnl_data

    def generate_cash_flow_statement(self, start_date, end_date, farm_id=None):
        """
        Generates a Cash Flow statement for a given period.
        """

        # --- Cash Inflows ---
        sales_inflow = self.session.query(func.sum(Sale.total_afg)).filter(
            Sale.date >= start_date, Sale.date <= end_date
        ).scalar() or 0
        
        payments_received = self.session.query(func.sum(Payment.amount_afg)).filter(
            Payment.date >= start_date, Payment.date <= end_date,
            Payment.payment_type == 'Received'
        ).scalar() or 0

        total_inflows = sales_inflow + payments_received

        # --- Cash Outflows ---
        purchases_outflow = self.session.query(func.sum(Purchase.total_afg)).filter(
            Purchase.date >= start_date, Purchase.date <= end_date
        ).scalar() or 0

        expenses_outflow_query = self.session.query(func.sum(Expense.amount_afg)).filter(
            Expense.date >= start_date, Expense.date <= end_date
        )
        if farm_id:
            expenses_outflow_query = expenses_outflow_query.filter(Expense.farm_id == farm_id)
        expenses_outflow = expenses_outflow_query.scalar() or 0

        payments_paid = self.session.query(func.sum(Payment.amount_afg)).filter(
            Payment.date >= start_date, Payment.date <= end_date,
            Payment.payment_type == 'Paid'
        ).scalar() or 0
        
        total_outflows = purchases_outflow + expenses_outflow + payments_paid

        # --- Net Cash Flow ---
        net_cash_flow = total_inflows - total_outflows

        cash_flow_data = {
            "start_date": start_date,
            "end_date": end_date,
            "farm_id": farm_id,
            "total_inflows": total_inflows,
            "inflows_from_sales": sales_inflow,
            "inflows_from_payments": payments_received,
            "total_outflows": total_outflows,
            "outflows_for_purchases": purchases_outflow,
            "outflows_for_expenses": expenses_outflow,
            "outflows_for_payments": payments_paid,
            "net_cash_flow": net_cash_flow
        }
        return cash_flow_data
