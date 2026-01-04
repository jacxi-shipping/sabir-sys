from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'egg_farm_system'))
from database.db import DatabaseManager
from modules.users import UserManager

def run():
    DatabaseManager.initialize()
    u = UserManager.get_user_by_username('admin')
    if not u:
        print('admin user missing')
        return
    uid = u.id
    old = 'admin'
    newp = 'Adm1n!23'
    try:
        UserManager.change_password(uid, old, newp, force=False)
        print('changed password to', newp)
        ok = UserManager.verify_credentials('admin', newp)
        print('verify with new password:', ok)
    except Exception as e:
        print('password flow failed:', e)

if __name__ == '__main__':
    run()
