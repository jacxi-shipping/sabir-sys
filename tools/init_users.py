import sys
from pathlib import Path

# Ensure egg_farm_system package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / 'egg_farm_system'))

from database.db import DatabaseManager
from modules.users import UserManager


if __name__ == '__main__':
    DatabaseManager.initialize()
    u = UserManager.get_user_by_username('admin')
    if not u:
        UserManager.create_user('admin', 'admin', 'Administrator', 'admin')
        print('created admin')
    else:
        print('admin exists')
