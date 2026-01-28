"""
Integration guide for using performance optimizations in existing modules

This file shows how to integrate the new optimization utilities into your
existing business logic modules.
"""

# ==============================================================================
# EXAMPLE 1: Reports Module Integration
# ==============================================================================

# BEFORE (Slow - causes N+1 queries and full table scans)
def get_sales_report_old(session, start_date, end_date):
    sales = session.query(Sale).filter(
        Sale.date >= start_date,
        Sale.date <= end_date
    ).all()
    
    result = []
    for sale in sales:
        party = session.query(Party).filter(Party.id == sale.party_id).first()  # N+1!
        result.append({
            'date': sale.date,
            'party': party.name,
            'quantity': sale.quantity,
            'total': sale.total_afg
        })
    return result


# AFTER (Fast - uses caching and eager loading)
from egg_farm_system.utils.advanced_caching import report_cache
from egg_farm_system.utils.query_optimizer import QueryOptimizer
from egg_farm_system.utils.performance_monitoring import measure_time

def get_sales_report_new(session, start_date, end_date):
    # Check cache first
    cache_key = f"sales_report_{start_date}_{end_date}"
    cached = report_cache.get_report("sales", {'start': start_date, 'end': end_date})
    if cached:
        return cached
    
    with measure_time("generate_sales_report"):
        # Use optimized query with eager loading
        sales = QueryOptimizer.get_sales_with_parties_optimized(
            session, start_date, end_date
        )
        
        result = [
            {
                'date': sale.date,
                'party': sale.party.name,  # No additional query!
                'quantity': sale.quantity,
                'total': sale.total_afg
            }
            for sale in sales
        ]
    
    # Cache the result
    report_cache.set_report("sales", {'start': start_date, 'end': end_date}, result)
    return result


# ==============================================================================
# EXAMPLE 2: Dashboard Widget Integration
# ==============================================================================

# BEFORE (Slow - queries run repeatedly)
class DashboardWidget:
    def refresh_data(self):
        session = DatabaseManager.get_session()
        try:
            # These queries run every time refresh_data is called
            total_eggs = sum(p.total_eggs for p in 
                           session.query(EggProduction).all())  # Full table scan!
            total_sales = session.query(func.sum(Sale.total_afg)).scalar() or 0
            total_expenses = session.query(func.sum(Expense.amount_afg)).scalar() or 0
        finally:
            session.close()


# AFTER (Fast - uses dashboard cache and aggregation)
from egg_farm_system.utils.advanced_caching import dashboard_cache
from egg_farm_system.utils.query_optimizer import AggregationHelper

class DashboardWidget:
    def refresh_data(self):
        # Check dashboard cache
        cached = dashboard_cache.get_daily_metrics(self.farm_id)
        if cached:
            self.update_ui(cached)
            return
        
        with measure_time("dashboard_refresh"):
            session = DatabaseManager.get_session()
            try:
                # Use database-level aggregation instead of Python loops
                agg = AggregationHelper.get_sales_summary(session, start_date, end_date)
                
                metrics = {
                    'total_eggs': agg.total_eggs,
                    'total_afg': agg.total_afg or 0,
                    'avg_rate': agg.avg_rate_afg or 0
                }
            finally:
                session.close()
        
        # Cache the metrics
        dashboard_cache.set_daily_metrics(self.farm_id, metrics)
        self.update_ui(metrics)


# ==============================================================================
# EXAMPLE 3: Party List Display Integration
# ==============================================================================

# BEFORE (Loads all parties in memory)
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

class PartyListWidget(QTableWidget):
    def load_parties(self):
        session = DatabaseManager.get_session()
        try:
            parties = session.query(Party).order_by(Party.name).all()  # Could be 100,000!
            
            self.setRowCount(len(parties))
            for row, party in enumerate(parties):
                self.setItem(row, 0, QTableWidgetItem(party.name))
                self.setItem(row, 1, QTableWidgetItem(party.phone or ''))
        finally:
            session.close()


# AFTER (Loads incrementally as user scrolls)
from egg_farm_system.utils.ui_performance import IncrementalDataLoader
from egg_farm_system.utils.advanced_caching import query_cache

class PartyListWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.loader = None
        
    def load_parties(self):
        # Define data source
        def fetch_parties(offset, limit):
            session = DatabaseManager.get_session()
            try:
                return session.query(Party).order_by(Party.name).offset(offset).limit(limit).all()
            finally:
                session.close()
        
        # Create incremental loader
        self.loader = IncrementalDataLoader(fetch_parties, initial_load=50, increment=25)
        
        # Load first batch
        parties = self.loader.load_initial()
        self.add_rows(parties)
        
        # Connect scroll event
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)
    
    def on_scroll(self):
        # Load more when user reaches bottom
        if self.loader and self.is_near_bottom():
            new_parties = self.loader.load_more()
            self.add_rows(new_parties)
    
    def add_rows(self, parties):
        for party in parties:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(party.name))
            self.setItem(row, 1, QTableWidgetItem(party.phone or ''))


