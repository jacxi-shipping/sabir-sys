"""
Employee and Salary Management Module
"""
import logging
from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Employee, SalaryPayment, SalaryPeriod, Expense

logger = logging.getLogger(__name__)

class EmployeeManager:
    """Manages CRUD operations for Employees."""

    def __init__(self):
        self.session = DatabaseManager.get_session()

    def create_employee(self, full_name, job_title, salary_amount, salary_period, hire_date=None):
        """Creates a new employee."""
        try:
            employee = Employee(
                full_name=full_name,
                job_title=job_title,
                salary_amount=salary_amount,
                salary_period=salary_period,
                hire_date=hire_date or datetime.utcnow()
            )
            self.session.add(employee)
            self.session.commit()
            logger.info(f"Employee created: {full_name}")
            return employee
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating employee: {e}")
            raise

    def get_all_employees(self, active_only=True):
        """Retrieves all employees."""
        try:
            query = self.session.query(Employee)
            if active_only:
                query = query.filter(Employee.is_active == True)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all employees: {e}")
            return []

    def get_employee_by_id(self, employee_id):
        """Retrieves a single employee by their ID."""
        try:
            return self.session.query(Employee).filter(Employee.id == employee_id).first()
        except Exception as e:
            logger.error(f"Error getting employee by ID: {e}")
            return None

    def update_employee(self, employee_id, **data):
        """Updates an employee's details."""
        try:
            employee = self.get_employee_by_id(employee_id)
            if not employee:
                raise ValueError("Employee not found.")
            for key, value in data.items():
                setattr(employee, key, value)
            self.session.commit()
            logger.info(f"Employee {employee_id} updated.")
            return employee
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating employee: {e}")
            raise
    
    def set_employee_status(self, employee_id, is_active: bool):
        """Sets an employee's active status."""
        return self.update_employee(employee_id, is_active=is_active)


class SalaryManager:
    """Manages salary payments."""

    def __init__(self):
        self.session = DatabaseManager.get_session()

    def record_payment(self, employee_id, amount_paid, period_start, period_end, payment_date=None, notes=None):
        """Records a salary payment and creates a corresponding expense."""
        try:
            employee = self.session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise ValueError("Employee not found.")

            # 1. Create the salary payment record
            payment = SalaryPayment(
                employee_id=employee_id,
                amount_paid=amount_paid,
                period_start=period_start,
                period_end=period_end,
                payment_date=payment_date or datetime.utcnow(),
                notes=notes
            )
            self.session.add(payment)

            # 2. Create a corresponding expense record
            # We assume salary is a general expense not tied to a specific farm.
            # You might want to associate it with a farm if needed.
            expense = Expense(
                farm_id=1, # Defaulting to farm 1, this could be improved
                category="Salaries",
                description=f"Salary for {employee.full_name} for period {period_start.date()} to {period_end.date()}",
                amount_afg=amount_paid,
                amount_usd=0, # Assuming salary is paid in AFN
                exchange_rate_used=1,
                date=payment.payment_date
            )
            self.session.add(expense)
            
            self.session.commit()
            logger.info(f"Salary payment of {amount_paid} recorded for employee {employee_id}")
            return payment
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording salary payment: {e}")
            raise
            
    def get_payments_for_employee(self, employee_id):
        """Retrieves all salary payments for a given employee."""
        try:
            return self.session.query(SalaryPayment).filter(SalaryPayment.employee_id == employee_id).all()
        except Exception as e:
            logger.error(f"Error getting payments for employee {employee_id}: {e}")
            return []

