"""
Resets the password for the 'admin' user.
Can be run interactively or with a password provided as a command-line argument.
"""
import sys
import argparse
from pathlib import Path
import getpass

# Ensure egg_farm_system package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.users import UserManager

def reset_admin_password(new_password_arg=None):
    """Finds the admin user and resets their password."""
    print("Initializing database...")
    DatabaseManager.initialize()
    
    print("Looking for 'admin' user...")
    admin_user = UserManager.get_user_by_username('admin')
    
    if not admin_user:
        print("Error: The 'admin' user was not found in the database.")
        print("Please run the 'tools/init_users.py' script first to create the admin user.")
        return

    print("Admin user found.")
    
    new_password = new_password_arg
    if not new_password:
        # Interactive password prompt
        while True:
            try:
                new_password = getpass.getpass(prompt="Enter the new password for admin: ")
                if UserManager.validate_password_policy(new_password):
                    confirm_password = getpass.getpass(prompt="Confirm the new password: ")
                    if new_password == confirm_password:
                        break
                    else:
                        print("Passwords do not match. Please try again.")
                else:
                    print("Password does not meet the policy requirements:")
                    print("- Minimum 8 characters")
                    print("- At least one uppercase letter, one lowercase letter, and one digit")
                    print("- At least one special character (e.g., !@#$%)")
            except Exception as e:
                print(f"An error occurred: {e}")
                return
    else:
        # Password provided as argument, validate it
        if not UserManager.validate_password_policy(new_password):
            print("Error: The provided password does not meet the policy requirements.")
            return

    try:
        UserManager.set_password(admin_user.id, new_password)
        print("\nSuccessfully reset the password for 'admin'.")
        if new_password_arg:
            print("WARNING: The new password was passed as a command-line argument and may be saved in your shell history.")
        print("You can now log in with the new password.")
    except Exception as e:
        print(f"\nAn error occurred while setting the new password: {e}")
    finally:
        DatabaseManager.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reset the admin user's password.")
    parser.add_argument('--password', type=str, help='The new password for the admin user.')
    args = parser.parse_args()
    
    reset_admin_password(args.password)

