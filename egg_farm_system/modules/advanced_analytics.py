"""
Advanced Analytics and Reporting Module
Provides predictive analytics, trend analysis, and advanced reporting capabilities
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, Shed, EggProduction, Sale, Purchase, Expense, FeedIssue, 
    RawMaterial, FinishedFeed, LedgerEntry
)
from egg_farm_system.utils.performance_monitoring import measure_time
import logging

logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    """Advanced analytics and prediction engine"""
    
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
    
    @measure_time("production_forecast")
    def forecast_egg_production(self, farm_id: int, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Forecast egg production using machine learning algorithms
        Returns detailed predictions with confidence intervals
        """
        try:
            # Get historical production data (last 90 days)
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=90)
            
            # Get farm and shed data
            farm = self.session.query(Farm).filter(Farm.id == farm_id).first()
            if not farm:
                return {"error": "Farm not found"}
            
            shed_ids = [shed.id for shed in farm.sheds]
            if not shed_ids:
                return {"error": "No sheds found for farm"}
            
            # Get production data
            productions = self.session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids),
                EggProduction.date >= start_date,
                EggProduction.date <= end_date
            ).order_by(EggProduction.date).all()
            
            if len(productions) < 10:
                return {"error": "Insufficient historical data for forecasting"}
            
            # Prepare data for ML
            df = self._prepare_production_data(productions)
            
            # Train multiple models and ensemble them
            models = self._train_production_models(df)
            
            # Generate forecasts
            forecast_dates = [end_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
            forecasts = self._generate_ensemble_forecast(models, forecast_dates, df)
            
            return {
                "farm_id": farm_id,
                "forecast_period": f"{start_date} to {forecast_dates[-1]}",
                "historical_period": f"{start_date} to {end_date}",
                "forecast_days": days_ahead,
                "forecasts": forecasts,
                "model_performance": self._calculate_model_performance(models, df),
                "seasonal_insights": self._analyze_seasonal_patterns(df),
                "confidence_intervals": self._calculate_confidence_intervals(forecasts)
            }
            
        except Exception as e:
            logger.error(f"Error in production forecast: {e}")
            return {"error": f"Forecast generation failed: {str(e)}"}
    
    def _prepare_production_data(self, productions: List) -> pd.DataFrame:
        """Prepare production data for machine learning"""
        data = []
        
        for prod in productions:
            # Group by date
            date_key = prod.date.date()
            if data and data[-1]['date'] == date_key:
                # Aggregate same day
                data[-1]['total_eggs'] += prod.total_eggs
                data[-1]['usable_eggs'] += prod.usable_eggs
                data[-1]['small_count'] += prod.small_count
                data[-1]['medium_count'] += prod.medium_count
                data[-1]['large_count'] += prod.large_count
                data[-1]['broken_count'] += prod.broken_count
            else:
                data.append({
                    'date': date_key,
                    'total_eggs': prod.total_eggs,
                    'usable_eggs': prod.usable_eggs,
                    'small_count': prod.small_count,
                    'medium_count': prod.medium_count,
                    'large_count': prod.large_count,
                    'broken_count': prod.broken_count,
                    'day_of_week': prod.date.weekday(),
                    'day_of_month': prod.date.day,
                    'month': prod.date.month,
                    'quarter': (prod.date.month - 1) // 3 + 1
                })
        
        df = pd.DataFrame(data)
        
        # Add derived features
        df['usable_ratio'] = df['usable_eggs'] / df['total_eggs']
        df['broken_ratio'] = df['broken_count'] / df['total_eggs']
        df['large_ratio'] = df['large_count'] / df['usable_eggs']
        
        # Add rolling averages
        df['total_eggs_7d_avg'] = df['total_eggs'].rolling(window=7).mean()
        df['total_eggs_30d_avg'] = df['total_eggs'].rolling(window=30).mean()
        
        # Add trend features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        
        return df.fillna(method='bfill')
    
    def _train_production_models(self, df: pd.DataFrame) -> Dict:
        """Train multiple ML models for production forecasting"""
        if len(df) < 20:
            return {"error": "Insufficient data for model training"}
        
        # Prepare features and target
        feature_cols = [
            'day_of_week', 'day_of_month', 'month', 'quarter',
            'total_eggs_7d_avg', 'total_eggs_30d_avg',
            'usable_ratio', 'broken_ratio', 'large_ratio',
            'days_since_start'
        ]
        
        X = df[feature_cols].fillna(0)
        y = df['total_eggs']
        
        # Split data for validation (use last 20% for testing)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        models = {}
        
        try:
            # Linear Regression
            lr = LinearRegression()
            lr.fit(X_train, y_train)
            lr_pred = lr.predict(X_test)
            models['linear_regression'] = {
                'model': lr,
                'mae': mean_absolute_error(y_test, lr_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, lr_pred)),
                'r2': r2_score(y_test, lr_pred)
            }
            
            # Random Forest
            rf = RandomForestRegressor(n_estimators=50, random_state=42)
            rf.fit(X_train, y_train)
            rf_pred = rf.predict(X_test)
            models['random_forest'] = {
                'model': rf,
                'mae': mean_absolute_error(y_test, rf_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, rf_pred)),
                'r2': r2_score(y_test, rf_pred)
            }
            
            # Simple trend model
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            trend_model = LinearRegression()
            trend_model.fit(X_train_scaled, y_train)
            trend_pred = trend_model.predict(X_test_scaled)
            models['trend_model'] = {
                'model': trend_model,
                'scaler': scaler,
                'mae': mean_absolute_error(y_test, trend_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, trend_pred)),
                'r2': r2_score(y_test, trend_pred)
            }
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return {"error": f"Model training failed: {str(e)}"}
        
        return models
    
    def _generate_ensemble_forecast(self, models: Dict, forecast_dates: List, df: pd.DataFrame) -> List[Dict]:
        """Generate ensemble forecast using multiple models"""
        forecasts = []
        
        # Get last known values for context
        last_row = df.iloc[-1]
        
        for date in forecast_dates:
            date_features = {
                'day_of_week': date.weekday(),
                'day_of_month': date.day,
                'month': date.month,
                'quarter': (date.month - 1) // 3 + 1,
                'total_eggs_7d_avg': last_row['total_eggs_7d_avg'],
                'total_eggs_30d_avg': last_row['total_eggs_30d_avg'],
                'usable_ratio': last_row['usable_ratio'],
                'broken_ratio': last_row['broken_ratio'],
                'large_ratio': last_row['large_ratio'],
                'days_since_start': (date - df['date'].min()).days
            }
            
            # Get predictions from each model
            predictions = []
            for model_name, model_info in models.items():
                if model_name == "error":
                    continue
                    
                try:
                    if model_name == "trend_model":
                        X_scaled = model_info['scaler'].transform([list(date_features.values())])
                        pred = model_info['model'].predict(X_scaled)[0]
                    else:
                        pred = model_info['model'].predict([list(date_features.values())])[0]
                    
                    predictions.append(max(0, pred))  # Ensure non-negative
                    
                except Exception as e:
                    logger.warning(f"Prediction failed for {model_name}: {e}")
            
            if predictions:
                # Ensemble prediction (weighted average based on R2 score)
                weights = []
                valid_predictions = []
                
                for i, (model_name, model_info) in enumerate(models.items()):
                    if model_name == "error" or i >= len(predictions):
                        continue
                    weight = max(0.1, model_info.get('r2', 0))  # Minimum weight of 0.1
                    weights.append(weight)
                    valid_predictions.append(predictions[i])
                
                if weights and valid_predictions:
                    ensemble_pred = np.average(valid_predictions, weights=weights)
                    
                    forecasts.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'predicted_total_eggs': round(ensemble_pred),
                        'predicted_usable_eggs': round(ensemble_pred * last_row['usable_ratio']),
                        'predicted_small': round(ensemble_pred * last_row['usable_ratio'] * 0.3),
                        'predicted_medium': round(ensemble_pred * last_row['usable_ratio'] * 0.4),
                        'predicted_large': round(ensemble_pred * last_row['usable_ratio'] * 0.3),
                        'model_consensus': len(predictions),
                        'prediction_range': {
                            'low': round(ensemble_pred * 0.85),
                            'high': round(ensemble_pred * 1.15)
                        }
                    })
        
        return forecasts
    
    def _calculate_model_performance(self, models: Dict, df: pd.DataFrame) -> Dict:
        """Calculate and return model performance metrics"""
        performance = {}
        
        for model_name, model_info in models.items():
            if model_name == "error":
                continue
                
            performance[model_name] = {
                'mae': round(model_info.get('mae', 0), 2),
                'rmse': round(model_info.get('rmse', 0), 2),
                'r2_score': round(model_info.get('r2', 0), 3),
                'accuracy': round(model_info.get('r2', 0) * 100, 1)
            }
        
        return performance
    
    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze seasonal patterns in production data"""
        try:
            # Monthly patterns
            monthly_avg = df.groupby('month')['total_eggs'].mean()
            
            # Day of week patterns
            dow_avg = df.groupby('day_of_week')['total_eggs'].mean()
            
            # Quarterly patterns
            quarterly_avg = df.groupby('quarter')['total_eggs'].mean()
            
            # Trend analysis
            correlation_coef, p_value = stats.pearsonr(df['days_since_start'], df['total_eggs'])
            
            return {
                'monthly_patterns': monthly_avg.to_dict(),
                'day_of_week_patterns': dow_avg.to_dict(),
                'quarterly_patterns': quarterly_avg.to_dict(),
                'overall_trend': {
                    'correlation': round(correlation_coef, 3),
                    'p_value': round(p_value, 3),
                    'direction': 'increasing' if correlation_coef > 0 else 'decreasing',
                    'significance': 'significant' if p_value < 0.05 else 'not significant'
                },
                'seasonal_insights': self._generate_seasonal_insights(monthly_avg, dow_avg, quarterly_avg)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return {"error": "Seasonal analysis failed"}
    
    def _generate_seasonal_insights(self, monthly_avg, dow_avg, quarterly_avg) -> List[str]:
        """Generate insights from seasonal patterns"""
        insights = []
        
        # Find best and worst months
        best_month = monthly_avg.idxmax()
        worst_month = monthly_avg.idxmin()
        insights.append(f"Best production month: {best_month} (avg: {monthly_avg[best_month]:.0f} eggs)")
        insights.append(f"Lowest production month: {worst_month} (avg: {monthly_avg[worst_month]:.0f} eggs)")
        
        # Find best and worst days
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        best_day = dow_avg.idxmax()
        worst_day = dow_avg.idxmin()
        insights.append(f"Best production day: {day_names[best_day]} (avg: {dow_avg[best_day]:.0f} eggs)")
        insights.append(f"Lowest production day: {day_names[worst_day]} (avg: {dow_avg[worst_day]:.0f} eggs)")
        
        return insights
    
    def _calculate_confidence_intervals(self, forecasts: List[Dict]) -> Dict:
        """Calculate confidence intervals for forecasts"""
        if not forecasts:
            return {}
        
        try:
            # Use prediction ranges to estimate confidence
            total_predictions = len(forecasts)
            avg_range_width = np.mean([
                f['prediction_range']['high'] - f['prediction_range']['low'] 
                for f in forecasts
            ])
            
            return {
                'confidence_level': '85%',  # Based on our prediction range methodology
                'average_uncertainty': round(avg_range_width / 2),
                'forecast_quality': 'high' if avg_range_width < 50 else 'medium' if avg_range_width < 100 else 'low',
                'total_forecasts': total_predictions
            }
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return {"error": "Confidence interval calculation failed"}
    
    @measure_time("financial_forecast")
    def forecast_financial_performance(self, farm_id: int, months_ahead: int = 6) -> Dict[str, Any]:
        """
        Forecast financial performance including revenue, costs, and profitability
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=365)  # Last year
            
            # Get farm data
            farm = self.session.query(Farm).filter(Farm.id == farm_id).first()
            if not farm:
                return {"error": "Farm not found"}
            
            # Get financial data
            sales_data = self._get_monthly_sales_data(farm_id, start_date, end_date)
            expense_data = self._get_monthly_expense_data(farm_id, start_date, end_date)
            
            if not sales_data or not expense_data:
                return {"error": "Insufficient financial data for forecasting"}
            
            # Generate forecasts
            revenue_forecast = self._forecast_financial_series(sales_data, months_ahead, 'revenue')
            expense_forecast = self._forecast_financial_series(expense_data, months_ahead, 'expenses')
            
            # Calculate profitability
            profitability_forecast = []
            for i, revenue_item in enumerate(revenue_forecast):
                revenue = revenue_item['value']
                expense = expense_forecast[i]['value']
                profit = revenue - expense
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                profitability_forecast.append({
                    'month': revenue_item['month'],
                    'revenue': round(revenue),
                    'expenses': round(expense),
                    'profit': round(profit),
                    'margin_percent': round(margin, 1)
                })
            
            return {
                "farm_id": farm_id,
                "forecast_period": f"{months_ahead} months ahead",
                "historical_period": f"{start_date} to {end_date}",
                "revenue_forecast": revenue_forecast,
                "expense_forecast": expense_forecast,
                "profitability_forecast": profitability_forecast,
                "financial_insights": self._analyze_financial_trends(sales_data, expense_data)
            }
            
        except Exception as e:
            logger.error(f"Error in financial forecast: {e}")
            return {"error": f"Financial forecast failed: {str(e)}"}
    
    def _get_monthly_sales_data(self, farm_id: int, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """Get monthly sales data for forecasting"""
        try:
            # This would be implemented based on actual sales structure
            # For now, return sample data structure
            sales = self.session.query(Sale).filter(
                Sale.date >= start_date,
                Sale.date <= end_date
            ).all()
            
            monthly_data = {}
            for sale in sales:
                month_key = sale.date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'revenue_afg': 0,
                        'revenue_usd': 0,
                        'month': month_key
                    }
                
                monthly_data[month_key]['revenue_afg'] += sale.total_amount_afg or 0
                monthly_data[month_key]['revenue_usd'] += sale.total_amount_usd or 0
            
            return list(monthly_data.values())
            
        except Exception as e:
            logger.error(f"Error getting sales data: {e}")
            return []
    
    def _get_monthly_expense_data(self, farm_id: int, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """Get monthly expense data for forecasting"""
        try:
            expenses = self.session.query(Expense).filter(
                Expense.date >= start_date,
                Expense.date <= end_date
            ).all()
            
            monthly_data = {}
            for expense in expenses:
                month_key = expense.date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'expense_afg': 0,
                        'expense_usd': 0,
                        'month': month_key
                    }
                
                monthly_data[month_key]['expense_afg'] += expense.amount_afg or 0
                monthly_data[month_key]['expense_usd'] += expense.amount_usd or 0
            
            return list(monthly_data.values())
            
        except Exception as e:
            logger.error(f"Error getting expense data: {e}")
            return []
    
    def _forecast_financial_series(self, data: List[Dict], periods_ahead: int, value_type: str) -> List[Dict]:
        """Forecast financial time series"""
        try:
            if len(data) < 6:
                # Use simple moving average if insufficient data
                avg_value = np.mean([d[f'{value_type}_afg'] for d in data])
                forecasts = []
                for i in range(1, periods_ahead + 1):
                    month = datetime.utcnow().replace(day=1) + timedelta(days=32*i)
                    month = month.replace(day=1)
                    forecasts.append({
                        'month': month.strftime('%Y-%m'),
                        'value': avg_value,
                        'method': 'moving_average'
                    })
                return forecasts
            
            # Prepare time series
            values = [d[f'{value_type}_afg'] for d in data]
            months = [d['month'] for d in data]
            
            # Simple trend analysis
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Generate forecasts
            forecasts = []
            for i in range(1, periods_ahead + 1):
                predicted_value = slope * (len(values) + i - 1) + intercept
                predicted_value = max(0, predicted_value)  # Ensure non-negative
                
                # Calculate confidence interval
                uncertainty = std_err * np.sqrt(1 + 1/len(values))
                lower_bound = max(0, predicted_value - 1.96 * uncertainty)
                upper_bound = predicted_value + 1.96 * uncertainty
                
                month = datetime.utcnow().replace(day=1) + timedelta(days=32*i)
                month = month.replace(day=1)
                
                forecasts.append({
                    'month': month.strftime('%Y-%m'),
                    'value': round(predicted_value),
                    'lower_bound': round(lower_bound),
                    'upper_bound': round(upper_bound),
                    'confidence': 'high' if r_value**2 > 0.7 else 'medium' if r_value**2 > 0.4 else 'low',
                    'trend_strength': round(r_value**2, 3)
                })
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting financial series: {e}")
            return []
    
    def _analyze_financial_trends(self, sales_data: List[Dict], expense_data: List[Dict]) -> List[str]:
        """Analyze financial trends and generate insights"""
        insights = []
        
        try:
            if len(sales_data) >= 6:
                revenues = [d['revenue_afg'] for d in sales_data[-6:]]
                expenses = [d['expense_afg'] for d in expense_data[-6:]] if expense_data else [0] * 6
                
                # Revenue trend
                revenue_trend = 'increasing' if revenues[-1] > revenues[0] else 'decreasing'
                revenue_change = ((revenues[-1] - revenues[0]) / revenues[0] * 100) if revenues[0] > 0 else 0
                insights.append(f"Revenue trend (6 months): {revenue_trend} ({revenue_change:+.1f}%)")
                
                # Expense trend
                expense_trend = 'increasing' if expenses[-1] > expenses[0] else 'decreasing'
                expense_change = ((expenses[-1] - expenses[0]) / expenses[0] * 100) if expenses[0] > 0 else 0
                insights.append(f"Expense trend (6 months): {expense_trend} ({expense_change:+.1f}%)")
                
                # Profitability
                current_profit = revenues[-1] - expenses[-1] if expenses else revenues[-1]
                previous_profit = revenues[0] - expenses[0] if expenses and len(expenses) >= 6 else revenues[0]
                
                if previous_profit != 0:
                    profit_change = ((current_profit - previous_profit) / abs(previous_profit) * 100)
                    insights.append(f"Profitability change (6 months): {profit_change:+.1f}%")
                
                # Seasonal patterns
                monthly_avg = {}
                for sale in sales_data:
                    month = int(sale['month'].split('-')[1])
                    if month not in monthly_avg:
                        monthly_avg[month] = []
                    monthly_avg[month].append(sale['revenue_afg'])
                
                if monthly_avg:
                    best_month = max(monthly_avg.keys(), key=lambda m: np.mean(monthly_avg[m]))
                    worst_month = min(monthly_avg.keys(), key=lambda m: np.mean(monthly_avg[m]))
                    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    insights.append(f"Best revenue month: {month_names[best_month]}")
                    insights.append(f"Lowest revenue month: {month_names[worst_month]}")
            
        except Exception as e:
            logger.error(f"Error analyzing financial trends: {e}")
            insights.append("Financial trend analysis incomplete due to data limitations")
        
        return insights
    
    @measure_time("inventory_analytics")
    def analyze_inventory_optimization(self, farm_id: int) -> Dict[str, Any]:
        """
        Analyze inventory for optimization opportunities
        """
        try:
            # Get current inventory levels
            raw_materials = self.session.query(RawMaterial).all()
            finished_feeds = self.session.query(FinishedFeed).all()
            
            # ABC Analysis for inventory categorization
            abc_analysis = self._perform_abc_analysis(raw_materials, finished_feeds)
            
            # Reorder point analysis
            reorder_analysis = self._calculate_reorder_points(raw_materials, finished_feeds)
            
            # Stock-out risk assessment
            stockout_risk = self._assess_stockout_risk(raw_materials, finished_feeds)
            
            # Optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                abc_analysis, reorder_analysis, stockout_risk
            )
            
            return {
                "farm_id": farm_id,
                "analysis_date": datetime.utcnow().strftime('%Y-%m-%d'),
                "abc_analysis": abc_analysis,
                "reorder_analysis": reorder_analysis,
                "stockout_risk": stockout_risk,
                "optimization_recommendations": recommendations,
                "potential_savings": self._calculate_potential_savings(abc_analysis, reorder_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in inventory optimization analysis: {e}")
            return {"error": f"Inventory analysis failed: {str(e)}"}
    
    def _perform_abc_analysis(self, raw_materials: List, finished_feeds: List) -> Dict:
        """Perform ABC analysis on inventory items"""
        try:
            # Combine all items with their values
            items = []
            
            # Add raw materials
            for material in raw_materials:
                value = material.current_stock * material.cost_afg
                items.append({
                    'id': material.id,
                    'name': material.name,
                    'type': 'raw_material',
                    'current_stock': material.current_stock,
                    'unit_cost': material.cost_afg,
                    'total_value': value,
                    'usage_frequency': self._get_usage_frequency(material.name, 'raw_material')
                })
            
            # Add finished feeds
            for feed in finished_feeds:
                value = feed.current_stock * feed.cost_per_kg_afg
                items.append({
                    'id': feed.id,
                    'name': feed.feed_type.value,
                    'type': 'finished_feed',
                    'current_stock': feed.current_stock,
                    'unit_cost': feed.cost_per_kg_afg,
                    'total_value': value,
                    'usage_frequency': self._get_usage_frequency(feed.feed_type.value, 'finished_feed')
                })
            
            # Sort by total value (descending)
            items.sort(key=lambda x: x['total_value'], reverse=True)
            
            # Calculate cumulative percentages
            total_value = sum(item['total_value'] for item in items)
            cumulative_value = 0
            
            for item in items:
                cumulative_value += item['total_value']
                item['cumulative_value_percent'] = (cumulative_value / total_value * 100) if total_value > 0 else 0
            
            # Categorize into ABC
            for item in items:
                if item['cumulative_value_percent'] <= 80:
                    item['abc_category'] = 'A'
                elif item['cumulative_value_percent'] <= 95:
                    item['abc_category'] = 'B'
                else:
                    item['abc_category'] = 'C'
            
            # Summary statistics
            category_summary = {'A': [], 'B': [], 'C': []}
            for item in items:
                category_summary[item['abc_category']].append(item)
            
            return {
                'items': items,
                'summary': {
                    'total_items': len(items),
                    'total_value': round(total_value),
                    'category_A': {
                        'count': len(category_summary['A']),
                        'value': round(sum(item['total_value'] for item in category_summary['A'])),
                        'value_percent': round(sum(item['total_value'] for item in category_summary['A']) / total_value * 100, 1) if total_value > 0 else 0
                    },
                    'category_B': {
                        'count': len(category_summary['B']),
                        'value': round(sum(item['total_value'] for item in category_summary['B'])),
                        'value_percent': round(sum(item['total_value'] for item in category_summary['B']) / total_value * 100, 1) if total_value > 0 else 0
                    },
                    'category_C': {
                        'count': len(category_summary['C']),
                        'value': round(sum(item['total_value'] for item in category_summary['C'])),
                        'value_percent': round(sum(item['total_value'] for item in category_summary['C']) / total_value * 100, 1) if total_value > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ABC analysis: {e}")
            return {"error": "ABC analysis failed"}
    
    def _get_usage_frequency(self, item_name: str, item_type: str) -> int:
        """Get usage frequency for an item (simplified implementation)"""
        # This would typically query usage history
        # For now, return a placeholder frequency
        return 10  # Assume moderate usage
    
    def _calculate_reorder_points(self, raw_materials: List, finished_feeds: List) -> Dict:
        """Calculate optimal reorder points for inventory items"""
        try:
            reorder_points = []
            
            for material in raw_materials:
                # Simplified reorder point calculation
                # In practice, this would consider lead time, demand variability, service level
                avg_usage = 10  # Assume 10 units per day average usage
                lead_time = 7   # Assume 7 days lead time
                safety_stock = avg_usage * 2  # 2 days safety stock
                
                reorder_point = (avg_usage * lead_time) + safety_stock
                
                reorder_points.append({
                    'item_id': material.id,
                    'item_name': material.name,
                    'item_type': 'raw_material',
                    'current_stock': material.current_stock,
                    'reorder_point': reorder_point,
                    'reorder_quantity': max(material.low_stock_alert * 2, 50),  # Minimum order quantity
                    'action_needed': material.current_stock <= reorder_point,
                    'urgency': 'high' if material.current_stock <= safety_stock else 'medium' if material.current_stock <= reorder_point else 'low'
                })
            
            for feed in finished_feeds:
                # Feed-specific reorder calculation
                avg_daily_usage = 50  # Assume 50kg per day
                lead_time = 5  # Assume 5 days lead time
                safety_stock = avg_daily_usage * 3  # 3 days safety stock
                
                reorder_point = (avg_daily_usage * lead_time) + safety_stock
                
                reorder_points.append({
                    'item_id': feed.id,
                    'item_name': feed.feed_type.value,
                    'item_type': 'finished_feed',
                    'current_stock': feed.current_stock,
                    'reorder_point': reorder_point,
                    'reorder_quantity': max(feed.low_stock_alert * 3, 200),  # Minimum order quantity
                    'action_needed': feed.current_stock <= reorder_point,
                    'urgency': 'high' if feed.current_stock <= safety_stock else 'medium' if feed.current_stock <= reorder_point else 'low'
                })
            
            # Summary statistics
            total_items = len(reorder_points)
            items_needing_reorder = sum(1 for item in reorder_points if item['action_needed'])
            high_urgency = sum(1 for item in reorder_points if item['urgency'] == 'high')
            
            return {
                'reorder_points': reorder_points,
                'summary': {
                    'total_items': total_items,
                    'items_needing_reorder': items_needing_reorder,
                    'high_urgency_items': high_urgency,
                    'reorder_percentage': round(items_needing_reorder / total_items * 100, 1) if total_items > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating reorder points: {e}")
            return {"error": "Reorder point calculation failed"}
    
    def _assess_stockout_risk(self, raw_materials: List, finished_feeds: List) -> Dict:
        """Assess risk of stockout for inventory items"""
        try:
            risk_assessment = []
            
            for material in raw_materials:
                # Simplified risk assessment
                days_of_stock = material.current_stock / 10 if material.current_stock > 0 else 0
                
                if days_of_stock <= 7:
                    risk_level = 'critical'
                elif days_of_stock <= 14:
                    risk_level = 'high'
                elif days_of_stock <= 30:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                risk_assessment.append({
                    'item_id': material.id,
                    'item_name': material.name,
                    'item_type': 'raw_material',
                    'current_stock': material.current_stock,
                    'days_of_stock': round(days_of_stock),
                    'risk_level': risk_level,
                    'financial_impact': material.current_stock * material.cost_afg
                })
            
            for feed in finished_feeds:
                days_of_stock = feed.current_stock / 50 if feed.current_stock > 0 else 0
                
                if days_of_stock <= 3:
                    risk_level = 'critical'
                elif days_of_stock <= 7:
                    risk_level = 'high'
                elif days_of_stock <= 14:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                risk_assessment.append({
                    'item_id': feed.id,
                    'item_name': feed.feed_type.value,
                    'item_type': 'finished_feed',
                    'current_stock': feed.current_stock,
                    'days_of_stock': round(days_of_stock),
                    'risk_level': risk_level,
                    'financial_impact': feed.current_stock * feed.cost_per_kg_afg
                })
            
            # Risk summary
            risk_summary = {'critical': [], 'high': [], 'medium': [], 'low': []}
            for item in risk_assessment:
                risk_summary[item['risk_level']].append(item)
            
            return {
                'risk_assessment': risk_assessment,
                'summary': {
                    'critical_items': len(risk_summary['critical']),
                    'high_risk_items': len(risk_summary['high']),
                    'medium_risk_items': len(risk_summary['medium']),
                    'low_risk_items': len(risk_summary['low']),
                    'total_at_risk_value': round(sum(item['financial_impact'] for item in risk_assessment if item['risk_level'] in ['critical', 'high']))
                }
            }
            
        except Exception as e:
            logger.error(f"Error assessing stockout risk: {e}")
            return {"error": "Stockout risk assessment failed"}
    
    def _generate_optimization_recommendations(self, abc_analysis: Dict, reorder_analysis: Dict, stockout_risk: Dict) -> List[str]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        try:
            # ABC Analysis recommendations
            if 'summary' in abc_analysis:
                summary = abc_analysis['summary']
                if summary['category_A']['count'] > 0:
                    recommendations.append(f"Focus on {summary['category_A']['count']} high-value Category A items - they represent {summary['category_A']['value_percent']}% of total inventory value")
                
                if summary['category_C']['count'] > len(abc_analysis['items']) * 0.5:
                    recommendations.append("Consider reducing stock levels for low-value Category C items to free up capital")
            
            # Reorder point recommendations
            if 'summary' in reorder_analysis:
                summary = reorder_analysis['summary']
                if summary['high_urgency_items'] > 0:
                    recommendations.append(f"Urgent: {summary['high_urgency_items']} items require immediate reordering")
                
                if summary['reorder_percentage'] > 30:
                    recommendations.append("High reorder percentage suggests need for improved demand forecasting")
            
            # Stockout risk recommendations
            if 'summary' in stockout_risk:
                summary = stockout_risk['summary']
                if summary['critical_items'] > 0:
                    recommendations.append(f"Critical: {summary['critical_items']} items at critical stockout risk - immediate action required")
                
                if summary['total_at_risk_value'] > 0:
                    recommendations.append(f"Total at-risk inventory value: {summary['total_at_risk_value']} AFG")
            
            # General optimization recommendations
            recommendations.extend([
                "Implement automated reorder triggers for Category A items",
                "Review and optimize reorder quantities to reduce carrying costs",
                "Establish supplier relationships for faster lead times",
                "Consider implementing just-in-time inventory for fast-moving items"
            ])
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations due to data limitations")
        
        return recommendations
    
    def _calculate_potential_savings(self, abc_analysis: Dict, reorder_analysis: Dict) -> Dict:
        """Calculate potential cost savings from optimization"""
        try:
            # Simplified savings calculation
            total_inventory_value = 0
            carrying_cost_rate = 0.25  # Assume 25% annual carrying cost
            
            if 'summary' in abc_analysis:
                total_inventory_value = abc_analysis['summary']['total_value']
            
            # Calculate current carrying cost
            current_carrying_cost = total_inventory_value * carrying_cost_rate
            
            # Estimate potential savings from optimization
            # Assume 10-20% reduction in carrying costs through better inventory management
            potential_savings_low = current_carrying_cost * 0.10
            potential_savings_high = current_carrying_cost * 0.20
            
            # Stockout cost avoidance
            stockout_cost_avoidance = 0
            if 'summary' in reorder_analysis:
                high_urgency_items = reorder_analysis['summary']['high_urgency_items']
                stockout_cost_avoidance = high_urgency_items * 5000  # Assume 5000 AFG cost per stockout
            
            return {
                'current_annual_carrying_cost': round(current_carrying_cost),
                'potential_carrying_cost_savings': {
                    'low_estimate': round(potential_savings_low),
                    'high_estimate': round(potential_savings_high)
                },
                'stockout_cost_avoidance': round(stockout_cost_avoidance),
                'total_potential_savings': round(potential_savings_low + stockout_cost_avoidance),
                'optimization_roi': 'High'
            }
            
        except Exception as e:
            logger.error(f"Error calculating potential savings: {e}")
            return {"error": "Savings calculation failed"}
