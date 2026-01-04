from pathlib import Path
import logging
import traceback
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableView, QFileDialog, QAbstractItemView
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPainter
from PySide6.QtPrintSupport import QPrinter

logger = logging.getLogger(__name__)


class DataTableWidget(QWidget):
    """Reusable datatable with search, simple column filter, CSV/PDF export."""

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Controls
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search...')
        self.search.textChanged.connect(self._on_search)

        self.filter_col = QComboBox()
        self.filter_col.addItem('All columns', -1)
        self.filter_col.currentIndexChanged.connect(self._on_search)

        self.export_pdf_btn = QPushButton()
        self.export_pdf_btn.setText('Export PDF')
        self.export_csv_btn = QPushButton()
        self.export_csv_btn.setText('Export CSV')

        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_csv_btn.clicked.connect(self.export_csv)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.search)
        ctrl_layout.addWidget(self.filter_col)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.export_csv_btn)
        ctrl_layout.addWidget(self.export_pdf_btn)

        layout = QVBoxLayout()
        layout.addLayout(ctrl_layout)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

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
            for row in rows:
                # coerce values to str to avoid non-string model issues
                items = [QStandardItem(str(c) if c is not None else '') for c in row]
                for it in items:
                    it.setEditable(False)
                self.model.appendRow(items)
        except Exception as e:
            logger.exception("Failed to set rows in DataTableWidget: %s", e)
            traceback.print_exc()

    def clear(self):
        self.model.clear()

    def set_cell_widget(self, row, col, widget):
        # set a widget in the view at given source-model row/col
        try:
            idx = self.model.index(row, col)
            if idx.isValid():
                # map source to proxy index
                pidx = self.proxy.mapFromSource(idx)
                if pidx.isValid():
                    self.view.setIndexWidget(pidx, widget)
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

    def export_pdf(self, path=None):
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, "Export PDF", str(Path.cwd() / 'table.pdf'), "PDF Files (*.pdf)")
            if not path:
                return
        # Create printer and painter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)

        painter = QPainter(printer)

        # Page geometry and margins
        page_rect = printer.pageRect()
        margin = 40  # device units
        x = page_rect.x() + margin
        y = page_rect.y() + margin
        w = page_rect.width() - 2 * margin
        h = page_rect.height() - 2 * margin

        # Prepare font metrics for layout
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()

        cols = self.model.columnCount()
        headers = [self.model.headerData(i, Qt.Horizontal) or "" for i in range(cols)]

        # Determine column widths proportional to header text widths (fallback equal)
        col_widths = []
        total_w = 0
        for i in range(cols):
            # approximate width using header and a few sample rows
            header_w = fm.horizontalAdvance(str(headers[i])) + 20
            sample_w = header_w
            for r in range(min(5, self.model.rowCount())):
                item = self.model.item(r, i)
                if item:
                    sample_w = max(sample_w, fm.horizontalAdvance(item.text()) + 10)
            col_widths.append(sample_w)
            total_w += sample_w

        # scale to printable width
        if total_w > 0:
            scale = w / total_w
        else:
            scale = 1.0
        col_widths = [int(max(40, cw * scale)) for cw in col_widths]

        # Row height
        row_h = fm.height() + 6

        # Header height
        header_h = fm.height() + 8

        # How many rows per page
        rows_per_page = max(1, (h - header_h) // row_h)

        # Paginate and draw
        row_count = self.model.rowCount()
        page = 0
        r = 0
        while r < row_count:
            # Draw title/header for page
            painter.save()
            painter.translate(x, y)

            # Draw table header background
            painter.fillRect(0, 0, sum(col_widths), header_h, Qt.lightGray)
            cx = 0
            for i, wcol in enumerate(col_widths):
                painter.drawRect(cx, 0, wcol, header_h)
                painter.drawText(cx + 4, fm.ascent() + 4, str(headers[i]))
                cx += wcol

            # Draw rows
            ry = header_h
            for pr in range(rows_per_page):
                if r >= row_count:
                    break
                cx = 0
                # alternate background
                if pr % 2 == 0:
                    painter.fillRect(0, ry, sum(col_widths), row_h, Qt.white)
                else:
                    painter.fillRect(0, ry, sum(col_widths), row_h, Qt.lightGray.lighter(120))

                for i, wcol in enumerate(col_widths):
                    painter.drawRect(cx, ry, wcol, row_h)
                    item = self.model.item(r, i)
                    text = item.text() if item is not None else ''
                    painter.drawText(cx + 4, ry + fm.ascent() + 3, str(text))
                    cx += wcol

                ry += row_h
                r += 1

            painter.restore()

            page += 1
            if r < row_count:
                printer.newPage()

        painter.end()

    def export_csv(self, path=None):
        import csv
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, "Export CSV", str(Path.cwd() / 'table.csv'), "CSV Files (*.csv)")
            if not path:
                return
        headers = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in range(self.model.rowCount()):
                row = [self.model.item(r, c).text() if self.model.item(r, c) is not None else '' for c in range(self.model.columnCount())]
                writer.writerow(row)
