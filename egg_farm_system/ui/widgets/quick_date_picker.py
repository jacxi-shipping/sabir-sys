"""
Enhanced date picker with quick selection buttons.

Provides QuickDatePicker and QuickDateTimePicker widgets with convenient
buttons for selecting common dates (Today, Yesterday, This Week, This Month).
"""
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QDateTimeEdit, 
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, QDate, QDateTime, Signal


class QuickDatePicker(QWidget):
    """Date picker with quick selection buttons.
    
    Features:
    - Standard QDateEdit with calendar popup
    - Quick buttons: Today, Yesterday, This Week, This Month
    - Emits dateChanged signal when date changes
    """
    
    dateChanged = Signal(object)  # emits QDate
    
    def __init__(self, parent=None, show_quick_buttons=True):
        super().__init__(parent)
        self.show_quick_buttons = show_quick_buttons
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Date edit
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.date_edit)
        
        # Quick selection buttons
        if self.show_quick_buttons:
            quick_layout = QHBoxLayout()
            quick_layout.setSpacing(5)
            
            # Create buttons
            self.today_btn = QPushButton("Today", self)
            self.today_btn.setToolTip("Set date to today")
            self.today_btn.clicked.connect(self._set_today)
            
            self.yesterday_btn = QPushButton("Yesterday", self)
            self.yesterday_btn.setToolTip("Set date to yesterday")
            self.yesterday_btn.clicked.connect(self._set_yesterday)
            
            self.week_btn = QPushButton("This Week", self)
            self.week_btn.setToolTip("Set date to the start of this week (Monday)")
            self.week_btn.clicked.connect(self._set_this_week)
            
            self.month_btn = QPushButton("This Month", self)
            self.month_btn.setToolTip("Set date to the 1st of this month")
            self.month_btn.clicked.connect(self._set_this_month)
            
            # Style buttons
            button_style = """
                QPushButton {
                    padding: 4px 8px;
                    font-size: 11px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """
            for btn in [self.today_btn, self.yesterday_btn, self.week_btn, self.month_btn]:
                btn.setStyleSheet(button_style)
                quick_layout.addWidget(btn)
            
            quick_layout.addStretch()
            layout.addLayout(quick_layout)
    
    def _on_date_changed(self, qdate):
        """Handle date change"""
        self.dateChanged.emit(qdate)
    
    def _set_today(self):
        """Set date to today"""
        self.date_edit.setDate(QDate.currentDate())
    
    def _set_yesterday(self):
        """Set date to yesterday"""
        yesterday = QDate.currentDate().addDays(-1)
        self.date_edit.setDate(yesterday)
    
    def _set_this_week(self):
        """Set date to the start of this week (Monday)"""
        today = date.today()
        days_since_monday = today.weekday()  # Monday is 0
        week_start = today - timedelta(days=days_since_monday)
        self.date_edit.setDate(QDate(week_start.year, week_start.month, week_start.day))
    
    def _set_this_month(self):
        """Set date to the 1st of this month"""
        today = date.today()
        month_start = date(today.year, today.month, 1)
        self.date_edit.setDate(QDate(month_start.year, month_start.month, month_start.day))
    
    def date(self):
        """Get the selected date as QDate"""
        return self.date_edit.date()
    
    def setDate(self, qdate):
        """Set the date"""
        self.date_edit.setDate(qdate)
    
    def toPython(self):
        """Get the selected date as Python date"""
        qd = self.date_edit.date()
        return date(qd.year(), qd.month(), qd.day())
    
    def setReadOnly(self, read_only):
        """Set read-only mode"""
        self.date_edit.setReadOnly(read_only)
        if self.show_quick_buttons:
            for btn in [self.today_btn, self.yesterday_btn, self.week_btn, self.month_btn]:
                btn.setEnabled(not read_only)


class QuickDateTimePicker(QWidget):
    """DateTime picker with quick selection buttons.
    
    Features:
    - Standard QDateTimeEdit with calendar popup
    - Quick buttons: Now, Today, Yesterday
    - Emits dateTimeChanged signal when datetime changes
    """
    
    dateTimeChanged = Signal(object)  # emits QDateTime
    
    def __init__(self, parent=None, show_quick_buttons=True):
        super().__init__(parent)
        self.show_quick_buttons = show_quick_buttons
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # DateTime edit
        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.dateTimeChanged.connect(self._on_datetime_changed)
        layout.addWidget(self.datetime_edit)
        
        # Quick selection buttons
        if self.show_quick_buttons:
            quick_layout = QHBoxLayout()
            quick_layout.setSpacing(5)
            
            # Create buttons
            self.now_btn = QPushButton("Now", self)
            self.now_btn.setToolTip("Set to current date and time")
            self.now_btn.clicked.connect(self._set_now)
            
            self.today_btn = QPushButton("Today", self)
            self.today_btn.setToolTip("Set to today at 00:00")
            self.today_btn.clicked.connect(self._set_today)
            
            self.yesterday_btn = QPushButton("Yesterday", self)
            self.yesterday_btn.setToolTip("Set to yesterday at 00:00")
            self.yesterday_btn.clicked.connect(self._set_yesterday)
            
            # Style buttons
            button_style = """
                QPushButton {
                    padding: 4px 8px;
                    font-size: 11px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """
            for btn in [self.now_btn, self.today_btn, self.yesterday_btn]:
                btn.setStyleSheet(button_style)
                quick_layout.addWidget(btn)
            
            quick_layout.addStretch()
            layout.addLayout(quick_layout)
    
    def _on_datetime_changed(self, qdatetime):
        """Handle datetime change"""
        self.dateTimeChanged.emit(qdatetime)
    
    def _set_now(self):
        """Set to current datetime"""
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
    
    def _set_today(self):
        """Set to today at 00:00"""
        today = QDate.currentDate()
        self.datetime_edit.setDateTime(QDateTime(today))
    
    def _set_yesterday(self):
        """Set to yesterday at 00:00"""
        yesterday = QDate.currentDate().addDays(-1)
        self.datetime_edit.setDateTime(QDateTime(yesterday))
    
    def dateTime(self):
        """Get the selected datetime as QDateTime"""
        return self.datetime_edit.dateTime()
    
    def setDateTime(self, qdatetime):
        """Set the datetime"""
        self.datetime_edit.setDateTime(qdatetime)
    
    def toPython(self):
        """Get the selected datetime as Python datetime"""
        qdt = self.datetime_edit.dateTime()
        return datetime(
            qdt.date().year(), qdt.date().month(), qdt.date().day(),
            qdt.time().hour(), qdt.time().minute(), qdt.time().second()
        )
    
    def setReadOnly(self, read_only):
        """Set read-only mode"""
        self.datetime_edit.setReadOnly(read_only)
        if self.show_quick_buttons:
            for btn in [self.now_btn, self.today_btn, self.yesterday_btn]:
                btn.setEnabled(not read_only)
