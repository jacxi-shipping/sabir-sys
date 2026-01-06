"""
Backup and Restore Widget
"""
import logging
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QFileDialog, QLineEdit, QTextEdit,
    QGroupBox, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from egg_farm_system.utils.backup_manager import BackupManager
from egg_farm_system.config import DATA_DIR

logger = logging.getLogger(__name__)


class BackupRestoreWidget(QWidget):
    """Widget for backup and restore operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_manager = BackupManager()
        self.init_ui()
        self.refresh_backup_list()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Backup & Restore")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Backup section
        backup_group = QGroupBox("Create Backup")
        backup_layout = QVBoxLayout()
        
        # Comment input
        form_layout = QFormLayout()
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("Optional comment for this backup...")
        form_layout.addRow("Comment:", self.comment_edit)
        backup_layout.addLayout(form_layout)
        
        # Options
        from PySide6.QtWidgets import QCheckBox
        self.include_logs_check = QCheckBox("Include log files in backup")
        backup_layout.addWidget(self.include_logs_check)
        
        # Backup button
        backup_btn = QPushButton("Create Backup Now")
        backup_btn.setMinimumHeight(40)
        backup_btn.clicked.connect(self.create_backup)
        backup_layout.addWidget(backup_btn)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Restore section
        restore_group = QGroupBox("Restore from Backup")
        restore_layout = QVBoxLayout()
        
        # Backup list
        restore_layout.addWidget(QLabel("Available Backups:"))
        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(200)
        self.backup_list.itemDoubleClicked.connect(self.restore_backup)
        restore_layout.addWidget(self.backup_list)
        
        # Restore buttons
        btn_layout = QHBoxLayout()
        restore_btn = QPushButton("Restore Selected Backup")
        restore_btn.clicked.connect(self.restore_selected_backup)
        btn_layout.addWidget(restore_btn)
        
        restore_from_file_btn = QPushButton("Restore from File...")
        restore_from_file_btn.clicked.connect(self.restore_from_file)
        btn_layout.addWidget(restore_from_file_btn)
        
        restore_layout.addLayout(btn_layout)
        restore_group.setLayout(restore_layout)
        layout.addWidget(restore_group)
        
        # Backup info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.info_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_backup_list)
        action_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_backup)
        action_layout.addWidget(delete_btn)
        
        cleanup_btn = QPushButton("Cleanup Old Backups")
        cleanup_btn.clicked.connect(self.cleanup_backups)
        action_layout.addWidget(cleanup_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        layout.addStretch()
    
    def create_backup(self):
        """Create a new backup"""
        try:
            comment = self.comment_edit.text().strip()
            include_logs = self.include_logs_check.isChecked()
            
            # Show progress
            QMessageBox.information(self, "Creating Backup", 
                                  "Creating backup... This may take a moment.")
            
            backup_path = self.backup_manager.create_backup(
                include_logs=include_logs,
                comment=comment
            )
            
            QMessageBox.information(self, "Success", 
                                  f"Backup created successfully!\n\nLocation: {backup_path}\nSize: {self._format_size(backup_path.stat().st_size)}")
            
            self.comment_edit.clear()
            self.refresh_backup_list()
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create backup:\n{str(e)}")
    
    def restore_selected_backup(self):
        """Restore selected backup from list"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore.")
            return
        
        backup_path = current_item.data(Qt.UserRole)
        self._restore_backup(backup_path)
    
    def restore_from_file(self):
        """Restore backup from file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            str(self.backup_manager.backup_dir),
            "Backup Files (*.zip);;All Files (*.*)"
        )
        
        if file_path:
            self._restore_backup(Path(file_path))
    
    def restore_backup(self, item: QListWidgetItem):
        """Restore backup (called on double-click)"""
        backup_path = item.data(Qt.UserRole)
        self._restore_backup(backup_path)
    
    def _restore_backup(self, backup_path: Path):
        """Internal restore backup method"""
        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore from backup?\n\n"
            f"File: {backup_path.name}\n\n"
            f"WARNING: This will replace your current database. "
            f"A backup of your current database will be created first.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            QMessageBox.information(self, "Restoring", 
                                  "Restoring backup... Please wait.")
            
            self.backup_manager.restore_backup(backup_path, restore_logs=False)
            
            QMessageBox.information(self, "Success", 
                                  "Backup restored successfully!\n\n"
                                  "The application will need to be restarted.")
            
            self.refresh_backup_list()
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            QMessageBox.critical(self, "Error", f"Failed to restore backup:\n{str(e)}")
    
    def delete_selected_backup(self):
        """Delete selected backup"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a backup to delete.")
            return
        
        backup_path = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this backup?\n\n{backup_path.name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.backup_manager.delete_backup(backup_path):
                QMessageBox.information(self, "Deleted", "Backup deleted successfully.")
                self.refresh_backup_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete backup.")
    
    def cleanup_backups(self):
        """Cleanup old backups"""
        reply = QMessageBox.question(
            self,
            "Cleanup Backups",
            "This will delete old backups, keeping only the 10 most recent.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted = self.backup_manager.cleanup_old_backups(keep_count=10)
            QMessageBox.information(self, "Cleanup Complete", 
                                  f"Deleted {deleted} old backup(s).")
            self.refresh_backup_list()
    
    def refresh_backup_list(self):
        """Refresh the backup list"""
        self.backup_list.clear()
        
        backups = self.backup_manager.list_backups()
        
        if not backups:
            self.info_label.setText("No backups found. Create your first backup above.")
            return
        
        for backup in backups:
            item = QListWidgetItem()
            item.setText(f"{backup['filename']}\n"
                         f"Created: {backup['created']}\n"
                         f"Size: {self._format_size(backup['size'])}")
            if backup['comment']:
                item.setText(item.text() + f"\nComment: {backup['comment']}")
            item.setData(Qt.UserRole, backup['path'])
            self.backup_list.addItem(item)
        
        self.info_label.setText(f"Found {len(backups)} backup(s). Double-click to restore.")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

