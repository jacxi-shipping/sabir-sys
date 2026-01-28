**Egg Farm System — Complete Documentation**

**Overview**
- **Purpose:** A desktop management application for small/medium poultry egg farms. It handles farms, flocks, feed, raw materials, purchases, sales, parties (customers/suppliers), ledgers, and financial reports.
- **Stack:** Python 3.x, PySide6 (Qt Widgets), SQLAlchemy ORM with SQLite, modular codebase under `egg_farm_system`.

**Features**
- **Dashboard:** High-level metrics, quick actions, notifications.
- **Farm & Sheds Management:** CRUD for farms and their sheds; eager-loaded relationships to avoid ORM issues.
- **Flocks & Egg Production:** Track flocks, production, mortalities, and feed consumption.
- **Inventory & Raw Materials:** Manage raw materials, stock, and raw-material sale modal (redesigned).
- **Purchases & Sales:** Create and manage purchase orders and sales with ledger integration.
- **Parties (Customers/Suppliers):** Add and manage parties, view transactions, and add manual transactions via `AddTransactionDialog`.
- **Ledger & Financial Reports:** Post debit/credit entries, run basic financial reports and ledgers.
- **Users & Settings:** Basic user management and app settings.
- **Theming & Styling:** Centralized theming via `styles.qss` and helper `ui_helpers.create_button()`.
- **Internationalization (i18n):** `tr(...)` wrapper and `TRANSLATIONS` loader; Pashto (`ps`) additions included.
- **Testing:** UI smoke tests available under `tools/` (includes Pashto smoke test).

**Installation**
- **Prerequisites:** Python 3.10+ (recommended), pip, virtualenv (optional).
- **Install dependencies:**
  - Create venv (optional): `python -m venv .venv`
  - Activate and install: `pip install -r requirements.txt`
- **Run application (development):**
  - From repository root run: `python run.py`

**Quickstart**
- On first run the app will initialize the SQLite database and run lightweight migrations.
- Use the Dashboard to navigate into Farms, Parties, Inventory, and Ledger modules.
- To add a manual transaction from the Parties page click the header `Add Transaction` button — this opens the `AddTransactionDialog` supporting both Debit and Credit and independent AFG/USD amounts.

**Repository Layout (key files & folders)**
- `egg_farm_system/` — main package.
  - `app.py` : application entrypoint and theme initialization.
  - `config.py` : configuration values (DB URI, defaults).
  - `database/` : `db.py` (DatabaseManager), migration helpers.
  - `modules/` : business logic modules (e.g., `farms.py`, `parties.py`, `ledger.py`, `raw_materials.py`).
  - `ui/` : Qt widgets and forms.
    - `forms/` : dialogs and form windows (e.g., `add_transaction_dialog.py`, `raw_material_sale_dialog.py`, `party_forms.py`).
    - `widgets/` : reusable widgets (loading overlays, notification center, etc.).
    - `ui_helpers.py` : `apply_theme()` and `create_button()` helper.
  - `utils/` : helpers such as `i18n.py` and `i18n_additional_ps.py`.

**Architecture & Patterns**
- **Separation of concerns:** UI code under `ui/`; domain logic under `modules/`; DB access centralized via `database/db.py`.
- **Database sessions:** Modules use `DatabaseManager.get_session()` and manager classes (e.g., `LedgerManager`, `PartyManager`) that accept sessions for transactional operations.
- **Dialogs/Forms:** QDialog-based forms that validate inputs then call manager APIs to persist data.
- **Styling & Buttons:** Rather than calling `setStyleSheet()` inline, the code uses `ui_helpers.create_button()` and class-based selectors in `styles.qss` for consistent look-and-feel.

**Internationalization (i18n)**
- The project uses a `tr()` wrapper around UI strings and a `TRANSLATIONS` dictionary loader in `egg_farm_system/utils/i18n.py`.
- Additional Pashto translations were auto-generated and stored in `egg_farm_system/utils/i18n_additional_ps.py`. These additions should be manually reviewed for accuracy.

**Theming**
- The app applies `styles.qss` at startup via `apply_theme()` in `egg_farm_system/ui/ui_helpers.py`.
- Button types: primary, success, danger, ghost — set via the `class` property on `QPushButton` created by `create_button()`.

**Database & Migrations**
- Default SQLite DB: `sqlite:///egg_farm.db` (configurable in `config.py`).
- Migrations: lightweight migration scripts are present under `egg_farm_system/database/` and project helpers. On app start minimal schema checks/migrations run automatically.

**Testing & Smoke Tests**
- Quick UI smoke tests are available in `tools/` (e.g., `ui_smoke_ps.py`) which run the app in sequence and save screenshots to `egg_farm_system/assets/screenshots/`.
- Unit tests: Not exhaustive; focus is primarily UI smoke and integration scripts.

**Troubleshooting (common issues & fixes)**
- IndentationError when importing revised dialog files: ensure Python file indentation is consistent (spaces only) — see `egg_farm_system/ui/forms/add_transaction_dialog.py` (recent fix applied).
- DetachedInstanceError from SQLAlchemy on UI-bound model objects: use eager-loading or expunge objects before returning from DB manager functions (see `modules/farms.py` changes).
- Missing translations: check `egg_farm_system/utils/i18n.py` and the `TRANSLATIONS` dict; add or correct entries in `i18n_additional_ps.py`.

**Contributing**
- Follow project style: consistent 4-space indentation, descriptive function names, avoid inline `setStyleSheet` — use `create_button()`.
- For UI text, wrap in `tr(...)` to include in i18n processing.
- Run smoke tests after UI changes: `python tools/ui_smoke_ps.py` (Pashto) or the English smoke test script.

**Where to look for functionality**
- Parties & Transactions: `egg_farm_system/modules/parties.py`, `egg_farm_system/modules/ledger.py`, `egg_farm_system/ui/forms/add_transaction_dialog.py`, `egg_farm_system/ui/forms/party_forms.py`.
- Raw Material Sale Modal (redesigned): `egg_farm_system/ui/forms/raw_material_sale_dialog.py` and `egg_farm_system/modules/raw_materials_*.py`.
- Theming utilities: `egg_farm_system/ui/ui_helpers.py`, `egg_farm_system/styles.qss`.
- i18n: `egg_farm_system/utils/i18n.py`, `egg_farm_system/utils/i18n_additional_ps.py`.

**Next steps & Recommendations**
- Review and refine auto-generated Pashto translations for correctness.
- Expand unit/integration tests for critical business logic (ledger posting, inventory adjustments).
- Continue migrating any remaining inline-styled widgets to `create_button()` + `styles.qss` classes for consistent UI.

**Contact / Maintainers**
- Repository maintainer: (update README or DEVELOPER.md with your name/email).

---
File created: `DOCUMENTATION.md` — please review and tell me if you'd like additional sections (API reference, ER diagram, or developer setup scripts).
