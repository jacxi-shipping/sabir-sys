from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Setting


class SettingsManager:
    """Manage application settings stored in the database."""

    @staticmethod
    def get_setting(key: str, default=None):
        session = DatabaseManager.get_session()
        try:
            s = session.query(Setting).filter(Setting.key == key).first()
            return s.value if s else default
        finally:
            session.close()

    @staticmethod
    def set_setting(key: str, value: str, description: str = None):
        session = DatabaseManager.get_session()
        try:
            s = session.query(Setting).filter(Setting.key == key).first()
            if s:
                s.value = value
                if description is not None:
                    s.description = description
            else:
                s = Setting(key=key, value=value, description=description)
                session.add(s)
            session.commit()
            return s
        finally:
            session.close()

    @staticmethod
    def get_all_settings():
        session = DatabaseManager.get_session()
        try:
            return session.query(Setting).order_by(Setting.key).all()
        finally:
            session.close()
