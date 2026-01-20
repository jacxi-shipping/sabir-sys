"""
Backup and Restore Manager for Egg Farm Management System
"""
from egg_farm_system.utils.i18n import tr

import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, List, Dict
import json

from egg_farm_system.config import DATA_DIR, DB_PATH, LOGS_DIR
from egg_farm_system.database.db import DatabaseManager

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and restores"""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize BackupManager
        
        Args:
            backup_dir: Directory to store backups. Defaults to DATA_DIR / "backups"
        """
        if backup_dir is None:
            backup_dir = DATA_DIR / "backups"
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, include_logs: bool = False, comment: str = "") -> Path:
        """
        Create a backup of the database and optionally logs
        
        Args:
            include_logs: Whether to include log files in backup
            comment: Optional comment/description for the backup
            
        Returns:
            Path to the created backup file
        """
        try:
            # Ensure database is closed before backup
            DatabaseManager.close()
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"egg_farm_backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename
            
            # Create zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                if DB_PATH.exists():
                    zipf.write(DB_PATH, arcname="egg_farm.db")
                    logger.info(f"Added database to backup: {DB_PATH}")
                
                # Add logs if requested
                if include_logs and LOGS_DIR.exists():
                    for log_file in LOGS_DIR.glob("*.log"):
                        zipf.write(log_file, arcname=f"logs/{log_file.name}")
                        logger.info(f"Added log file to backup: {log_file}")
                
                # Add metadata
                metadata = {
                    "timestamp": timestamp,
                    "datetime": datetime.now().isoformat(),
                    "comment": comment,
                    "database_size": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
                    "includes_logs": include_logs
                }
                zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            raise
    
    def restore_backup(self, backup_path: Path, restore_logs: bool = False) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup zip file
            restore_logs: Whether to restore log files
            
        Returns:
            True if restore was successful
        """
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Close database connection
            DatabaseManager.close()
            
            # Create temporary directory for extraction
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Verify backup contains database
                db_backup = temp_dir / "egg_farm.db"
                if not db_backup.exists():
                    raise ValueError("Backup file does not contain database")
                
                # Backup current database before restore
                if DB_PATH.exists():
                    current_backup = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy2(DB_PATH, current_backup)
                    logger.info(f"Current database backed up to: {current_backup}")
                
                # Restore database
                shutil.copy2(db_backup, DB_PATH)
                logger.info(f"Database restored from: {backup_path}")
                
                # Restore logs if requested
                if restore_logs:
                    logs_backup = temp_dir / "logs"
                    if logs_backup.exists():
                        for log_file in logs_backup.glob("*.log"):
                            dest = LOGS_DIR / log_file.name
                            shutil.copy2(log_file, dest)
                            logger.info(f"Log file restored: {dest}")
                
                # Reinitialize database
                DatabaseManager.initialize()
                
                return True
                
            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}", exc_info=True)
            raise
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("egg_farm_backup_*.zip"), reverse=True):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "backup_metadata.json" in zipf.namelist():
                        metadata_str = zipf.read("backup_metadata.json").decode('utf-8')
                        metadata = json.loads(metadata_str)
                    else:
                        # Fallback for old backups without metadata
                        stat = backup_file.stat()
                        metadata = {
                            "timestamp": backup_file.stem.split("_")[-2] + "_" + backup_file.stem.split("_")[-1],
                            "datetime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "comment": "",
                            "database_size": 0,
                            "includes_logs": False
                        }
                
                backups.append({
                    "path": backup_file,
                    "filename": backup_file.name,
                    "size": backup_file.stat().st_size,
                    "created": metadata.get("datetime", ""),
                    "comment": metadata.get("comment", ""),
                    "includes_logs": metadata.get("includes_logs", False)
                })
            except Exception as e:
                logger.warning(f"Failed to read backup metadata for {backup_file}: {e}")
        
        return backups
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Delete a backup file
        
        Args:
            backup_path: Path to backup file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            if backup_path.exists() and backup_path.suffix == ".zip":
                backup_path.unlink()
                logger.info(f"Backup deleted: {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def get_backup_info(self, backup_path: Path) -> Optional[Dict]:
        """
        Get information about a backup file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Dictionary with backup information or None
        """
        try:
            if not backup_path.exists():
                return None
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if "backup_metadata.json" in zipf.namelist():
                    metadata_str = zipf.read("backup_metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_str)
                else:
                    stat = backup_path.stat()
                    metadata = {
                        "timestamp": "",
                        "datetime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "comment": "",
                        "database_size": 0,
                        "includes_logs": False
                    }
            
            return {
                "path": backup_path,
                "filename": backup_path.name,
                "size": backup_path.stat().st_size,
                "created": metadata.get("datetime", ""),
                "comment": metadata.get("comment", ""),
                "includes_logs": metadata.get("includes_logs", False),
                "database_size": metadata.get("database_size", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return None
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Delete old backups, keeping only the most recent N backups
        
        Args:
            keep_count: Number of recent backups to keep
            
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        if len(backups) <= keep_count:
            return 0
        
        deleted = 0
        for backup in backups[keep_count:]:
            if self.delete_backup(backup["path"]):
                deleted += 1
        
        logger.info(f"Cleaned up {deleted} old backups, kept {keep_count} most recent")
        return deleted

