from pathlib import Path
import logging
import traceback
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableView, QFileDialog, QAbstractItemView, QLabel, QSpinBox,
    QCheckBox, QMenu, QHeaderView, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPainter, QAction, QColor, QFont
from PySide6.QtPrintSupport import QPrinter

logger = logging.getLogger(__name__)


class DataTableWidget(QWidget):
    """Enhanced datatable with search, filtering, pagination, column management, and export."""

    # Signals
    row_selected = Signal(int)  # Emitted when a row is selected
    row_double_clicked = Signal(int)  # Emitted when a row is double-clicked

    def __init__(self, parent=None, enable_pagination=True):
        super().__init__(parent)
        self.enable_pagination = enable_pagination
        self.current_page = 1
        self.page_size = 25
        self.column_visibility = {}  # Track column visibility
        
        self.model = QStandardItemModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setAlternatingRowColors(True)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.horizontalHeader().customContextMenuRequested.connect(self._show_column_menu)
        self.view.doubleClicked.connect(self._on_row_double_clicked)
        self.view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        # Set consistent column stretching
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Set row height to accommodate action buttons (increased for better UX)
        self.view.verticalHeader().setMinimumSectionSize(45)
        self.view.verticalHeader().setDefaultSectionSize(45)
        self.view.setMinimumHeight(200)

        # Controls
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search...')
        self.search.textChanged.connect(self._on_search)

        self.filter_col = QComboBox()
        self.filter_col.addItem('All columns', -1)
        self.filter_col.currentIndexChanged.connect(self._on_search)

        # Pagination controls
        if self.enable_pagination:
            self.page_size_combo = QComboBox()
            self.page_size_combo.addItems(['10', '25', '50', '100', 'All'])
            self.page_size_combo.setCurrentText('25')
            self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
            
            self.page_label = QLabel("Page 1 of 1")
            self.prev_btn = QPushButton("◀")
            self.prev_btn.clicked.connect(self._prev_page)
            self.next_btn = QPushButton("▶")
            self.next_btn.clicked.connect(self._next_page)
            
            self.total_label = QLabel("Total: 0")

        self.export_pdf_btn = QPushButton()
        self.export_pdf_btn.setText('Export PDF')
        self.export_csv_btn = QPushButton()
        self.export_csv_btn.setText('Export CSV')
        self.export_excel_btn = QPushButton()
        self.export_excel_btn.setText('Export Excel')

        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_excel_btn.clicked.connect(self.export_excel)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.search)
        ctrl_layout.addWidget(self.filter_col)
        ctrl_layout.addStretch()
        
        if self.enable_pagination:
            ctrl_layout.addWidget(QLabel("Page size:"))
            ctrl_layout.addWidget(self.page_size_combo)
            ctrl_layout.addWidget(self.total_label)
            ctrl_layout.addWidget(self.prev_btn)
            ctrl_layout.addWidget(self.page_label)
            ctrl_layout.addWidget(self.next_btn)
        
        ctrl_layout.addWidget(self.export_csv_btn)
        ctrl_layout.addWidget(self.export_excel_btn)
        ctrl_layout.addWidget(self.export_pdf_btn)

        # Stacked widget for table and empty state
        self.stacked = QStackedWidget()
        
        # Empty state widget
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout()
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        empty_label = QLabel("No data available")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_font = QFont()
        empty_font.setPointSize(14)
        empty_font.setBold(True)
        empty_label.setFont(empty_font)
        empty_label.setStyleSheet("color: #666; padding: 40px;")
        empty_layout.addWidget(empty_label)
        self.empty_state.setLayout(empty_layout)
        
        self.stacked.addWidget(self.view)  # Index 0
        self.stacked.addWidget(self.empty_state)  # Index 1
        
        layout = QVBoxLayout()
        layout.addLayout(ctrl_layout)
        layout.addWidget(self.stacked)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self._update_pagination()

    def _on_search(self, *_):
        text = self.search.text()
        col = self.filter_col.currentData()
        if col is None or col == -1:
            # filter all columns by delegating to proxy's regular expression
            self.proxy.setFilterKeyColumn(-1)
            self.proxy.setFilterFixedString(text)
        else:
            self.proxy.setFilterKeyColumn(col)
            self.proxy.setFilterFixedString(text)
        self.current_page = 1
        self._update_pagination()
    
    def _on_page_size_changed(self, size_text):
        """Handle page size change"""
        if size_text == 'All':
            self.page_size = -1  # -1 means show all
        else:
            self.page_size = int(size_text)
        self.current_page = 1
        self._update_pagination()
    
    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_pagination()
    
    def _next_page(self):
        """Go to next page"""
        total_pages = self._get_total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_pagination()
    
    def _get_total_pages(self):
        """Calculate total number of pages"""
        if self.page_size == -1:
            return 1
        total_rows = self.proxy.rowCount()
        return max(1, (total_rows + self.page_size - 1) // self.page_size)
    
    def _update_pagination(self):
        """Update pagination display and filter"""
        if not self.enable_pagination:
            return
        
        total_rows = self.proxy.rowCount()
        total_pages = self._get_total_pages()
        
        # Update labels
        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        self.total_label.setText(f"Total: {total_rows}")
        
        # Enable/disable navigation buttons
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        
        # Apply pagination filter
        if self.page_size == -1:
            # Show all rows
            for row in range(total_rows):
                index = self.proxy.index(row, 0)
                if index.isValid():
                    self.view.setRowHidden(row, False)
        else:
            start_row = (self.current_page - 1) * self.page_size
            end_row = min(start_row + self.page_size, total_rows)
            
            # Hide all rows first
            for row in range(total_rows):
                index = self.proxy.index(row, 0)
                if index.isValid():
                    self.view.setRowHidden(row, True)
            
            # Show rows for current page
            for row in range(start_row, end_row):
                index = self.proxy.index(row, 0)
                if index.isValid():
                    self.view.setRowHidden(row, False)
    
    def _show_column_menu(self, position):
        """Show context menu for column management"""
        menu = QMenu(self)
        
        # Add toggle visibility for each column
        for col in range(self.model.columnCount()):
            header = self.model.headerData(col, Qt.Horizontal)
            if header:
                action = QAction(header, self)
                action.setCheckable(True)
                action.setChecked(not self.view.isColumnHidden(col))
                action.triggered.connect(lambda checked, c=col: self._toggle_column_visibility(c, checked))
                menu.addAction(action)
        
        menu.addSeparator()
        
        # Reset columns action
        reset_action = QAction("Reset Column Widths", self)
        reset_action.triggered.connect(self._reset_column_widths)
        menu.addAction(reset_action)
        
        menu.exec_(self.view.horizontalHeader().mapToGlobal(position))
    
    def _toggle_column_visibility(self, column: int, visible: bool):
        """Toggle column visibility"""
        self.view.setColumnHidden(column, not visible)
        self.column_visibility[column] = visible
    
    def _reset_column_widths(self):
        """Reset all column widths to fit contents"""
        self.view.resizeColumnsToContents()
    
    def _on_row_double_clicked(self, index):
        """Handle row double click"""
        source_index = self.proxy.mapToSource(index)
        if source_index.isValid():
            self.row_double_clicked.emit(source_index.row())
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected = self.view.selectionModel().selectedRows()
        if selected:
            source_index = self.proxy.mapToSource(selected[0])
            if source_index.isValid():
                self.row_selected.emit(source_index.row())

    def set_headers(self, headers):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        # rebuild filter column combo
        self.filter_col.clear()
        self.filter_col.addItem('All columns', -1)
        for i, h in enumerate(headers):
            self.filter_col.addItem(h, i)

    def set_rows(self, rows):
        """Rows is an iterable of iterables matching headers length."""
        try:
            self.model.setRowCount(0)
            row_list = list(rows) if rows else []
            for row in row_list:
                # coerce values to str to avoid non-string model issues
                items = [QStandardItem(str(c) if c is not None else '') for c in row]
                for it in items:
                    it.setEditable(False)
                self.model.appendRow(items)
            
            # Show empty state if no rows
            if len(row_list) == 0:
                self.stacked.setCurrentIndex(1)  # Show empty state
            else:
                self.stacked.setCurrentIndex(0)  # Show table
            
            self._update_pagination()
        except Exception as e:
            logger.exception("Failed to set rows in DataTableWidget: %s", e)
            traceback.print_exc()

    def clear(self):
        self.model.clear()
        self.stacked.setCurrentIndex(1)  # Show empty state

    def set_cell_widget(self, row, col, widget):
        # set a widget in the view at given source-model row/col
        try:
            idx = self.model.index(row, col)
            if idx.isValid():
                # map source to proxy index
                pidx = self.proxy.mapFromSource(idx)
                if pidx.isValid():
                    # Ensure widget has proper size (larger for better UX)
                    if hasattr(widget, 'setMinimumHeight'):
                        widget.setMinimumHeight(40)
                    if hasattr(widget, 'setMaximumHeight'):
                        widget.setMaximumHeight(40)
                    self.view.setIndexWidget(pidx, widget)
                    # Set row height to accommodate widget
                    self.view.setRowHeight(pidx.row(), 45)
        except Exception as e:
            logger.exception("Failed to set cell widget at %s,%s: %s", row, col, e)
            traceback.print_exc()

    # Backwards compatibility shims for code that used QTableWidget APIs
    def setItem(self, row, col, item):
        """Compatibility: accept a QTableWidgetItem and put its text into the model."""
        try:
            text = item.text() if hasattr(item, 'text') else str(item)
            qitem = QStandardItem(str(text))
            qitem.setEditable(False)
            # ensure model has enough rows/cols
            if self.model.rowCount() <= row:
                self.model.setRowCount(row + 1)
            if self.model.columnCount() <= col:
                self.model.setColumnCount(col + 1)
            self.model.setItem(row, col, qitem)
        except Exception as e:
            logger.exception("Failed to setItem at %s,%s: %s", row, col, e)
            traceback.print_exc()

    def setCellWidget(self, row, col, widget):
        """Compatibility wrapper mapping QTableWidget.setCellWidget -> set_cell_widget."""
        self.set_cell_widget(row, col, widget)

    def setRowCount(self, n):
        try:
            self.model.setRowCount(n)
        except Exception:
            logger.exception("Failed to setRowCount(%s)", n)

    def setColumnCount(self, n):
        try:
            self.model.setColumnCount(n)
        except Exception:
            logger.exception("Failed to setColumnCount(%s)", n)

    def setHorizontalHeaderLabels(self, headers):
        self.set_headers(headers)
    
    def _detect_title_from_parent(self):
        """Try to detect appropriate title from parent widget"""
        parent = self.parent()
        while parent:
            # Check for common widget titles
            if hasattr(parent, 'windowTitle'):
                title = parent.windowTitle()
                if title and title != "Egg Farm Management System":
                    return title
            if hasattr(parent, 'title'):
                title = getattr(parent, 'title', None)
                if title:
                    return str(title)
            # Check for common form widget patterns
            widget_name = parent.__class__.__name__ if hasattr(parent, '__class__') else ""
            if 'Form' in widget_name or 'Widget' in widget_name:
                # Extract meaningful name
                name = widget_name.replace('FormWidget', '').replace('Widget', '')
                if name:
                    return name.replace('_', ' ').title()
            parent = parent.parent() if hasattr(parent, 'parent') else None
        return None

    def export_pdf(self, path=None, title=None, subtitle=None, 
                  company_name=None, company_address=None, company_phone=None):
        """Export table to professional PDF with headers and footers"""
        try:
            from egg_farm_system.utils.pdf_exporter import ProfessionalPDFExporter
            from egg_farm_system.config import COMPANY_NAME, COMPANY_ADDRESS, COMPANY_PHONE
            
            # Get headers and rows from model
            cols = self.model.columnCount()
            headers = [self.model.headerData(i, Qt.Horizontal) or "" for i in range(cols)]
            
            # Get visible columns only
            visible_cols = [i for i in range(cols) if not self.view.isColumnHidden(i)]
            visible_headers = [headers[i] for i in visible_cols]
            
            # Get rows (only visible columns)
            rows = []
            for r in range(self.model.rowCount()):
                row = []
                for c in visible_cols:
                    item = self.model.item(r, c)
                    row.append(item.text() if item is not None else '')
                rows.append(row)
            
            # Use defaults if not provided
            if title is None:
                # Try to detect title from parent widget
                title = self._detect_title_from_parent() or "Data Report"
            if company_name is None:
                company_name = COMPANY_NAME or "Egg Farm Management System"
            if company_address is None:
                company_address = COMPANY_ADDRESS
            if company_phone is None:
                company_phone = COMPANY_PHONE
            
            # Export using professional exporter
            exporter = ProfessionalPDFExporter()
            exporter.export_table(
                headers=visible_headers,
                rows=rows,
                path=path,
                title=title,
                subtitle=subtitle,
                company_name=company_name,
                company_address=company_address,
                company_phone=company_phone,
                parent=self
            )
        except Exception as e:
            logger.exception(f"Error exporting PDF: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {e}")

    def export_csv(self, path=None, export_filtered=True, export_selected=False):
        """Export to CSV with options for filtered/selected data"""
        import csv
        try:
            if path is None:
                result = QFileDialog.getSaveFileName(self, "Export CSV", str(Path.cwd() / 'table.csv'), "CSV Files (*.csv)")
                if isinstance(result, tuple):
                    path, _ = result
                else:
                    path = result
                # Check if user cancelled or path is invalid
                if not path or not isinstance(path, str) or path == '':
                    return
            # Ensure path is a string (user may have cancelled)
            if not isinstance(path, str) or path == '':
                logger.debug(f"CSV export cancelled or invalid path")
                return
            
            # Get visible columns only
            visible_cols = [i for i in range(self.model.columnCount()) if not self.view.isColumnHidden(i)]
            headers = [self.model.headerData(i, Qt.Horizontal) or f"Column {i+1}" for i in visible_cols]
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                if export_selected:
                    # Export only selected rows
                    selected = self.view.selectionModel().selectedRows()
                    for index in selected:
                        source_index = self.proxy.mapToSource(index)
                        if source_index.isValid():
                            row = [self.model.item(source_index.row(), c).text() 
                                   if self.model.item(source_index.row(), c) is not None else '' 
                                   for c in visible_cols]
                            writer.writerow(row)
                else:
                    # Export all visible rows (respecting filter)
                    for r in range(self.proxy.rowCount()):
                        if export_filtered and self.view.isRowHidden(r):
                            continue
                        source_index = self.proxy.mapToSource(self.proxy.index(r, 0))
                        if source_index.isValid():
                            row = [self.model.item(source_index.row(), c).text() 
                                   if self.model.item(source_index.row(), c) is not None else '' 
                                   for c in visible_cols]
                            writer.writerow(row)
            
            QMessageBox.information(self, "Success", f"Data exported to {path}")
        except Exception as e:
            logger.exception(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")
    
    def export_excel(self, path=None, export_filtered=True, export_selected=False):
        """Export to Excel with options for filtered/selected data"""
        try:
            from egg_farm_system.utils.excel_export import ExcelExporter
        except ImportError:
            logger.error("Excel export requires openpyxl")
            return
        
        if path is None:
            result = QFileDialog.getSaveFileName(
                self, "Export Excel", str(Path.cwd() / 'table.xlsx'), 
                "Excel Files (*.xlsx);;All Files (*.*)"
            )
            if isinstance(result, tuple):
                path, _ = result
            else:
                path = result
            # Check if user cancelled or path is invalid
            if not path or not isinstance(path, str) or path == '':
                return
        # Ensure path is a string (user may have cancelled)
        if not isinstance(path, str) or path == '':
            logger.debug(f"Excel export cancelled or invalid path")
            return
        
        # Get visible columns only
        visible_cols = [i for i in range(self.model.columnCount()) if not self.view.isColumnHidden(i)]
        headers = [self.model.headerData(i, Qt.Horizontal) for i in visible_cols]
        
        rows = []
        if export_selected:
            # Export only selected rows
            selected = self.view.selectionModel().selectedRows()
            for index in selected:
                source_index = self.proxy.mapToSource(index)
                if source_index.isValid():
                    row = [self.model.item(source_index.row(), c).text() 
                           if self.model.item(source_index.row(), c) is not None else '' 
                           for c in visible_cols]
                    rows.append(row)
        else:
            # Export all visible rows (respecting filter)
            for r in range(self.proxy.rowCount()):
                if export_filtered and self.view.isRowHidden(r):
                    continue
                source_index = self.proxy.mapToSource(self.proxy.index(r, 0))
                if source_index.isValid():
                    row = [self.model.item(source_index.row(), c).text() 
                           if self.model.item(source_index.row(), c) is not None else '' 
                           for c in visible_cols]
                    rows.append(row)
        
        exporter = ExcelExporter()
        exporter.export_table_data(headers, rows, Path(path), "Data")
