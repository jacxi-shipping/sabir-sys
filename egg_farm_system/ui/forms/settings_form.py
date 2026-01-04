from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox
from PySide6.QtCore import Qt
from modules.settings import SettingsManager


class SettingsForm(QWidget):
    """Simple settings editor"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list = QListWidget()
        layout.addWidget(self.list)

        form_h = QHBoxLayout()
        form_h.addWidget(QLabel('Key:'))
        self.key_edit = QLineEdit()
        form_h.addWidget(self.key_edit)
        form_h.addWidget(QLabel('Value:'))
        self.value_edit = QLineEdit()
        form_h.addWidget(self.value_edit)

        layout.addLayout(form_h)

        btn_h = QHBoxLayout()
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_setting)
        btn_h.addWidget(save_btn)
        btn_h.addStretch()
        layout.addLayout(btn_h)

        self.setLayout(layout)

    def load_settings(self):
        self.list.clear()
        for s in SettingsManager.get_all_settings():
            self.list.addItem(f"{s.key} = {s.value}")

    def save_setting(self):
        key = self.key_edit.text().strip()
        value = self.value_edit.text().strip()
        if not key:
            QMessageBox.warning(self, 'Validation', 'Key is required')
            return
        SettingsManager.set_setting(key, value)
        QMessageBox.information(self, 'Saved', 'Setting saved')
        self.load_settings()
