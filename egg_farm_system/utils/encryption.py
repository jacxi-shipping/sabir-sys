"""
Simple encryption utility for sensitive settings
Uses Fernet (symmetric encryption) from cryptography library
"""
import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import logging

logger = logging.getLogger(__name__)


class SettingsEncryption:
    """Encryption for sensitive settings like passwords"""
    
    def __init__(self):
        """Initialize encryption with a key derived from system-specific data"""
        self._cipher = None
        
    def _get_or_create_key(self) -> bytes:
        """
        Get or create encryption key based on system-specific data
        
        The key is derived from a combination of:
        1. A stored salt (or generated if first run)
        2. System-specific identifier (hostname + user)
        
        This provides reasonable security for local storage without requiring
        the user to remember an additional password.
        """
        from egg_farm_system.config import DATA_DIR
        
        key_file = DATA_DIR / ".encryption_key"
        
        # Try to load existing key
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not load encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key securely
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Unix-like systems)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass  # Windows doesn't support chmod
            logger.info("Generated new encryption key")
        except Exception as e:
            logger.error(f"Could not save encryption key: {e}")
        
        return key
    
    def _get_cipher(self):
        """Get or create cipher instance"""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            cipher = self._get_cipher()
            encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            # Fall back to plaintext in case of error (not ideal but prevents data loss)
            return plaintext
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt a string value
        
        Args:
            encrypted: The base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            return ""
        
        try:
            cipher = self._get_cipher()
            decrypted_bytes = cipher.decrypt(encrypted.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.warning(f"Decryption failed, returning as-is: {e}")
            # If decryption fails, assume it's plaintext (for backward compatibility)
            return encrypted


# Global instance
_encryption = SettingsEncryption()


def encrypt_setting(value: str) -> str:
    """Encrypt a setting value"""
    return _encryption.encrypt(value)


def decrypt_setting(value: str) -> str:
    """Decrypt a setting value"""
    return _encryption.decrypt(value)
