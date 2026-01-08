# Additional Issues Found - Egg Farm Management System

## Medium Priority Issues

### 1. Database Session Leaks in Manager Classes ⚠️

**Problem**: Many manager classes create sessions in `__init__` but never guarantee they're closed. Sessions remain open for the lifetime of the manager instance.

**Affected Classes** (13 classes):
- `SalesManager`
- `PurchaseManager`
- `ExpenseManager`
- `PaymentManager`
- `FarmManager`
- `ShedManager`
- `PartyManager`
- `EggProductionManager`
- `RawMaterialManager`
- `FeedFormulaManager`
- `FeedProductionManager`
- `FeedIssueManager`
- `EquipmentManager`
- `ReportGenerator`
- `GlobalSearchManager`

**Example**:
```python
class SalesManager:
    def __init__(self):
        self.session = DatabaseManager.get_session()  # Session created but never closed automatically
```

**Impact**: 
- Database connections accumulate over time
- Can exhaust SQLite connection limits
- Memory leaks in long-running sessions

**Recommendation**: 
- Use context managers or ensure `close_session()` is called
- Or refactor to use per-method sessions (like `FlockManager`)

---

### 2. Missing Error Handling in Silent Exception ⚠️

**File**: `egg_farm_system/app.py` (lines 44-45)

**Problem**: Stylesheet loading errors are silently swallowed without logging.

```python
except Exception:
    pass  # No logging, no user feedback
```

**Impact**: 
- Errors are hidden, making debugging difficult
- Users won't know if styles failed to load

**Recommendation**: 
```python
except Exception as e:
    logger.warning(f"Failed to load stylesheet: {e}")
```

---

### 3. Potential Session Mismatch in EquipmentManager ⚠️

**File**: `egg_farm_system/modules/equipments.py` (lines 56-70)

**Problem**: `update_equipment()` calls `get_equipment_by_id()` which uses `self.session`, but if the equipment was queried in a different session, it might not be found or might be stale.

```python
def update_equipment(self, equipment_id, **data):
    equipment = self.get_equipment_by_id(equipment_id)  # Uses self.session
    # ... but equipment might be from a different session context
```

**Impact**: 
- Potential stale data issues
- Update might fail silently if equipment not found in current session

**Recommendation**: 
- Query equipment directly in the same method
- Or ensure session consistency

---

### 4. Missing Variable Definition in Calculations ⚠️

**File**: `egg_farm_system/utils/calculations.py` (line 210)

**Problem**: `weighted_average_cost()` references `total_cost` but it's never defined.

```python
def weighted_average_cost(purchases):
    # ...
    total_qty = sum(p['quantity'] for p in purchases)
    if total_qty == 0:
        return 0
    
    return total_cost / total_qty  # ❌ total_cost is never defined!
```

**Impact**: 
- `NameError` when this function is called
- Function is completely broken

**Recommendation**: 
```python
total_cost = sum(p['quantity'] * p['unit_cost'] for p in purchases)
```

---

### 5. Session Management in FinancialReportGenerator ⚠️

**File**: `egg_farm_system/modules/financial_reports.py`

**Problem**: Class expects a session to be passed in `__init__` but doesn't manage its lifecycle. The caller is responsible for closing it, but this isn't documented.

```python
def __init__(self, session):
    self.session = session  # Who closes this?
```

**Impact**: 
- Unclear ownership of session lifecycle
- Potential session leaks if caller forgets to close

**Recommendation**: 
- Document that caller must close session
- Or use context manager pattern
- Or create/close session internally

---

### 6. GlobalSearchManager Session Never Closed ⚠️

**File**: `egg_farm_system/utils/global_search.py` (line 21)

**Problem**: Creates a session in `__init__` but never closes it. No `close_session()` method.

```python
def __init__(self):
    self.session = DatabaseManager.get_session()  # Never closed
```

**Impact**: 
- Session leak every time GlobalSearchManager is instantiated

**Recommendation**: 
- Add `close_session()` method
- Or use per-method sessions

---

