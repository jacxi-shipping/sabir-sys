"""
Theme management for the Egg Farm System
"""

# pylint: disable=too-many-lines

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt, QObject, Signal

class ThemeManager(QObject):
    """Manages application themes with dynamic switching support"""
    
    # Theme constants
    LIGHT = "light"
    DARK = "dark"
    FARM = "farm"  # Farm-themed palette
    
    # Current theme (shared across app)
    _current_theme = FARM
    
    # Signal emitted when theme changes
    theme_changed = Signal(str)
    
    # Common palette colors
    PRIMARY = "#1976d2"
    PRIMARY_HOVER = "#1565c0"
    ERROR = "#d32f2f"
    SUCCESS = "#388e3c"
    WARNING = "#f57c00"
    
    # Farm Theme Colors - Poultry & Livestock inspired
    FARM_BARN_RED = "#8B4513"  # Classic barn red
    FARM_BARN_RED_HOVER = "#A0522D"  # Lighter barn red
    FARM_HAY_YELLOW = "#D4A574"  # Warm hay/straw yellow
    FARM_EARTH_BROWN = "#6B4423"  # Rich earth brown
    FARM_PASTURE_GREEN = "#6B8E23"  # Pasture green
    FARM_EGGSHELL_CREAM = "#FFF8DC"  # Eggshell cream
    FARM_WARM_BEIGE = "#F5DEB3"  # Warm beige
    FARM_RUST_ORANGE = "#CD853F"  # Rust orange accents
    FARM_DEEP_BROWN = "#654321"  # Deep brown (wood/barn)
    FARM_GOLDEN_WHEAT = "#F4A460"  # Golden wheat
    FARM_SOIL_BROWN = "#8B6F47"  # Soil brown
    FARM_GRASS_GREEN = "#9ACD32"  # Fresh grass green

    @classmethod
    def set_current_theme(cls, theme_name: str):
        """Set the current theme"""
        cls._current_theme = theme_name
    
    @classmethod
    def get_current_theme(cls) -> str:
        """Get the current theme"""
        return cls._current_theme
    
    @classmethod
    def get_color(cls, color_key: str) -> str:
        """Get theme-aware color by key"""
        color_map = {
            'sidebar_bg': {
                'light': '#f5f7fb',
                'dark': '#252526',
                'farm': '#F5DEB3'
            },
            'sidebar_text': {
                'light': '#2b2b2b',
                'dark': '#cccccc',
                'farm': '#654321'
            },
            'sidebar_hover_bg': {
                'light': 'rgba(25,118,210,0.1)',
                'dark': 'rgba(255, 255, 255, 0.1)',
                'farm': 'rgba(139, 69, 19, 0.12)'
            },
            'content_bg': {
                'light': '#ffffff',
                'dark': '#1e1e1e',
                'farm': '#FFF8DC'
            },
            'text': {
                'light': '#222222',
                'dark': '#e0e0e0',
                'farm': '#2C1810'
            },
            'border': {
                'light': '#e0e0e0',
                'dark': '#404040',
                'farm': 'rgba(139, 111, 71, 0.2)'
            },
            'button_bg': {
                'light': '#34495e',
                'dark': '#424242',
                'farm': '#8B4513'
            },
            'button_hover_bg': {
                'light': '#2c3e50',
                'dark': '#505050',
                'farm': '#A0522D'
            }
        }
        return color_map.get(color_key, {}).get(cls._current_theme, color_map.get(color_key, {}).get('light', '#000000'))
    
    @staticmethod
    def get_stylesheet(theme_name):
        if theme_name == ThemeManager.DARK:
            return ThemeManager._get_dark_stylesheet()
        elif theme_name == ThemeManager.FARM:
            return ThemeManager._get_farm_stylesheet()
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
        
        /* Sidebar Special Buttons */
        QPushButton[class="sidebar-dashboard"] {{
            text-align: left;
            padding: 10px 15px;
            border: none;
            background-color: #424242;
            color: #64b5f6;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton[class="sidebar-dashboard"]:hover {{
            background-color: #4a4a4a;
        }}
        
        QPushButton[class="sidebar-action"] {{
            text-align: left;
            padding: 10px 18px;
            border: none;
            background-color: #353535;
            color: #cccccc;
            border-radius: 8px;
            font-weight: 600;
            font-size: 11pt;
        }}
        
        QPushButton[class="sidebar-action"]:hover {{
            background-color: #424242;
            color: white;
        }}
        
        QPushButton[class="sidebar-logout"] {{
            text-align: left;
            padding: 10px 18px;
            border: none;
            background-color: #D32F2F;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            font-size: 11pt;
        }}
        
        QPushButton[class="sidebar-logout"]:hover {{
            background-color: #EF5350;
        }}
        
        QComboBox[class="sidebar-combo"] {{
            background-color: #353535;
            color: #cccccc;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 5px;
        }}
        
        QComboBox[class="sidebar-combo"]:hover {{
            background-color: #424242;
        }}
        
        QPushButton[class="nav-group-header"] {{
            text-align: left;
            padding: 10px 15px;
            font-weight: bold;
            font-size: 11pt;
            border: none;
            background-color: #353535;
            color: #cccccc;
            border-radius: 4px;
        }}
        
        QPushButton[class="nav-group-header"]:hover {{
            background-color: #3a3a3a;
        }}
        
        QPushButton[class="nav-group-header"]:checked {{
            background-color: #3a3a3a;
        }}
        
        QPushButton[class="nav-group-item"] {{
            text-align: left;
            padding: 10px 20px 10px 30px;
            border: none;
            background-color: transparent;
            color: #cccccc;
            border-radius: 6px;
            font-weight: 500;
            font-size: 11pt;
        }}
        
        QPushButton[class="nav-group-item"]:hover {{
            background-color: rgba(100, 181, 246, 0.15);
            color: #64b5f6;
            border-left: 3px solid #64b5f6;
            padding-left: 27px;
        }}
        
        /* Breadcrumbs */
        QWidget#breadcrumbs QPushButton {{
            border: none;
            background-color: transparent;
            color: #64b5f6;
            text-align: left;
            padding: 2px 5px;
        }}
        
        QWidget#breadcrumbs QPushButton:hover {{
            text-decoration: underline;
        }}
        
        QPushButton[class="breadcrumb-current"] {{
            color: #e0e0e0 !important;
            font-weight: bold;
        }}
        
        QLabel[class="breadcrumb-separator"] {{
            color: #707070;
        }}

        /* Command Palette */
        QLabel[class="command-palette-header"] {{
            background-color: #1976d2;
            color: white;
            padding: 10px;
            font-weight: bold;
            font-size: 11pt;
        }}

        QLineEdit[class="command-palette-search"] {{
            border: none;
            border-bottom: 2px solid #1976d2;
            padding: 12px;
            font-size: 11pt;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }}

        QLineEdit[class="command-palette-search"]:focus {{
            border-bottom: 2px solid #64b5f6;
        }}

        QListWidget[class="command-palette-list"] {{
            border: none;
            background-color: #2d2d2d;
            outline: none;
        }}

        QListWidget[class="command-palette-list"]::item {{
            padding: 10px;
            border-bottom: 1px solid #404040;
        }}

        QListWidget[class="command-palette-list"]::item:hover {{
            background-color: #3a3a3a;
        }}

        QListWidget[class="command-palette-list"]::item:selected {{
            background-color: #424242;
            color: #64b5f6;
        }}

        QLabel[class="command-palette-footer"] {{
            background-color: #353535;
            color: #aaaaaa;
            padding: 8px;
            font-size: 9pt;
            border-top: 1px solid #404040;
        }}

        /* Notifications */
        QFrame[class="notification-item"] {{
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 8px;
            margin: 2px;
            background-color: #2d2d2d;
        }}

        QFrame[class="notification-item"]:hover {{
            background-color: #353535;
        }}

        QFrame[class="notification-item"][unread="true"] {{
            border-left: 4px solid #64b5f6;
        }}

        QLabel[class="notification-message"] {{
            color: #bbbbbb;
        }}

        QLabel[class="notification-timestamp"] {{
            color: #888888;
            font-size: 9pt;
        }}

        QLabel[class="notification-empty"] {{
            color: #888888;
            padding: 20px;
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
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateTimeEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
            border: 1px solid #64b5f6;
            background-color: #3a3a3a;
        }}
        
        QComboBox::drop-down {{
          border: none;
          width: 30px;
        }}
        
        QComboBox::down-arrow {{
          image: none;
          border-left: 5px solid transparent;
          border-right: 5px solid transparent;
          border-top: 6px solid #64b5f6;
          width: 0;
          height: 0;
        }}
        
        QComboBox QAbstractItemView {{
          background-color: #2d2d2d;
          border: 1px solid #404040;
          selection-background-color: #424242;
          selection-color: #64b5f6;
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
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background: #2d2d2d;
            width: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical {{
            background: #505050;
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: #606060;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: #2d2d2d;
            height: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: #505050;
            min-width: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: #606060;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: none;
            background-color: #2d2d2d;
            border-radius: 8px;
            top: -1px;
        }}
        
        QTabBar::tab {{
            background: #353535;
            color: #aaaaaa;
            padding: 12px 24px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
            font-weight: 500;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background: #424242;
            color: #64b5f6;
            font-weight: 700;
        }}
        
        QTabBar::tab:hover:!selected {{
            background: #3a3a3a;
            color: #cccccc;
        }}
        
        /* Tooltips */
        QToolTip {{
            background-color: #424242;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10pt;
        }}
        
        /* Checkboxes and Radio Buttons */
        QCheckBox, QRadioButton {{
            spacing: 8px;
            font-size: 11pt;
            color: #e0e0e0;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid #606060;
            border-radius: 4px;
            background-color: #333333;
        }}
        
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border: 2px solid #64b5f6;
            background-color: #3a3a3a;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: #1976d2;
            border: 2px solid #1976d2;
        }}
        
        QRadioButton::indicator {{
            border-radius: 10px;
        }}
        
        /* Progress Bars */
        QProgressBar {{
            border: none;
            border-radius: 8px;
            text-align: center;
            background-color: #353535;
            height: 24px;
            font-weight: 600;
            color: #e0e0e0;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop:0 #1976d2,
              stop:1 #64b5f6);
            border-radius: 8px;
        }}
        
        /* List Widgets */
        QListWidget {{
            border: 1px solid #404040;
            border-radius: 8px;
            background-color: #2d2d2d;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 10px;
            border-radius: 6px;
            margin: 2px;
            color: #e0e0e0;
        }}
        
        QListWidget::item:hover {{
            background-color: #3a3a3a;
        }}
        
        QListWidget::item:selected {{
            background: #424242;
            color: #64b5f6;
            font-weight: 600;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: #2d2d2d;
            border-bottom: 1px solid #404040;
            padding: 4px;
        }}
        
        QMenuBar::item {{
            padding: 8px 16px;
            border-radius: 4px;
            color: #e0e0e0;
        }}
        
        QMenuBar::item:selected {{
            background-color: #424242;
            color: #64b5f6;
        }}
        
        QMenu {{
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            color: #e0e0e0;
        }}
        
        QMenu::item:selected {{
            background-color: #424242;
            color: #64b5f6;
        }}
        
        QMenu::separator {{
            height: 1px;
            background: #404040;
            margin: 4px 8px;
        }}
        
        /* Dialog Buttons */
        QDialogButtonBox QPushButton {{
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        /* Status Labels */
        QLabel[state="success"] {{
            color: #4CAF50;
            font-weight: bold;
        }}
        
        QLabel[state="warning"] {{
            color: #FFA726;
            font-weight: bold;
        }}
        
        QLabel[state="error"] {{
            color: #EF5350;
            font-weight: bold;
        }}
        
        QLabel[state="info"] {{
            color: #64b5f6;
        }}
        
        /* Success/Error/Warning Buttons */
        QPushButton[class="success"] {{
            background-color: #388E3C;
        }}
        
        QPushButton[class="success"]:hover {{
            background-color: #4CAF50;
        }}
        
        QPushButton[class="warning"] {{
            background-color: #F57C00;
        }}
        
        QPushButton[class="warning"]:hover {{
            background-color: #FFA726;
        }}
        
        QPushButton[class="error"], QPushButton[class="danger"] {{
            background-color: #D32F2F;
        }}
        
        QPushButton[class="error"]:hover, QPushButton[class="danger"]:hover {{
            background-color: #EF5350;
        }}
        
        QPushButton[class="ghost"] {{
            background-color: transparent;
            color: #e0e0e0;
            border: 1px solid #606060;
        }}
        
        QPushButton[class="ghost"]:hover {{
            background-color: #3a3a3a;
            border-color: #64b5f6;
        }}
        
        /* Loading overlay and messages */
        QWidget[class="loading-overlay"] {{
          background-color: rgba(0, 0, 0, 180);
        }}
        
        QLabel[class="loading-label"] {{
          background-color: rgba(45, 45, 45, 240);
          border-radius: 8px;
          padding: 18px 24px;
          font-size: 14px;
          font-weight: bold;
          color: #e0e0e0;
          border: 1px solid #606060;
        }}
        
        QLabel[class="success-message"] {{
          color: #c8e6c9;
          background-color: #1b5e20;
          border: 1px solid #388e3c;
          border-radius: 4px;
          padding: 8px 12px;
          font-size: 13px;
        }}
        
        QLabel[class="badge-unread"] {{
          background-color: #EF5350;
          color: white;
          border-radius: 10px;
          padding: 2px 8px;
          font-weight: bold;
        }}
        
        /* Info Banners */
        QLabel[class="info-banner"] {{
            color: #bbbbbb;
            padding: 8px;
            background-color: #353535;
            border-radius: 4px;
        }}
        
        QLabel[class="info-banner-secondary"] {{
            color: #aaaaaa;
            padding: 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
        }}
        
        QLabel[class="warning-banner"] {{
            color: #FFCA28;
            padding: 8px;
            background-color: #3a3000;
            border-radius: 4px;
            border: 1px solid #6a5a00;
        }}
        
        /* QDialog - Full Dialog Styling */
        QDialog {{
            background-color: #2d2d2d;
            color: #e0e0e0;
        }}
        
        QDialog QLabel {{
            color: #e0e0e0;
        }}
        
        QDialog QGroupBox {{
            border: 1px solid #404040;
            border-radius: 6px;
            margin-top: 6px;
            padding: 8px;
            background-color: #353535;
            color: #e0e0e0;
        }}
        
        /* QMessageBox */
        QMessageBox {{
            background-color: #2d2d2d;
            color: #e0e0e0;
        }}
        
        QMessageBox QLabel {{
            color: #e0e0e0;
            font-size: 11pt;
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        /* QSpinBox/QDoubleSpinBox Arrow Buttons */
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            background-color: #424242;
            border-left: 1px solid #404040;
            border-top-right-radius: 4px;
            width: 18px;
        }}
        
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background-color: #505050;
        }}
        
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            background-color: #424242;
            border-left: 1px solid #404040;
            border-bottom-right-radius: 4px;
            width: 18px;
        }}
        
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: #505050;
        }}
        
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #64b5f6;
            width: 0;
            height: 0;
        }}
        
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #64b5f6;
            width: 0;
            height: 0;
        }}
        
        QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
        QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
            border-top-color: #606060;
            border-bottom-color: #606060;
        }}
        
        /* QTreeWidget */
        QTreeWidget {{
            border: 1px solid #404040;
            border-radius: 8px;
            background-color: #2d2d2d;
            alternate-background-color: #353535;
            selection-background-color: #424242;
            selection-color: #64b5f6;
            outline: none;
        }}
        
        QTreeWidget::item {{
            padding: 8px;
            border-radius: 4px;
            color: #e0e0e0;
        }}
        
        QTreeWidget::item:hover {{
            background-color: #3a3a3a;
        }}
        
        QTreeWidget::item:selected {{
            background-color: #424242;
            color: #64b5f6;
        }}
        
        QTreeWidget::branch {{
            background-color: #2d2d2d;
        }}
        
        QTreeWidget::branch:hover {{
            background-color: #3a3a3a;
        }}
        
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            image: none;
            border: none;
        }}
        
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            image: none;
            border: none;
        }}
        
        QTreeView::indicator:checked {{
            background-color: #1976d2;
            border: 2px solid #1976d2;
        }}
        
        QTreeView::indicator:unchecked {{
            background-color: #333333;
            border: 2px solid #606060;
        }}
        
        /* QSlider */
        QSlider::groove:horizontal {{
            background: #353535;
            height: 8px;
            border-radius: 4px;
            border: 1px solid #404040;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #64b5f6,
                stop:1 #1976d2);
            border: 2px solid #1976d2;
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #90caf9,
                stop:1 #42a5f5);
        }}
        
        QSlider::groove:vertical {{
            background: #353535;
            width: 8px;
            border-radius: 4px;
            border: 1px solid #404040;
        }}
        
        QSlider::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #64b5f6,
                stop:1 #1976d2);
            border: 2px solid #1976d2;
            height: 18px;
            width: 18px;
            margin: 0 -6px;
            border-radius: 9px;
        }}
        
        QSlider::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #90caf9,
                stop:1 #42a5f5);
        }}
        
        /* QToolBar */
        QToolBar {{
            background-color: #2d2d2d;
            border: none;
            border-bottom: 1px solid #404040;
            padding: 4px;
            spacing: 4px;
        }}
        
        QToolBar::separator {{
            background-color: #404040;
            width: 1px;
            margin: 4px 8px;
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            color: #e0e0e0;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
        }}
        
        QToolBar QToolButton:hover {{
            background-color: #3a3a3a;
        }}
        
        QToolBar QToolButton:pressed {{
            background-color: #424242;
        }}
        
        QToolBar QToolButton:checked {{
            background-color: #424242;
            color: #64b5f6;
        }}
        
        /* QStatusBar */
        QStatusBar {{
            background-color: #2d2d2d;
            border-top: 1px solid #404040;
            color: #aaaaaa;
            padding: 4px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        QStatusBar QLabel {{
            color: #aaaaaa;
            padding: 2px 8px;
        }}
        
        /* QSplitter */
        QSplitter::handle {{
            background-color: #404040;
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: #64b5f6;
        }}
        
        /* QDockWidget */
        QDockWidget {{
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
            color: #e0e0e0;
        }}
        
        QDockWidget::title {{
            background-color: #353535;
            padding: 8px;
            border: 1px solid #404040;
            border-radius: 4px;
            text-align: left;
            color: #e0e0e0;
            font-weight: bold;
        }}
        
        QDockWidget::close-button, QDockWidget::float-button {{
            background-color: #424242;
            border: 1px solid #404040;
            border-radius: 3px;
            padding: 2px;
        }}
        
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
            background-color: #505050;
        }}
        
        /* QCalendarWidget */
        QCalendarWidget {{
            background-color: #2d2d2d;
            color: #e0e0e0;
        }}
        
        QCalendarWidget QToolButton {{
            background-color: #353535;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 4px;
        }}
        
        QCalendarWidget QToolButton:hover {{
            background-color: #424242;
            border-color: #64b5f6;
        }}
        
        QCalendarWidget QMenu {{
            background-color: #2d2d2d;
            border: 1px solid #404040;
        }}
        
        QCalendarWidget QSpinBox {{
            background-color: #333333;
            border: 1px solid #404040;
            color: #e0e0e0;
        }}
        
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: #353535;
            border-bottom: 1px solid #404040;
        }}
        
        QCalendarWidget QAbstractItemView {{
            background-color: #2d2d2d;
            alternate-background-color: #353535;
            selection-background-color: #424242;
            selection-color: #64b5f6;
            gridline-color: #404040;
        }}
        
        QCalendarWidget QAbstractItemView:enabled {{
            color: #e0e0e0;
        }}
        
        QCalendarWidget QAbstractItemView:disabled {{
            color: #606060;
        }}
        
        /* Text Selection */
        QTextEdit, QPlainTextEdit {{
            selection-background-color: #424242;
            selection-color: #64b5f6;
        }}
        
        QLineEdit {{
            selection-background-color: #424242;
            selection-color: #64b5f6;
        }}
        
        /* Placeholder Text */
        QLineEdit[placeholderText]:!focus {{
            color: #606060;
        }}
        
        QTextEdit[placeholderText]:!focus {{
            color: #606060;
        }}
        
        /* Scrollbar Corner */
        QAbstractScrollArea::corner {{
            background-color: #2d2d2d;
            border: none;
        }}
        
        /* Disabled State Refinements */
        QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
        QDateTimeEdit:disabled, QDateEdit:disabled, QDoubleSpinBox:disabled,
        QTextEdit:disabled {{
            background-color: #2a2a2a;
            color: #606060;
            border: 1px solid #353535;
        }}
        
        QLabel:disabled {{
            color: #606060;
        }}
        
        QCheckBox:disabled, QRadioButton:disabled {{
            color: #606060;
        }}
        
        QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
            background-color: #2a2a2a;
            border: 2px solid #404040;
        }}
        
        /* QTableWidget/QTableView Enhancements */
        QTableWidget QTableCornerButton::section {{
            background-color: #383838;
            border: 1px solid #404040;
        }}
        
        QTableWidget::item:disabled {{
            color: #606060;
            background-color: #2a2a2a;
        }}
        
        /* Form Layout Spacing */
        QFormLayout {{
            spacing: 8px;
        }}
        
        /* Better Error/Warning Message Boxes */
        QMessageBox[icon="critical"] {{
            background-color: #3a1010;
        }}
        
        QMessageBox[icon="warning"] {{
            background-color: #3a2a10;
        }}
        
        QMessageBox[icon="information"] {{
            background-color: #10203a;
        }}
        """

    @staticmethod
    def _get_farm_stylesheet():
        """Premium Farm-themed stylesheet with modern design principles"""
        return f"""
        /* Premium Farm Theme - Professional UI/UX */
        QWidget {{
          font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
          font-size: 11pt;
          color: #2C1810;
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
            stop:0 {ThemeManager.FARM_EGGSHELL_CREAM}, 
            stop:1 #FEF9F3);
        }}

        QFrame#sidebar, QFrame[role="sidebar"] {{
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ThemeManager.FARM_WARM_BEIGE},
            stop:1 #F8E8D5);
          border-right: 1px solid rgba(101, 67, 33, 0.2);
        }}
        
        QFrame#content_area {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
              stop:0 {ThemeManager.FARM_EGGSHELL_CREAM}, 
              stop:1 #FEF9F3);
            padding: 24px;
        }}

        QGroupBox {{
          border: none;
          border-radius: 12px;
          margin-top: 12px;
          padding: 20px;
          background-color: #FFFFFF;
        }}

        QGroupBox::title {{
          subcontrol-origin: margin;
          left: 16px;
          padding: 0 8px;
          font-weight: 700;
          color: {ThemeManager.FARM_BARN_RED};
          font-size: 13pt;
          letter-spacing: 0.3px;
        }}

        QPushButton {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {ThemeManager.FARM_BARN_RED},
            stop:1 #7A3A0F);
          color: white;
          border-radius: 8px;
          padding: 10px 24px;
          border: none;
          font-weight: 600;
          font-size: 11pt;
          letter-spacing: 0.2px;
        }}

        QPushButton:hover {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {ThemeManager.FARM_BARN_RED_HOVER},
            stop:1 #8B4A1A);
        }}

        QPushButton:pressed {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #7A3A0F,
            stop:1 {ThemeManager.FARM_BARN_RED});
        }}
        
        QPushButton:disabled {{
          background: {ThemeManager.FARM_HAY_YELLOW};
          color: #999999;
        }}

        /* Premium Sidebar Buttons */
        QFrame#sidebar QPushButton {{
          background-color: transparent;
          color: {ThemeManager.FARM_DEEP_BROWN};
          text-align: left;
          padding: 12px 18px;
          border: none;
          border-radius: 8px;
          font-weight: 500;
          font-size: 11pt;
          margin: 2px 8px;
        }}

        QFrame#sidebar QPushButton:hover {{
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(139, 69, 19, 0.12),
            stop:1 rgba(139, 69, 19, 0.08));
          color: {ThemeManager.FARM_BARN_RED};
          border-left: 4px solid {ThemeManager.FARM_BARN_RED};
          padding-left: 14px;
        }}
        
        QFrame#sidebar QPushButton:checked {{
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(139, 69, 19, 0.2),
            stop:1 rgba(139, 69, 19, 0.15));
          color: {ThemeManager.FARM_BARN_RED};
          font-weight: 600;
          border-left: 4px solid {ThemeManager.FARM_BARN_RED};
        }}

        QFrame#sidebar QLabel {{
          color: {ThemeManager.FARM_EARTH_BROWN};
          font-weight: 700;
          font-size: 11pt;
          letter-spacing: 0.5px;
          padding: 8px 18px;
        }}

        /* Premium Tables */
        QTableWidget, QTableView {{
          gridline-color: rgba(139, 111, 71, 0.15);
          background-color: white;
          alternate-background-color: #FEFCF9;
          selection-background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(139, 69, 19, 0.15),
            stop:1 rgba(139, 69, 19, 0.1));
          selection-color: {ThemeManager.FARM_BARN_RED};
          border: none;
          border-radius: 8px;
          padding: 4px;
        }}
        
        QTableWidget::item, QTableView::item {{
          padding: 8px;
          border: none;
        }}

        QTableWidget::item:hover, QTableView::item:hover {{
          background-color: rgba(139, 69, 19, 0.08);
        }}
        
        QHeaderView::section {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {ThemeManager.FARM_GOLDEN_WHEAT},
            stop:1 #E8B87A);
          padding: 12px 16px;
          border: none;
          border-bottom: 2px solid {ThemeManager.FARM_RUST_ORANGE};
          color: {ThemeManager.FARM_DEEP_BROWN};
          font-weight: 700;
          font-size: 10pt;
          letter-spacing: 0.3px;
        }}

        QHeaderView::section:first {{
          border-top-left-radius: 8px;
        }}

        QHeaderView::section:last {{
          border-top-right-radius: 8px;
        }}

        /* Premium Inputs */
        QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{
          padding: 10px 14px;
          border: 1.5px solid rgba(139, 111, 71, 0.3);
          border-radius: 8px;
          background-color: white;
          color: #2C1810;
          font-size: 11pt;
          selection-background-color: rgba(139, 69, 19, 0.2);
          selection-color: {ThemeManager.FARM_BARN_RED};
        }}
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateTimeEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
          border: 2px solid {ThemeManager.FARM_BARN_RED};
          background-color: #FFFEFB;
        }}

        QComboBox::drop-down {{
          border: none;
          width: 30px;
        }}

        QComboBox::down-arrow {{
          image: none;
          border-left: 5px solid transparent;
          border-right: 5px solid transparent;
          border-top: 6px solid {ThemeManager.FARM_BARN_RED};
          width: 0;
          height: 0;
        }}

        QLabel#titleLabel {{
          font-size: 24pt;
          font-weight: 700;
          color: {ThemeManager.FARM_BARN_RED};
          letter-spacing: -0.5px;
          margin-bottom: 8px;
        }}
        
        /* Premium Cards/Widgets */
        QFrame[class="card"] {{
            background-color: white;
            border: none;
            border-radius: 12px;
            padding: 20px;
        }}
        
        /* Premium Dialogs */
        QDialog {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
              stop:0 {ThemeManager.FARM_EGGSHELL_CREAM}, 
              stop:1 #FEF9F3);
        }}

        /* Status Labels */
        QLabel[state="success"] {{
            color: {ThemeManager.FARM_PASTURE_GREEN};
            font-weight: bold;
        }}
        
        QLabel[state="warning"] {{
            color: {ThemeManager.FARM_RUST_ORANGE};
            font-weight: bold;
        }}
        
        QLabel[state="error"] {{
            color: #C62828;
            font-weight: bold;
        }}
        
        QLabel[state="info"] {{
            color: {ThemeManager.FARM_EARTH_BROWN};
        }}
        
        QLabel#totalLabel {{
            font-size: 14pt;
            font-weight: 800;
            color: {ThemeManager.FARM_DEEP_BROWN};
            padding: 4px;
        }}

        /* Premium Success/Error/Warning Buttons */
        QPushButton[class="success"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_PASTURE_GREEN},
              stop:1 #5A7A1F);
        }}
        
        QPushButton[class="success"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_GRASS_GREEN},
              stop:1 #6B8E23);
        }}
        
        QPushButton[class="warning"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_RUST_ORANGE},
              stop:1 #B8732F);
        }}
        
        QPushButton[class="warning"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_GOLDEN_WHEAT},
              stop:1 #E09A5A);
        }}
        
        QPushButton[class="error"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 #C62828,
              stop:1 #A02020);
        }}
        
        QPushButton[class="error"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 #D32F2F,
              stop:1 #B02020);
        }}
        
        /* Premium Scrollbars */
        QScrollBar:vertical {{
            background: rgba(245, 222, 179, 0.5);
            width: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop:0 {ThemeManager.FARM_BARN_RED},
              stop:1 {ThemeManager.FARM_BARN_RED_HOVER});
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop:0 {ThemeManager.FARM_BARN_RED_HOVER},
              stop:1 #B85A2A);
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: rgba(245, 222, 179, 0.5);
            height: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_BARN_RED},
              stop:1 {ThemeManager.FARM_BARN_RED_HOVER});
            min-width: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_BARN_RED_HOVER},
              stop:1 #B85A2A);
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Premium Tabs */
        QTabWidget::pane {{
            border: none;
            background-color: white;
            border-radius: 8px;
            top: -1px;
        }}
        
        QTabBar::tab {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_WARM_BEIGE},
              stop:1 #F0D9B8);
            color: {ThemeManager.FARM_DEEP_BROWN};
            padding: 12px 24px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
            font-weight: 500;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_BARN_RED},
              stop:1 #7A3A0F);
            color: white;
            font-weight: 700;
        }}
        
        QTabBar::tab:hover:!selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_GOLDEN_WHEAT},
              stop:1 #E8B87A);
            color: {ThemeManager.FARM_DEEP_BROWN};
        }}
        
        /* Premium Tooltips */
        QToolTip {{
            background-color: {ThemeManager.FARM_DEEP_BROWN};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10pt;
        }}
        
        /* Premium Checkboxes and Radio Buttons */
        QCheckBox, QRadioButton {{
            spacing: 8px;
            font-size: 11pt;
            color: #2C1810;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid rgba(139, 111, 71, 0.4);
            border-radius: 4px;
            background-color: white;
        }}
        
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border: 2px solid {ThemeManager.FARM_BARN_RED};
            background-color: rgba(139, 69, 19, 0.1);
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {ThemeManager.FARM_BARN_RED};
            border: 2px solid {ThemeManager.FARM_BARN_RED};
        }}
        
        QRadioButton::indicator {{
            border-radius: 10px;
        }}
        
        /* Premium Progress Bars */
        QProgressBar {{
            border: none;
            border-radius: 8px;
            text-align: center;
            background-color: rgba(139, 111, 71, 0.1);
            height: 24px;
            font-weight: 600;
            color: {ThemeManager.FARM_DEEP_BROWN};
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop:0 {ThemeManager.FARM_BARN_RED},
              stop:1 {ThemeManager.FARM_BARN_RED_HOVER});
            border-radius: 8px;
        }}
        
        /* Premium List Widgets */
        QListWidget {{
            border: 1.5px solid rgba(139, 111, 71, 0.2);
            border-radius: 8px;
            background-color: white;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 10px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QListWidget::item:hover {{
            background-color: rgba(139, 69, 19, 0.1);
        }}
        
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop:0 rgba(139, 69, 19, 0.2),
              stop:1 rgba(139, 69, 19, 0.15));
            color: {ThemeManager.FARM_BARN_RED};
            font-weight: 600;
        }}
        
        /* Premium Menu Bar */
        QMenuBar {{
            background-color: white;
            border-bottom: 1px solid rgba(139, 111, 71, 0.2);
            padding: 4px;
        }}
        
        QMenuBar::item {{
            padding: 8px 16px;
            border-radius: 4px;
            color: {ThemeManager.FARM_DEEP_BROWN};
        }}
        
        QMenuBar::item:selected {{
            background-color: rgba(139, 69, 19, 0.1);
            color: {ThemeManager.FARM_BARN_RED};
        }}
        
        QMenu {{
            background-color: white;
            border: 1px solid rgba(139, 111, 71, 0.2);
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            color: {ThemeManager.FARM_DEEP_BROWN};
        }}
        
        QMenu::item:selected {{
            background-color: rgba(139, 69, 19, 0.15);
            color: {ThemeManager.FARM_BARN_RED};
        }}
        """

    @staticmethod
    def apply_theme(app, theme_name):
        """Apply theme to the QApplication instance"""
        ThemeManager.set_current_theme(theme_name)

        # Load base stylesheet and append theme-specific rules
        qss = ""
        try:
            base_dir = Path(__file__).resolve().parent.parent
            qss_path = base_dir / "styles.qss"
            if qss_path.exists():
                qss = qss_path.read_text(encoding="utf-8") + "\n"
        except Exception:
            qss = ""

        qss += ThemeManager.get_stylesheet(theme_name)
        app.setStyleSheet(qss)

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
        elif theme_name == ThemeManager.FARM:
            # Set farm-themed palette
            palette.setColor(QPalette.Window, QColor(255, 248, 220))  # Eggshell cream
            palette.setColor(QPalette.WindowText, QColor(62, 39, 35))  # Dark brown text
            palette.setColor(QPalette.Base, QColor(255, 255, 255))  # White
            palette.setColor(QPalette.AlternateBase, QColor(255, 248, 220))  # Eggshell cream
            palette.setColor(QPalette.ToolTipBase, QColor(101, 67, 33))  # Deep brown
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))  # White
            palette.setColor(QPalette.Text, QColor(62, 39, 35))  # Dark brown
            palette.setColor(QPalette.Button, QColor(139, 69, 19))  # Barn red
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White
            palette.setColor(QPalette.BrightText, QColor(205, 133, 63))  # Rust orange
            palette.setColor(QPalette.Link, QColor(139, 69, 19))  # Barn red
            palette.setColor(QPalette.Highlight, QColor(139, 69, 19))  # Barn red
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # White
        
        app.setPalette(palette)
