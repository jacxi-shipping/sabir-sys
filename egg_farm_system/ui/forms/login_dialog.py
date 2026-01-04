from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox
from modules.users import UserManager


class LoginDialog(QDialog):
    """Simple username/password login dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Login')
        self.user = None

        layout = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow('Username:', self.username)
        layout.addRow('Password:', self.password)

        btn = QPushButton('Login')
        btn.clicked.connect(self.attempt_login)
        layout.addRow(btn)

        self.setLayout(layout)

    def attempt_login(self):
        uname = self.username.text().strip()
        pwd = self.password.text()
        if not uname or not pwd:
            QMessageBox.warning(self, 'Validation', 'Enter username and password')
            return

        ok = UserManager.verify_credentials(uname, pwd)
        if ok:
            self.user = UserManager.get_user_by_username(uname)
            self.accept()
        else:
            QMessageBox.warning(self, 'Login Failed', 'Invalid username or password')