### 7. Missing Null Checks in Some Query Results ⚠️

**Files**: Various modules

**Problem**: Some methods return query results without checking if they're None before accessing attributes.

**Example** (potential issue):
```python
def some_method(self):
    result = self.session.query(SomeModel).first()
    return result.some_attribute  # ❌ Could be None
```

**Impact**: 
- `AttributeError` if query returns None

**Note**: Most places handle this correctly, but worth reviewing all query results.

---

### 8. Inconsistent Error Return Values ⚠️

**Problem**: Some methods return `None` on error, others return empty lists `[]`, others raise exceptions.

**Examples**:
- `get_sales_summary()` returns `None` on error
- `get_sales()` returns `[]` on error
- `record_sale()` raises exception on error

**Impact**: 
- Inconsistent API makes error handling difficult
- Callers must check for both `None` and empty lists

**Recommendation**: 
- Standardize error handling pattern across all managers

---

### 9. Missing Input Validation ⚠️

**Problem**: Some methods don't validate inputs before database operations.

**Examples**:
- Negative quantities might be allowed
- Future dates might be allowed where they shouldn't be
- Empty strings might be accepted for required fields

**Impact**: 
- Invalid data in database
- Potential business logic errors

**Recommendation**: 
- Add validation at method entry points
- Use database constraints as backup

---

### 10. Read Operations Don't Use Transactions Properly ⚠️

**Problem**: Some read operations use sessions but don't need transactions. However, if an error occurs, the session might be left in a bad state.

**Example**:
```python
def get_sales(self, ...):
    try:
        query = self.session.query(Sale)  # Read operation
        return query.all()
    except Exception as e:
        logger.error(...)
        return []
    # No rollback needed, but session might be in bad state
```

**Impact**: 
- Minor: Session state issues if errors occur

**Note**: This is less critical for read operations, but worth noting.

---

## Low Priority Issues

### 11. Code Quality: Missing Type Hints

**Problem**: Most methods lack type hints, making code harder to understand and maintain.

**Impact**: 
- Reduced code clarity
- No IDE autocomplete benefits
- Harder to catch type errors

---

### 12. Code Quality: Inconsistent Docstring Format

**Problem**: Some methods have detailed docstrings, others have none or minimal ones.

**Impact**: 
- Reduced code documentation
- Harder for new developers to understand

---

### 13. Potential Performance Issue: N+1 Queries

**Problem**: Some methods might perform N+1 queries when loading related objects.

**Example** (hypothetical):
```python
for sale in sales:
    party = get_party_by_id(sale.party_id)  # Query for each sale
```

**Impact**: 
- Performance degradation with large datasets

**Note**: Need to review actual code to confirm this exists.

---

## Summary

### Critical Issues: 1
- ❌ **Missing variable definition** in `calculations.py` (will cause runtime error)

### Medium Priority: 9
- ⚠️ Session leaks in manager classes
- ⚠️ Silent exception swallowing
- ⚠️ Session mismatch potential
- ⚠️ Session lifecycle management issues
- ⚠️ Missing null checks
- ⚠️ Inconsistent error handling
- ⚠️ Missing input validation
- ⚠️ Read operation transaction handling

### Low Priority: 3
- 📝 Missing type hints
- 📝 Inconsistent documentation
- 📝 Potential N+1 queries

---

## Recommended Fix Priority

1. **URGENT**: Fix `total_cost` undefined variable in `calculations.py`
2. **HIGH**: Fix session leaks in manager classes
3. **MEDIUM**: Add error logging for silent exceptions
4. **MEDIUM**: Standardize error handling patterns
5. **LOW**: Add type hints and improve documentation

---

## Files Needing Attention

1. `egg_farm_system/utils/calculations.py` - **CRITICAL**: Missing variable
2. `egg_farm_system/app.py` - Silent exception
3. `egg_farm_system/modules/equipments.py` - Session mismatch
4. `egg_farm_system/utils/global_search.py` - Session leak
5. `egg_farm_system/modules/financial_reports.py` - Session lifecycle
6. All manager classes - Session leak pattern

