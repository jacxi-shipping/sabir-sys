"""
Reports generation and export module with performance optimizations
"""
import csv
from datetime import datetime, timedelta
from io import StringIO
from sqlalchemy import func
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, Shed, EggProduction, FeedIssue, Sale, Purchase, 
    Expense, Payment, Party
)
from egg_farm_system.utils.calculations import EggCalculations, FeedCalculations, FinancialCalculations
from egg_farm_system.utils.advanced_caching import report_cache, CacheInvalidationManager
from egg_farm_system.utils.query_optimizer import QueryOptimizer, AggregationHelper
from egg_farm_system.utils.performance_monitoring import measure_time, profile_operation
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate various reports"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()

    def get_daily_production_summary(self, farm_id, days=30):
        """
        Get daily egg production summary for the last N days for the dashboard.
        Uses caching for better performance.
        """
        # Check cache first
        cache_key = f"{farm_id}_{days}_{datetime.utcnow().date()}"
        cached = report_cache.get_report("daily_production", {'farm_id': farm_id, 'days': days})
        if cached:
            return cached
        
        try:
            with measure_time(f"production_summary_farm_{farm_id}"):
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=days - 1)

                # Get all sheds for the farm using optimized query
                sheds = self.session.query(Shed).filter(Shed.farm_id == farm_id).all()
                shed_ids = [s.id for s in sheds]

                if not shed_ids:
                    return {'dates': [], 'egg_counts': []}

                # Use database aggregation for better performance
                daily_data = AggregationHelper.get_daily_production_aggregate(
                    self.session, farm_id, start_date, end_date
                )

                # Create a dictionary for quick lookup
                data_map = {r[0]: r[1] for r in daily_data}

                # Fill in dates with no production
                all_dates = [start_date + timedelta(days=i) for i in range(days)]
                egg_counts = [data_map.get(date, 0) for date in all_dates]
                
                result = {'dates': all_dates, 'egg_counts': egg_counts}
        
        except Exception as e:
            logger.error(f"Error getting daily production summary: {e}")
            result = {'dates': [], 'egg_counts': []}
        
        # Cache the result
        report_cache.set_report("daily_production", {'farm_id': farm_id, 'days': days}, result)
        return result
    
    def daily_egg_production_report(self, farm_id, date):
        """Generate daily egg production report"""
        try:
            from egg_farm_system.modules.farms import FarmManager
            fm = FarmManager()
            farm = fm.get_farm_by_id(farm_id)
            if not farm:
                return None
            
            from datetime import timedelta
            start_date = datetime.combine(date.date(), datetime.min.time())
            end_date = start_date + timedelta(days=1)
            
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_([s.id for s in farm.sheds]),
                EggProduction.date >= start_date,
                EggProduction.date < end_date
            ).all()
            
            report_data = {
                'farm': farm.name,
                'date': date,
                'sheds': []
            }
            
            total_small = 0
            total_medium = 0
            total_large = 0
            total_broken = 0
            
            for shed in farm.sheds:
                shed_productions = [p for p in productions if p.shed_id == shed.id]
                shed_total = sum(p.total_eggs for p in shed_productions)
                shed_usable = sum(p.usable_eggs for p in shed_productions)
                
                total_small += sum(p.small_count for p in shed_productions)
                total_medium += sum(p.medium_count for p in shed_productions)
                total_large += sum(p.large_count for p in shed_productions)
                total_broken += sum(p.broken_count for p in shed_productions)
                
                report_data['sheds'].append({
                    'name': shed.name,
                    'total_eggs': shed_total,
                    'usable_eggs': shed_usable,
                    'small': sum(p.small_count for p in shed_productions),
                    'medium': sum(p.medium_count for p in shed_productions),
                    'large': sum(p.large_count for p in shed_productions),
                    'broken': sum(p.broken_count for p in shed_productions)
                })
            
            report_data['totals'] = {
                'small': total_small,
                'medium': total_medium,
                'large': total_large,
                'broken': total_broken,
                'total': total_small + total_medium + total_large + total_broken,
                'usable': total_small + total_medium + total_large
            }
            
            return report_data
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return None
    
    def monthly_egg_production_report(self, farm_id, year, month):
        """Generate monthly egg production report"""
        try:
            from egg_farm_system.modules.farms import FarmManager
            from datetime import date, timedelta
            
            fm = FarmManager()
            farm = fm.get_farm_by_id(farm_id)
            if not farm:
                return None
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_([s.id for s in farm.sheds]),
                EggProduction.date >= start_date,
                EggProduction.date < end_date
            ).all()
            
            daily_summary = {}
            for prod in productions:
                prod_date = prod.date.date()
                if prod_date not in daily_summary:
                    daily_summary[prod_date] = {
                        'total': 0, 'usable': 0, 'small': 0, 
                        'medium': 0, 'large': 0, 'broken': 0
                    }
                
                daily_summary[prod_date]['total'] += prod.total_eggs
                daily_summary[prod_date]['usable'] += prod.usable_eggs
                daily_summary[prod_date]['small'] += prod.small_count
                daily_summary[prod_date]['medium'] += prod.medium_count
                daily_summary[prod_date]['large'] += prod.large_count
                daily_summary[prod_date]['broken'] += prod.broken_count
            
            return {
                'farm': farm.name,
                'year': year,
                'month': month,
                'daily_summary': daily_summary
            }
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return None
    
    def feed_usage_report(self, farm_id, start_date, end_date):
        """Generate feed usage report"""
        try:
            from egg_farm_system.modules.farms import FarmManager
            fm = FarmManager()
            farm = fm.get_farm_by_id(farm_id)
            if not farm:
                return None
            
            feed_issues = self.session.query(FeedIssue).filter(
                FeedIssue.shed_id.in_([s.id for s in farm.sheds]),
                FeedIssue.date >= start_date,
                FeedIssue.date <= end_date
            ).all()
            
            report_data = {
                'farm': farm.name,
                'start_date': start_date,
                'end_date': end_date,
                'sheds': {}
            }
            
            for shed in farm.sheds:
                shed_issues = [f for f in feed_issues if f.shed_id == shed.id]
                issue_count = len(shed_issues)
                total_kg = sum(f.quantity_kg for f in shed_issues)
                
                # Determine predominant feed type if any
                feed_types = [f.feed.feed_type.value for f in shed_issues if f.feed]
                feed_type_str = max(set(feed_types), key=feed_types.count) if feed_types else "N/A"
                if len(set(feed_types)) > 1:
                    feed_type_str += " (Mixed)"

                report_data['sheds'][shed.name] = {
                    'total_kg': total_kg,
                    'total_cost_afg': sum(f.cost_afg for f in shed_issues),
                    'total_cost_usd': sum(f.cost_usd for f in shed_issues),
                    'issue_count': issue_count,
                    'avg_per_issue': total_kg / issue_count if issue_count > 0 else 0,
                    'feed_type': feed_type_str,
                    'daily_average': total_kg / max(len(set(f.date.date() for f in shed_issues)), 1)
                }
            
            return report_data
        except Exception as e:
            logger.error(f"Error generating feed usage report: {e}")
            return None
    
    def party_statement(self, party_id, start_date=None, end_date=None):
        """Generate party statement"""
        try:
            from egg_farm_system.modules.parties import PartyManager
            pm = PartyManager()
            party = pm.get_party_by_id(party_id)
            if not party:
                return None
            
            ledger_entries = party.ledger_entries
            if start_date:
                ledger_entries = [e for e in ledger_entries if e.date >= start_date]
            if end_date:
                ledger_entries = [e for e in ledger_entries if e.date <= end_date]
            
            ledger_entries = sorted(ledger_entries, key=lambda x: x.date)
            
            running_balance_afg = 0
            running_balance_usd = 0
            entries_with_balance = []
            
            for entry in ledger_entries:
                running_balance_afg += (entry.debit_afg - entry.credit_afg)
                running_balance_usd += (entry.debit_usd - entry.credit_usd)
                
                entries_with_balance.append({
                    'date': entry.date,
                    'description': entry.description,
                    'debit_afg': entry.debit_afg,
                    'credit_afg': entry.credit_afg,
                    'debit_usd': entry.debit_usd,
                    'credit_usd': entry.credit_usd,
                    'balance_afg': running_balance_afg,
                    'balance_usd': running_balance_usd
                })
            
            return {
                'party': party.name,
                'entries': entries_with_balance,
                'final_balance_afg': running_balance_afg,
                'final_balance_usd': running_balance_usd
            }
        except Exception as e:
            logger.error(f"Error generating party statement: {e}")
            return None
    
    def export_to_csv(self, data, report_name):
        """Export report data to CSV"""
        try:
            output = StringIO()
            
            if report_name == "daily_production":
                writer = csv.writer(output)
                writer.writerow(['Farm', data['farm']])
                writer.writerow(['Date', data['date']])
                writer.writerow([])
                writer.writerow(['Shed', 'Small', 'Medium', 'Large', 'Broken', 'Total', 'Usable'])
                
                for shed in data['sheds']:
                    writer.writerow([
                        shed['name'],
                        shed['small'],
                        shed['medium'],
                        shed['large'],
                        shed['broken'],
                        shed['total_eggs'],
                        shed['usable_eggs']
                    ])
                
                writer.writerow([])
                writer.writerow(['Total', 
                    data['totals']['small'],
                    data['totals']['medium'],
                    data['totals']['large'],
                    data['totals']['broken'],
                    data['totals']['total'],
                    data['totals']['usable']
                ])
            
            elif report_name == "feed_usage":
                writer = csv.writer(output)
                writer.writerow(['Farm', data['farm']])
                writer.writerow(['Period', f"{data['start_date']} to {data['end_date']}"])
                writer.writerow([])
                writer.writerow(['Shed', 'Total (kg)', 'Cost (AFG)', 'Cost (USD)', 'Daily Avg'])
                
                for shed_name, shed_data in data['sheds'].items():
                    writer.writerow([
                        shed_name,
                        shed_data['total_kg'],
                        shed_data['total_cost_afg'],
                        shed_data['total_cost_usd'],
                        shed_data['daily_average']
                    ])
            
            elif report_name == "party_statement":
                writer = csv.writer(output)
                writer.writerow(['Party', data['party']])
                writer.writerow([])
                writer.writerow(['Date', 'Description', 'Debit AFG', 'Credit AFG', 'Balance AFG', 
                                'Debit USD', 'Credit USD', 'Balance USD'])
                
                for entry in data['entries']:
                    writer.writerow([
                        entry['date'],
                        entry['description'],
                        entry['debit_afg'],
                        entry['credit_afg'],
                        entry['balance_afg'],
                        entry['debit_usd'],
                        entry['credit_usd'],
                        entry['balance_usd']
                    ])
                
                writer.writerow([])
                writer.writerow(['Final Balance AFG', data['final_balance_afg']])
                writer.writerow(['Final Balance USD', data['final_balance_usd']])
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()