"""
Audit Trail System for Egg Farm Management System
"""
from egg_farm_system.utils.i18n import tr

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions to audit"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"
    BACKUP = "backup"
    RESTORE = "restore"


class AuditLog(Base):
    """Audit log table"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, nullable=True)  # User who performed action
    username = Column(String(100), nullable=True)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    entity_type = Column(String(100), nullable=False)  # e.g., "Farm", "Sale", "Party"
    entity_id = Column(Integer, nullable=True)  # ID of affected entity
    entity_name = Column(String(255), nullable=True)  # Name/identifier of entity
    description = Column(Text, nullable=True)  # Human-readable description
    old_values = Column(Text, nullable=True)  # JSON of old values (for updates)
    new_values = Column(Text, nullable=True)  # JSON of new values
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action_type.value} {self.entity_type} {self.entity_id}>"


@dataclass
class AuditEntry:
    """Audit entry data class"""
    user_id: Optional[int]
    username: Optional[str]
    action_type: ActionType
    entity_type: str
    entity_id: Optional[int]
    entity_name: Optional[str]
    description: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditTrail:
    """Manages audit trail logging"""
    
    def __init__(self):
        # Ensure audit log table exists
        try:
            AuditLog.__table__.create(DatabaseManager._engine, checkfirst=True)
        except Exception as e:
            logger.debug(f"Audit log table may already exist: {e}")

    def _get_session(self):
        """Create a fresh database session for each operation."""
        return DatabaseManager.get_session()
    
    def log(self, entry: AuditEntry):
        """Log an audit entry"""
        session = self._get_session()
        try:
            audit_log = AuditLog(
                timestamp=datetime.utcnow(),
                user_id=entry.user_id,
                username=entry.username,
                action_type=entry.action_type,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                entity_name=entry.entity_name,
                description=entry.description,
                old_values=json.dumps(entry.old_values) if entry.old_values else None,
                new_values=json.dumps(entry.new_values) if entry.new_values else None,
                ip_address=entry.ip_address,
                user_agent=entry.user_agent
            )
            
            session.add(audit_log)
            session.commit()
            logger.debug(f"Audit log created: {entry.action_type.value} {entry.entity_type}")
        
        except Exception as e:
            logger.error(f"Error logging audit entry: {e}")
            session.rollback()
        finally:
            session.close()
    
    def log_action(self, user_id: Optional[int], username: Optional[str], action_type: ActionType,
                   entity_type: str, entity_id: Optional[int] = None, entity_name: Optional[str] = None,
                   description: Optional[str] = None, old_values: Optional[Dict] = None,
                   new_values: Optional[Dict] = None):
        """Convenience method to log an action"""
        entry = AuditEntry(
            user_id=user_id,
            username=username,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            old_values=old_values,
            new_values=new_values
        )
        self.log(entry)
    
    def get_logs(self, entity_type: Optional[str] = None, action_type: Optional[ActionType] = None,
                 user_id: Optional[int] = None, start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs with filters"""
        session = self._get_session()
        try:
            query = session.query(AuditLog)
            
            if entity_type:
                query = query.filter(AuditLog.entity_type == entity_type)
            
            if action_type:
                query = query.filter(AuditLog.action_type == action_type)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
        finally:
            session.close()
    
    def get_entity_history(self, entity_type: str, entity_id: int) -> List[AuditLog]:
        """Get history of changes for a specific entity"""
        session = self._get_session()
        try:
            return session.query(AuditLog).filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            ).order_by(AuditLog.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error getting entity history: {e}")
            return []
        finally:
            session.close()
    
    def get_user_activity(self, user_id: int, days: int = 30) -> List[AuditLog]:
        """Get activity for a user"""
        session = self._get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return session.query(AuditLog).filter(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            ).order_by(AuditLog.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return []
        finally:
            session.close()
    
    def close(self):
        """Close database session"""
        return


# Global audit trail instance
_audit_trail: Optional[AuditTrail] = None


def get_audit_trail() -> AuditTrail:
    """Get global audit trail instance"""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail


def audit_decorator(action_type: ActionType, entity_type: str):
    """Decorator to automatically audit function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get user from context if available
            user_id = kwargs.get('user_id') or (args[0].current_user.id if hasattr(args[0], 'current_user') and args[0].current_user else None)
            username = kwargs.get('username') or (args[0].current_user.username if hasattr(args[0], 'current_user') and args[0].current_user else None)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log the action
            if result:
                entity_id = getattr(result, 'id', None) if result else None
                entity_name = getattr(result, 'name', None) if result else None
                
                get_audit_trail().log_action(
                    user_id=user_id,
                    username=username,
                    action_type=action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_name=entity_name,
                    description=f"{action_type.value.title()} {entity_type}"
                )
            
            return result
        return wrapper
    return decorator

