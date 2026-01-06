"""
Calculation utilities for egg farm system
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from egg_farm_system.database.models import Flock, FeedIssue, EggProduction, Mortality


class EggCalculations:
    """Egg production calculations"""
    
    @staticmethod
    def egg_production_percentage(total_eggs, live_bird_count, days=1):
        """Calculate egg production percentage"""
        if live_bird_count == 0 or days == 0:
            return 0
        return (total_eggs / (live_bird_count * days)) * 100
    
    @staticmethod
    def eggs_per_bird(total_eggs, live_bird_count):
        """Calculate eggs per bird"""
        if live_bird_count == 0:
            return 0
        return total_eggs / live_bird_count
    
    @staticmethod
    def usable_egg_percentage(usable_eggs, total_eggs):
        """Calculate percentage of usable eggs"""
        if total_eggs == 0:
            return 0
        return (usable_eggs / total_eggs) * 100

    @staticmethod
    def calculate_production_forecast(history_data, days_to_forecast=7):
        """
        Predict future production using simple linear regression (Least Squares).
        history_data: List of (day_index, value) tuples or just list of values.
        Returns: List of predicted values for the next 'days_to_forecast' days.
        """
        if not history_data or len(history_data) < 2:
            return []

        # If data is just values, convert to (index, value)
        if isinstance(history_data[0], (int, float)):
            data = list(enumerate(history_data))
        else:
            data = history_data

        n = len(data)
        sum_x = sum(d[0] for d in data)
        sum_y = sum(d[1] for d in data)
        sum_xy = sum(d[0] * d[1] for d in data)
        sum_xx = sum(d[0] ** 2 for d in data)

        # Calculate slope (m) and intercept (c) for y = mx + c
        # Denominator check to avoid division by zero
        denom = (n * sum_xx - sum_x ** 2)
        if denom == 0:
            return [sum_y / n] * days_to_forecast # Return average if slope is undefined

        m = (n * sum_xy - sum_x * sum_y) / denom
        c = (sum_y - m * sum_x) / n

        # Generate predictions
        last_x = data[-1][0]
        predictions = []
        for i in range(1, days_to_forecast + 1):
            next_x = last_x + i
            pred_y = m * next_x + c
            predictions.append(max(0, pred_y)) # Ensure no negative production
            
        return predictions

    @staticmethod
    def calculate_hdp_for_flock(session, flock_id, start_date, end_date):
        """
        Calculates the Hen-Day Production % for a specific flock over a given period.
        """
        flock = session.query(Flock).filter(Flock.id == flock_id).first()
        if not flock:
            return 0, 0, 0

        shed_id = flock.shed_id
        
        # Get total eggs produced
        total_eggs = session.query(func.sum(
            EggProduction.small_count + EggProduction.medium_count + EggProduction.large_count + EggProduction.broken_count
        )).filter(
            EggProduction.shed_id == shed_id,
            EggProduction.date >= start_date,
            EggProduction.date <= end_date
        ).scalar() or 0

        # Calculate average live bird count for the period
        num_days = (end_date - start_date).days + 1
        total_bird_days = 0
        current_date = start_date
        while current_date <= end_date:
            total_bird_days += flock.get_live_count(as_of_date=current_date)
            current_date += timedelta(days=1)
        
        avg_live_birds = total_bird_days / num_days if num_days > 0 else 0

        hdp = EggCalculations.egg_production_percentage(total_eggs, avg_live_birds, num_days)
        
        return hdp, total_eggs, avg_live_birds


class FeedCalculations:
    """Feed-related calculations"""
    
    @staticmethod
    def cost_per_egg(total_feed_cost, total_eggs):
        """Calculate feed cost per egg"""
        if total_eggs == 0:
            return 0
        return total_feed_cost / total_eggs
    
    @staticmethod
    def feed_efficiency_ratio(total_feed_kg, total_eggs):
        """Calculate feed efficiency (kg feed per 1000 eggs)"""
        if total_eggs == 0:
            return 0
        return (total_feed_kg / total_eggs) * 1000

    @staticmethod
    def feed_conversion_ratio_per_dozen(total_feed_kg, total_eggs):
        """Calculate feed conversion ratio (kg feed per dozen eggs)"""
        if total_eggs == 0:
            return 0
        dozens = total_eggs / 12
        if dozens == 0:
            return 0
        return total_feed_kg / dozens
    
    @staticmethod
    def daily_feed_requirement(live_bird_count, daily_consumption_per_bird_kg=0.12):
        """Calculate daily feed requirement"""
        return live_bird_count * daily_consumption_per_bird_kg

    @staticmethod
    def calculate_fcr_for_flock(session, flock_id, start_date, end_date):
        """
        Calculates the Feed Conversion Ratio for a specific flock over a given period.
        """
        flock = session.query(Flock).filter(Flock.id == flock_id).first()
        if not flock:
            return 0, 0, 0

        shed_id = flock.shed_id

        # Get total feed issued
        total_feed_kg = session.query(func.sum(FeedIssue.quantity_kg)).filter(
            FeedIssue.shed_id == shed_id,
            FeedIssue.date >= start_date,
            FeedIssue.date <= end_date
        ).scalar() or 0

        # Get total eggs produced
        total_eggs_query = session.query(
            func.sum(EggProduction.small_count + EggProduction.medium_count + EggProduction.large_count + EggProduction.broken_count)
        ).filter(
            EggProduction.shed_id == shed_id,
            EggProduction.date >= start_date,
            EggProduction.date <= end_date
        )
        total_eggs = total_eggs_query.scalar() or 0
        
        fcr = FeedCalculations.feed_conversion_ratio_per_dozen(total_feed_kg, total_eggs)
        
        return fcr, total_feed_kg, total_eggs


class FinancialCalculations:
    """Financial calculations"""
    
    @staticmethod
    def calculate_profit(revenue, expenses):
        """Calculate profit"""
        return revenue - expenses
    
    @staticmethod
    def calculate_profit_percentage(profit, revenue):
        """Calculate profit percentage"""
        if revenue == 0:
            return 0
        return (profit / revenue) * 100
    
    @staticmethod
    def calculate_margin(profit, revenue):
        """Calculate profit margin"""
        if revenue == 0:
            return 0
        return (profit / revenue) * 100
    
    @staticmethod
    def weighted_average_cost(purchases):
        """
        Calculate weighted average cost from purchases.
        purchases: list of dicts with 'quantity' and 'unit_cost'
        """
        if not purchases:
            return 0
        
        total_qty = sum(p['quantity'] for p in purchases)
        if total_qty == 0:
            return 0
        
        total_cost = sum(p['quantity'] * p['unit_cost'] for p in purchases)
        return total_cost / total_qty


class MortalityCalculations:
    """Mortality and bird count calculations"""
    
    @staticmethod
    def live_bird_count(initial_count, cumulative_mortality):
        """Calculate live bird count"""
        return max(0, initial_count - cumulative_mortality)
    
    @staticmethod
    def mortality_percentage(initial_count, cumulative_mortality):
        """Calculate mortality percentage"""
        if initial_count == 0:
            return 0
        return (cumulative_mortality / initial_count) * 100
    
    @staticmethod
    def flock_age_days(start_date, end_date=None):
        """Calculate flock age in days"""
        if end_date is None:
            end_date = datetime.utcnow()
        return (end_date - start_date).days
    
    @staticmethod
    def flock_age_weeks(start_date, end_date=None):
        """Calculate flock age in weeks"""
        days = MortalityCalculations.flock_age_days(start_date, end_date)
        return days / 7

    @staticmethod
    def calculate_mortality_rate_for_period(session, flock_id, start_date, end_date):
        """
        Calculates the mortality rate for a specific flock over a given period.
        """
        flock = session.query(Flock).filter(Flock.id == flock_id).first()
        if not flock:
            return 0, 0, 0

        # Get live bird count at the beginning of the period
        bird_count_start = flock.get_live_count(as_of_date=start_date)

        # Get number of deaths during the period
        deaths_in_period = session.query(func.sum(Mortality.count)).filter(
            Mortality.flock_id == flock_id,
            Mortality.date >= start_date,
            Mortality.date <= end_date
        ).scalar() or 0

        if bird_count_start == 0:
            return 0, deaths_in_period, bird_count_start

        mortality_rate = (deaths_in_period / bird_count_start) * 100
        
        return mortality_rate, deaths_in_period, bird_count_start


class InventoryCalculations:
    """Inventory valuation and calculations"""
    
    @staticmethod
    def inventory_value(quantity, unit_cost):
        """Calculate inventory value"""
        return quantity * unit_cost
    
    @staticmethod
    def average_cost_method(opening_stock, opening_cost, purchases):
        """
        Calculate average cost using weighted average method.
        Returns: average cost per unit
        """
        total_qty = opening_stock + sum(p['quantity'] for p in purchases)
        if total_qty == 0:
            return 0
        
        total_cost = (opening_stock * opening_cost) + sum(p['quantity'] * p['unit_cost'] for p in purchases)
        return total_cost / total_qty

