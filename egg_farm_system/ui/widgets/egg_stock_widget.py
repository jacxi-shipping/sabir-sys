"""
Egg Stock Management Widget
Shows available eggs by grade with tray/carton conversion
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QGridLayout, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
import logging

from egg_farm_system.utils.egg_management import EggManagementSystem
from egg_farm_system.modules.farms import FarmManager

logger = logging.getLogger(__name__)


class EggStockWidget(QWidget):
    """Widget for viewing egg stock by grade"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.egg_manager = EggManagementSystem()
        self.farm_manager = FarmManager()
        self.farm_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel(tr("Egg Stock Management"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Farm selector
        farm_layout = QHBoxLayout()
        farm_layout.addWidget(QLabel(tr("Farm:")))
        self.farm_combo = QComboBox()
        self.farm_combo.currentIndexChanged.connect(self.on_farm_changed)
        farm_layout.addWidget(self.farm_combo)
        farm_layout.addStretch()
        
        refresh_btn = QPushButton(tr("Refresh"))
        refresh_btn.clicked.connect(self.refresh_stock)
        farm_layout.addWidget(refresh_btn)
        layout.addLayout(farm_layout)
        
        # Stock Summary Group
        stock_group = QGroupBox("Stock Summary by Grade")
        stock_layout = QGridLayout()
        stock_layout.setSpacing(12)
        
        # Headers
        stock_layout.addWidget(QLabel(tr("<b>Grade</b>")), 0, 0)
        stock_layout.addWidget(QLabel(tr("<b>Eggs</b>")), 0, 1)
        stock_layout.addWidget(QLabel(tr("<b>Trays</b>")), 0, 2)
        stock_layout.addWidget(QLabel(tr("<b>Cartons</b>")), 0, 3)
        
        # Grade rows
        self.small_label = QLabel("0")
        self.small_tray_label = QLabel(tr("0.00"))
        self.small_carton_label = QLabel(tr("0.00"))
        stock_layout.addWidget(QLabel(tr("Small:")), 1, 0)
        stock_layout.addWidget(self.small_label, 1, 1)
        stock_layout.addWidget(self.small_tray_label, 1, 2)
        stock_layout.addWidget(self.small_carton_label, 1, 3)
        
        self.medium_label = QLabel("0")
        self.medium_tray_label = QLabel(tr("0.00"))
        self.medium_carton_label = QLabel(tr("0.00"))
        stock_layout.addWidget(QLabel(tr("Medium:")), 2, 0)
        stock_layout.addWidget(self.medium_label, 2, 1)
        stock_layout.addWidget(self.medium_tray_label, 2, 2)
        stock_layout.addWidget(self.medium_carton_label, 2, 3)
        
        self.large_label = QLabel("0")
        self.large_tray_label = QLabel(tr("0.00"))
        self.large_carton_label = QLabel(tr("0.00"))
        stock_layout.addWidget(QLabel(tr("Large:")), 3, 0)
        stock_layout.addWidget(self.large_label, 3, 1)
        stock_layout.addWidget(self.large_tray_label, 3, 2)
        stock_layout.addWidget(self.large_carton_label, 3, 3)
        
        self.broken_label = QLabel("0")
        self.broken_tray_label = QLabel(tr("0.00"))
        self.broken_carton_label = QLabel(tr("0.00"))
        stock_layout.addWidget(QLabel(tr("Broken:")), 4, 0)
        stock_layout.addWidget(self.broken_label, 4, 1)
        stock_layout.addWidget(self.broken_tray_label, 4, 2)
        stock_layout.addWidget(self.broken_carton_label, 4, 3)
        
        # Total row
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(11)
        
        self.total_label = QLabel("0")
        self.total_label.setFont(total_font)
        self.total_tray_label = QLabel(tr("0.00"))
        self.total_tray_label.setFont(total_font)
        self.total_carton_label = QLabel(tr("0.00"))
        self.total_carton_label.setFont(total_font)
        
        stock_layout.addWidget(QLabel(tr("<b>Total:</b>")), 5, 0)
        stock_layout.addWidget(self.total_label, 5, 1)
        stock_layout.addWidget(self.total_tray_label, 5, 2)
        stock_layout.addWidget(self.total_carton_label, 5, 3)
        
        stock_group.setLayout(stock_layout)
        layout.addWidget(stock_group)
        
        # Usable Eggs Group
        usable_group = QGroupBox("Usable Eggs (Excluding Broken)")
        usable_layout = QGridLayout()
        usable_layout.setSpacing(8)
        
        self.usable_label = QLabel("0")
        usable_font = QFont()
        usable_font.setBold(True)
        usable_font.setPointSize(12)
        self.usable_label.setFont(usable_font)
        
        self.usable_tray_label = QLabel(tr("0.00"))
        self.usable_tray_label.setFont(usable_font)
        self.usable_carton_label = QLabel(tr("0.00"))
        self.usable_carton_label.setFont(usable_font)
        
        usable_layout.addWidget(QLabel(tr("Usable Eggs:")), 0, 0)
        usable_layout.addWidget(self.usable_label, 0, 1)
        usable_layout.addWidget(QLabel("="), 0, 2)
        usable_layout.addWidget(self.usable_tray_label, 0, 3)
        usable_layout.addWidget(QLabel(tr("trays")), 0, 4)
        usable_layout.addWidget(QLabel("="), 0, 5)
        usable_layout.addWidget(self.usable_carton_label, 0, 6)
        usable_layout.addWidget(QLabel(tr("cartons")), 0, 7)
        
        usable_group.setLayout(usable_layout)
        layout.addWidget(usable_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Load farms
        self.load_farms()
    
    def load_farms(self):
        """Load farms into combo box"""
        try:
            self.farm_combo.clear()
            farms = self.farm_manager.get_all_farms()
            for farm in farms:
                self.farm_combo.addItem(farm.name, farm.id)
            
            if farms:
                self.farm_id = farms[0].id
                self.refresh_stock()
        except Exception as e:
            logger.error(f"Error loading farms: {e}")
    
    def on_farm_changed(self):
        """Handle farm selection change"""
        self.farm_id = self.farm_combo.currentData()
        self.refresh_stock()
    
    def refresh_stock(self):
        """Refresh stock display"""
        try:
            if not self.farm_id:
                return
            
            summary = self.egg_manager.get_egg_stock_summary(self.farm_id)
            
            # Update labels
            self.small_label.setText(f"{summary['small']:,}")
            self.medium_label.setText(f"{summary['medium']:,}")
            self.large_label.setText(f"{summary['large']:,}")
            self.broken_label.setText(f"{summary['broken']:,}")
            self.total_label.setText(f"{summary['total']:,}")
            self.usable_label.setText(f"{summary['usable']:,}")
            
            # Update tray conversions
            self.small_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['small']):.2f}")
            self.medium_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['medium']):.2f}")
            self.large_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['large']):.2f}")
            self.broken_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['broken']):.2f}")
            self.total_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['total']):.2f}")
            self.usable_tray_label.setText(f"{self.egg_manager.eggs_to_trays(summary['usable']):.2f}")
            
            # Update carton conversions
            self.small_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['small']):.2f}")
            self.medium_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['medium']):.2f}")
            self.large_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['large']):.2f}")
            self.broken_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['broken']):.2f}")
            self.total_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['total']):.2f}")
            self.usable_carton_label.setText(f"{self.egg_manager.eggs_to_cartons(summary['usable']):.2f}")
        
        except Exception as e:
            logger.error(f"Error refreshing stock: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to refresh stock: {str(e)}")
    
    def set_farm_id(self, farm_id):
        """Set farm ID and refresh"""
        self.farm_id = farm_id
        # Find and select in combo
        for i in range(self.farm_combo.count()):
            if self.farm_combo.itemData(i) == farm_id:
                self.farm_combo.setCurrentIndex(i)
                break
        self.refresh_stock()

