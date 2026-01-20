# Egg Farm System

A desktop management application for small/medium poultry egg farms.

This repository provides farm, flock, inventory, purchase/sales, parties, ledger, and reporting features with a PySide6 UI and an SQLite backend.

## Highlights & New Features
- Redesigned Raw Material Sale modal — clearer UX and validation.
- New `AddTransactionDialog` supporting both Debit and Credit entries and independent AFG/USD amounts (no automatic conversion).
- Centralized theming via `egg_farm_system/styles.qss` and `egg_farm_system/ui/ui_helpers.py` (`apply_theme()` and `create_button()`).
- Full Pashto (`ps`) i18n additions merged (auto-generated entries added to `egg_farm_system/utils/i18n_additional_ps.py`).
- Fixed Employees page and Farm management DB issues (eager-loading relationships to avoid DetachedInstance errors).
- Many UI components migrated from inline `setStyleSheet()` to class-based styles for consistent theming.
- Manager-based DB operations (`LedgerManager`, `PartyManager`, etc.) and safer session handling.
- UI smoke tests available under `tools/` (including a Pashto smoke test that saves screenshots to `egg_farm_system/assets/screenshots/`).

## Installation
1. Install Python 3.10+.
2. (Optional) Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run (development)
From the repository root run:

```powershell
python run.py
```

On first run the app initializes the SQLite database and applies minimal migrations.

## Quick Usage Notes
- Open the Dashboard to navigate to Farms, Parties, Inventory, Sales, and Ledger.
- To add a manual transaction: open the Parties page and click the `Add Transaction` header button — the dialog supports choosing a party, selecting Transaction Type (Debit/Credit), entering amounts (AFG/USD independently), and saving to the ledger.

## Tests & Smoke Checks
- Run the Pashto UI smoke test:

```powershell
$env:PYTHONPATH = 'C:\Users\iam_s\Desktop\sabir-farm - Copy'; python tools/ui_smoke_ps.py
```

Screenshots are saved under `egg_farm_system/assets/screenshots/` when smoke tests run.

## Where to find more details
- Full developer documentation: [DOCUMENTATION.md](DOCUMENTATION.md)
- Key code locations:
  - UI helpers & theming: `egg_farm_system/ui/ui_helpers.py`, `egg_farm_system/styles.qss`
  - Add Transaction dialog: `egg_farm_system/ui/forms/add_transaction_dialog.py`
  - Raw Material Sale modal: `egg_farm_system/ui/forms/raw_material_sale_dialog.py`
  - i18n extras: `egg_farm_system/utils/i18n_additional_ps.py`

## Contributing
- Use 4-space indentation, wrap UI strings with `tr(...)`, and prefer `create_button()` over inline styles.
- Run smoke tests after UI changes and add or update translations as needed.

---
If you want, I can expand this README with an ER diagram, API reference, example workflows, or developer setup tips. Tell me which you'd like next.
# Egg Farm Management System

A comprehensive Windows desktop application for managing egg farms with SQLite database and dual currency support.

## Features

- **Farm Management**: Create and manage up to 4 farms
- **Shed & Flock Management**: Track sheds, flocks, and bird mortality
- **Egg Production**: Daily egg collection with grading (Small, Medium, Large, Broken)
- **Feed Manufacturing**: Raw material management, feed formulation, and batch production
- **Inventory Management**: Raw materials, finished feed, low stock alerts
- **Party Management**: Unified customer/supplier system
- **Ledger & Accounting**: Complete financial tracking with dual currency (AFG/USD)
- **Sales & Purchases**: Transaction recording with auto ledger posting
- **Expenses & Payments**: Expense tracking and payment management
- **Reports**: Daily/monthly production, feed usage, party statements, CSV export
- **Dashboard**: Key metrics at a glance

## Technology Stack

- **Python 3.11+**
- **PySide6** (Qt for Python) - UI Framework
- **SQLAlchemy** - ORM
- **SQLite** - Local Database
- **matplotlib/pyqtgraph** - Charts and Analytics

## Installation

1. Install Python 3.11 or later
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python egg_farm_system/app.py
```

## Building to EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed egg_farm_system/app.py
```

## Project Structure

```
egg_farm_system/
├── app.py                 # Main entry point
├── config.py             # Configuration settings
├── database/
│   ├── db.py            # Database manager
│   └── models.py        # SQLAlchemy models
├── modules/
│   ├── farms.py         # Farm management
│   ├── sheds.py         # Shed management
│   ├── flocks.py        # Flock management
│   ├── egg_production.py # Egg tracking
│   ├── feed_mill.py     # Feed manufacturing
│   ├── inventory.py     # Inventory management
│   ├── parties.py       # Party management
│   ├── ledger.py        # Accounting
│   ├── sales.py         # Sales transactions
│   ├── purchases.py     # Purchase transactions
│   ├── expenses.py      # Expenses & payments
│   └── reports.py       # Report generation
├── ui/
│   ├── main_window.py   # Main window
│   ├── dashboard.py     # Dashboard widget
│   ├── forms/           # Form widgets
│   └── reports/         # Report viewer
├── utils/
│   ├── currency.py      # Currency utilities
│   └── calculations.py  # Business calculations
└── assets/              # Images and resources
```

## Database

- **Type**: SQLite (.db file in data/ directory)
- **Auto-created**: On first run
- **Location**: `/data/egg_farm.db`

## Accounting System

### Ledger Balance Rules
- **Positive Balance**: Party owes us
- **Negative Balance**: We owe the party

### Dual Currency
- **Base Currency**: AFG
- **Secondary Currency**: USD
- **Exchange Rate**: Configurable, stored per transaction

## Key Business Logic

1. **Egg Production**: Tracked by shed with automatic grading
2. **Feed Manufacturing**: Cost calculated from raw materials
3. **Inventory**: Weighted average cost method for valuation
4. **Party Ledger**: Single unified ledger per party
5. **Auto Posting**: All transactions automatically post to ledger

## Default Settings

- Max Farms: 4
- Base Currency: AFG
- Secondary Currency: USD
- Default Exchange Rate: 78 AFG = 1 USD

## Notes

- Multi-user application with role-based access control (Admin/User)
- Secure login system with password hashing
- Fully offline - no internet required
- Windows desktop application
- Ready for PyInstaller conversion to .exe

## Future Enhancements

- Advanced charting and analytics
- Backup and restore functionality
- Cloud sync capability
- Mobile companion app