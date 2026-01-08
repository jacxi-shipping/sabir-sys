"""
Standardized error handling utility
"""
import logging
from typing import Optional, Callable
from PySide6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for UI operations"""
    
    @staticmethod
    def handle_error(parent: QWidget, error: Exception, context: str = "", 
                    show_details: bool = False, custom_message: Optional[str] = None):
        """
        Handle an error and show appropriate message to user
        
        Args:
            parent: Parent widget for message box
            error: The exception that occurred
            context: Context description (e.g., "saving farm", "loading data")
            show_details: Whether to show technical error details
            custom_message: Custom error message to show instead of default
        """
        logger.error(f"Error {context}: {error}", exc_info=True)
        
        if custom_message:
            message = custom_message
        else:
            message = f"An error occurred while {context}."
        
        if show_details:
            message += f"\n\nTechnical details:\n{str(error)}"
        
        QMessageBox.critical(parent, "Error", message)
    
    @staticmethod
    def handle_validation_error(parent: QWidget, message: str):
        """Handle validation errors"""
        QMessageBox.warning(parent, "Validation Error", message)
    
    @staticmethod
    def handle_warning(parent: QWidget, message: str, title: str = "Warning"):
        """Handle warnings"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def handle_info(parent: QWidget, message: str, title: str = "Information"):
        """Handle informational messages"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def safe_execute(parent: QWidget, func: Callable, context: str = "", 
                    on_success: Optional[Callable] = None, 
                    on_error: Optional[Callable] = None,
                    show_error: bool = True):
        """
        Safely execute a function with error handling
        
        Args:
            parent: Parent widget
            func: Function to execute
            context: Context description for error messages
            on_success: Callback to call on success
            on_error: Callback to call on error (receives exception)
            show_error: Whether to show error message to user
        """
        try:
            result = func()
            if on_success:
                on_success(result)
            return result
        except ValueError as e:
            if show_error:
                ErrorHandler.handle_validation_error(parent, str(e))
            if on_error:
                on_error(e)
            return None
        except Exception as e:
            if show_error:
                ErrorHandler.handle_error(parent, e, context)
            if on_error:
                on_error(e)
            return None

