from egg_farm_system.utils.i18n import tr
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox
from egg_farm_system.modules.users import UserManager


class PasswordChangeDialog(QDialog):
    """Dialog to change a user's password.
    If target_user_id is None, it changes the current user's password and requires the old password.
    If force=True, it allows admin to set a new password without old password verification.
    """

    def __init__(self, parent=None, target_user_id=None, force=False):
        super().__init__(parent)
        self.setWindowTitle(tr('Change Password'))
        self.target_user_id = target_user_id
        self.force = force

        layout = QFormLayout()

        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        if not self.force:
            layout.addRow('Old Password:', self.old_password)
        layout.addRow('New Password:', self.new_password)
        layout.addRow('Confirm New:', self.confirm_password)

        btn = QPushButton(tr('Change'))
        btn.clicked.connect(self.attempt_change)
        layout.addRow(btn)

        self.setLayout(layout)

    def attempt_change(self):
        newp = self.new_password.text()
        conf = self.confirm_password.text()
        if newp != conf:
            QMessageBox.warning(self, tr('Validation'), 'New passwords do not match')
            return
        try:
            if self.force:
                ok = UserManager.change_password(self.target_user_id, None, newp, force=True)
            else:
                ok = UserManager.change_password(self.target_user_id, self.old_password.text(), newp, force=False)
            if ok:
                QMessageBox.information(self, tr('Success'), 'Password changed')
                self.accept()
            else:
                QMessageBox.warning(self, tr('Failed'), 'Old password incorrect or user not found')
        except ValueError as ve:
            QMessageBox.warning(self, tr('Validation'), str(ve))
        except Exception as e:
            QMessageBox.critical(self, tr('Error'), f'Failed to change password: {e}')
