"""
Simple CLI to purchase Carton/Tray packaging and update RawMaterial stock.
Usage: python tools/purchase_packaging_cli.py
"""
from datetime import datetime
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.database.db import DatabaseManager

def prompt_float(prompt, default=0.0):
    try:
        val = input(prompt).strip()
        return float(val) if val else default
    except Exception:
        return default

def prompt_int(prompt, default=0):
    try:
        val = input(prompt).strip()
        return int(val) if val else default
    except Exception:
        return default

if __name__ == '__main__':
    DatabaseManager.initialize()
    party_id = prompt_int('Party ID (supplier) [1]: ', 1)
    print('Choose packaging type:')
    print('1) Carton')
    print('2) Tray')
    choice = input('Choice [1]: ').strip() or '1'
    material_name = 'Carton' if choice == '1' else 'Tray'
    qty = prompt_int(f'Quantity of {material_name} to purchase: ', 0)
    rate_afg = prompt_float('Rate per unit (AFG): ', 0.0)
    rate_usd = prompt_float('Rate per unit (USD): ', 0.0)
    date = datetime.utcnow()
    notes = input('Notes (optional): ').strip() or None

    pm = PurchaseManager()
    try:
        purchase = pm.record_packaging_purchase(
            party_id=party_id,
            material_name=material_name,
            quantity=qty,
            rate_afg=rate_afg,
            rate_usd=rate_usd,
            exchange_rate_used=78.0,
            date=date,
            notes=notes,
            payment_method='Cash'
        )
        print(f'Purchase recorded: id={purchase.id}, material={material_name}, qty={qty}')
    except Exception as e:
        print('Error recording purchase:', e)
    finally:
        pm.close_session()
        DatabaseManager.close()
