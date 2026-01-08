"""
Widget for Production Analytics Reports
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import QDate
from egg_farm_system.database.models import Flock
from egg_farm_system.utils.calculations import FeedCalculations, EggCalculations, MortalityCalculations

class ProductionAnalyticsWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Production Analytics")

        self.setup_ui()
        self.load_flocks()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Filters ---
        filters_group = QGroupBox("Filters")
        filters_layout = QFormLayout()
        self.flock_combo = QComboBox()
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit.setDate(QDate.currentDate())
        filters_layout.addRow("Flock:", self.flock_combo)
        filters_layout.addRow("Start Date:", self.start_date_edit)
        filters_layout.addRow("End Date:", self.end_date_edit)
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        self.calculate_button = QPushButton("Calculate Analytics")
        self.calculate_button.clicked.connect(self.run_calculations)
        main_layout.addWidget(self.calculate_button)

        # --- FCR Group ---
        fcr_group = QGroupBox("Feed Conversion Ratio (FCR)")
        fcr_layout = QFormLayout()
        self.fcr_result_label = QLabel("FCR (kg/dozen): Not calculated")
        self.feed_result_label = QLabel("Total Feed (kg): Not calculated")
        self.eggs_result_label = QLabel("Total Eggs: Not calculated")
        fcr_layout.addRow(self.fcr_result_label)
        fcr_layout.addRow(self.feed_result_label)
        fcr_layout.addRow(self.eggs_result_label)
        fcr_group.setLayout(fcr_layout)
        main_layout.addWidget(fcr_group)

        # --- HDP Group ---
        hdp_group = QGroupBox("Hen-Day Production (HDP)")
        hdp_layout = QFormLayout()
        self.hdp_result_label = QLabel("HDP (%): Not calculated")
        self.avg_birds_label = QLabel("Avg. Live Birds: Not calculated")
        hdp_layout.addRow(self.hdp_result_label)
        hdp_layout.addRow(self.avg_birds_label)
        hdp_group.setLayout(hdp_layout)
        main_layout.addWidget(hdp_group)

        # --- Mortality Group ---
        mortality_group = QGroupBox("Mortality")
        mortality_layout = QFormLayout()
        self.mortality_rate_label = QLabel("Mortality Rate (%): Not calculated")
        self.total_deaths_label = QLabel("Total Deaths: Not calculated")
        self.start_birds_label = QLabel("Birds at Start: Not calculated")
        mortality_layout.addRow(self.mortality_rate_label)
        mortality_layout.addRow(self.total_deaths_label)
        mortality_layout.addRow(self.start_birds_label)
        mortality_group.setLayout(mortality_layout)
        main_layout.addWidget(mortality_group)


        self.setLayout(main_layout)

    def load_flocks(self):
        flocks = self.session.query(Flock).all()
        for flock in flocks:
            self.flock_combo.addItem(flock.name, userData=flock.id)

    def run_calculations(self):
        flock_id = self.flock_combo.currentData()
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()

        if not flock_id:
            QMessageBox.warning(self, "Warning", "Please select a flock.")
            return

        # FCR Calculation
        fcr, total_feed, total_eggs_fcr = FeedCalculations.calculate_fcr_for_flock(
            self.session, flock_id, start_date, end_date
        )
        self.fcr_result_label.setText(f"FCR (kg/dozen): {fcr:.2f}")
        self.feed_result_label.setText(f"Total Feed (kg): {total_feed:.2f}")
        self.eggs_result_label.setText(f"Total Eggs: {total_eggs_fcr}")

        # HDP Calculation
        hdp, total_eggs_hdp, avg_birds = EggCalculations.calculate_hdp_for_flock(
            self.session, flock_id, start_date, end_date
        )
        self.hdp_result_label.setText(f"HDP (%): {hdp:.2f}%")
        self.avg_birds_label.setText(f"Avg. Live Birds: {avg_birds:.2f}")
        # This will be the same as total_eggs_fcr, but good to keep logic separate
        self.eggs_result_label.setText(f"Total Eggs: {total_eggs_hdp}")

        # Mortality Calculation
        mortality_rate, total_deaths, start_birds = MortalityCalculations.calculate_mortality_rate_for_period(
            self.session, flock_id, start_date, end_date
        )
        self.mortality_rate_label.setText(f"Mortality Rate (%): {mortality_rate:.2f}%")
        self.total_deaths_label.setText(f"Total Deaths: {total_deaths}")
        self.start_birds_label.setText(f"Birds at Start: {start_birds}")
