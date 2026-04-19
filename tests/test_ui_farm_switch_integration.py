"""UI integration regressions for farm switching propagation."""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QComboBox, QVBoxLayout, QWidget

from egg_farm_system.ui.main_window import MainWindow
from egg_farm_system.ui.dashboard import DashboardWidget
from egg_farm_system.ui.forms.inventory_forms import InventoryFormWidget
from egg_farm_system.ui.forms.party_forms import PartyFormWidget
from egg_farm_system.ui.forms.transaction_forms import TransactionFormWidget
from egg_farm_system.ui.reports.report_viewer import ReportViewerWidget
from egg_farm_system.ui.widgets.cash_flow_widget import CashFlowWidget


class _ScreenSetFarmRefresh(QWidget):
    def __init__(self):
        super().__init__()
        self.received_farm_id = None
        self.refresh_count = 0

    def set_farm_id(self, farm_id):
        self.received_farm_id = farm_id

    def refresh_data(self):
        self.refresh_count += 1


class _ScreenFarmPropRefreshStock(QWidget):
    def __init__(self):
        super().__init__()
        self.farm_id = None
        self.refresh_stock_count = 0

    def refresh_stock(self):
        self.refresh_stock_count += 1


def _build_host_with_current_widget(widget, selected_farm_id):
    host = SimpleNamespace()
    host.farm_combo = QComboBox()
    host.farm_combo.addItem("Farm A", 1)
    host.farm_combo.addItem("Farm B", 2)

    target_index = host.farm_combo.findData(selected_farm_id)
    host.farm_combo.setCurrentIndex(target_index)

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)
    host._container = container
    host.content_layout = layout

    def _get_current_farm_id():
        return host.farm_combo.currentData()

    host.get_current_farm_id = _get_current_farm_id
    return host


@pytest.mark.parametrize("screen_cls", [_ScreenSetFarmRefresh, _ScreenFarmPropRefreshStock])
def test_main_window_on_farm_changed_propagates_to_active_screen(qapp, screen_cls):
    screen = screen_cls()
    host = _build_host_with_current_widget(screen, selected_farm_id=2)

    MainWindow.on_farm_changed(host)

    if isinstance(screen, _ScreenSetFarmRefresh):
        assert screen.received_farm_id == 2
        assert screen.refresh_count == 1
    else:
        assert screen.farm_id == 2
        assert screen.refresh_stock_count == 1


@pytest.mark.parametrize(
    "screen_name,screen_class",
    [
        ("dashboard", DashboardWidget),
        ("inventory", InventoryFormWidget),
        ("parties", PartyFormWidget),
        ("transactions", TransactionFormWidget),
        ("reports", ReportViewerWidget),
        ("cash_flow", CashFlowWidget),
    ],
)
def test_key_screen_classes_support_farm_switch_contract(screen_name, screen_class):
    assert hasattr(screen_class, "set_farm_id"), f"{screen_name} screen missing set_farm_id"
