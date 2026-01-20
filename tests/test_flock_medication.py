from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.farms import FarmManager
import uuid
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager


def setup_module(module):
    # Ensure DB initialized
    DatabaseManager.initialize()


def test_add_medication_and_mortality():
    fm = FarmManager()
    try:
        # Use a unique farm name to avoid collisions with other tests
        farm = fm.create_farm(name=f"Test Farm {uuid.uuid4().hex[:8]}")
        sm = ShedManager()
        try:
            shed = sm.create_shed(farm.id, name="Test Shed", capacity=10000)
            flock_m = FlockManager()
            try:
                flock = flock_m.create_flock(shed.id, "Test Flock", datetime.utcnow(), 100)
                # Add medication
                med = flock_m.add_medication(flock.id, datetime.utcnow(), "Vaccine-A", 5.0, dose_unit='ml', administered_by='Tech1', notes='First dose')
                assert med is not None
                meds = flock_m.get_medications(flock.id)
                assert any(m.medication_name == 'Vaccine-A' for m in meds)
                # Add mortality
                mort = flock_m.add_mortality(flock.id, datetime.utcnow(), 2, notes='Predation')
                assert mort is not None
                morts = flock_m.get_mortalities(flock.id)
                assert any(m.count == 2 for m in morts)
            finally:
                pass
        finally:
            pass
    finally:
        pass
