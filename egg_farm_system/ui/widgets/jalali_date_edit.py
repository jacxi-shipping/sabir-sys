"""
Jalali date/time input widgets.

Provides `JalaliDateEdit` and `JalaliDateTimeEdit` which display and allow
picking Jalali dates. Internally values are stored/returned as Python
`date`/`datetime` in Gregorian (so DB stays Gregorian). Uses `jdatetime`
for conversions.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import jdatetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QToolButton, QDialog, QVBoxLayout,
    QComboBox, QDialogButtonBox, QSpinBox, QLabel
)
from PySide6.QtCore import Signal


def _jalali_to_gregorian(y: int, m: int, d: int) -> date:
    return jdatetime.date(year=y, month=m, day=d).togregorian()


def _gregorian_to_jalali(dt: date) -> jdatetime.date:
    return jdatetime.date.fromgregorian(date=dt)


class JalaliDateEdit(QWidget):
    """Simple Jalali date picker.

    - Displays selected date as Jalali `YYYY-MM-DD` in a read-only line edit.
    - Clicking the picker button opens a dialog with year/month/day selectors.
    - `date()` returns a Python `date` in Gregorian (matching existing app storage).
    - `setDate(date)` accepts a Python `date` (Gregorian) or `None`.
    """

    dateChanged = Signal(object)  # emits Python date or None

    def __init__(self, parent=None, initial: Optional[date] = None):
        super().__init__(parent)
        self._date: Optional[date] = None

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        self.display = QLineEdit(self)
        self.display.setReadOnly(True)
        h.addWidget(self.display)
        self.btn = QToolButton(self)
        self.btn.setText("⋯")
        self.btn.clicked.connect(self._open_picker)
        h.addWidget(self.btn)

        if initial:
            self.setDate(initial)
        else:
            self.setDate(date.today())

    def setReadOnly(self, read_only: bool):
        self.display.setReadOnly(read_only)
        self.btn.setEnabled(not read_only)

    def date(self) -> Optional[date]:
        return self._date

    def setDate(self, d: Optional[date]):
        self._date = d
        if d:
            j = _gregorian_to_jalali(d)
            self.display.setText(f"{j.year:04d}-{j.month:02d}-{j.day:02d}")
        else:
            self.display.setText("")
        self.dateChanged.emit(self._date)

    def _open_picker(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Select Date (Jalali)")
        layout = QVBoxLayout(dlg)

        today_j = _gregorian_to_jalali(self._date or date.today())

        year_combo = QComboBox()
        cur_year = today_j.year
        for y in range(cur_year - 50, cur_year + 11):
            year_combo.addItem(str(y), y)
        year_combo.setCurrentText(str(today_j.year))

        month_combo = QComboBox()
        for m in range(1, 13):
            month_combo.addItem(str(m), m)
        month_combo.setCurrentIndex(today_j.month - 1)

        day_spin = QSpinBox()
        day_spin.setRange(1, 31)
        day_spin.setValue(today_j.day)

        # Update day max when month/year changes
        def _update_day_max():
            y = int(year_combo.currentData())
            m = int(month_combo.currentData())
            # determine days in jalali month
            try:
                # convert last day of month by trying day=31..28
                maxd = 31
                while maxd > 27:
                    try:
                        jdatetime.date(y, m, maxd)
                        break
                    except Exception:
                        maxd -= 1
                day_spin.setRange(1, maxd)
                if day_spin.value() > maxd:
                    day_spin.setValue(maxd)
            except Exception:
                day_spin.setRange(1, 31)

        year_combo.currentIndexChanged.connect(_update_day_max)
        month_combo.currentIndexChanged.connect(_update_day_max)

        layout.addWidget(QLabel("Year:"))
        layout.addWidget(year_combo)
        layout.addWidget(QLabel("Month:"))
        layout.addWidget(month_combo)
        layout.addWidget(QLabel("Day:"))
        layout.addWidget(day_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.Accepted:
            y = int(year_combo.currentData())
            m = int(month_combo.currentData())
            d = int(day_spin.value())
            g = _jalali_to_gregorian(y, m, d)
            self.setDate(g)


class JalaliDateTimeEdit(JalaliDateEdit):
    """Jalali date+time picker. Extends JalaliDateEdit and stores/returns Python datetime."""

    def __init__(self, parent=None, initial: Optional[datetime] = None):
        super().__init__(parent, initial.date() if initial else None)
        self._time_hour = 0
        self._time_minute = 0
        if initial:
            self._time_hour = initial.hour
            self._time_minute = initial.minute

    def setDateTime(self, dt: Optional[datetime]):
        if dt:
            super().setDate(dt.date())
            self._time_hour = dt.hour
            self._time_minute = dt.minute
        else:
            super().setDate(None)

    def dateTime(self) -> Optional[datetime]:
        d = self.date()
        if d is None:
            return None
        return datetime(d.year, d.month, d.day, self._time_hour, self._time_minute)

    # Override picker to include time
    def _open_picker(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Select Date & Time (Jalali)")
        layout = QVBoxLayout(dlg)

        today_j = _gregorian_to_jalali(self._date or date.today())

        year_combo = QComboBox()
        cur_year = today_j.year
        for y in range(cur_year - 50, cur_year + 11):
            year_combo.addItem(str(y), y)
        year_combo.setCurrentText(str(today_j.year))

        month_combo = QComboBox()
        for m in range(1, 13):
            month_combo.addItem(str(m), m)
        month_combo.setCurrentIndex(today_j.month - 1)

        day_spin = QSpinBox()
        day_spin.setRange(1, 31)
        day_spin.setValue(today_j.day)

        hour_spin = QSpinBox()
        hour_spin.setRange(0, 23)
        hour_spin.setValue(self._time_hour)
        minute_spin = QSpinBox()
        minute_spin.setRange(0, 59)
        minute_spin.setValue(self._time_minute)

        def _update_day_max():
            y = int(year_combo.currentData())
            m = int(month_combo.currentData())
            try:
                maxd = 31
                while maxd > 27:
                    try:
                        jdatetime.date(y, m, maxd)
                        break
                    except Exception:
                        maxd -= 1
                day_spin.setRange(1, maxd)
                if day_spin.value() > maxd:
                    day_spin.setValue(maxd)
            except Exception:
                day_spin.setRange(1, 31)

        year_combo.currentIndexChanged.connect(_update_day_max)
        month_combo.currentIndexChanged.connect(_update_day_max)

        layout.addWidget(QLabel("Year:"))
        layout.addWidget(year_combo)
        layout.addWidget(QLabel("Month:"))
        layout.addWidget(month_combo)
        layout.addWidget(QLabel("Day:"))
        layout.addWidget(day_spin)
        layout.addWidget(QLabel("Hour:"))
        layout.addWidget(hour_spin)
        layout.addWidget(QLabel("Minute:"))
        layout.addWidget(minute_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.Accepted:
            y = int(year_combo.currentData())
            m = int(month_combo.currentData())
            d = int(day_spin.value())
            h = int(hour_spin.value())
            mi = int(minute_spin.value())
            g = _jalali_to_gregorian(y, m, d)
            self._time_hour = h
            self._time_minute = mi
            self.setDate(g)
