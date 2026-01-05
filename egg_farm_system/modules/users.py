from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import User
from sqlalchemy.orm import Session
import hashlib, os
import re


def _hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return salt.hex() + ':' + dk.hex()


def _verify_password(stored: str, password: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        dk = bytes.fromhex(dk_hex)
        check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return check == dk
    except Exception:
        return False


class UserManager:
    """Simple user management backed by the database."""

    @staticmethod
    def create_user(username: str, password: str, full_name: str = None, role: str = 'user') -> User:
        session = DatabaseManager.get_session()
        try:
            user = User(
                username=username,
                password_hash=_hash_password(password),
                full_name=full_name,
                role=role
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    @staticmethod
    def get_user_by_username(username: str):
        session = DatabaseManager.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    @staticmethod
    def verify_credentials(username: str, password: str) -> bool:
        user = UserManager.get_user_by_username(username)
        if not user:
            return False
        return _verify_password(user.password_hash, password)

    @staticmethod
    def validate_password_policy(password: str) -> bool:
        """Enforce a simple password policy:
        - Minimum 8 chars
        - At least one uppercase, one lowercase, one digit
        - At least one special character
        """
        if not password or len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[\W_]", password):
            return False
        return True

    @staticmethod
    def set_password(user_id: int, new_password: str):
        session = DatabaseManager.get_session()
        try:
            u = session.query(User).filter(User.id == user_id).first()
            if not u:
                return False
            u.password_hash = _hash_password(new_password)
            session.commit()
            return True
        finally:
            session.close()

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str, force: bool = False) -> bool:
        """Change password for a user. If force=True, skip old_password check (admin override)."""
        if not force:
            # verify old password
            session = DatabaseManager.get_session()
            try:
                u = session.query(User).filter(User.id == user_id).first()
                if not u:
                    return False
                if not _verify_password(u.password_hash, old_password):
                    return False
            finally:
                session.close()

        # validate policy
        if not UserManager.validate_password_policy(new_password):
            raise ValueError("Password does not meet policy requirements")

        return UserManager.set_password(user_id, new_password)

    @staticmethod
    def get_all_users():
        session = DatabaseManager.get_session()
        try:
            return session.query(User).all()
        finally:
            session.close()

    @staticmethod
    def delete_user(user_id: int):
        session = DatabaseManager.get_session()
        try:
            u = session.query(User).filter(User.id == user_id).first()
            if u:
                session.delete(u)
                session.commit()
                return True
            return False
        finally:
            session.close()
