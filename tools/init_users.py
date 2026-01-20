import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.users import UserManager


if __name__ == '__main__':
    DatabaseManager.initialize()
    u = UserManager.get_user_by_username('admin')
    if not u:
        UserManager.create_user('admin', 'admin', 'Administrator', 'admin')
        print('created admin')
    else:
        print('admin exists')
