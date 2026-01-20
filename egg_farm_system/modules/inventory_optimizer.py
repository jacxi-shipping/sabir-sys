"""
Inventory Optimization Module
Provides advanced inventory management with EOQ, demand forecasting, and optimization algorithms
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from scipy import optimize
import math
import logging

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, RawMaterial, FinishedFeed, Purchase, Sale, FeedIssue, EggProduction
)
from egg_farm_system.utils.performance_monitoring import measure_time

logger = logging.getLogger(__name__)

class InventoryOptimizer:
    """Advanced inventory optimization engine"""
    
    def __init__(self, session=None):
        self._owned_session = False
        if session:
            self.session = session
        else:
            self.session = DatabaseManager.get_session()
            self._owned_session = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()
    
    def close_session(self):
        """Close database session if owned"""
        if self._owned_session and self.session:
            self.session.close()
    
    @measure_time("demand_forecast")
    def forecast_demand(self, item_id: int, item_type: str, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Forecast demand for inventory items using multiple methods
        """
        try:
            # Get historical consumption data
            historical_data = self._get_historical_consumption(item_id, item_type, days=90)
            
            if len(historical_data) < 10:
                return {
                    "error": "Insufficient historical data for demand forecasting",
                    "item_id": item_id,
                    "item_type": item_type
                }
            
            # Generate forecasts using different methods
            forecasts = {}
            
            # Simple moving average forecast
            forecasts['moving_average'] = self._moving_average_forecast(historical_data, days_ahead)
            
            # Exponential smoothing forecast
            forecasts['exponential_smoothing'] = self._exponential_smoothing_forecast(historical_data, days_ahead)
            
            # Linear trend forecast
            forecasts['linear_trend'] = self._linear_trend_forecast(historical_data, days_ahead)
            
            # Seasonal forecast (if sufficient data)
            if len(historical_data) >= 30:
                forecasts['seasonal'] = self._seasonal_forecast(historical_data, days_ahead)
            
            # Ensemble forecast
            ensemble_forecast = self._create_ensemble_forecast(forecasts)
            
            # Calculate forecast accuracy metrics
            accuracy_metrics = self._calculate_forecast_accuracy(historical_data, forecasts)
            
            # Demand variability analysis
            variability_analysis = self._analyze_demand_variability(historical_data)
            
            return {
                "item_id": item_id,
                "item_type": item_type,
                "forecast_period": f"{days_ahead} days ahead",
                "historical_period": f"{len(historical_data)} days",
                "individual_forecasts": forecasts,
                "ensemble_forecast": ensemble_forecast,
                "accuracy_metrics": accuracy_metrics,
                "variability_analysis": variability_analysis,
                "recommendations": self._generate_demand_recommendations(forecasts, variability_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in demand forecasting: {e}")
            return {"error": f"Demand forecasting failed: {str(e)}"}
    
    def _get_historical_consumption(self, item_id: int, item_type: str, days: int = 90) -> List[Dict]:
        """Get historical consumption data for an item"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            consumption_data = []
            
            if item_type == 'raw_material':
                # Get consumption from purchases (negative inventory movements)
                purchases = self.session.query(Purchase).filter(
                    Purchase.date >= start_date,
                    Purchase.date <= end_date
                ).all()
                
                # Group by date and sum consumption
                daily_consumption = {}
                for purchase in purchases:
                    date_key = purchase.date.date()
                    if date_key not in daily_consumption:
                        daily_consumption[date_key] = 0
                    daily_consumption[date_key] += purchase.quantity
                
                # Convert to list format
                for date, consumption in daily_consumption.items():
                    consumption_data.append({
                        'date': date,
                        'consumption': consumption
                    })
            
            elif item_type == 'finished_feed':
                # Get consumption from feed issues
                feed_issues = self.session.query(FeedIssue).filter(
                    FeedIssue.date >= start_date,
                    FeedIssue.date <= end_date
                ).all()
                
                daily_consumption = {}
                for issue in feed_issues:
                    date_key = issue.date.date()
                    if date_key not in daily_consumption:
                        daily_consumption[date_key] = 0
                    daily_consumption[date_key] += issue.quantity_kg
                
                for date, consumption in daily_consumption.items():
                    consumption_data.append({
                        'date': date,
                        'consumption': consumption
                    })
            
            elif item_type == 'egg_inventory':
                # Get egg production data
                productions = self.session.query(EggProduction).filter(
                    EggProduction.date >= start_date,
                    EggProduction.date <= end_date
                ).all()
                
                daily_consumption = {}
                for prod in productions:
                    date_key = prod.date.date()
                    if date_key not in daily_consumption:
                        daily_consumption[date_key] = 0
                    daily_consumption[date_key] += prod.usable_eggs
                
                for date, consumption in daily_consumption.items():
                    consumption_data.append({
                        'date': date,
                        'consumption': consumption
                    })
            
            # Sort by date
            consumption_data.sort(key=lambda x: x['date'])
            
            return consumption_data
            
        except Exception as e:
            logger.error(f"Error getting historical consumption: {e}")
            return []
    
    def _moving_average_forecast(self, historical_data: List[Dict], periods_ahead: int) -> Dict:
        """Generate moving average forecast"""
        try:
            if len(historical_data) < 7:
                return {"error": "Insufficient data for moving average"}
            
            # Calculate different moving averages
            ma_7 = np.mean([d['consumption'] for d in historical_data[-7:]])
            ma_14 = np.mean([d['consumption'] for d in historical_data[-14:]]) if len(historical_data) >= 14 else ma_7
            ma_30 = np.mean([d['consumption'] for d in historical_data[-30:]]) if len(historical_data) >= 30 else ma_14
            
            # Use weighted average of moving averages
            weights = [0.5, 0.3, 0.2]  # More weight on recent periods
            forecasts = []
            
            for i in range(1, periods_ahead + 1):
                predicted = (weights[0] * ma_7 + weights[1] * ma_14 + weights[2] * ma_30)
                
                forecasts.append({
                    'period': i,
                    'date': (datetime.utcnow().date() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'predicted_consumption': round(predicted),
                    'confidence': 'medium'
                })
            
            return {
                "method": "Moving Average",
                "forecasts": forecasts,
                "ma_7": round(ma_7, 2),
                "ma_14": round(ma_14, 2),
                "ma_30": round(ma_30, 2)
            }
            
        except Exception as e:
            logger.error(f"Error in moving average forecast: {e}")
            return {"error": "Moving average forecast failed"}
    
    def _exponential_smoothing_forecast(self, historical_data: List[Dict], periods_ahead: int) -> Dict:
        """Generate exponential smoothing forecast"""
        try:
            if len(historical_data) < 5:
                return {"error": "Insufficient data for exponential smoothing"}
            
            # Simple exponential smoothing
            alpha = 0.3  # Smoothing parameter
            forecasts = []
            
            # Calculate smoothed values
            smoothed_values = []
            current_smooth = historical_data[0]['consumption']
            
            for data in historical_data:
                current_smooth = alpha * data['consumption'] + (1 - alpha) * current_smooth
                smoothed_values.append(current_smooth)
            
            # Forecast using last smoothed value
            last_smoothed = smoothed_values[-1]
            
            for i in range(1, periods_ahead + 1):
                # Add trend component if data is long enough
                if len(smoothed_values) >= 10:
                    # Simple trend calculation
                    trend = (smoothed_values[-1] - smoothed_values[-5]) / 5
                    predicted = last_smoothed + (i * trend)
                else:
                    predicted = last_smoothed
                
                predicted = max(0, predicted)  # Ensure non-negative
                
                forecasts.append({
                    'period': i,
                    'date': (datetime.utcnow().date() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'predicted_consumption': round(predicted),
                    'confidence': 'high' if len(historical_data) >= 20 else 'medium'
                })
            
            return {
                "method": "Exponential Smoothing",
                "alpha": alpha,
                "last_smoothed_value": round(last_smoothed, 2),
                "forecasts": forecasts
            }
            
        except Exception as e:
            logger.error(f"Error in exponential smoothing forecast: {e}")
            return {"error": "Exponential smoothing forecast failed"}
    
    def _linear_trend_forecast(self, historical_data: List[Dict], periods_ahead: int) -> Dict:
        """Generate linear trend forecast"""
        try:
            if len(historical_data) < 10:
                return {"error": "Insufficient data for trend analysis"}
            
            # Prepare data for linear regression
            x = np.arange(len(historical_data))
            y = np.array([d['consumption'] for d in historical_data])
            
            # Calculate linear regression
            slope, intercept, r_value, p_value, std_err = np.polyfit(x, y, 1)
            
            # Generate forecasts
            forecasts = []
            for i in range(1, periods_ahead + 1):
                predicted = slope * (len(historical_data) + i - 1) + intercept
                predicted = max(0, predicted)  # Ensure non-negative
                
                # Calculate prediction interval
                uncertainty = std_err * np.sqrt(1 + 1/len(historical_data))
                lower_bound = max(0, predicted - 1.96 * uncertainty)
                upper_bound = predicted + 1.96 * uncertainty
                
                forecasts.append({
                    'period': i,
                    'date': (datetime.utcnow().date() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'predicted_consumption': round(predicted),
                    'lower_bound': round(lower_bound),
                    'upper_bound': round(upper_bound),
                    'confidence': 'high' if r_value**2 > 0.7 else 'medium' if r_value**2 > 0.4 else 'low'
                })
            
            return {
                "method": "Linear Trend",
                "slope": round(slope, 4),
                "intercept": round(intercept, 2),
                "r_squared": round(r_value**2, 3),
                "trend_strength": "strong" if r_value**2 > 0.7 else "moderate" if r_value**2 > 0.4 else "weak",
                "forecasts": forecasts
            }
            
        except Exception as e:
            logger.error(f"Error in linear trend forecast: {e}")
            return {"error": "Linear trend forecast failed"}
    
    def _seasonal_forecast(self, historical_data: List[Dict], periods_ahead: int) -> Dict:
        """Generate seasonal forecast"""
        try:
            if len(historical_data) < 30:
                return {"error": "Insufficient data for seasonal analysis"}
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_month'] = df['date'].dt.day
            
            # Calculate seasonal factors
            weekly_factors = {}
            for day in range(7):
                day_data = df[df['day_of_week'] == day]['consumption']
                if len(day_data) > 0:
                    weekly_factors[day] = day_data.mean() / df['consumption'].mean()
                else:
                    weekly_factors[day] = 1.0
            
            # Calculate overall trend
            x = np.arange(len(df))
            slope, intercept, _, _, _ = np.polyfit(x, df['consumption'], 1)
            
            # Generate forecasts
            forecasts = []
            base_date = datetime.utcnow().date()
            
            for i in range(1, periods_ahead + 1):
                forecast_date = base_date + timedelta(days=i)
                day_of_week = forecast_date.weekday()
                
                # Base forecast using trend
                trend_value = slope * (len(df) + i - 1) + intercept
                base_forecast = max(0, trend_value)
                
                # Apply seasonal factor
                seasonal_factor = weekly_factors.get(day_of_week, 1.0)
                predicted = base_forecast * seasonal_factor
                
                forecasts.append({
                    'period': i,
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'predicted_consumption': round(predicted),
                    'seasonal_factor': round(seasonal_factor, 3),
                    'day_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
                })
            
            return {
                "method": "Seasonal",
                "weekly_factors": weekly_factors,
                "trend_slope": round(slope, 4),
                "forecasts": forecasts
            }
            
        except Exception as e:
            logger.error(f"Error in seasonal forecast: {e}")
            return {"error": "Seasonal forecast failed"}
    
    def _create_ensemble_forecast(self, forecasts: Dict) -> Dict:
        """Create ensemble forecast from multiple methods"""
        try:
            ensemble_data = {}
            
            # Find common periods across all methods
            common_periods = None
            for method, forecast in forecasts.items():
                if 'error' in forecast:
                    continue
                
                method_periods = set(f['period'] for f in forecast['forecasts'])
                if common_periods is None:
                    common_periods = method_periods
                else:
                    common_periods = common_periods.intersection(method_periods)
            
            if not common_periods:
                return {"error": "No common periods found for ensemble"}
            
            # Create ensemble for each period
            ensemble_forecasts = []
            
            for period in sorted(common_periods):
                predictions = []
                method_weights = []
                
                for method, forecast in forecasts.items():
                    if 'error' in forecast:
                        continue
                    
                    # Find prediction for this period
                    period_forecast = next((f for f in forecast['forecasts'] if f['period'] == period), None)
                    if period_forecast:
                        predictions.append(period_forecast['predicted_consumption'])
                        # Weight based on method reliability
                        if method == 'linear_trend':
                            method_weights.append(0.4)
                        elif method == 'exponential_smoothing':
                            method_weights.append(0.3)
                        elif method == 'seasonal':
                            method_weights.append(0.2)
                        else:
                            method_weights.append(0.1)
                
                if predictions:
                    # Weighted average
                    ensemble_pred = np.average(predictions, weights=method_weights)
                    prediction_std = np.std(predictions)
                    
                    # Get date from first available method
                    first_method = next(m for m, f in forecasts.items() if 'error' not in f)
                    date = next(f['date'] for f in forecasts[first_method]['forecasts'] if f['period'] == period)
                    
                    ensemble_forecasts.append({
                        'period': period,
                        'date': date,
                        'predicted_consumption': round(ensemble_pred),
                        'uncertainty': round(prediction_std, 2),
                        'confidence': 'high' if prediction_std < ensemble_pred * 0.1 else 'medium' if prediction_std < ensemble_pred * 0.2 else 'low',
                        'method_agreement': len(predictions)
                    })
            
            return {
                "method": "Ensemble",
                "forecasts": ensemble_forecasts,
                "participating_methods": len([f for f in forecasts.values() if 'error' not in f])
            }
            
        except Exception as e:
            logger.error(f"Error creating ensemble forecast: {e}")
            return {"error": "Ensemble forecast failed"}
    
    def _calculate_forecast_accuracy(self, historical_data: List[Dict], forecasts: Dict) -> Dict:
        """Calculate accuracy metrics for forecasts"""
        try:
            if len(historical_data) < 10:
                return {"error": "Insufficient data for accuracy calculation"}
            
            # Split historical data for validation
            split_point = len(historical_data) - min(7, len(historical_data) // 4)
            validation_data = historical_data[split_point:]
            training_data = historical_data[:split_point]
            
            accuracy_metrics = {}
            
            for method, forecast in forecasts.items():
                if 'error' in forecast:
                    continue
                
                # Calculate accuracy using training data
                method_accuracy = []
                
                for i, actual_data in enumerate(validation_data):
                    # Get corresponding prediction (simplified)
                    if i < len(forecast['forecasts']):
                        predicted = forecast['forecasts'][i]['predicted_consumption']
                        actual = actual_data['consumption']
                        
                        # Calculate percentage error
                        error = abs(predicted - actual) / actual * 100 if actual > 0 else 0
                        method_accuracy.append(error)
                
                if method_accuracy:
                    accuracy_metrics[method] = {
                        'mean_absolute_error': round(np.mean(method_accuracy), 2),
                        'mean_absolute_percentage_error': round(np.mean(method_accuracy), 2),
                        'forecast_bias': round(np.mean([f - actual_data['consumption'] for f, actual_data in zip([f['predicted_consumption'] for f in forecast['forecasts']], validation_data)]), 2)
                    }
            
            return accuracy_metrics
            
        except Exception as e:
            logger.error(f"Error calculating forecast accuracy: {e}")
            return {"error": "Accuracy calculation failed"}
    
    def _analyze_demand_variability(self, historical_data: List[Dict]) -> Dict:
        """Analyze demand variability patterns"""
        try:
            if len(historical_data) < 10:
                return {"error": "Insufficient data for variability analysis"}
            
            consumptions = [d['consumption'] for d in historical_data]
            
            # Basic statistics
            mean_consumption = np.mean(consumptions)
            std_consumption = np.std(consumptions)
            cv = std_consumption / mean_consumption if mean_consumption > 0 else 0
            
            # Identify high variability periods
            high_variability_threshold = mean_consumption + 2 * std_consumption
            high_variability_periods = [
                d for d in historical_data 
                if d['consumption'] > high_variability_threshold
            ]
            
            # Calculate demand patterns
            weekly_pattern = {}
            daily_consumptions = {d['date']: d['consumption'] for d in historical_data}
            
            for i, data in enumerate(historical_data):
                day_of_week = data['date'].weekday()
                if day_of_week not in weekly_pattern:
                    weekly_pattern[day_of_week] = []
                weekly_pattern[day_of_week].append(data['consumption'])
            
            # Calculate average consumption by day of week
            weekly_averages = {}
            for day, consumptions_list in weekly_pattern.items():
                weekly_averages[day] = np.mean(consumptions_list)
            
            return {
                "mean_demand": round(mean_consumption, 2),
                "standard_deviation": round(std_consumption, 2),
                "coefficient_of_variation": round(cv, 3),
                "demand_classification": "high_variability" if cv > 0.5 else "moderate_variability" if cv > 0.2 else "low_variability",
                "high_variability_periods": len(high_variability_periods),
                "weekly_pattern": {str(k): round(v, 2) for k, v in weekly_averages.items()},
                "total_periods_analyzed": len(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing demand variability: {e}")
            return {"error": "Variability analysis failed"}
    
    def _generate_demand_recommendations(self, forecasts: Dict, variability_analysis: Dict) -> List[str]:
        """Generate recommendations based on demand analysis"""
        recommendations = []
        
        try:
            # Variability-based recommendations
            if 'error' not in variability_analysis:
                cv = variability_analysis.get('coefficient_of_variation', 0)
                
                if cv > 0.5:
                    recommendations.append("High demand variability detected - consider maintaining higher safety stock levels")
                elif cv > 0.2:
                    recommendations.append("Moderate demand variability - use moderate safety stock levels")
                else:
                    recommendations.append("Low demand variability - can use tighter inventory controls")
                
                # High variability periods
                if variability_analysis.get('high_variability_periods', 0) > 0:
                    recommendations.append("Monitor and investigate causes of high demand periods")
            
            # Forecast method recommendations
            if 'linear_trend' in forecasts and 'error' not in forecasts['linear_trend']:
                r_squared = forecasts['linear_trend'].get('r_squared', 0)
                if r_squared > 0.7:
                    recommendations.append("Strong trend detected - plan for consistent demand changes")
                elif r_squared < 0.3:
                    recommendations.append("No clear trend - focus on average demand levels")
            
            # Ensemble method recommendations
            if 'ensemble' in forecasts and 'error' not in forecasts['ensemble']:
                participation = forecasts['ensemble'].get('participating_methods', 0)
                if participation >= 3:
                    recommendations.append("High forecast confidence due to multiple method agreement")
                elif participation == 1:
                    recommendations.append("Low forecast confidence - consider gathering more data")
            
            # General recommendations
            recommendations.extend([
                "Update forecasts regularly as new data becomes available",
                "Monitor actual vs. predicted demand to refine forecasting models",
                "Consider external factors (seasonality, market conditions) in planning"
            ])
            
        except Exception as e:
            logger.error(f"Error generating demand recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations due to analysis limitations")
        
        return recommendations
    
    @measure_time("eoq_calculation")
    def calculate_economic_order_quantity(self, item_id: int, item_type: str, **kwargs) -> Dict[str, Any]:
        """
        Calculate Economic Order Quantity (EOQ) and related metrics
        """
        try:
            # Get item details
            item = self._get_item_details(item_id, item_type)
            if not item:
                return {"error": "Item not found"}
            
            # Get cost parameters
            unit_cost = kwargs.get('unit_cost', item.get('unit_cost', 0))
            ordering_cost = kwargs.get('ordering_cost', 1000)  # Default ordering cost
            holding_cost_rate = kwargs.get('holding_cost_rate', 0.25)  # 25% annual holding cost rate
            
            # Get annual demand from historical data
            annual_demand = kwargs.get('annual_demand', self._calculate_annual_demand(item_id, item_type))
            
            if annual_demand <= 0:
                return {"error": "Invalid annual demand value"}
            
            # Calculate holding cost per unit per year
            holding_cost_per_unit = unit_cost * holding_cost_rate
            
            # Calculate EOQ
            eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
            
            # Calculate related metrics
            number_of_orders = annual_demand / eoq if eoq > 0 else 0
            time_between_orders = 365 / number_of_orders if number_of_orders > 0 else 0
            total_cost = math.sqrt(2 * annual_demand * ordering_cost * holding_cost_per_unit)
            annual_holding_cost = (eoq / 2) * holding_cost_per_unit
            annual_ordering_cost = (annual_demand / eoq) * ordering_cost if eoq > 0 else 0
            
            # Sensitivity analysis
            sensitivity_analysis = self._calculate_eoq_sensitivity(
                annual_demand, ordering_cost, holding_cost_per_unit
            )
            
            # Comparison with current practices
            current_practice_comparison = self._compare_with_current_practice(
                item, eoq, annual_demand
            )
            
            return {
                "item_id": item_id,
                "item_type": item_type,
                "item_name": item.get('name', 'Unknown'),
                "eoq_analysis": {
                    "economic_order_quantity": round(eoq),
                    "annual_demand": round(annual_demand),
                    "unit_cost": unit_cost,
                    "ordering_cost": ordering_cost,
                    "holding_cost_rate": holding_cost_rate,
                    "holding_cost_per_unit": round(holding_cost_per_unit, 2)
                },
                "derived_metrics": {
                    "optimal_orders_per_year": round(number_of_orders, 2),
                    "time_between_orders_days": round(time_between_orders, 1),
                    "total_annual_cost": round(total_cost, 2),
                    "annual_holding_cost": round(annual_holding_cost, 2),
                    "annual_ordering_cost": round(annual_ordering_cost, 2),
                    "cost_breakdown": {
                        "holding_cost_percent": round(annual_holding_cost / total_cost * 100, 1) if total_cost > 0 else 0,
                        "ordering_cost_percent": round(annual_ordering_cost / total_cost * 100, 1) if total_cost > 0 else 0
                    }
                },
                "sensitivity_analysis": sensitivity_analysis,
                "current_practice_comparison": current_practice_comparison,
                "recommendations": self._generate_eoq_recommendations(eoq, current_practice_comparison, annual_demand)
            }
            
        except Exception as e:
            logger.error(f"Error calculating EOQ: {e}")
            return {"error": f"EOQ calculation failed: {str(e)}"}
    
    def _get_item_details(self, item_id: int, item_type: str) -> Optional[Dict]:
        """Get details for an inventory item"""
        try:
            if item_type == 'raw_material':
                item = self.session.query(RawMaterial).filter(RawMaterial.id == item_id).first()
                if item:
                    return {
                        'id': item.id,
                        'name': item.name,
                        'unit': item.unit,
                        'unit_cost': item.cost_afg,
                        'current_stock': item.current_stock,
                        'low_stock_alert': item.low_stock_alert
                    }
            
            elif item_type == 'finished_feed':
                item = self.session.query(FinishedFeed).filter(FinishedFeed.id == item_id).first()
                if item:
                    return {
                        'id': item.id,
                        'name': item.feed_type.value,
                        'unit': 'kg',
                        'unit_cost': item.cost_per_kg_afg,
                        'current_stock': item.current_stock,
                        'low_stock_alert': item.low_stock_alert
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting item details: {e}")
            return None
    
    def _calculate_annual_demand(self, item_id: int, item_type: str) -> float:
        """Calculate annual demand for an item based on historical data"""
        try:
            # Get last 12 months of consumption data
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=365)
            
            consumption_data = self._get_historical_consumption(item_id, item_type, days=365)
            
            if not consumption_data:
                return 0
            
            # Calculate total annual consumption
            total_consumption = sum(d['consumption'] for d in consumption_data)
            
            # Adjust for incomplete year if needed
            days_in_data = len(consumption_data)
            annual_equivalent = (total_consumption / days_in_data) * 365 if days_in_data > 0 else 0
            
            return annual_equivalent
            
        except Exception as e:
            logger.error(f"Error calculating annual demand: {e}")
            return 0
    
    def _calculate_eoq_sensitivity(self, annual_demand: float, ordering_cost: float, holding_cost_per_unit: float) -> Dict:
        """Perform sensitivity analysis on EOQ calculation"""
        try:
            base_eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
            
            # Test variations in key parameters
            variations = {
                'demand_variation': [-0.3, -0.1, 0.1, 0.3],
                'ordering_cost_variation': [-0.3, -0.1, 0.1, 0.3],
                'holding_cost_variation': [-0.3, -0.1, 0.1, 0.3]
            }
            
            sensitivity_results = {}
            
            # Demand sensitivity
            demand_sensitivity = []
            for variation in variations['demand_variation']:
                new_demand = annual_demand * (1 + variation)
                new_eoq = math.sqrt((2 * new_demand * ordering_cost) / holding_cost_per_unit)
                demand_sensitivity.append({
                    'variation': f"{variation:+.0%}",
                    'new_demand': round(new_demand),
                    'new_eoq': round(new_eoq),
                    'eoq_change': round(((new_eoq - base_eoq) / base_eoq) * 100, 1) if base_eoq > 0 else 0
                })
            
            # Ordering cost sensitivity
            ordering_sensitivity = []
            for variation in variations['ordering_cost_variation']:
                new_cost = ordering_cost * (1 + variation)
                new_eoq = math.sqrt((2 * annual_demand * new_cost) / holding_cost_per_unit)
                ordering_sensitivity.append({
                    'variation': f"{variation:+.0%}",
                    'new_ordering_cost': round(new_cost),
                    'new_eoq': round(new_eoq),
                    'eoq_change': round(((new_eoq - base_eoq) / base_eoq) * 100, 1) if base_eoq > 0 else 0
                })
            
            # Holding cost sensitivity
            holding_sensitivity = []
            for variation in variations['holding_cost_variation']:
                new_holding_cost = holding_cost_per_unit * (1 + variation)
                new_eoq = math.sqrt((2 * annual_demand * ordering_cost) / new_holding_cost)
                holding_sensitivity.append({
                    'variation': f"{variation:+.0%}",
                    'new_holding_cost': round(new_holding_cost, 2),
                    'new_eoq': round(new_eoq),
                    'eoq_change': round(((new_eoq - base_eoq) / base_eoq) * 100, 1) if base_eoq > 0 else 0
                })
            
            return {
                "base_eoq": round(base_eoq),
                "demand_sensitivity": demand_sensitivity,
                "ordering_cost_sensitivity": ordering_sensitivity,
                "holding_cost_sensitivity": holding_sensitivity,
                "insights": [
                    "EOQ is most sensitive to demand changes",
                    "Ordering cost variations have moderate impact",
                    "Holding cost changes have inverse impact on EOQ"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in EOQ sensitivity analysis: {e}")
            return {"error": "Sensitivity analysis failed"}
    
    def _compare_with_current_practice(self, item: Dict, eoq: float, annual_demand: float) -> Dict:
        """Compare EOQ recommendation with current practices"""
        try:
            current_stock = item.get('current_stock', 0)
            current_order_quantity = current_stock  # Assume current stock represents typical order
            
            # Calculate current metrics
            current_orders_per_year = annual_demand / current_order_quantity if current_order_quantity > 0 else 0
            current_time_between_orders = 365 / current_orders_per_year if current_orders_per_year > 0 else 0
            
            # Cost comparison (simplified)
            ordering_cost = 1000
            holding_cost_rate = 0.25
            unit_cost = item.get('unit_cost', 0)
            holding_cost_per_unit = unit_cost * holding_cost_rate
            
            current_total_cost = (current_orders_per_year * ordering_cost) + ((current_order_quantity / 2) * holding_cost_per_unit)
            optimal_total_cost = math.sqrt(2 * annual_demand * ordering_cost * holding_cost_per_unit)
            
            potential_savings = current_total_cost - optimal_total_cost if current_total_cost > optimal_total_cost else 0
            
            return {
                "current_practice": {
                    "typical_order_quantity": round(current_order_quantity),
                    "orders_per_year": round(current_orders_per_year, 2),
                    "time_between_orders_days": round(current_time_between_orders, 1),
                    "estimated_annual_cost": round(current_total_cost, 2)
                },
                "eoq_recommendation": {
                    "optimal_order_quantity": round(eoq),
                    "optimal_orders_per_year": round(annual_demand / eoq, 2) if eoq > 0 else 0,
                    "optimal_time_between_orders": round(365 / (annual_demand / eoq), 1) if eoq > 0 else 0,
                    "optimal_annual_cost": round(optimal_total_cost, 2)
                },
                "comparison": {
                    "order_quantity_change": round(((eoq - current_order_quantity) / current_order_quantity) * 100, 1) if current_order_quantity > 0 else 0,
                    "potential_annual_savings": round(potential_savings, 2),
                    "savings_percentage": round((potential_savings / current_total_cost) * 100, 1) if current_total_cost > 0 else 0,
                    "recommendation": "adopt_eoq" if potential_savings > 0 else "maintain_current"
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing with current practice: {e}")
            return {"error": "Current practice comparison failed"}
    
    def _generate_eoq_recommendations(self, eoq: float, current_practice_comparison: Dict, annual_demand: float) -> List[str]:
        """Generate recommendations based on EOQ analysis"""
        recommendations = []
        
        try:
            if 'comparison' in current_practice_comparison:
                comparison = current_practice_comparison['comparison']
                savings = comparison.get('potential_annual_savings', 0)
                savings_pct = comparison.get('savings_percentage', 0)
                
                if savings > 0:
                    recommendations.append(f"Consider implementing EOQ - potential annual savings of {savings} AFG ({savings_pct:.1f}%)")
                    
                    if savings_pct > 20:
                        recommendations.append("High savings potential - prioritize implementation")
                    elif savings_pct > 10:
                        recommendations.append("Moderate savings potential - implement when convenient")
                    else:
                        recommendations.append("Low savings potential - consider if operational benefits outweigh costs")
                
                # Order quantity recommendations
                order_change = comparison.get('order_quantity_change', 0)
                if abs(order_change) > 50:
                    if order_change > 0:
                        recommendations.append(f"Current orders may be too small - increase to {round(eoq)} units")
                    else:
                        recommendations.append(f"Current orders may be too large - reduce to {round(eoq)} units")
            
            # Frequency recommendations
            if eoq > 0 and annual_demand > 0:
                orders_per_year = annual_demand / eoq
                if orders_per_year > 24:
                    recommendations.append("High order frequency - consider if suppliers can handle frequent orders")
                elif orders_per_year < 4:
                    recommendations.append("Low order frequency - ensure product freshness and storage capacity")
            
            # Implementation recommendations
            recommendations.extend([
                "Monitor actual demand to validate EOQ assumptions",
                "Consider quantity discounts from suppliers for larger orders",
                "Implement gradual transition to avoid disruption",
                "Regularly review and update EOQ parameters"
            ])
            
        except Exception as e:
            logger.error(f"Error generating EOQ recommendations: {e}")
            recommendations.append("Unable to generate specific EOQ recommendations")
        
        return recommendations
    
    @measure_time("inventory_optimization")
    def optimize_inventory_levels(self, farm_id: int) -> Dict[str, Any]:
        """
        Comprehensive inventory optimization analysis
        """
        try:
            # Get all inventory items
            raw_materials = self.session.query(RawMaterial).all()
            finished_feeds = self.session.query(FinishedFeed).all()
            
            # Optimize each item
            optimization_results = []
            
            # Optimize raw materials
            for material in raw_materials:
                result = self._optimize_single_item(
                    material.id, 'raw_material', material.name, 
                    material.current_stock, material.cost_afg
                )
                if result:
                    optimization_results.append(result)
            
            # Optimize finished feeds
            for feed in finished_feeds:
                result = self._optimize_single_item(
                    feed.id, 'finished_feed', feed.feed_type.value,
                    feed.current_stock, feed.cost_per_kg_afg
                )
                if result:
                    optimization_results.append(result)
            
            # Overall optimization summary
            optimization_summary = self._create_optimization_summary(optimization_results)
            
            # Investment analysis
            investment_analysis = self._analyze_investment_requirements(optimization_results)
            
            # Implementation plan
            implementation_plan = self._create_implementation_plan(optimization_results)
            
            return {
                "farm_id": farm_id,
                "analysis_date": datetime.utcnow().strftime('%Y-%m-%d'),
                "total_items_analyzed": len(optimization_results),
                "individual_optimizations": optimization_results,
                "optimization_summary": optimization_summary,
                "investment_analysis": investment_analysis,
                "implementation_plan": implementation_plan,
                "expected_benefits": self._calculate_expected_benefits(optimization_results)
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive inventory optimization: {e}")
            return {"error": f"Inventory optimization failed: {str(e)}"}
    
    def _optimize_single_item(self, item_id: int, item_type: str, item_name: str, 
                           current_stock: float, unit_cost: float) -> Optional[Dict]:
        """Optimize a single inventory item"""
        try:
            # Get demand forecast
            demand_forecast = self.forecast_demand(item_id, item_type, days_ahead=30)
            
            if 'error' in demand_forecast:
                return None
            
            # Calculate EOQ
            annual_demand = sum(f['predicted_consumption'] for f in demand_forecast['ensemble_forecast']['forecasts']) * 12
            eoq_result = self.calculate_economic_order_quantity(
                item_id, item_type, 
                unit_cost=unit_cost, 
                annual_demand=annual_demand
            )
            
            if 'error' in eoq_result:
                return None
            
            # Determine optimal stock level
            eoq = eoq_result['eoq_analysis']['economic_order_quantity']
            safety_stock = self._calculate_safety_stock(item_id, item_type, demand_forecast)
            optimal_stock_level = eoq + safety_stock
            
            # Calculate optimization metrics
            current_investment = current_stock * unit_cost
            optimal_investment = optimal_stock_level * unit_cost
            investment_change = optimal_investment - current_investment
            
            # Risk assessment
            risk_level = self._assess_inventory_risk(current_stock, optimal_stock_level, demand_forecast)
            
            return {
                "item_id": item_id,
                "item_type": item_type,
                "item_name": item_name,
                "current_metrics": {
                    "current_stock": current_stock,
                    "current_investment": round(current_investment, 2),
                    "unit_cost": unit_cost
                },
                "optimal_metrics": {
                    "eoq": round(eoq),
                    "safety_stock": round(safety_stock),
                    "optimal_stock_level": round(optimal_stock_level),
                    "optimal_investment": round(optimal_investment, 2)
                },
                "optimization_analysis": {
                    "investment_change": round(investment_change, 2),
                    "investment_change_percent": round((investment_change / current_investment) * 100, 1) if current_investment > 0 else 0,
                    "risk_level": risk_level,
                    "priority": self._determine_optimization_priority(investment_change, risk_level)
                },
                "demand_forecast": demand_forecast['ensemble_forecast'],
                "eoq_analysis": eoq_result
            }
            
        except Exception as e:
            logger.error(f"Error optimizing item {item_id}: {e}")
            return None
    
    def _calculate_safety_stock(self, item_id: int, item_type: str, demand_forecast: Dict) -> float:
        """Calculate safety stock requirement"""
        try:
            if 'variability_analysis' in demand_forecast:
                cv = demand_forecast['variability_analysis'].get('coefficient_of_variation', 0.2)
                lead_time = 7  # Assume 7 days lead time
                
                # Get average daily demand from ensemble forecast
                daily_demands = [f['predicted_consumption'] for f in demand_forecast['ensemble_forecast']['forecasts']]
                avg_daily_demand = np.mean(daily_demands) if daily_demands else 10
                
                # Safety stock calculation using service level approach
                # 95% service level = 1.65 standard deviations
                service_factor = 1.65
                demand_variability = avg_daily_demand * cv
                safety_stock = service_factor * demand_variability * math.sqrt(lead_time)
                
                return max(0, safety_stock)
            
            # Default safety stock if no variability data
            return 10  # 10 units default
            
        except Exception as e:
            logger.error(f"Error calculating safety stock: {e}")
            return 10
    
    def _assess_inventory_risk(self, current_stock: float, optimal_stock: float, demand_forecast: Dict) -> str:
        """Assess inventory risk level"""
        try:
            # Stock level risk
            if current_stock < optimal_stock * 0.5:
                stock_risk = 'high'
            elif current_stock < optimal_stock * 0.8:
                stock_risk = 'medium'
            else:
                stock_risk = 'low'
            
            # Demand uncertainty risk
            if 'variability_analysis' in demand_forecast:
                cv = demand_forecast['variability_analysis'].get('coefficient_of_variation', 0)
                if cv > 0.5:
                    demand_risk = 'high'
                elif cv > 0.2:
                    demand_risk = 'medium'
                else:
                    demand_risk = 'low'
            else:
                demand_risk = 'medium'
            
            # Overall risk assessment
            if stock_risk == 'high' or demand_risk == 'high':
                return 'high'
            elif stock_risk == 'medium' or demand_risk == 'medium':
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error assessing inventory risk: {e}")
            return 'medium'
    
    def _determine_optimization_priority(self, investment_change: float, risk_level: str) -> str:
        """Determine optimization priority"""
        try:
            if risk_level == 'high' and investment_change < 0:
                return 'critical'
            elif risk_level == 'high' or (risk_level == 'medium' and abs(investment_change) > 1000):
                return 'high'
            elif risk_level == 'medium' or abs(investment_change) > 500:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error determining optimization priority: {e}")
            return 'medium'
    
    def _create_optimization_summary(self, optimization_results: List[Dict]) -> Dict:
        """Create summary of optimization analysis"""
        try:
            if not optimization_results:
                return {"error": "No optimization results to summarize"}
            
            total_items = len(optimization_results)
            
            # Priority analysis
            priorities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            total_investment_change = 0
            high_risk_items = 0
            
            for result in optimization_results:
                priority = result['optimization_analysis']['priority']
                priorities[priority] += 1
                
                investment_change = result['optimization_analysis']['investment_change']
                total_investment_change += investment_change
                
                if result['optimization_analysis']['risk_level'] == 'high':
                    high_risk_items += 1
            
            # Investment requirements
            reduction_needed = sum(
                result['optimization_analysis']['investment_change'] 
                for result in optimization_results 
                if result['optimization_analysis']['investment_change'] < 0
            )
            increase_needed = sum(
                result['optimization_analysis']['investment_change'] 
                for result in optimization_results 
                if result['optimization_analysis']['investment_change'] > 0
            )
            
            return {
                "total_items": total_items,
                "priority_distribution": priorities,
                "high_risk_items": high_risk_items,
                "total_investment_change": round(total_investment_change, 2),
                "investment_reduction_needed": round(abs(reduction_needed), 2) if reduction_needed < 0 else 0,
                "investment_increase_needed": round(increase_needed, 2),
                "optimization_complexity": "high" if priorities['critical'] + priorities['high'] > total_items * 0.3 else "medium" if priorities['high'] > 0 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error creating optimization summary: {e}")
            return {"error": "Optimization summary creation failed"}
    
    def _analyze_investment_requirements(self, optimization_results: List[Dict]) -> Dict:
        """Analyze investment requirements for optimization"""
        try:
            if not optimization_results:
                return {"error": "No results for investment analysis"}
            
            # Categorize by investment requirements
            no_investment = []
            small_investment = []  # < 1000 AFG
            medium_investment = []  # 1000-10000 AFG
            large_investment = []  # > 10000 AFG
            
            for result in optimization_results:
                change = result['optimization_analysis']['investment_change']
                
                if abs(change) < 100:
                    no_investment.append(result)
                elif abs(change) < 1000:
                    small_investment.append(result)
                elif abs(change) < 10000:
                    medium_investment.append(result)
                else:
                    large_investment.append(result)
            
            # Calculate total investment needed
            total_investment_needed = sum(
                abs(result['optimization_analysis']['investment_change']) 
                for result in optimization_results
                if result['optimization_analysis']['investment_change'] > 0
            )
            
            return {
                "investment_categories": {
                    "no_investment": {
                        "count": len(no_investment),
                        "items": [r['item_name'] for r in no_investment]
                    },
                    "small_investment": {
                        "count": len(small_investment),
                        "items": [r['item_name'] for r in small_investment],
                        "total_amount": round(sum(abs(r['optimization_analysis']['investment_change']) for r in small_investment), 2)
                    },
                    "medium_investment": {
                        "count": len(medium_investment),
                        "items": [r['item_name'] for r in medium_investment],
                        "total_amount": round(sum(abs(r['optimization_analysis']['investment_change']) for r in medium_investment), 2)
                    },
                    "large_investment": {
                        "count": len(large_investment),
                        "items": [r['item_name'] for r in large_investment],
                        "total_amount": round(sum(abs(r['optimization_analysis']['investment_change']) for r in large_investment), 2)
                    }
                },
                "total_investment_needed": round(total_investment_needed, 2),
                "implementation_phases": self._suggest_implementation_phases(optimization_results)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing investment requirements: {e}")
            return {"error": "Investment analysis failed"}
    
    def _suggest_implementation_phases(self, optimization_results: List[Dict]) -> List[Dict]:
        """Suggest phased implementation approach"""
        try:
            # Phase 1: Critical and high-priority low-cost items
            phase1_items = [
                r for r in optimization_results 
                if r['optimization_analysis']['priority'] in ['critical', 'high'] 
                and abs(r['optimization_analysis']['investment_change']) < 1000
            ]
            
            # Phase 2: Medium-priority items
            phase2_items = [
                r for r in optimization_results 
                if r['optimization_analysis']['priority'] == 'medium'
            ]
            
            # Phase 3: Low-priority and high-cost items
            phase3_items = [
                r for r in optimization_results 
                if r['optimization_analysis']['priority'] == 'low'
            ]
            
            phases = []
            
            if phase1_items:
                phases.append({
                    "phase": 1,
                    "name": "Quick Wins",
                    "description": "High impact, low cost optimizations",
                    "items": len(phase1_items),
                    "estimated_cost": round(sum(abs(r['optimization_analysis']['investment_change']) for r in phase1_items), 2),
                    "priority_items": [r['item_name'] for r in phase1_items[:5]]  # Top 5
                })
            
            if phase2_items:
                phases.append({
                    "phase": 2,
                    "name": "Medium-term Optimizations",
                    "description": "Moderate cost, moderate benefit items",
                    "items": len(phase2_items),
                    "estimated_cost": round(sum(abs(r['optimization_analysis']['investment_change']) for r in phase2_items), 2),
                    "priority_items": [r['item_name'] for r in phase2_items[:5]]
                })
            
            if phase3_items:
                phases.append({
                    "phase": 3,
                    "name": "Long-term Optimizations",
                    "description": "Lower priority, high cost items",
                    "items": len(phase3_items),
                    "estimated_cost": round(sum(abs(r['optimization_analysis']['investment_change']) for r in phase3_items), 2),
                    "priority_items": [r['item_name'] for r in phase3_items[:3]]
                })
            
            return phases
            
        except Exception as e:
            logger.error(f"Error suggesting implementation phases: {e}")
            return []
    
    def _create_implementation_plan(self, optimization_results: List[Dict]) -> Dict:
        """Create detailed implementation plan"""
        try:
            # Sort by priority
            sorted_results = sorted(
                optimization_results, 
                key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['optimization_analysis']['priority']]
            )
            
            implementation_steps = []
            
            for i, result in enumerate(sorted_results[:10]):  # Top 10 items
                item = result['item_name']
                priority = result['optimization_analysis']['priority']
                change = result['optimization_analysis']['investment_change']
                risk = result['optimization_analysis']['risk_level']
                
                if change > 0:
                    action = f"Increase stock to {result['optimal_metrics']['optimal_stock_level']:.0f} units"
                elif change < 0:
                    action = f"Reduce stock to {result['optimal_metrics']['optimal_stock_level']:.0f} units"
                else:
                    action = "Maintain current stock level"
                
                implementation_steps.append({
                    "step": i + 1,
                    "item": item,
                    "priority": priority,
                    "current_stock": result['current_metrics']['current_stock'],
                    "optimal_stock": result['optimal_metrics']['optimal_stock_level'],
                    "action": action,
                    "investment_required": abs(change),
                    "risk_level": risk,
                    "timeline": "1-2 weeks" if priority == 'critical' else "1 month" if priority == 'high' else "2-3 months"
                })
            
            return {
                "total_optimization_steps": len(implementation_steps),
                "immediate_actions": [
                    step for step in implementation_steps 
                    if step['priority'] in ['critical', 'high']
                ],
                "all_steps": implementation_steps,
                "estimated_total_timeline": "3-6 months",
                "success_metrics": [
                    "Reduced stockout incidents",
                    "Improved inventory turnover",
                    "Lower holding costs",
                    "Better cash flow management"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating implementation plan: {e}")
            return {"error": "Implementation plan creation failed"}
    
    def _calculate_expected_benefits(self, optimization_results: List[Dict]) -> Dict:
        """Calculate expected benefits from optimization"""
        try:
            if not optimization_results:
                return {"error": "No results for benefit calculation"}
            
            # Estimate cost savings
            total_potential_savings = 0
            stockout_risk_reduction = 0
            
            for result in optimization_results:
                # Holding cost savings (simplified)
                current_investment = result['current_metrics']['current_investment']
                optimal_investment = result['optimal_metrics']['optimal_investment']
                
                # Assume 25% annual holding cost rate
                holding_cost_rate = 0.25
                current_holding_cost = current_investment * holding_cost_rate
                optimal_holding_cost = optimal_investment * holding_cost_rate
                
                annual_savings = current_holding_cost - optimal_holding_cost
                total_potential_savings += max(0, annual_savings)
                
                # Stockout risk reduction
                if result['optimization_analysis']['risk_level'] == 'high':
                    stockout_risk_reduction += 1
            
            # Operational benefits
            operational_benefits = {
                "improved_visibility": "Better inventory tracking and forecasting",
                "reduced_manual_work": "Automated reorder points and quantities",
                "better_decision_making": "Data-driven inventory decisions",
                "enhanced_supplier_relations": "Predictable ordering patterns"
            }
            
            return {
                "financial_benefits": {
                    "annual_cost_savings": round(total_potential_savings, 2),
                    "monthly_savings": round(total_potential_savings / 12, 2),
                    "roi_timeline": "6-12 months"
                },
                "operational_benefits": operational_benefits,
                "risk_reduction": {
                    "high_risk_items_addressed": stockout_risk_reduction,
                    "improved_service_level": "Expected 95%+ service level achievement",
                    "reduced_emergency_orders": "Fewer urgent, high-cost purchases"
                },
                "strategic_benefits": [
                    "Optimized cash flow management",
                    "Improved supplier negotiations",
                    "Enhanced operational efficiency",
                    "Better financial planning"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating expected benefits: {e}")
            return {"error": "Benefit calculation failed"}
