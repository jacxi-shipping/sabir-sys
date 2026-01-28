"""
Financial Features Module
Provides budgeting, forecasting, and advanced financial planning capabilities
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
import math
import logging

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    Farm, Sale, Purchase, Expense, Ledger, Party, Payment
)
from egg_farm_system.utils.performance_monitoring import measure_time

logger = logging.getLogger(__name__)

class FinancialPlanner:
    """Advanced financial planning and budgeting engine"""
    
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
    
    @measure_time("budget_planning")
    def create_budget(self, farm_id: int, year: int, **kwargs) -> Dict[str, Any]:
        """
        Create comprehensive annual budget for a farm
        """
        try:
            # Get farm details
            farm = self.session.query(Farm).filter(Farm.id == farm_id).first()
            if not farm:
                return {"error": "Farm not found"}
            
            # Get historical financial data for baseline
            historical_data = self._get_historical_financial_data(farm_id, year - 2, year - 1)
            
            # Get business assumptions
            assumptions = self._get_business_assumptions(farm_id, **kwargs)
            
            # Create revenue budget
            revenue_budget = self._create_revenue_budget(farm, historical_data, assumptions, year)
            
            # Create expense budget
            expense_budget = self._create_expense_budget(farm, historical_data, assumptions, year)
            
            # Create cash flow budget
            cash_flow_budget = self._create_cash_flow_budget(revenue_budget, expense_budget, assumptions)
            
            # Create budget summary
            budget_summary = self._create_budget_summary(revenue_budget, expense_budget, cash_flow_budget)
            
            # Budget analysis and insights
            budget_analysis = self._analyze_budget(revenue_budget, expense_budget, historical_data)
            
            # Create budget scenarios
            scenarios = self._create_budget_scenarios(revenue_budget, expense_budget, assumptions)
            
            return {
                "farm_id": farm_id,
                "farm_name": farm.name,
                "budget_year": year,
                "creation_date": datetime.utcnow().strftime('%Y-%m-%d'),
                "assumptions": assumptions,
                "revenue_budget": revenue_budget,
                "expense_budget": expense_budget,
                "cash_flow_budget": cash_flow_budget,
                "budget_summary": budget_summary,
                "budget_analysis": budget_analysis,
                "budget_scenarios": scenarios,
                "recommendations": self._generate_budget_recommendations(budget_summary, budget_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error creating budget: {e}")
            return {"error": f"Budget creation failed: {str(e)}"}
    
    def _get_historical_financial_data(self, farm_id, start_year, end_year):
        """Get historical financial data for budgeting baseline"""
        try:
            # Get sales data
            sales_query = self.session.query(Sale).join(
                Party, Sale.party_id == Party.id
            ).filter(
                Sale.date >= datetime(start_year, 1, 1),
                Sale.date <= datetime(end_year, 12, 31)
            )
            
            # Add farm filter if needed (assuming all sales are for this farm)
            sales_data = sales_query.all()
            
            # Get expense data
            expenses_query = self.session.query(Expense).filter(
                Expense.date >= datetime(start_year, 1, 1),
                Expense.date <= datetime(end_year, 12, 31)
            )
            
            expense_data = expenses_query.all()
            
            # Get purchase data
            purchases_query = self.session.query(Purchase).filter(
                Purchase.date >= datetime(start_year, 1, 1),
                Purchase.date <= datetime(end_year, 12, 31)
            )
            
            purchase_data = purchases_query.all()
            
            # Aggregate by year and category
            historical_summary = {
                "sales": {"by_year": {}, "by_month": {}, "by_category": {}},
                "expenses": {"by_year": {}, "by_month": {}, "by_category": {}},
                "purchases": {"by_year": {}, "by_month": {}, "by_category": {}}
            }
            
            # Process sales data
            for sale in sales_data:
                year = sale.date.year
                month = sale.date.month
                category = "Egg Sales"  # Default category
                
                # By year
                if year not in historical_summary["sales"]["by_year"]:
                    historical_summary["sales"]["by_year"][year] = {"afg": 0, "usd": 0}
                historical_summary["sales"]["by_year"][year]["afg"] += sale.total_amount_afg or 0
                historical_summary["sales"]["by_year"][year]["usd"] += sale.total_amount_usd or 0
                
                # By month
                month_key = f"{year}-{month:02d}"
                if month_key not in historical_summary["sales"]["by_month"]:
                    historical_summary["sales"]["by_month"][month_key] = {"afg": 0, "usd": 0}
                historical_summary["sales"]["by_month"][month_key]["afg"] += sale.total_amount_afg or 0
                historical_summary["sales"]["by_month"][month_key]["usd"] += sale.total_amount_usd or 0
                
                # By category
                if category not in historical_summary["sales"]["by_category"]:
                    historical_summary["sales"]["by_category"][category] = {"afg": 0, "usd": 0}
                historical_summary["sales"]["by_category"][category]["afg"] += sale.total_amount_afg or 0
                historical_summary["sales"]["by_category"][category]["usd"] += sale.total_amount_usd or 0
            
            # Process expense data
            for expense in expense_data:
                year = expense.date.year
                month = expense.date.month
                category = expense.category or "General"
                
                # By year
                if year not in historical_summary["expenses"]["by_year"]:
                    historical_summary["expenses"]["by_year"][year] = {"afg": 0, "usd": 0}
                historical_summary["expenses"]["by_year"][year]["afg"] += expense.amount_afg or 0
                historical_summary["expenses"]["by_year"][year]["usd"] += expense.amount_usd or 0
                
                # By month
                month_key = f"{year}-{month:02d}"
                if month_key not in historical_summary["expenses"]["by_month"]:
                    historical_summary["expenses"]["by_month"][month_key] = {"afg": 0, "usd": 0}
                historical_summary["expenses"]["by_month"][month_key]["afg"] += expense.amount_afg or 0
                historical_summary["expenses"]["by_month"][month_key]["usd"] += expense.amount_usd or 0
                
                # By category
                if category not in historical_summary["expenses"]["by_category"]:
                    historical_summary["expenses"]["by_category"][category] = {"afg": 0, "usd": 0}
                historical_summary["expenses"]["by_category"][category]["afg"] += expense.amount_afg or 0
                historical_summary["expenses"]["by_category"][category]["usd"] += expense.amount_usd or 0
            
            # Process purchase data
            for purchase in purchase_data:
                year = purchase.date.year
                month = purchase.date.month
                category = "Raw Materials"  # Default category
                
                # By year
                if year not in historical_summary["purchases"]["by_year"]:
                    historical_summary["purchases"]["by_year"][year] = {"afg": 0, "usd": 0}
                historical_summary["purchases"]["by_year"][year]["afg"] += purchase.total_amount_afg or 0
                historical_summary["purchases"]["by_year"][year]["usd"] += purchase.total_amount_usd or 0
                
                # By month
                month_key = f"{year}-{month:02d}"
                if month_key not in historical_summary["purchases"]["by_month"]:
                    historical_summary["purchases"]["by_month"][month_key] = {"afg": 0, "usd": 0}
                historical_summary["purchases"]["by_month"][month_key]["afg"] += purchase.total_amount_afg or 0
                historical_summary["purchases"]["by_month"][month_key]["usd"] += purchase.total_amount_usd or 0
                
                # By category
                if category not in historical_summary["purchases"]["by_category"]:
                    historical_summary["purchases"]["by_category"][category] = {"afg": 0, "usd": 0}
                historical_summary["purchases"]["by_category"][category]["afg"] += purchase.total_amount_afg or 0
                historical_summary["purchases"]["by_category"][category]["usd"] += purchase.total_amount_usd or 0
            
            return historical_summary
            
        except Exception as e:
            logger.error(f"Error getting historical financial data: {e}")
            return {}
    
    def _get_business_assumptions(self, farm_id, **kwargs):
        """Get or create business assumptions for budgeting"""
        try:
            # Get from kwargs or use defaults
            assumptions = {
                "egg_price_growth_rate": kwargs.get('egg_price_growth', 0.05),  # 5% annual growth
                "feed_cost_inflation": kwargs.get('feed_inflation', 0.08),  # 8% annual inflation
                "operational_efficiency": kwargs.get('efficiency_gain', 0.03),  # 3% efficiency improvement
                "production_growth": kwargs.get('production_growth', 0.10),  # 10% production increase
                "expense_inflation": kwargs.get('expense_inflation', 0.06),  # 6% general inflation
                "seasonal_factors": {
                    "Q1": kwargs.get('q1_factor', 0.95),  # Winter - lower production
                    "Q2": kwargs.get('q2_factor', 1.05),  # Spring - better production
                    "Q3": kwargs.get('q3_factor', 1.10),  # Summer - peak production
                    "Q4": kwargs.get('q4_factor', 1.00)   # Fall - normal production
                },
                "economic_factors": {
                    "exchange_rate_afg_to_usd": kwargs.get('exchange_rate', 90.0),
                    "interest_rate": kwargs.get('interest_rate', 0.15),
                    "tax_rate": kwargs.get('tax_rate', 0.20)
                },
                "operational_assumptions": {
                    "production_capacity_utilization": kwargs.get('capacity_utilization', 0.85),
                    "feed_conversion_ratio": kwargs.get('feed_conversion', 2.1),
                    "mortality_rate": kwargs.get('mortality_rate', 0.05),
                    "egg_grade_distribution": {
                        "small": kwargs.get('small_ratio', 0.25),
                        "medium": kwargs.get('medium_ratio', 0.45),
                        "large": kwargs.get('large_ratio', 0.30)
                    }
                }
            }
            
            return assumptions
            
        except Exception as e:
            logger.error(f"Error getting business assumptions: {e}")
            return {}
    
    def _create_revenue_budget(self, farm, historical_data, assumptions, budget_year):
        """Create revenue budget"""
        try:
            # Get base revenue from historical data
            recent_sales = historical_data.get("sales", {}).get("by_year", {})
            if recent_sales:
                base_year = max(recent_sales.keys())
                base_revenue_afg = recent_sales[base_year].get("afg", 0)
                base_revenue_usd = recent_sales[base_year].get("usd", 0)
            else:
                base_revenue_afg = 0
                base_revenue_usd = 0
            
            # Calculate projected revenue growth
            production_growth = assumptions.get("production_growth", 0.10)
            price_growth = assumptions.get("egg_price_growth_rate", 0.05)
            
            # Revenue categories
            revenue_categories = {}
            
            # Egg sales (main revenue source)
            egg_revenue_afg = base_revenue_afg * (1 + production_growth) * (1 + price_growth)
            egg_revenue_usd = base_revenue_usd * (1 + production_growth) * (1 + price_growth)
            
            revenue_categories["egg_sales"] = {
                "budget_afg": round(egg_revenue_afg),
                "budget_usd": round(egg_revenue_usd),
                "growth_rate": round((production_growth + price_growth) * 100, 1),
                "seasonal_distribution": self._create_seasonal_revenue_distribution(egg_revenue_afg, assumptions)
            }
            
            # Other potential revenue sources
            other_revenues = {
                "bird_sales": round(egg_revenue_afg * 0.05),  # 5% of egg revenue
                "manure_sales": round(egg_revenue_afg * 0.02),  # 2% of egg revenue
                "consulting_services": round(egg_revenue_afg * 0.03)  # 3% of egg revenue
            }
            
            revenue_categories["other_revenues"] = {
                "budget_afg": sum(other_revenues.values()),
                "budget_usd": round(sum(other_revenues.values()) / assumptions["economic_factors"]["exchange_rate_afg_to_usd"]),
                "breakdown": other_revenues
            }
            
            # Monthly distribution
            monthly_distribution = self._create_monthly_revenue_distribution(revenue_categories, assumptions)
            
            # Summary
            total_budget_afg = sum(cat["budget_afg"] for cat in revenue_categories.values())
            total_budget_usd = sum(cat["budget_usd"] for cat in revenue_categories.values())
            
            return {
                "categories": revenue_categories,
                "monthly_distribution": monthly_distribution,
                "summary": {
                    "total_budget_afg": total_budget_afg,
                    "total_budget_usd": total_budget_usd,
                    "average_monthly_afg": round(total_budget_afg / 12),
                    "average_monthly_usd": round(total_budget_usd / 12)
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating revenue budget: {e}")
            return {"error": "Revenue budget creation failed"}
    
    def _create_expense_budget(self, farm, historical_data, assumptions, budget_year):
        """Create comprehensive expense budget"""
        try:
            # Get base expenses from historical data
            recent_expenses = historical_data.get("expenses", {}).get("by_category", {})
            recent_purchases = historical_data.get("purchases", {}).get("by_category", {})
            
            # Expense categories
            expense_categories = {}
            
            # Feed costs (largest expense)
            base_feed_cost = recent_purchases.get("Raw Materials", {}).get("afg", 0)
            feed_inflation = assumptions.get("feed_cost_inflation", 0.08)
            production_growth = assumptions.get("production_growth", 0.10)
            
            feed_cost_afg = base_feed_cost * (1 + feed_inflation) * (1 + production_growth)
            feed_cost_usd = round(feed_cost_afg / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
            
            expense_categories["feed_costs"] = {
                "budget_afg": round(feed_cost_afg),
                "budget_usd": feed_cost_usd,
                "inflation_rate": round(feed_inflation * 100, 1),
                "percentage_of_revenue": round((feed_cost_afg / max(feed_cost_afg, 1)) * 100, 1)
            }
            
            # Labor costs
            base_labor_cost = sum(exp.get("afg", 0) for exp_type in recent_expenses.values() 
                                for exp in [exp_type] if "labor" in str(exp).lower())
            
            if base_labor_cost == 0:
                base_labor_cost = feed_cost_afg * 0.15  # Estimate 15% of feed costs
            
            labor_inflation = assumptions.get("expense_inflation", 0.06)
            efficiency_gain = assumptions.get("operational_efficiency", 0.03)
            
            labor_cost_afg = base_labor_cost * (1 + labor_inflation - efficiency_gain)
            labor_cost_usd = round(labor_cost_afg / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
            
            expense_categories["labor_costs"] = {
                "budget_afg": round(labor_cost_afg),
                "budget_usd": labor_cost_usd,
                "efficiency_improvement": round(efficiency_gain * 100, 1),
                "categories": {
                    "salaries": round(labor_cost_afg * 0.70),
                    "benefits": round(labor_cost_afg * 0.20),
                    "training": round(labor_cost_afg * 0.10)
                }
            }
            
            # Utilities and maintenance
            utilities_base = base_labor_cost * 0.25  # Estimate based on labor costs
            utilities_cost_afg = utilities_base * (1 + labor_inflation)
            utilities_cost_usd = round(utilities_cost_afg / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
            
            expense_categories["utilities_maintenance"] = {
                "budget_afg": round(utilities_cost_afg),
                "budget_usd": utilities_cost_usd,
                "breakdown": {
                    "electricity": round(utilities_cost_afg * 0.40),
                    "water": round(utilities_cost_afg * 0.20),
                    "maintenance": round(utilities_cost_afg * 0.25),
                    "insurance": round(utilities_cost_afg * 0.15)
                }
            }
            
            # Other operating expenses
            other_expenses = {
                "veterinary_care": round(labor_cost_afg * 0.08),
                "equipment_purchases": round(labor_cost_afg * 0.12),
                "transportation": round(labor_cost_afg * 0.06),
                "marketing": round(labor_cost_afg * 0.04),
                "office_expenses": round(labor_cost_afg * 0.03),
                "miscellaneous": round(labor_cost_afg * 0.05)
            }
            
            other_total_afg = sum(other_expenses.values())
            other_total_usd = round(other_total_afg / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
            
            expense_categories["other_operating_expenses"] = {
                "budget_afg": other_total_afg,
                "budget_usd": other_total_usd,
                "breakdown": other_expenses
            }
            
            # Financial expenses
            interest_rate = assumptions["economic_factors"]["interest_rate"]
            estimated_loan_amount = feed_cost_afg * 0.30  # Assume 30% of feed costs are financed
            interest_expense = estimated_loan_amount * interest_rate
            
            expense_categories["financial_expenses"] = {
                "budget_afg": round(interest_expense),
                "budget_usd": round(interest_expense / assumptions["economic_factors"]["exchange_rate_afg_to_usd"]),
                "assumptions": {
                    "loan_amount": round(estimated_loan_amount),
                    "interest_rate": round(interest_rate * 100, 1)
                }
            }
            
            # Monthly distribution
            monthly_distribution = self._create_monthly_expense_distribution(expense_categories, assumptions)
            
            # Summary
            total_budget_afg = sum(cat["budget_afg"] for cat in expense_categories.values())
            total_budget_usd = sum(cat["budget_usd"] for cat in expense_categories.values())
            
            return {
                "categories": expense_categories,
                "monthly_distribution": monthly_distribution,
                "summary": {
                    "total_budget_afg": total_budget_afg,
                    "total_budget_usd": total_budget_usd,
                    "average_monthly_afg": round(total_budget_afg / 12),
                    "average_monthly_usd": round(total_budget_usd / 12)
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating expense budget: {e}")
            return {"error": "Expense budget creation failed"}
    
    def _create_cash_flow_budget(self, revenue_budget, expense_budget, _):
        """Create cash flow budget"""
        try:
            revenue_data = revenue_budget.get("monthly_distribution", {})
            expense_data = expense_budget.get("monthly_distribution", {})
            
            # Create monthly cash flow projections
            monthly_cash_flow = {}
            operating_cash_flow = {}
            
            for month in range(1, 13):
                month_key = f"month_{month:02d}"
                
                # Revenue and expenses for the month
                monthly_revenue = revenue_data.get(month_key, {}).get("total_afg", 0)
                monthly_expenses = expense_data.get(month_key, {}).get("total_afg", 0)
                
                # Operating cash flow
                operating_flow = monthly_revenue - monthly_expenses
                
                # Working capital changes (simplified)
                # Assume 5% of revenue for working capital needs
                working_capital_change = monthly_revenue * 0.05
                
                # Net cash flow
                net_cash_flow = operating_flow - working_capital_change
                
                monthly_cash_flow[month_key] = {
                    "revenue": monthly_revenue,
                    "expenses": monthly_expenses,
                    "operating_cash_flow": operating_flow,
                    "working_capital_change": working_capital_change,
                    "net_cash_flow": net_cash_flow,
                    "cumulative_cash_flow": 0  # Will be calculated below
                }
                
                operating_cash_flow[month_key] = operating_flow
            
            # Calculate cumulative cash flow
            cumulative = 0
            for month_key in sorted(monthly_cash_flow.keys()):
                cumulative += monthly_cash_flow[month_key]["net_cash_flow"]
                monthly_cash_flow[month_key]["cumulative_cash_flow"] = cumulative
            
            # Cash flow summary
            total_revenue = sum(m["revenue"] for m in monthly_cash_flow.values())
            total_expenses = sum(m["expenses"] for m in monthly_cash_flow.values())
            total_operating_flow = sum(m["operating_cash_flow"] for m in monthly_cash_flow.values())
            total_net_flow = sum(m["net_cash_flow"] for m in monthly_cash_flow.values())
            
            # Identify critical periods
            min_cash_flow = min(m["cumulative_cash_flow"] for m in monthly_cash_flow.values())
            cash_flow_gaps = [
                month for month, data in monthly_cash_flow.items() 
                if data["cumulative_cash_flow"] < 0
            ]
            
            return {
                "monthly_projections": monthly_cash_flow,
                "summary": {
                    "total_revenue": round(total_revenue),
                    "total_expenses": round(total_expenses),
                    "total_operating_cash_flow": round(total_operating_flow),
                    "total_net_cash_flow": round(total_net_flow),
                    "minimum_cash_position": round(min_cash_flow),
                    "cash_flow_gaps": len(cash_flow_gaps)
                },
                "cash_flow_analysis": {
                    "peak_financing_need": round(abs(min_cash_flow)) if min_cash_flow < 0 else 0,
                    "average_monthly_operating_flow": round(total_operating_flow / 12),
                    "cash_flow_seasonality": "high" if (min_val := abs(min(m["operating_cash_flow"] for m in monthly_cash_flow.values()))) > 0 and max(m["operating_cash_flow"] for m in monthly_cash_flow.values()) / min_val > 2 else "moderate"
                },
                "recommendations": self._generate_cash_flow_recommendations(monthly_cash_flow)
            }
            
        except Exception as e:
            logger.error(f"Error creating cash flow budget: {e}")
            return {"error": "Cash flow budget creation failed"}
    
    def _create_budget_summary(self, revenue_budget, expense_budget, cash_flow_budget):
        """Create comprehensive budget summary"""
        try:
            revenue_summary = revenue_budget.get("summary", {})
            expense_summary = expense_budget.get("summary", {})
            cash_flow_summary = cash_flow_budget.get("summary", {})
            
            # Profit & Loss projection
            gross_profit = revenue_summary.get("total_budget_afg", 0) - expense_summary.get("total_budget_afg", 0)
            gross_profit_margin = (gross_profit / max(revenue_summary.get("total_budget_afg", 1), 1)) * 100
            
            # Key financial ratios
            total_revenue = revenue_summary.get("total_budget_afg", 0)
            total_expenses = expense_summary.get("total_budget_afg", 0)
            
            # Expense ratios
            feed_cost_ratio = (expense_budget.get("categories", {}).get("feed_costs", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            labor_cost_ratio = (expense_budget.get("categories", {}).get("labor_costs", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            other_expense_ratio = 100 - feed_cost_ratio - labor_cost_ratio
            
            return {
                "profit_loss_projection": {
                    "total_revenue": total_revenue,
                    "total_expenses": total_expenses,
                    "gross_profit": gross_profit,
                    "gross_profit_margin": round(gross_profit_margin, 1),
                    "monthly_average_profit": round(gross_profit / 12)
                },
                "cost_structure": {
                    "feed_costs": {
                        "amount": expense_budget.get("categories", {}).get("feed_costs", {}).get("budget_afg", 0),
                        "percentage_of_revenue": round(feed_cost_ratio, 1),
                        "percentage_of_total_expenses": round((expense_budget.get("categories", {}).get("feed_costs", {}).get("budget_afg", 0) / max(total_expenses, 1)) * 100, 1)
                    },
                    "labor_costs": {
                        "amount": expense_budget.get("categories", {}).get("labor_costs", {}).get("budget_afg", 0),
                        "percentage_of_revenue": round(labor_cost_ratio, 1),
                        "percentage_of_total_expenses": round((expense_budget.get("categories", {}).get("labor_costs", {}).get("budget_afg", 0) / max(total_expenses, 1)) * 100, 1)
                    },
                    "other_expenses": {
                        "amount": total_expenses - expense_budget.get("categories", {}).get("feed_costs", {}).get("budget_afg", 0) - expense_budget.get("categories", {}).get("labor_costs", {}).get("budget_afg", 0),
                        "percentage_of_revenue": round(other_expense_ratio, 1),
                        "percentage_of_total_expenses": round((100 - feed_cost_ratio - labor_cost_ratio), 1)
                    }
                },
                "cash_flow_summary": cash_flow_summary,
                "key_ratios": {
                    "revenue_per_month": round(total_revenue / 12),
                    "expenses_per_month": round(total_expenses / 12),
                    "profit_per_month": round(gross_profit / 12),
                    "break_even_revenue": round(total_expenses),
                    "profitability_status": "profitable" if gross_profit > 0 else "loss_making"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating budget summary: {e}")
            return {"error": "Budget summary creation failed"}
    
    def _analyze_budget(self, revenue_budget, expense_budget, historical_data):
        """Analyze budget for insights and recommendations"""
        try:
            analysis = {
                "historical_comparison": {},
                "variance_analysis": {},
                "risk_assessment": {},
                "optimization_opportunities": []
            }
            
            # Historical comparison
            if historical_data:
                recent_sales = historical_data.get("sales", {}).get("by_year", {})
                recent_expenses = historical_data.get("expenses", {}).get("by_year", {})
                
                if recent_sales:
                    last_year_revenue = list(recent_sales.values())[-1].get("afg", 0)
                    budgeted_revenue = revenue_budget.get("summary", {}).get("total_budget_afg", 0)
                    
                    if last_year_revenue > 0:
                        revenue_growth = ((budgeted_revenue - last_year_revenue) / last_year_revenue) * 100
                        analysis["historical_comparison"]["revenue_growth"] = round(revenue_growth, 1)
                        analysis["historical_comparison"]["revenue_growth_assessment"] = "strong" if revenue_growth > 15 else "moderate" if revenue_growth > 5 else "conservative"
                
                if recent_expenses:
                    last_year_expenses = sum(exp.get("afg", 0) for exp in recent_expenses.values())
                    budgeted_expenses = expense_budget.get("summary", {}).get("total_budget_afg", 0)
                    
                    if last_year_expenses > 0:
                        expense_growth = ((budgeted_expenses - last_year_expenses) / last_year_expenses) * 100
                        analysis["historical_comparison"]["expense_growth"] = round(expense_growth, 1)
            
            # Risk assessment
            revenue_categories = revenue_budget.get("categories", {})
            total_revenue = sum(cat.get("budget_afg", 0) for cat in revenue_categories.values())
            
            # Revenue concentration risk
            egg_sales_percentage = (revenue_categories.get("egg_sales", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            analysis["risk_assessment"]["revenue_concentration_risk"] = "high" if egg_sales_percentage > 90 else "moderate" if egg_sales_percentage > 70 else "low"
            
            # Cost structure risk
            feed_percentage = (expense_budget.get("categories", {}).get("feed_costs", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            analysis["risk_assessment"]["feed_cost_risk"] = "high" if feed_percentage > 60 else "moderate" if feed_percentage > 40 else "low"
            
            # Optimization opportunities
            opportunities = []
            
            # Revenue diversification
            other_revenue_percentage = (revenue_categories.get("other_revenues", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            if other_revenue_percentage < 10:
                opportunities.append("Consider diversifying revenue streams to reduce dependency on egg sales")
            
            # Cost optimization
            if feed_percentage > 50:
                opportunities.append("High feed costs - consider feed efficiency improvements or supplier negotiations")
            
            # Labor efficiency
            labor_percentage = (expense_budget.get("categories", {}).get("labor_costs", {}).get("budget_afg", 0) / max(total_revenue, 1)) * 100
            if labor_percentage > 20:
                opportunities.append("Labor costs are high - consider automation or productivity improvements")
            
            analysis["optimization_opportunities"] = opportunities
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing budget: {e}")
            return {"error": "Budget analysis failed"}
    
    def _create_budget_scenarios(self, revenue_budget, expense_budget, assumptions):
        """Create budget scenarios (optimistic, realistic, pessimistic)"""
        try:
            base_revenue = revenue_budget.get("summary", {}).get("total_budget_afg", 0)
            base_expenses = expense_budget.get("summary", {}).get("total_budget_afg", 0)
            
            scenarios = {}
            
            # Pessimistic scenario
            pessimistic_revenue = base_revenue * 0.85  # 15% lower revenue
            pessimistic_expenses = base_expenses * 1.05  # 5% higher expenses
            pessimistic_profit = pessimistic_revenue - pessimistic_expenses
            
            scenarios["pessimistic"] = {
                "revenue": round(pessimistic_revenue),
                "expenses": round(pessimistic_expenses),
                "profit": round(pessimistic_profit),
                "profit_margin": round((pessimistic_profit / max(pessimistic_revenue, 1)) * 100, 1),
                "probability": 20,
                "key_assumptions": [
                    "Disease outbreak reducing production by 20%",
                    "Market price decline of 15%",
                    "Feed cost inflation of 10%"
                ]
            }
            
            # Realistic scenario (baseline)
            realistic_profit = base_revenue - base_expenses
            
            scenarios["realistic"] = {
                "revenue": base_revenue,
                "expenses": base_expenses,
                "profit": round(realistic_profit),
                "profit_margin": round((realistic_profit / max(base_revenue, 1)) * 100, 1),
                "probability": 60,
                "key_assumptions": [
                    "Normal production levels",
                    "Expected market conditions",
                    "Planned efficiency improvements"
                ]
            }
            
            # Optimistic scenario
            optimistic_revenue = base_revenue * 1.25  # 25% higher revenue
            optimistic_expenses = base_expenses * 0.95  # 5% lower expenses
            optimistic_profit = optimistic_revenue - optimistic_expenses
            
            scenarios["optimistic"] = {
                "revenue": round(optimistic_revenue),
                "expenses": round(optimistic_expenses),
                "profit": round(optimistic_profit),
                "profit_margin": round((optimistic_profit / max(optimistic_revenue, 1)) * 100, 1),
                "probability": 20,
                "key_assumptions": [
                    "Exceptional production performance",
                    "Premium market pricing",
                    "Significant cost efficiencies"
                ]
            }
            
            # Expected value calculation
            expected_profit = (
                scenarios["pessimistic"]["profit"] * 0.20 +
                scenarios["realistic"]["profit"] * 0.60 +
                scenarios["optimistic"]["profit"] * 0.20
            )
            
            scenarios["expected_value"] = {
                "profit": round(expected_profit),
                "profit_margin": round((expected_profit / max(base_revenue, 1)) * 100, 1),
                "risk_assessment": "moderate" if optimistic_profit - pessimistic_profit > base_revenue * 0.5 else "low"
            }
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error creating budget scenarios: {e}")
            return {"error": "Budget scenarios creation failed"}
    
    def _generate_budget_recommendations(self, budget_summary, budget_analysis):
        """Generate budget recommendations"""
        recommendations = []
        
        try:
            # Profitability recommendations
            profit_margin = budget_summary.get("profit_loss_projection", {}).get("gross_profit_margin", 0)
            if profit_margin < 10:
                recommendations.append("Low profit margin - focus on cost reduction and revenue optimization")
            elif profit_margin > 25:
                recommendations.append("Strong profit margin - consider reinvestment for growth")
            
            # Cash flow recommendations
            cash_flow_gaps = budget_summary.get("cash_flow_summary", {}).get("cash_flow_gaps", 0)
            if cash_flow_gaps > 0:
                recommendations.append("Cash flow gaps identified - arrange financing or adjust timing")
            
            # Cost optimization
            feed_cost_ratio = budget_summary.get("cost_structure", {}).get("feed_costs", {}).get("percentage_of_revenue", 0)
            if feed_cost_ratio > 60:
                recommendations.append("High feed costs - negotiate with suppliers or improve feed efficiency")
            
            # Revenue diversification
            analysis_opportunities = budget_analysis.get("optimization_opportunities", [])
            recommendations.extend(analysis_opportunities)
            
            # General recommendations
            recommendations.extend([
                "Monitor actual vs. budgeted performance monthly",
                "Update budget quarterly based on actual performance",
                "Establish key performance indicators for tracking",
                "Consider scenario planning for risk management"
            ])
            
        except Exception as e:
            logger.error(f"Error generating budget recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations
    
    @measure_time("financial_forecasting")
    def create_financial_forecast(self, farm_id: int, months_ahead: int = 12) -> Dict[str, Any]:
        """
        Create detailed financial forecasting with multiple scenarios
        """
        try:
            # Get current financial position
            current_position = self._get_current_financial_position(farm_id)
            
            # Get historical trends
            trends = self._analyze_financial_trends(farm_id, months=24)
            
            # Generate forecasts
            revenue_forecast = self._forecast_revenue_trends(trends, months_ahead)
            expense_forecast = self._forecast_expense_trends(trends, months_ahead)
            cash_flow_forecast = self._forecast_cash_flow(revenue_forecast, expense_forecast)
            
            # Create forecasting scenarios
            forecast_scenarios = self._create_forecast_scenarios(revenue_forecast, expense_forecast)
            
            # Financial projections
            projections = self._create_financial_projections(revenue_forecast, expense_forecast)
            
            # Risk analysis
            risk_analysis = self._analyze_forecast_risks(forecast_scenarios)
            
            return {
                "farm_id": farm_id,
                "forecast_period": f"{months_ahead} months ahead",
                "current_position": current_position,
                "historical_trends": trends,
                "forecasts": {
                    "revenue": revenue_forecast,
                    "expenses": expense_forecast,
                    "cash_flow": cash_flow_forecast
                },
                "scenarios": forecast_scenarios,
                "projections": projections,
                "risk_analysis": risk_analysis,
                "recommendations": self._generate_forecast_recommendations(forecast_scenarios, risk_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error creating financial forecast: {e}")
            return {"error": f"Financial forecasting failed: {str(e)}"}
    
    def _get_current_financial_position(self, _):
        """Get current financial position"""
        try:
            # Get current month's financial data
            current_month = datetime.utcnow().replace(day=1)
            next_month = (current_month + timedelta(days=32)).replace(day=1)
            
            # Current month sales
            current_sales = self.session.query(Sale).filter(
                Sale.date >= current_month,
                Sale.date < next_month
            ).all()
            
            # Current month expenses
            current_expenses = self.session.query(Expense).filter(
                Expense.date >= current_month,
                Expense.date < next_month
            ).all()
            
            # Calculate totals
            current_revenue_afg = sum(sale.total_amount_afg or 0 for sale in current_sales)
            current_revenue_usd = sum(sale.total_amount_usd or 0 for sale in current_sales)
            current_expenses_afg = sum(expense.amount_afg or 0 for expense in current_expenses)
            current_expenses_usd = sum(expense.amount_usd or 0 for expense in current_expenses)
            
            # Calculate profit
            current_profit_afg = current_revenue_afg - current_expenses_afg
            current_profit_usd = current_revenue_usd - current_expenses_usd
            
            return {
                "month": current_month.strftime('%Y-%m'),
                "revenue": {
                    "afg": round(current_revenue_afg),
                    "usd": round(current_revenue_usd)
                },
                "expenses": {
                    "afg": round(current_expenses_afg),
                    "usd": round(current_expenses_usd)
                },
                "profit": {
                    "afg": round(current_profit_afg),
                    "usd": round(current_profit_usd),
                    "margin_afg": round((current_profit_afg / max(current_revenue_afg, 1)) * 100, 1),
                    "margin_usd": round((current_profit_usd / max(current_revenue_usd, 1)) * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting current financial position: {e}")
            return {"error": "Current position analysis failed"}
    
    def _analyze_financial_trends(self, farm_id: int, months: int = 24) -> Dict:
        """Analyze historical financial trends"""
        try:
            end_date = datetime.utcnow().replace(day=1)
            start_date = (end_date - timedelta(days=months*30)).replace(day=1)
            
            # Get monthly aggregated data
            monthly_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_month = (current_date + timedelta(days=32)).replace(day=1)
                
                # Get sales for the month
                sales = self.session.query(Sale).filter(
                    Sale.date >= current_date,
                    Sale.date < next_month
                ).all()
                
                # Get expenses for the month
                expenses = self.session.query(Expense).filter(
                    Expense.date >= current_date,
                    Expense.date < next_month
                ).all()
                
                # Calculate monthly totals
                monthly_revenue_afg = sum(sale.total_amount_afg or 0 for sale in sales)
                monthly_revenue_usd = sum(sale.total_amount_usd or 0 for sale in sales)
                monthly_expenses_afg = sum(expense.amount_afg or 0 for expense in expenses)
                monthly_expenses_usd = sum(expense.amount_usd or 0 for expense in expenses)
                monthly_profit_afg = monthly_revenue_afg - monthly_expenses_afg
                monthly_profit_usd = monthly_revenue_usd - monthly_expenses_usd
                
                monthly_data.append({
                    "month": current_date.strftime('%Y-%m'),
                    "revenue_afg": monthly_revenue_afg,
                    "revenue_usd": monthly_revenue_usd,
                    "expenses_afg": monthly_expenses_afg,
                    "expenses_usd": monthly_expenses_usd,
                    "profit_afg": monthly_profit_afg,
                    "profit_usd": monthly_profit_usd,
                    "profit_margin_afg": (monthly_profit_afg / max(monthly_revenue_afg, 1)) * 100,
                    "profit_margin_usd": (monthly_profit_usd / max(monthly_revenue_usd, 1)) * 100
                })
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # Calculate trend statistics
            revenue_trend_afg = self._calculate_trend([d["revenue_afg"] for d in monthly_data])
            revenue_trend_usd = self._calculate_trend([d["revenue_usd"] for d in monthly_data])
            expense_trend_afg = self._calculate_trend([d["expenses_afg"] for d in monthly_data])
            profit_trend_afg = self._calculate_trend([d["profit_afg"] for d in monthly_data])
            
            # Seasonal analysis
            seasonal_patterns = self._analyze_seasonal_patterns(monthly_data)
            
            return {
                "monthly_data": monthly_data,
                "trends": {
                    "revenue_afg": revenue_trend_afg,
                    "revenue_usd": revenue_trend_usd,
                    "expenses_afg": expense_trend_afg,
                    "profit_afg": profit_trend_afg
                },
                "seasonal_patterns": seasonal_patterns,
                "summary": {
                    "average_monthly_revenue_afg": round(np.mean([d["revenue_afg"] for d in monthly_data])),
                    "average_monthly_revenue_usd": round(np.mean([d["revenue_usd"] for d in monthly_data])),
                    "average_monthly_expenses_afg": round(np.mean([d["expenses_afg"] for d in monthly_data])),
                    "average_monthly_profit_afg": round(np.mean([d["profit_afg"] for d in monthly_data])),
                    "profit_volatility": round(np.std([d["profit_afg"] for d in monthly_data]), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing financial trends: {e}")
            return {"error": "Trend analysis failed"}
    
    def _calculate_trend(self, data: List[float]) -> Dict:
        """Calculate trend statistics for a data series"""
        try:
            if len(data) < 2:
                return {"slope": 0, "r_squared": 0, "trend": "stable"}
            
            x = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = np.polyfit(x, data, 1)
            
            trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            trend_strength = "strong" if r_value**2 > 0.7 else "moderate" if r_value**2 > 0.4 else "weak"
            
            return {
                "slope": round(slope, 2),
                "r_squared": round(r_value**2, 3),
                "trend": trend_direction,
                "strength": trend_strength,
                "monthly_change_rate": round((slope / np.mean(data)) * 100, 2) if np.mean(data) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {"slope": 0, "r_squared": 0, "trend": "stable"}
    
    def _analyze_seasonal_patterns(self, monthly_data: List[Dict]) -> Dict:
        """Analyze seasonal patterns in financial data"""
        try:
            # Group by month number
            monthly_groups = {}
            for data in monthly_data:
                month_num = int(data["month"].split('-')[1])
                if month_num not in monthly_groups:
                    monthly_groups[month_num] = []
                monthly_groups[month_num].append(data["revenue_afg"])
            
            # Calculate seasonal indices
            overall_avg = np.mean([d["revenue_afg"] for d in monthly_data])
            seasonal_indices = {}
            
            for month_num in range(1, 13):
                if month_num in monthly_groups:
                    month_avg = np.mean(monthly_groups[month_num])
                    seasonal_indices[month_num] = round(month_avg / overall_avg, 3) if overall_avg > 0 else 1.0
            
            # Identify peak and low seasons
            if seasonal_indices:
                peak_month = max(seasonal_indices.keys(), key=lambda m: seasonal_indices[m])
                low_month = min(seasonal_indices.keys(), key=lambda m: seasonal_indices[m])
            else:
                peak_month = low_month = 6  # Default mid-year
            
            return {
                "seasonal_indices": seasonal_indices,
                "peak_month": peak_month,
                "low_month": low_month,
                "seasonality_strength": round(max(seasonal_indices.values()) - min(seasonal_indices.values()), 3) if seasonal_indices else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return {"error": "Seasonal analysis failed"}
    
    def _forecast_revenue_trends(self, trends, months_ahead):
        """Forecast revenue based on historical trends"""
        try:
            historical_data = trends.get("monthly_data", [])
            revenue_trend = trends.get("trends", {}).get("revenue_afg", {})
            seasonal_patterns = trends.get("seasonal_patterns", {})
            
            if not historical_data:
                return {"error": "Insufficient historical data for revenue forecasting"}
            
            # Get last known values
            last_revenue = historical_data[-1]["revenue_afg"] if historical_data else 0
            trend_slope = revenue_trend.get("slope", 0)
            
            # Generate forecasts
            monthly_forecasts = []
            for i in range(1, months_ahead + 1):
                # Base trend forecast
                base_forecast = last_revenue + (trend_slope * i)
                
                # Apply seasonal adjustment
                forecast_month = (datetime.utcnow().month + i - 1) % 12 + 1
                seasonal_factor = seasonal_patterns.get("seasonal_indices", {}).get(forecast_month, 1.0)
                
                # Final forecast
                forecasted_revenue = base_forecast * seasonal_factor
                
                monthly_forecasts.append({
                    "month": i,
                    "forecasted_revenue": round(max(0, forecasted_revenue)),
                    "base_forecast": round(max(0, base_forecast)),
                    "seasonal_factor": seasonal_factor,
                    "confidence": "high" if revenue_trend.get("strength") == "strong" else "medium"
                })
            
            # Summary statistics
            total_forecasted_revenue = sum(f["forecasted_revenue"] for f in monthly_forecasts)
            average_monthly_revenue = total_forecasted_revenue / months_ahead
            
            return {
                "monthly_forecasts": monthly_forecasts,
                "summary": {
                    "total_forecasted_revenue": round(total_forecasted_revenue),
                    "average_monthly_revenue": round(average_monthly_revenue),
                    "trend_direction": revenue_trend.get("trend", "stable"),
                    "confidence_level": revenue_trend.get("strength", "moderate")
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting revenue trends: {e}")
            return {"error": "Revenue forecasting failed"}
    
    def _forecast_expense_trends(self, trends, months_ahead):
        """Forecast expenses based on historical trends"""
        try:
            historical_data = trends.get("monthly_data", [])
            expense_trend = trends.get("trends", {}).get("expenses_afg", {})
            
            if not historical_data:
                return {"error": "Insufficient historical data for expense forecasting"}
            
            # Get last known values
            last_expenses = historical_data[-1]["expenses_afg"] if historical_data else 0
            trend_slope = expense_trend.get("slope", 0)
            
            # Apply inflation factor (assume 6% annual inflation)
            monthly_inflation = (1.06 ** (1/12)) - 1
            
            # Generate forecasts
            monthly_forecasts = []
            for i in range(1, months_ahead + 1):
                # Base trend forecast
                base_forecast = last_expenses + (trend_slope * i)
                
                # Apply inflation adjustment
                inflation_factor = (1 + monthly_inflation) ** i
                forecasted_expenses = base_forecast * inflation_factor
                
                monthly_forecasts.append({
                    "month": i,
                    "forecasted_expenses": round(max(0, forecasted_expenses)),
                    "base_forecast": round(max(0, base_forecast)),
                    "inflation_factor": round(inflation_factor, 3),
                    "confidence": "high" if expense_trend.get("strength") == "strong" else "medium"
                })
            
            # Summary statistics
            total_forecasted_expenses = sum(f["forecasted_expenses"] for f in monthly_forecasts)
            average_monthly_expenses = total_forecasted_expenses / months_ahead
            
            return {
                "monthly_forecasts": monthly_forecasts,
                "summary": {
                    "total_forecasted_expenses": round(total_forecasted_expenses),
                    "average_monthly_expenses": round(average_monthly_expenses),
                    "trend_direction": expense_trend.get("trend", "stable"),
                    "annual_inflation_rate": 6.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting expense trends: {e}")
            return {"error": "Expense forecasting failed"}
    
    def _forecast_cash_flow(self, revenue_forecast, expense_forecast):
        """Forecast cash flow based on revenue and expense forecasts"""
        try:
            revenue_forecasts = revenue_forecast.get("monthly_forecasts", [])
            expense_forecasts = expense_forecast.get("monthly_forecasts", [])
            
            if not revenue_forecasts or not expense_forecasts:
                return {"error": "Insufficient data for cash flow forecasting"}
            
            # Generate cash flow forecasts
            cash_flow_forecasts = []
            cumulative_cash_flow = 0
            
            for i, revenue_forecast in enumerate(revenue_forecasts):
                revenue = revenue_forecast["forecasted_revenue"]
                expenses = revenue_forecast["forecasted_expenses"]
                net_cash_flow = revenue - expenses
                cumulative_cash_flow += net_cash_flow
                
                cash_flow_forecasts.append({
                    "month": i + 1,
                    "revenue": revenue,
                    "expenses": expenses,
                    "net_cash_flow": round(net_cash_flow),
                    "cumulative_cash_flow": round(cumulative_cash_flow)
                })
            
            # Calculate cash flow metrics
            total_net_cash_flow = sum(cf["net_cash_flow"] for cf in cash_flow_forecasts)
            min_cumulative = min(cf["cumulative_cash_flow"] for cf in cash_flow_forecasts)
            max_cumulative = max(cf["cumulative_cash_flow"] for cf in cash_flow_forecasts)
            
            return {
                "monthly_forecasts": cash_flow_forecasts,
                "summary": {
                    "total_net_cash_flow": round(total_net_cash_flow),
                    "average_monthly_net": round(total_net_cash_flow / len(cash_flow_forecasts)),
                    "minimum_cash_position": round(min_cumulative),
                    "maximum_cash_position": round(max_cumulative),
                    "cash_flow_trend": "positive" if total_net_cash_flow > 0 else "negative"
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting cash flow: {e}")
            return {"error": "Cash flow forecasting failed"}
    
    def _create_forecast_scenarios(self, revenue_forecast: Dict, expense_forecast: Dict) -> Dict:
        """Create multiple forecast scenarios"""
        try:
            scenarios = {}
            
            # Base case (most likely)
            scenarios["base_case"] = self._create_single_scenario(
                revenue_forecast, expense_forecast, "Base Case", "Most likely scenario based on historical trends"
            )
            
            # Optimistic scenario
            optimistic_revenue = self._adjust_forecast_scenarios(revenue_forecast, 1.15)  # 15% higher
            optimistic_expenses = self._adjust_forecast_scenarios(expense_forecast, 0.95)  # 5% lower
            scenarios["optimistic"] = self._create_single_scenario(
                optimistic_revenue, optimistic_expenses, "Optimistic", "Best case scenario with favorable conditions"
            )
            
            # Pessimistic scenario
            pessimistic_revenue = self._adjust_forecast_scenarios(revenue_forecast, 0.85)  # 15% lower
            pessimistic_expenses = self._adjust_forecast_scenarios(expense_forecast, 1.05)  # 5% higher
            scenarios["pessimistic"] = self._create_single_scenario(
                pessimistic_revenue, pessimistic_expenses, "Pessimistic", "Worst case scenario with adverse conditions"
            )
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error creating forecast scenarios: {e}")
            return {"error": "Scenario creation failed"}
    
    def _create_single_scenario(self, revenue_forecast, expense_forecast, name, description):
        """Create a single forecast scenario"""
        try:
            revenue_forecasts = revenue_forecast.get("monthly_forecasts", [])
            expense_forecasts = expense_forecast.get("monthly_forecasts", [])
            
            total_revenue = sum(f["forecasted_revenue"] for f in revenue_forecasts)
            total_expenses = sum(f["forecasted_expenses"] for f in expense_forecasts)
            net_profit = total_revenue - total_expenses
            
            return {
                "name": name,
                "description": description,
                "total_revenue": round(total_revenue),
                "total_expenses": round(total_expenses),
                "net_profit": round(net_profit),
                "profit_margin": round((net_profit / max(total_revenue, 1)) * 100, 1),
                "monthly_averages": {
                    "revenue": round(total_revenue / len(revenue_forecasts)),
                    "expenses": round(total_expenses / len(expense_forecasts)),
                    "profit": round(net_profit / len(revenue_forecasts))
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating single scenario: {e}")
            return {"error": "Single scenario creation failed"}
    
    def _adjust_forecast_scenarios(self, forecast: Dict, adjustment_factor: float) -> Dict:
        """Adjust forecast data by a factor"""
        try:
            adjusted_forecasts = []
            for f in forecast.get("monthly_forecasts", []):
                adjusted_f = f.copy()
                if "forecasted_revenue" in adjusted_f:
                    adjusted_f["forecasted_revenue"] = round(f["forecasted_revenue"] * adjustment_factor)
                elif "forecasted_expenses" in adjusted_f:
                    adjusted_f["forecasted_expenses"] = round(f["forecasted_expenses"] * adjustment_factor)
                adjusted_forecasts.append(adjusted_f)
            
            return {
                "monthly_forecasts": adjusted_forecasts,
                "summary": forecast.get("summary", {})
            }
            
        except Exception as e:
            logger.error(f"Error adjusting forecast scenarios: {e}")
            return forecast
    
    def _create_financial_projections(self, revenue_forecast: Dict, expense_forecast: Dict) -> Dict:
        """Create comprehensive financial projections"""
        try:
            # Get scenario data
            scenarios = self._create_forecast_scenarios(revenue_forecast, expense_forecast)
            
            # Calculate projected ratios and metrics
            projections = {}
            
            for scenario_name, scenario in scenarios.items():
                projections[scenario_name] = {
                    "profitability_ratios": {
                        "profit_margin": scenario["profit_margin"],
                        "revenue_growth_rate": 0,  # Would need historical comparison
                        "expense_ratio": round((scenario["total_expenses"] / max(scenario["total_revenue"], 1)) * 100, 1)
                    },
                    "cash_flow_metrics": {
                        "operating_cash_flow": scenario["net_profit"],
                        "cash_flow_per_month": scenario["monthly_averages"]["profit"],
                        "cash_flow_stability": "stable" if abs(scenario["profit_margin"]) > 10 else "volatile"
                    },
                    "financial_health": self._assess_financial_health(scenario)
                }
            
            return projections
            
        except Exception as e:
            logger.error(f"Error creating financial projections: {e}")
            return {"error": "Financial projections failed"}
    
    def _assess_financial_health(self, scenario):
        """Assess financial health based on scenario data"""
        try:
            profit_margin = scenario["profit_margin"]
            
            if profit_margin > 20:
                health_status = "excellent"
                health_score = 5
            elif profit_margin > 15:
                health_status = "good"
                health_score = 4
            elif profit_margin > 10:
                health_status = "fair"
                health_score = 3
            elif profit_margin > 5:
                health_status = "poor"
                health_score = 2
            else:
                health_status = "critical"
                health_score = 1
            
            return {
                "status": health_status,
                "score": health_score,
                "key_concerns": self._identify_financial_concerns(scenario),
                "recommendations": self._generate_health_recommendations(health_status)
            }
            
        except Exception as e:
            logger.error(f"Error assessing financial health: {e}")
            return {"status": "unknown", "score": 0}
    
    def _identify_financial_concerns(self, scenario):
        """Identify financial concerns from scenario"""
        concerns = []
        
        profit_margin = scenario["profit_margin"]
        profit = scenario["net_profit"]
        
        if profit_margin < 0:
            concerns.append("Projected losses in this scenario")
        elif profit_margin < 5:
            concerns.append("Very low profit margins")
        
        if profit < 0:
            concerns.append("Negative cash flow")
        
        return concerns
    
    def _generate_health_recommendations(self, health_status):
        """Generate recommendations based on financial health"""
        recommendations = []
        
        if health_status in ["poor", "critical"]:
            recommendations.extend([
                "Focus on cost reduction strategies",
                "Review and optimize pricing",
                "Improve operational efficiency"
            ])
        elif health_status == "fair":
            recommendations.extend([
                "Monitor key performance indicators",
                "Consider moderate growth investments"
            ])
        else:
            recommendations.extend([
                "Strong financial performance - consider expansion",
                "Invest in quality improvements",
                "Build cash reserves"
            ])
        
        return recommendations
    
    def _analyze_forecast_risks(self, scenarios):
        """Analyze risks in financial forecasts"""
        try:
            scenario_profits = [s["net_profit"] for s in scenarios.values()]
            
            # Calculate risk metrics
            profit_variance = np.var(scenario_profits)
            profit_range = max(scenario_profits) - min(scenario_profits)
            expected_profit = np.mean(scenario_profits)
            
            # Risk assessment
            risk_level = "high" if profit_range > expected_profit * 0.5 else "moderate" if profit_range > expected_profit * 0.2 else "low"
            
            # Key risk factors
            risk_factors = []
            
            if min(scenario_profits) < 0:
                risk_factors.append("Potential for losses in adverse scenarios")
            
            profit_volatility = profit_range / max(abs(expected_profit), 1)
            if profit_volatility > 0.3:
                risk_factors.append("High profit volatility")
            
            return {
                "risk_level": risk_level,
                "profit_variance": round(profit_variance, 2),
                "profit_range": round(profit_range),
                "expected_profit": round(expected_profit),
                "risk_factors": risk_factors,
                "risk_mitigation": self._suggest_risk_mitigation(risk_level, scenarios)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing forecast risks: {e}")
            return {"error": "Risk analysis failed"}
    
    def _suggest_risk_mitigation(self, risk_level, _):
        """Suggest risk mitigation strategies"""
        strategies = []
        
        if risk_level == "high":
            strategies.extend([
                "Develop contingency plans for adverse scenarios",
                "Build cash reserves for unexpected challenges",
                "Diversify revenue streams",
                "Implement flexible cost structure"
            ])
        elif risk_level == "moderate":
            strategies.extend([
                "Monitor key performance indicators closely",
                "Maintain moderate cash reserves",
                "Regular scenario planning updates"
            ])
        else:
            strategies.extend([
                "Maintain current risk management practices",
                "Consider strategic investments for growth"
            ])
        
        return strategies
    
    def _generate_forecast_recommendations(self, scenarios: Dict, risk_analysis: Dict) -> List[str]:
        """Generate recommendations based on forecast analysis"""
        recommendations = []
        
        try:
            # Scenario-based recommendations
            base_case = scenarios.get("base_case", {})
            optimistic = scenarios.get("optimistic", {})
            pessimistic = scenarios.get("pessimistic", {})
            
            if base_case.get("profit_margin", 0) > 15:
                recommendations.append("Strong financial outlook - consider expansion opportunities")
            elif base_case.get("profit_margin", 0) < 10:
                recommendations.append("Moderate profitability - focus on efficiency improvements")
            
            # Risk-based recommendations
            risk_level = risk_analysis.get("risk_level", "moderate")
            if risk_level == "high":
                recommendations.append("High risk detected - implement robust risk management")
            
            # Cash flow recommendations
            cash_flow_concerns = risk_analysis.get("risk_factors", [])
            if any("losses" in concern.lower() for concern in cash_flow_concerns):
                recommendations.append("Prepare contingency plans for potential losses")
            
            # General recommendations
            recommendations.extend([
                "Update forecasts monthly with actual performance data",
                "Establish early warning indicators for key metrics",
                "Review and adjust assumptions quarterly",
                "Consider professional financial advisory support"
            ])
            
        except Exception as e:
            logger.error(f"Error generating forecast recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations
    
    # Helper methods for budget creation
    def _create_seasonal_revenue_distribution(self, base_revenue: float, assumptions: Dict) -> Dict:
        """Create seasonal revenue distribution"""
        seasonal_factors = assumptions.get("seasonal_factors", {})
        
        total_factor = sum(seasonal_factors.values())
        normalized_factors = {k: v/total_factor * 4 for k, v in seasonal_factors.items()}
        
        return {
            "Q1": round(base_revenue * normalized_factors.get("Q1", 0.95)),
            "Q2": round(base_revenue * normalized_factors.get("Q2", 1.05)),
            "Q3": round(base_revenue * normalized_factors.get("Q3", 1.10)),
            "Q4": round(base_revenue * normalized_factors.get("Q4", 1.00))
        }
    
    def _create_monthly_revenue_distribution(self, revenue_categories: Dict, assumptions: Dict) -> Dict:
        """Create monthly revenue distribution"""
        monthly_distribution = {}
        
        for quarter, amount in revenue_categories.get("egg_sales", {}).get("seasonal_distribution", {}).items():
            monthly_amount = amount / 3  # Split quarter into months
            for month_offset in range(3):
                month_num = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}[quarter] + month_offset
                if month_num <= 12:
                    month_key = f"month_{month_num:02d}"
                    monthly_distribution[month_key] = {
                        "total_afg": round(monthly_amount),
                        "total_usd": round(monthly_amount / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
                    }
        
        return monthly_distribution
    
    def _create_monthly_expense_distribution(self, expense_categories: Dict, assumptions: Dict) -> Dict:
        """Create monthly expense distribution"""
        monthly_distribution = {}
        
        # Most expenses are relatively stable monthly
        monthly_expense_base = sum(cat.get("budget_afg", 0) for cat in expense_categories.values()) / 12
        
        for month in range(1, 13):
            month_key = f"month_{month:02d}"
            # Apply seasonal adjustments for some expenses
            seasonal_factor = assumptions.get("seasonal_factors", {}).get(f"Q{((month-1)//3)+1}", 1.0)
            adjusted_expense = monthly_expense_base * seasonal_factor
            
            monthly_distribution[month_key] = {
                "total_afg": round(adjusted_expense),
                "total_usd": round(adjusted_expense / assumptions["economic_factors"]["exchange_rate_afg_to_usd"])
            }
        
        return monthly_distribution
    
    def _generate_cash_flow_recommendations(self, monthly_cash_flow: Dict) -> List[str]:
        """Generate cash flow management recommendations"""
        recommendations = []
        
        # Check for cash flow gaps
        min_cumulative = min(m["cumulative_cash_flow"] for m in monthly_cash_flow.values())
        if min_cumulative < 0:
            recommendations.append(f"Potential cash shortfall of {abs(min_cumulative):,.0f} AFG - arrange financing")
        
        # Check for seasonal patterns
        monthly_flows = [m["operating_cash_flow"] for m in monthly_cash_flow.values()]
        if max(monthly_flows) / abs(min(monthly_flows)) > 2:
            recommendations.append("High seasonal variation in cash flow - plan for working capital management")
        
        # General recommendations
        recommendations.extend([
            "Monitor cash flow weekly during critical periods",
            "Maintain line of credit for seasonal variations",
            "Consider accelerating receivables collection",
            "Negotiate payment terms with suppliers"
        ])
        
        return recommendations