# ==============================================================================
# EXAMPLE 4: Financial Report Integration
# ==============================================================================

# BEFORE (Slow - multiple queries, no caching)
from egg_farm_system.modules.financial_reports import FinancialReportGenerator

def generate_pnl_report(farm_id, start_date, end_date):
    session = DatabaseManager.get_session()
    try:
        generator = FinancialReportGenerator(session)
        return generator.generate_pnl_statement(start_date, end_date, farm_id)
    finally:
        session.close()


# AFTER (Fast - optimized queries and aggressive caching)
from egg_farm_system.utils.advanced_caching import report_cache, CacheInvalidationManager

@cache_result(ttl_seconds=1800)  # Cache for 30 minutes
def generate_pnl_report_optimized(farm_id, start_date, end_date):
    # Check cache first
    cached = report_cache.get_report("pnl", {
        'farm_id': farm_id,
        'start': start_date,
        'end': end_date
    })
    if cached:
        return cached
    
    with measure_time(f"pnl_report_{farm_id}"):
        session = DatabaseManager.get_session()
        try:
            generator = FinancialReportGenerator(session)
            pnl = generator.generate_pnl_statement(start_date, end_date, farm_id)
        finally:
            session.close()
    
    # Cache result
    report_cache.set_report("pnl", {
        'farm_id': farm_id,
        'start': start_date,
        'end': end_date
    }, pnl)
    
    return pnl


# Invalidate cache when expense is created
def record_expense_optimized(...):
    # ... existing expense recording code ...
    CacheInvalidationManager.on_expense_created()


# ==============================================================================
# EXAMPLE 5: Bulk Import Integration
# ==============================================================================

# BEFORE (Slow - inserts one by one)
def import_sales_data_old(sales_list):
    session = DatabaseManager.get_session()
    try:
        for sale_data in sales_list:
            sale = Sale(**sale_data)
            session.add(sale)
        session.commit()  # Commits all at once, but still slow
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


# AFTER (Fast - batch inserts)
from egg_farm_system.utils.query_optimizer import BulkQueryHelper

def import_sales_data_optimized(sales_list):
    session = DatabaseManager.get_session()
    try:
        # Convert to model objects
        sales = [Sale(**data) for data in sales_list]
        
        # Use bulk insert with batching
        BulkQueryHelper.bulk_insert(session, sales, batch_size=100)
        
        # Invalidate caches
        CacheInvalidationManager.on_sale_created()
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        raise
    finally:
        session.close()


# ==============================================================================
# EXAMPLE 6: Filtered Table View Integration
# ==============================================================================

# BEFORE (Filters in Python, slow for large datasets)
class SalesTableWidget(QTableWidget):
    def filter_by_party(self, party_name):
        session = DatabaseManager.get_session()
        try:
            # Loads all sales, filters in Python
            all_sales = session.query(Sale).all()  # Could be millions!
            filtered = [s for s in all_sales if party_name.lower() in s.party.name.lower()]
        finally:
            session.close()


# AFTER (Uses FilteredTableHelper with efficient filtering)
from egg_farm_system.utils.ui_performance import FilteredTableHelper

class SalesTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        
        def load_all_sales():
            session = DatabaseManager.get_session()
            try:
                return [
                    {
                        'id': s.id,
                        'date': s.date.strftime('%Y-%m-%d'),
                        'party': s.party.name,
                        'quantity': s.quantity,
                        'total': s.total_afg
                    }
                    for s in QueryOptimizer.get_sales_with_parties_optimized(session)
                ]
            finally:
                session.close()
        
        self.table = FilteredTableHelper(load_all_sales, filter_fields=['party', 'date'])
    
    def filter_by_party(self, party_name):
        self.table.set_filter('party', party_name)
        filtered_sales = self.table.get_filtered_data()
        self.display_rows(filtered_sales)


# ==============================================================================
# TIPS FOR INTEGRATION
# ==============================================================================

"""
1. Start with high-frequency operations
   - Dashboard refresh
   - Report generation
   - List views with pagination

2. Add caching conservatively
   - Start with 5-10 minute TTL
   - Adjust based on data update frequency
   - Invalidate cache when data changes

3. Use eager loading for relationships
   - Always check for N+1 query patterns
   - Use QueryOptimizer.get_*_optimized() methods
   - Profile before and after

4. Monitor performance improvements
   - Use @measure_time decorator
   - Check cache hit rates
   - Profile slow queries

5. Test cache invalidation
   - Ensure cache is cleared when data changes
   - Verify fresh data after invalidation
   - Monitor for stale data issues
"""
