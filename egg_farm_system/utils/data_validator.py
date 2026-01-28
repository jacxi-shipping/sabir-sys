"""
Data validation for bulk imports
"""
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate imported data before insertion"""
    
    @staticmethod
    def validate_parties(data: list) -> tuple:
        """
        Validate parties import data
        
        Args:
            data: List of dictionaries with party data
            
        Returns:
            Tuple of (valid_rows, errors)
        """
        valid = []
        errors = []
        
        for idx, row in enumerate(data, start=1):
            try:
                # Check required fields
                if not row.get('name') or not str(row.get('name')).strip():
                    errors.append(f"Row {idx}: Name is required and cannot be empty")
                    continue
                
                # Validate phone format if provided
                phone = str(row.get('phone', '')).strip()
                if phone:
                    # Allow various phone formats
                    if not re.match(r'^[\+\d\-\(\)\s]{7,20}$', phone):
                        errors.append(f"Row {idx}: Invalid phone format: {phone}")
                        continue
                
                # Clean and prepare data
                validated_row = {
                    'name': str(row['name']).strip(),
                    'phone': phone if phone else None,
                    'address': str(row.get('address', '')).strip() if row.get('address') else None,
                    'notes': str(row.get('notes', '')).strip() if row.get('notes') else None
                }
                
                valid.append(validated_row)
                
            except Exception as e:
                errors.append(f"Row {idx}: Validation error - {str(e)}")
        
        return valid, errors
    
    @staticmethod
    def validate_raw_materials(data: list) -> tuple:
        """
        Validate raw materials import data
        
        Args:
            data: List of dictionaries with raw material data
            
        Returns:
            Tuple of (valid_rows, errors)
        """
        valid = []
        errors = []
        
        for idx, row in enumerate(data, start=1):
            try:
                # Check required fields
                if not row.get('name') or not str(row.get('name')).strip():
                    errors.append(f"Row {idx}: Name is required")
                    continue
                
                if not row.get('unit') or not str(row.get('unit')).strip():
                    errors.append(f"Row {idx}: Unit is required")
                    continue
                
                # Validate low stock alert if provided
                low_stock_alert = row.get('low_stock_alert', 0)
                try:
                    low_stock_alert = float(low_stock_alert) if low_stock_alert else 0
                    if low_stock_alert < 0:
                        errors.append(f"Row {idx}: Low stock alert cannot be negative")
                        continue
                except ValueError:
                    errors.append(f"Row {idx}: Low stock alert must be a number")
                    continue
                
                # Clean and prepare data
                validated_row = {
                    'name': str(row['name']).strip(),
                    'unit': str(row['unit']).strip(),
                    'low_stock_alert': low_stock_alert,
                    'supplier_name': str(row.get('supplier_name', '')).strip() if row.get('supplier_name') else None,
                    'notes': str(row.get('notes', '')).strip() if row.get('notes') else None
                }
                
                valid.append(validated_row)
                
            except Exception as e:
                errors.append(f"Row {idx}: Validation error - {str(e)}")
        
        return valid, errors
    
    @staticmethod
    def validate_expenses(data: list) -> tuple:
        """
        Validate expenses import data
        
        Args:
            data: List of dictionaries with expense data
            
        Returns:
            Tuple of (valid_rows, errors)
        """
        valid = []
        errors = []
        
        valid_categories = ['Labor', 'Medicine', 'Electricity', 'Water', 'Transport', 'Miscellaneous']
        
        for idx, row in enumerate(data, start=1):
            try:
                # Check required fields
                if not row.get('date'):
                    errors.append(f"Row {idx}: Date is required")
                    continue
                
                # Farm name is required
                if not row.get('farm_name') or not str(row.get('farm_name')).strip():
                    errors.append(f"Row {idx}: Farm name is required")
                    continue
                
                # Validate date
                try:
                    if isinstance(row['date'], str):
                        expense_date = datetime.strptime(str(row['date']).strip(), '%Y-%m-%d').date()
                    else:
                        expense_date = row['date']
                except ValueError:
                    errors.append(f"Row {idx}: Invalid date format (use YYYY-MM-DD)")
                    continue
                
                # Validate category
                category = str(row.get('category', '')).strip()
                if not category:
                    errors.append(f"Row {idx}: Category is required")
                    continue
                
                if category not in valid_categories:
                    errors.append(f"Row {idx}: Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}")
                    continue
                
                # Validate amount
                if not row.get('amount_afg'):
                    errors.append(f"Row {idx}: Amount (AFG) is required")
                    continue
                
                try:
                    amount_afg = float(row['amount_afg'])
                    if amount_afg <= 0:
                        errors.append(f"Row {idx}: Amount must be greater than 0")
                        continue
                except ValueError:
                    errors.append(f"Row {idx}: Amount (AFG) must be a valid number")
                    continue
                
                # Validate USD amount if provided, otherwise default to 0
                amount_usd = 0
                if row.get('amount_usd'):
                    try:
                        amount_usd = float(row['amount_usd'])
                        if amount_usd < 0:
                            errors.append(f"Row {idx}: Amount (USD) cannot be negative")
                            continue
                    except ValueError:
                        errors.append(f"Row {idx}: Amount (USD) must be a valid number")
                        continue
                
                # Validate payment method
                payment_method = str(row.get('payment_method', 'Cash')).strip()
                if payment_method not in ['Cash', 'Credit']:
                    payment_method = 'Cash'
                
                # Clean and prepare data
                validated_row = {
                    'date': expense_date,
                    'farm_name': str(row['farm_name']).strip(),
                    'category': category,
                    'amount_afg': amount_afg,
                    'amount_usd': amount_usd,
                    'description': str(row.get('description', '')).strip() if row.get('description') else None,
                    'payment_method': payment_method
                }
                
                valid.append(validated_row)
                
            except Exception as e:
                errors.append(f"Row {idx}: Validation error - {str(e)}")
        
        return valid, errors
    
    @staticmethod
    def validate_employees(data: list) -> tuple:
        """
        Validate employees import data
        
        Args:
            data: List of dictionaries with employee data
            
        Returns:
            Tuple of (valid_rows, errors)
        """
        valid = []
        errors = []
        
        for idx, row in enumerate(data, start=1):
            try:
                # Check required fields
                if not row.get('full_name') or not str(row.get('full_name')).strip():
                    errors.append(f"Row {idx}: Full name is required")
                    continue
                
                if not row.get('job_title') or not str(row.get('job_title')).strip():
                    errors.append(f"Row {idx}: Job title is required")
                    continue
                
                # Validate hire date if provided
                hire_date = None
                if row.get('hire_date'):
                    try:
                        if isinstance(row['hire_date'], str):
                            hire_date = datetime.strptime(str(row['hire_date']).strip(), '%Y-%m-%d').date()
                        else:
                            hire_date = row['hire_date']
                    except ValueError:
                        errors.append(f"Row {idx}: Invalid hire date format (use YYYY-MM-DD)")
                        continue
                
                # Validate salary amount
                if not row.get('salary_amount'):
                    errors.append(f"Row {idx}: Salary amount is required")
                    continue
                
                try:
                    salary_amount = float(row['salary_amount'])
                    if salary_amount <= 0:
                        errors.append(f"Row {idx}: Salary amount must be greater than 0")
                        continue
                except ValueError:
                    errors.append(f"Row {idx}: Salary amount must be a valid number")
                    continue
                
                # Validate salary period
                salary_period = str(row.get('salary_period', 'Monthly')).strip()
                if salary_period not in ['Monthly', 'Daily']:
                    errors.append(f"Row {idx}: Salary period must be 'Monthly' or 'Daily'")
                    continue
                
                # Validate is_active
                is_active = True
                if row.get('is_active'):
                    is_active_str = str(row['is_active']).strip().lower()
                    if is_active_str in ['no', 'false', '0', 'inactive']:
                        is_active = False
                
                # Clean and prepare data
                validated_row = {
                    'full_name': str(row['full_name']).strip(),
                    'job_title': str(row['job_title']).strip(),
                    'hire_date': hire_date,
                    'salary_amount': salary_amount,
                    'salary_period': salary_period,
                    'is_active': is_active
                }
                
                valid.append(validated_row)
                
            except Exception as e:
                errors.append(f"Row {idx}: Validation error - {str(e)}")
        
        return valid, errors
