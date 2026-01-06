"""
Theme management for the Egg Farm System
"""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class ThemeManager:
    LIGHT = "light"
    DARK = "dark"
    
    # Common palette colors
    PRIMARY = "#1976d2"
    PRIMARY_HOVER = "#1565c0"
    ERROR = "#d32f2f"
    SUCCESS = "#388e3c"
    WARNING = "#f57c00"

    @staticmethod
    def get_stylesheet(theme_name):
        if theme_name == ThemeManager.DARK:
            return ThemeManager._get_dark_stylesheet()
        return ThemeManager._get_light_stylesheet()

    @staticmethod
    def _get_light_stylesheet():
        return f"""
        /* Light Theme */
        QWidget {{
          font-family: "Segoe UI", Roboto, Arial, sans-serif;
          font-size: 11pt;
          color: #222222;
          background-color: #fafafa;
        }}

        QFrame#sidebar, QFrame[role="sidebar"] {{
          background-color: #f5f7fb;
          border-right: 1px solid #e6e9ee;
        }}
        
        QFrame#content_area {{
            background-color: #ffffff;
        }}

        QGroupBox {{
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          margin-top: 6px;
          padding: 8px;
          background-color: #ffffff;
        }}

        QGroupBox::title {{
          subcontrol-origin: margin;
          left: 8px;
          padding: 0 3px;
          font-weight: 600;
          color: #333333;
        }}

        QPushButton {{
          background-color: {ThemeManager.PRIMARY};
          color: white;
          border-radius: 4px;
          padding: 6px 10px;
          border: none;
        }}

        QPushButton:hover {{
          background-color: {ThemeManager.PRIMARY_HOVER};
        }}
        
        QPushButton:disabled {{
          background-color: #bdbdbd;
          color: #f5f5f5;
        }}

        /* Sidebar Buttons */
        QFrame#sidebar QPushButton {{
          background-color: transparent;
          color: #2b2b2b;
          text-align: left;
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
        }}

        QFrame#sidebar QPushButton:hover {{
          background-color: rgba(25,118,210,0.1);
          color: {ThemeManager.PRIMARY};
        }}
        
        QFrame#sidebar QPushButton:checked {{
             background-color: rgba(25,118,210,0.15);
             color: {ThemeManager.PRIMARY};
             font-weight: bold;
             border-left: 3px solid {ThemeManager.PRIMARY};
        }}

        QFrame#sidebar QLabel {{
          color: #555555;
        }}

        /* Tables */
        QTableWidget, QTableView {{
          gridline-color: #e0e0e0;
          background-color: white;
          alternate-background-color: #f9f9f9;
          selection-background-color: {ThemeManager.PRIMARY};
          selection-color: white;
        }}
        
        QHeaderView::section {{
          background-color: #f0f4f8;
          padding: 6px;
          border: 1px solid #d0d7de;
          color: #333333;
          font-weight: bold;
        }}

        /* Inputs */
        QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{
          padding: 6px;
          border: 1px solid #d0d7de;
          border-radius: 4px;
          background-color: white;
          color: #222;
        }}
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border: 1px solid {ThemeManager.PRIMARY};
        }}

        QLabel#titleLabel {{
          font-size: 18pt;
          font-weight: 700;
          color: #1a1a1a;
        }}
        
        /* Cards/Widgets */
        QFrame[class="card"] {{
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        """

    @staticmethod
    def _get_dark_stylesheet():
        return f"""
        /* Dark Theme */
        QWidget {{
          font-family: "Segoe UI", Roboto, Arial, sans-serif;
          font-size: 11pt;
          color: #e0e0e0;
          background-color: #1e1e1e;
        }}

        QFrame#sidebar, QFrame[role="sidebar"] {{
          background-color: #252526;
          border-right: 1px solid #333333;
        }}
        
        QFrame#content_area {{
            background-color: #1e1e1e;
        }}

        QGroupBox {{
          border: 1px solid #404040;
          border-radius: 6px;
          margin-top: 6px;
          padding: 8px;
          background-color: #2d2d2d;
        }}

        QGroupBox::title {{
          subcontrol-origin: margin;
          left: 8px;
          padding: 0 3px;
          font-weight: 600;
          color: #bbbbbb;
        }}

        QPushButton {{
          background-color: {ThemeManager.PRIMARY};
          color: white;
          border-radius: 4px;
          padding: 6px 10px;
          border: none;
        }}

        QPushButton:hover {{
          background-color: {ThemeManager.PRIMARY_HOVER};
        }}
        
        QPushButton:disabled {{
          background-color: #4a4a4a;
          color: #888888;
        }}

        /* Sidebar Buttons */
        QFrame#sidebar QPushButton {{
          background-color: transparent;
          color: #cccccc;
          text-align: left;
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
        }}

        QFrame#sidebar QPushButton:hover {{
          background-color: rgba(255, 255, 255, 0.1);
          color: white;
        }}
        
        QFrame#sidebar QPushButton:checked {{
             background-color: rgba(25,118,210,0.25);
             color: #64b5f6;
             font-weight: bold;
             border-left: 3px solid #64b5f6;
        }}

        QFrame#sidebar QLabel {{
          color: #aaaaaa;
        }}

        /* Tables */
        QTableWidget, QTableView {{
          gridline-color: #404040;
          background-color: #2d2d2d;
          alternate-background-color: #353535;
          selection-background-color: {ThemeManager.PRIMARY};
          selection-color: white;
          border: 1px solid #404040;
        }}
        
        QHeaderView::section {{
          background-color: #383838;
          padding: 6px;
          border: 1px solid #404040;
          color: #e0e0e0;
          font-weight: bold;
        }}

        /* Inputs */
        QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{
          padding: 6px;
          border: 1px solid #404040;
          border-radius: 4px;
          background-color: #333333;
          color: #e0e0e0;
        }}
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border: 1px solid #64b5f6;
        }}

        QLabel#titleLabel {{
          font-size: 18pt;
          font-weight: 700;
          color: #ffffff;
        }}
        
        /* Cards/Widgets */
        QFrame[class="card"] {{
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 8px;
        }}
        """

    @staticmethod
    def apply_theme(app, theme_name):
        """Apply theme to the QApplication instance"""
        app.setStyleSheet(ThemeManager.get_stylesheet(theme_name))
        
        # We can also set the QPalette if needed for things not covered by QSS
        palette = QPalette()
        if theme_name == ThemeManager.DARK:
            # Set dark palette defaults
            palette.setColor(QPalette.Window, QColor(30, 30, 30))
            palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
            palette.setColor(QPalette.Base, QColor(45, 45, 45))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(224, 224, 224))
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
