"""
Audit Helper - Easy integration of audit trail into modules
"""
import logging
from typing import Optional, Dict, Any
from functools import wraps

from egg_farm_system.utils.audit_trail import get_audit_trail, ActionType

logger = logging.getLogger(__name__)


def audit_create(entity_type: str):
    """Decorator to audit entity creation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from context
            user_id = kwargs.get('user_id')
            username = kwargs.get('username')
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log creation
            if result:
                entity_id = getattr(result, 'id', None)
                entity_name = getattr(result, 'name', None) or getattr(result, 'title', None)
                
                get_audit_trail().log_action(
                    user_id=user_id,
                    username=username,
                    action_type=ActionType.CREATE,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_name=entity_name,
                    description=f"Created {entity_type}: {entity_name or entity_id}",
                    new_values=_get_entity_dict(result) if result else None
                )
            
            return result
        return wrapper
    return decorator


def audit_update(entity_type: str):
    """Decorator to audit entity updates"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get entity ID
            entity_id = kwargs.get('entity_id') or (args[1] if len(args) > 1 else None)
            
            # Get old values before update
            old_values = None
            if entity_id and hasattr(args[0], 'get_entity_by_id'):
                try:
                    old_entity = args[0].get_entity_by_id(entity_id)
                    if old_entity:
                        old_values = _get_entity_dict(old_entity)
                except:
                    pass
            
            # Get user
            user_id = kwargs.get('user_id')
            username = kwargs.get('username')
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log update
            if result:
                entity_id = getattr(result, 'id', None) if not entity_id else entity_id
                entity_name = getattr(result, 'name', None) or getattr(result, 'title', None)
                
                get_audit_trail().log_action(
                    user_id=user_id,
                    username=username,
                    action_type=ActionType.UPDATE,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_name=entity_name,
                    description=f"Updated {entity_type}: {entity_name or entity_id}",
                    old_values=old_values,
                    new_values=_get_entity_dict(result) if result else None
                )
            
            return result
        return wrapper
    return decorator


def audit_delete(entity_type: str):
    """Decorator to audit entity deletion"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get entity ID
            entity_id = kwargs.get('entity_id') or (args[1] if len(args) > 1 else None)
            
            # Get entity before deletion
            entity_name = None
            old_values = None
            if entity_id and hasattr(args[0], 'get_entity_by_id'):
                try:
                    entity = args[0].get_entity_by_id(entity_id)
                    if entity:
                        entity_name = getattr(entity, 'name', None) or getattr(entity, 'title', None)
                        old_values = _get_entity_dict(entity)
                except:
                    pass
            
            # Get user
            user_id = kwargs.get('user_id')
            username = kwargs.get('username')
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log deletion
            get_audit_trail().log_action(
                user_id=user_id,
                username=username,
                action_type=ActionType.DELETE,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                description=f"Deleted {entity_type}: {entity_name or entity_id}",
                old_values=old_values
            )
            
            return result
        return wrapper
    return decorator


def _get_entity_dict(entity) -> Dict[str, Any]:
    """Get dictionary representation of entity"""
    if not entity:
        return {}
    
    result = {}
    # Get common attributes
    for attr in ['id', 'name', 'title', 'date', 'amount_afg', 'amount_usd', 'quantity']:
        if hasattr(entity, attr):
            value = getattr(entity, attr)
            if value is not None:
                result[attr] = str(value)
    
    return result

