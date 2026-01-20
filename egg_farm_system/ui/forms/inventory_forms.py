"""
Form widgets for inventory
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSizePolicy, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.ui.forms.packaging_purchase_dialog import PackagingPurchaseDialog
from egg_farm_system.ui.ui_helpers import create_button

class InventoryFormWidget(QWidget):
    """Inventory management widget"""
    
    def __init__(self):
        super().__init__()
        self.inventory_manager = InventoryManager()
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header with title and refresh button
        header_layout = QHBoxLayout()
        title = QLabel(tr("Inventory Management"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton(tr("Refresh"))
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setToolTip(tr("Refresh inventory data"))
        header_layout.addWidget(refresh_btn)

        purchase_btn = create_button(tr("Purchase Packaging"), style='success')
        purchase_btn.setToolTip(tr("Purchase Cartons or Trays"))
        purchase_btn.clicked.connect(self.open_packaging_purchase)
        header_layout.addWidget(purchase_btn)
        
        layout.addLayout(header_layout)
        
        # Tabs for different inventory types
        self.raw_materials_table = self.create_table(
            ["Material", "Stock (kg)", "Avg Price (AFG)", "Avg Price (USD)", "Total Value AFG", "Status"]
        )
        self.finished_feed_table = self.create_table(
            ["Feed Type", "Stock (kg)", "Cost/kg AFG", "Total Value AFG", "Status"]
        )
        
        # Raw materials section
        layout.addWidget(QLabel(tr("Raw Materials Inventory")))
        layout.addWidget(self.raw_materials_table)
        
        # Finished feed section
        layout.addWidget(QLabel(tr("Finished Feed Inventory")))
        layout.addWidget(self.finished_feed_table)
        
        # Summary
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        self.setLayout(layout)

    def open_packaging_purchase(self):
        dlg = PackagingPurchaseDialog(self)
        dlg.purchase_saved.connect(self.refresh_data)
        dlg.exec()
    
    def create_table(self, headers):
        """Create data table with consistent column stretching"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        # Set consistent resize behavior: stretch all columns for better UX
        for i in range(len(headers)):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setAlternatingRowColors(True)
        # Set row height
        table.verticalHeader().setMinimumSectionSize(40)
        table.verticalHeader().setDefaultSectionSize(40)
        return table
    
    def refresh_data(self):
        """Refresh inventory data"""
        try:
            # Clear cache to ensure fresh data
            from egg_farm_system.utils.advanced_caching import dashboard_cache
            dashboard_cache.invalidate_all()
            
            # Raw materials
            raw_materials = self.inventory_manager.get_raw_materials_inventory()
            self.raw_materials_table.setRowCount(len(raw_materials))
            
            if len(raw_materials) == 0:
                # Show message if no materials
                self.raw_materials_table.setRowCount(1)
                self.raw_materials_table.setItem(0, 0, QTableWidgetItem("No raw materials found. Add materials in Feed Management."))
                for col in range(1, 6):
                    self.raw_materials_table.setItem(0, col, QTableWidgetItem(""))
            else:
                for row, material in enumerate(raw_materials):
                    self.raw_materials_table.setItem(row, 0, QTableWidgetItem(material['name']))
                    self.raw_materials_table.setItem(row, 1, QTableWidgetItem(f"{material['stock']:.2f} {material.get('unit', 'kg')}"))
                    self.raw_materials_table.setItem(row, 2, QTableWidgetItem(f"{material['cost_afg']:,.2f}"))
                    self.raw_materials_table.setItem(row, 3, QTableWidgetItem(f"{material['cost_usd']:,.2f}"))
                    self.raw_materials_table.setItem(row, 4, QTableWidgetItem(f"{material['inventory_value_afg']:,.2f}"))
                    
                    status = "⚠ Low" if material['is_low'] else "OK"
                    self.raw_materials_table.setItem(row, 5, QTableWidgetItem(status))
            
            # Finished feed
            finished_feed = self.inventory_manager.get_finished_feed_inventory()
            self.finished_feed_table.setRowCount(len(finished_feed))
            
            for row, feed in enumerate(finished_feed):
                self.finished_feed_table.setItem(row, 0, QTableWidgetItem(feed['feed_type']))
                self.finished_feed_table.setItem(row, 1, QTableWidgetItem(f"{feed['stock_kg']:.2f}"))
                self.finished_feed_table.setItem(row, 2, QTableWidgetItem(f"{feed['cost_per_kg_afg']:.2f}"))
                self.finished_feed_table.setItem(row, 3, QTableWidgetItem(f"{feed['inventory_value_afg']:.2f}"))
                
                status = "⚠ Low" if feed['is_low'] else "OK"
                self.finished_feed_table.setItem(row, 4, QTableWidgetItem(status))
            
            # Summary
            totals = self.inventory_manager.get_total_inventory_value()
            summary_text = f"Total Inventory Value: Afs {totals['total_afg']:,.2f} (${totals['total_usd']:,.2f})"
            self.summary_label.setText(summary_text)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to load inventory: {e}")
