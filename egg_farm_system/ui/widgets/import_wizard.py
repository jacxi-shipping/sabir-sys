"""
Import Wizard for bulk data import
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QWidget, QComboBox, QFileDialog,
    QTextEdit, QTableWidget, QTableWidgetItem, QProgressBar,
    QRadioButton, QButtonGroup, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging
from pathlib import Path

from egg_farm_system.utils.template_generator import TemplateGenerator
from egg_farm_system.utils.data_importer import DataImporter

logger = logging.getLogger(__name__)


class ImportWizard(QDialog):
    """Step-by-step import wizard"""
    
    import_completed = Signal(dict)  # Emits import result
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Data Wizard")
        self.resize(700, 500)
        
        self.selected_entity_type = None
        self.selected_file = None
        self.import_result = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup wizard UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Import Data Wizard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Step indicator
        self.step_label = QLabel("Step 1 of 4")
        self.step_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.step_label)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Step 1: Select entity type
        self.step1 = self._create_entity_selection_page()
        
        # Step 2: Select file or download template
        self.step2 = self._create_file_selection_page()
        
        # Step 3: Preview and validation
        self.step3 = self._create_preview_page()
        
        # Step 4: Import progress and results
        self.step4 = self._create_results_page()
        
        # Add pages
        self.stacked_widget.addWidget(self.step1)
        self.stacked_widget.addWidget(self.step2)
        self.stacked_widget.addWidget(self.step3)
        self.stacked_widget.addWidget(self.step4)
        
        layout.addWidget(self.stacked_widget)
        
        # Navigation buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_back = QPushButton("< Back")
        self.btn_next = QPushButton("Next >")
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_next.clicked.connect(self.go_next)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_back)
        btn_layout.addWidget(self.btn_next)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Initial button states
        self.btn_back.setEnabled(False)
        self.update_navigation()
    
    def _create_entity_selection_page(self):
        """Create step 1: entity type selection"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select the type of data you want to import:")
        layout.addWidget(instructions)
        
        # Entity type selector
        self.entity_combo = QComboBox()
        entity_types = [
            ('parties', 'Parties (Customers/Suppliers)'),
            ('raw_materials', 'Raw Materials'),
            ('expenses', 'Expenses'),
            ('employees', 'Employees'),
        ]
        for key, label in entity_types:
            self.entity_combo.addItem(label, key)
        
        layout.addWidget(self.entity_combo)
        
        # Template info
        info_label = QLabel("After selecting the entity type, you can download a template to fill in your data.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_file_selection_page(self):
        """Create step 2: file selection or template download"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Choose an option:")
        layout.addWidget(instructions)
        
        # Option 1: Download template
        template_group = QGroupBox("Option 1: Download Template")
        template_layout = QVBoxLayout()
        
        template_info = QLabel("Download a template file, fill in your data, and come back to import it.")
        template_info.setWordWrap(True)
        template_layout.addWidget(template_info)
        
        template_btn_layout = QHBoxLayout()
        self.btn_download_csv = QPushButton("Download CSV Template")
        self.btn_download_excel = QPushButton("Download Excel Template")
        
        self.btn_download_csv.clicked.connect(self.download_csv_template)
        self.btn_download_excel.clicked.connect(self.download_excel_template)
        
        template_btn_layout.addWidget(self.btn_download_csv)
        template_btn_layout.addWidget(self.btn_download_excel)
        template_layout.addLayout(template_btn_layout)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Option 2: Select file
        file_group = QGroupBox("Option 2: Select File to Import")
        file_layout = QVBoxLayout()
        
        file_info = QLabel("Select a CSV or Excel file containing your data.")
        file_info.setWordWrap(True)
        file_layout.addWidget(file_info)
        
        file_btn_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.browse_file)
        
        file_btn_layout.addWidget(self.file_path_label)
        file_btn_layout.addWidget(self.btn_browse)
        file_layout.addLayout(file_btn_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_preview_page(self):
        """Create step 3: preview and validation"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Review the data before importing:")
        layout.addWidget(instructions)
        
        # Validation status
        self.validation_status = QLabel()
        layout.addWidget(self.validation_status)
        
        # Errors display
        self.errors_display = QTextEdit()
        self.errors_display.setReadOnly(True)
        self.errors_display.setMaximumHeight(150)
        layout.addWidget(self.errors_display)
        
        # Data preview
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)
        
        page.setLayout(layout)
        return page
    
    def _create_results_page(self):
        """Create step 4: import results"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Status
        self.result_status = QLabel()
        self.result_status.setAlignment(Qt.AlignCenter)
        result_font = QFont()
        result_font.setPointSize(14)
        result_font.setBold(True)
        self.result_status.setFont(result_font)
        layout.addWidget(self.result_status)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        # Errors (if any)
        self.result_errors = QTextEdit()
        self.result_errors.setReadOnly(True)
        layout.addWidget(self.result_errors)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def download_csv_template(self):
        """Download CSV template"""
        entity_type = self.entity_combo.currentData()
        
        filename = f"{entity_type}_template.csv"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Template",
            filename,
            "CSV Files (*.csv)"
        )
        
        if filepath:
            success = TemplateGenerator.generate_csv_template(entity_type, filepath)
            if success:
                self.file_path_label.setText(f"Template saved to: {filepath}")
                logger.info(f"CSV template saved: {filepath}")
    
    def download_excel_template(self):
        """Download Excel template"""
        entity_type = self.entity_combo.currentData()
        
        filename = f"{entity_type}_template.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel Template",
            filename,
            "Excel Files (*.xlsx)"
        )
        
        if filepath:
            success = TemplateGenerator.generate_excel_template(entity_type, filepath)
            if success:
                self.file_path_label.setText(f"Template saved to: {filepath}")
                logger.info(f"Excel template saved: {filepath}")
    
    def browse_file(self):
        """Browse for file to import"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Import",
            "",
            "Supported Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if filepath:
            self.selected_file = filepath
            self.file_path_label.setText(Path(filepath).name)
            logger.info(f"File selected: {filepath}")
    
    def go_back(self):
        """Go to previous step"""
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            self.update_navigation()
    
    def go_next(self):
        """Go to next step"""
        current_index = self.stacked_widget.currentIndex()
        
        # Validate before proceeding
        if current_index == 0:
            # Step 1: Just move to step 2
            self.selected_entity_type = self.entity_combo.currentData()
            self.stacked_widget.setCurrentIndex(1)
        
        elif current_index == 1:
            # Step 2: Validate file is selected
            if not self.selected_file:
                self.file_path_label.setText("⚠️ Please select a file to import")
                return
            self.preview_data()
            self.stacked_widget.setCurrentIndex(2)
        
        elif current_index == 2:
            # Step 3: Perform import
            self.perform_import()
            self.stacked_widget.setCurrentIndex(3)
        
        elif current_index == 3:
            # Step 4: Finish
            self.accept()
            return
        
        self.update_navigation()
    
    def update_navigation(self):
        """Update navigation button states"""
        current_index = self.stacked_widget.currentIndex()
        
        # Update step label
        self.step_label.setText(f"Step {current_index + 1} of 4")
        
        # Back button
        self.btn_back.setEnabled(current_index > 0)
        
        # Next button text
        if current_index == 3:
            self.btn_next.setText("Finish")
        elif current_index == 2:
            self.btn_next.setText("Import")
        else:
            self.btn_next.setText("Next >")
        
        # Disable next on step 1 if no file selected (except we're just selecting type)
        if current_index == 1:
            self.btn_next.setEnabled(True)  # Can always proceed to preview
        elif current_index == 2:
            self.btn_next.setEnabled(True)  # Can always attempt import
    
    def preview_data(self):
        """Preview data and show validation results"""
        try:
            importer = DataImporter()
            
            # Read file
            data = importer._read_file(self.selected_file)
            
            # Validate based on entity type
            from egg_farm_system.utils.data_validator import DataValidator
            
            if self.selected_entity_type == 'parties':
                valid, errors = DataValidator.validate_parties(data)
            elif self.selected_entity_type == 'raw_materials':
                valid, errors = DataValidator.validate_raw_materials(data)
            elif self.selected_entity_type == 'expenses':
                valid, errors = DataValidator.validate_expenses(data)
            elif self.selected_entity_type == 'employees':
                valid, errors = DataValidator.validate_employees(data)
            else:
                valid, errors = [], ["Unknown entity type"]
            
            # Update validation status
            if errors:
                self.validation_status.setText(f"⚠️ {len(errors)} validation error(s) found. Only valid rows will be imported.")
                self.validation_status.setStyleSheet("color: orange;")
                self.errors_display.setPlainText("\n".join(errors))
                self.errors_display.setVisible(True)
            else:
                self.validation_status.setText(f"✅ All {len(valid)} rows are valid!")
                self.validation_status.setStyleSheet("color: green;")
                self.errors_display.setVisible(False)
            
            # Show preview (first 10 valid rows)
            if valid:
                preview_data = valid[:10]
                if preview_data:
                    columns = list(preview_data[0].keys())
                    self.preview_table.setColumnCount(len(columns))
                    self.preview_table.setHorizontalHeaderLabels(columns)
                    self.preview_table.setRowCount(len(preview_data))
                    
                    for row_idx, row in enumerate(preview_data):
                        for col_idx, col_name in enumerate(columns):
                            value = str(row.get(col_name, ''))
                            self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            
            importer.close_session()
            
        except Exception as e:
            logger.error(f"Preview error: {e}")
            self.validation_status.setText(f"❌ Error reading file: {str(e)}")
            self.validation_status.setStyleSheet("color: red;")
    
    def perform_import(self):
        """Perform the actual import"""
        self.progress_bar.setValue(0)
        self.result_status.setText("Importing...")
        
        try:
            importer = DataImporter()
            
            # Perform import based on entity type
            if self.selected_entity_type == 'parties':
                result = importer.import_parties(self.selected_file)
            elif self.selected_entity_type == 'raw_materials':
                result = importer.import_raw_materials(self.selected_file)
            elif self.selected_entity_type == 'expenses':
                result = importer.import_expenses(self.selected_file)
            elif self.selected_entity_type == 'employees':
                result = importer.import_employees(self.selected_file)
            else:
                result = {'status': 'error', 'message': 'Unknown entity type', 'imported': 0, 'errors': []}
            
            self.import_result = result
            self.progress_bar.setValue(100)
            
            # Update result display
            if result['status'] in ['success', 'failed']:
                if result['imported'] > 0:
                    self.result_status.setText("✅ Import Completed!")
                    self.result_status.setStyleSheet("color: green;")
                else:
                    self.result_status.setText("⚠️ Import Completed with Warnings")
                    self.result_status.setStyleSheet("color: orange;")
                
                self.summary_label.setText(
                    f"Successfully imported: {result['imported']} records\n"
                    f"Errors: {len(result.get('errors', []))}"
                )
                
                if result.get('errors'):
                    self.result_errors.setPlainText("\n".join(result['errors'][:50]))  # Show first 50 errors
                    self.result_errors.setVisible(True)
                else:
                    self.result_errors.setVisible(False)
            else:
                self.result_status.setText("❌ Import Failed")
                self.result_status.setStyleSheet("color: red;")
                self.summary_label.setText(f"Error: {result.get('message', 'Unknown error')}")
                if result.get('errors'):
                    self.result_errors.setPlainText("\n".join(result['errors']))
                    self.result_errors.setVisible(True)
            
            # Emit signal
            self.import_completed.emit(result)
            
            importer.close_session()
            
        except Exception as e:
            logger.error(f"Import error: {e}")
            self.result_status.setText("❌ Import Failed")
            self.result_status.setStyleSheet("color: red;")
            self.summary_label.setText(f"Error: {str(e)}")
            self.progress_bar.setValue(0)
    
    def get_import_result(self):
        """Get the import result"""
        return self.import_result
