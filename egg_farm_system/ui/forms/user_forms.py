from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit,
    QLabel, QMessageBox, QDialog, QFormLayout
)
from egg_farm_system.modules.users import UserManager
from egg_farm_system.ui.forms.password_change_dialog import PasswordChangeDialog


class NewUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('New User')
        layout = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.full_name = QLineEdit()
        layout.addRow('Username:', self.username)
        layout.addRow('Password:', self.password)
        layout.addRow('Full name:', self.full_name)
        btn_h = QHBoxLayout()
        btn_h.setSpacing(10)
        btn_h.setContentsMargins(0, 10, 0, 0)
        btn_h.addStretch()
        save = QPushButton('Create')
        save.setMinimumWidth(100)
        save.setMinimumHeight(35)
        save.clicked.connect(self.accept)
        cancel = QPushButton('Cancel')
        cancel.setMinimumWidth(100)
        cancel.setMinimumHeight(35)
        cancel.clicked.connect(self.reject)
        btn_h.addWidget(save)
        btn_h.addWidget(cancel)
        layout.addRow(btn_h)
        self.setLayout(layout)


class UserManagementForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()
        self.list = QListWidget()
        layout.addWidget(self.list)

        btn_h = QHBoxLayout()
        add_btn = QPushButton('Add User')
        add_btn.clicked.connect(self.add_user)
        del_btn = QPushButton('Delete Selected')
        del_btn.clicked.connect(self.delete_selected)
        pwd_btn = QPushButton('Change Password')
        pwd_btn.clicked.connect(self.change_selected_password)
        btn_h.addWidget(add_btn)
        btn_h.addWidget(del_btn)
        btn_h.addWidget(pwd_btn)
        btn_h.addStretch()
        layout.addLayout(btn_h)

        self.setLayout(layout)

    def load_users(self):
        self.list.clear()
        for u in UserManager.get_all_users():
            self.list.addItem(f"{u.id}: {u.username} ({u.role})")

    def add_user(self):
        dlg = NewUserDialog(self)
        if dlg.exec():
            username = dlg.username.text().strip()
            password = dlg.password.text()
            full = dlg.full_name.text().strip()
            if not username or not password:
                QMessageBox.warning(self, 'Validation', 'Username and password required')
                return
            UserManager.create_user(username, password, full)
            QMessageBox.information(self, 'Created', 'User created')
            self.load_users()

    def delete_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        user_id = int(item.text().split(':', 1)[0])
        if UserManager.delete_user(user_id):
            QMessageBox.information(self, 'Deleted', 'User deleted')
            self.load_users()
        else:
            QMessageBox.warning(self, 'Error', 'Failed to delete user')

    def change_selected_password(self):
        item = self.list.currentItem()
        if not item:
            QMessageBox.warning(self, 'Selection', 'Select a user')
            return
        user_id = int(item.text().split(':', 1)[0])
        dlg = PasswordChangeDialog(self, target_user_id=user_id, force=True)
        if dlg.exec():
            QMessageBox.information(self, 'Success', 'Password updated')
