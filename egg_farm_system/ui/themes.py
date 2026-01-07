"""
Theme management for the Egg Farm System
"""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class ThemeManager:
    LIGHT = "light"
    DARK = "dark"
    FARM = "farm"  # Farm-themed palette
    
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
          box-shadow: 2px 0px 8px rgba(0, 0, 0, 0.08);
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
          box-shadow: 0px 2px 8px rgba(139, 69, 19, 0.08),
                      0px 1px 3px rgba(0, 0, 0, 0.05);
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
          box-shadow: 0px 2px 6px rgba(139, 69, 19, 0.25),
                      0px 1px 2px rgba(0, 0, 0, 0.1);
        }}

        QPushButton:hover {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {ThemeManager.FARM_BARN_RED_HOVER},
            stop:1 #8B4A1A);
          box-shadow: 0px 4px 12px rgba(139, 69, 19, 0.35),
                      0px 2px 4px rgba(0, 0, 0, 0.15);
          transform: translateY(-1px);
        }}

        QPushButton:pressed {{
          background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #7A3A0F,
            stop:1 {ThemeManager.FARM_BARN_RED});
          box-shadow: 0px 1px 3px rgba(139, 69, 19, 0.2);
          transform: translateY(0px);
        }}
        
        QPushButton:disabled {{
          background: {ThemeManager.FARM_HAY_YELLOW};
          color: #999999;
          box-shadow: none;
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
          transition: all 0.2s ease;
        }}

        QFrame#sidebar QPushButton:hover {{
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(139, 69, 19, 0.12),
            stop:1 rgba(139, 69, 19, 0.08));
          color: {ThemeManager.FARM_BARN_RED};
          border-left: 4px solid {ThemeManager.FARM_BARN_RED};
          padding-left: 14px;
          transform: translateX(2px);
        }}
        
        QFrame#sidebar QPushButton:checked {{
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(139, 69, 19, 0.2),
            stop:1 rgba(139, 69, 19, 0.15));
          color: {ThemeManager.FARM_BARN_RED};
          font-weight: 600;
          border-left: 4px solid {ThemeManager.FARM_BARN_RED};
          box-shadow: 2px 0px 6px rgba(139, 69, 19, 0.15);
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
          box-shadow: 0px 0px 0px 3px rgba(139, 69, 19, 0.1),
                      0px 2px 4px rgba(139, 69, 19, 0.08);
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
            box-shadow: 0px 2px 12px rgba(139, 69, 19, 0.1),
                        0px 1px 4px rgba(0, 0, 0, 0.06);
        }}
        
        /* Premium Success/Error/Warning Buttons */
        QPushButton[class="success"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_PASTURE_GREEN},
              stop:1 #5A7A1F);
            box-shadow: 0px 2px 6px rgba(107, 142, 35, 0.25);
        }}
        
        QPushButton[class="success"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_GRASS_GREEN},
              stop:1 #6B8E23);
            box-shadow: 0px 4px 12px rgba(107, 142, 35, 0.35);
        }}
        
        QPushButton[class="warning"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_RUST_ORANGE},
              stop:1 #B8732F);
            box-shadow: 0px 2px 6px rgba(205, 133, 63, 0.25);
        }}
        
        QPushButton[class="warning"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 {ThemeManager.FARM_GOLDEN_WHEAT},
              stop:1 #E09A5A);
            box-shadow: 0px 4px 12px rgba(205, 133, 63, 0.35);
        }}
        
        QPushButton[class="error"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 #C62828,
              stop:1 #A02020);
            box-shadow: 0px 2px 6px rgba(198, 40, 40, 0.25);
        }}
        
        QPushButton[class="error"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 #D32F2F,
              stop:1 #B02020);
            box-shadow: 0px 4px 12px rgba(198, 40, 40, 0.35);
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
            box-shadow: 0px 2px 8px rgba(139, 69, 19, 0.08);
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
            box-shadow: 0px -2px 8px rgba(139, 69, 19, 0.2);
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
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
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
