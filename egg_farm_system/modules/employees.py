"""
Employee and Salary Management Module
"""
from egg_farm_system.utils.i18n import tr

import logging
from datetime import datetime, date
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Employee, SalaryPayment, SalaryPeriod, Expense

logger = logging.getLogger(__name__)

class EmployeeManager:
    """Manages CRUD operations for Employees."""

    def create_employee(self, full_name, job_title, salary_amount, salary_period, hire_date=None):
        """Creates a new employee."""
        session = DatabaseManager.get_session()
        try:
            employee = Employee(
                full_name=full_name,
                job_title=job_title,
                salary_amount=salary_amount,
                salary_period=salary_period,
                hire_date=hire_date or datetime.utcnow()
            )
            session.add(employee)
            session.commit()
            logger.info(f"Employee created: {full_name}")
            return employee
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating employee: {e}")
            raise
        finally:
            session.close()

    def get_all_employees(self, active_only=True):
        """Retrieves all employees."""
        session = DatabaseManager.get_session()
        try:
            query = session.query(Employee)
            if active_only:
                query = query.filter(Employee.is_active == True)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all employees: {e}")
            return []
        finally:
            session.close()

    def get_employee_by_id(self, employee_id):
        """Retrieves a single employee by their ID."""
        session = DatabaseManager.get_session()
        try:
            return session.query(Employee).filter(Employee.id == employee_id).first()
        except Exception as e:
            logger.error(f"Error getting employee by ID: {e}")
            return None
        finally:
            session.close()

    def update_employee(self, employee_id, **data):
        """Updates an employee's details."""
        session = DatabaseManager.get_session()
        try:
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise ValueError("Employee not found.")
            for key, value in data.items():
                setattr(employee, key, value)
            session.commit()
            logger.info(f"Employee {employee_id} updated.")
            return employee
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating employee: {e}")
            raise
        finally:
            session.close()
    
    def set_employee_status(self, employee_id, is_active: bool):
        """Sets an employee's active status."""
        return self.update_employee(employee_id, is_active=is_active)


class SalaryManager:
    """Manages salary payments."""

    def record_payment(self, employee_id, amount_paid, period_start, period_end, payment_date=None, notes=None):
        """Records a salary payment and creates a corresponding expense."""
        session = DatabaseManager.get_session()
        try:
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise ValueError("Employee not found.")

            # Convert date objects to datetime if needed
            if isinstance(period_start, date) and not isinstance(period_start, datetime):
                period_start = datetime.combine(period_start, datetime.min.time())
            if isinstance(period_end, date) and not isinstance(period_end, datetime):
                period_end = datetime.combine(period_end, datetime.min.time())
            if payment_date is None:
                payment_date = datetime.utcnow()
            elif isinstance(payment_date, date) and not isinstance(payment_date, datetime):
                payment_date = datetime.combine(payment_date, datetime.min.time())

            # 1. Create the salary payment record
            payment = SalaryPayment(
                employee_id=employee_id,
                amount_paid=amount_paid,
                period_start=period_start,
                period_end=period_end,
                payment_date=payment_date,
                notes=notes
            )
            session.add(payment)

            # 2. Create a corresponding expense record
            # We assume salary is a general expense not tied to a specific farm.
            # You might want to associate it with a farm if needed.
            # Format dates for description (handle both date and datetime)
            period_start_str = period_start.strftime("%Y-%m-%d") if isinstance(period_start, datetime) else str(period_start)
            period_end_str = period_end.strftime("%Y-%m-%d") if isinstance(period_end, datetime) else str(period_end)
            
            expense = Expense(
                farm_id=1, # Defaulting to farm 1, this could be improved
                category="Salaries",
                description=f"Salary for {employee.full_name} for period {period_start_str} to {period_end_str}",
                amount_afg=amount_paid,
                amount_usd=0, # Assuming salary is paid in AFN
                exchange_rate_used=1,
                date=payment_date  # Use the converted datetime
            )
            session.add(expense)
            
            session.commit()
            logger.info(f"Salary payment of {amount_paid} recorded for employee {employee_id}")
            return payment
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording salary payment: {e}")
            raise
        finally:
            session.close()
            
    def get_payments_for_employee(self, employee_id):
        """Retrieves all salary payments for a given employee."""
        session = DatabaseManager.get_session()
        try:
            return session.query(SalaryPayment).filter(SalaryPayment.employee_id == employee_id).all()
        except Exception as e:
            logger.error(f"Error getting payments for employee {employee_id}: {e}")
            return []
        finally:
            session.close()

