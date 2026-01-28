# Cash and Credit Payment Logic - Complete Explanation

## Overview

The Egg Farm Management System supports two payment methods for sales and purchases:
- **Cash** - Immediate payment at the time of transaction
- **Credit** - Payment to be made later (creates receivables/payables)

This document explains how each payment method works, how it affects the accounting system, and provides practical examples.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [How Cash Transactions Work](#how-cash-transactions-work)
3. [How Credit Transactions Work](#how-credit-transactions-work)
4. [Party Ledger System](#party-ledger-system)
5. [Payment Records vs Ledger Entries](#payment-records-vs-ledger-entries)
6. [Examples](#examples)
7. [Technical Implementation](#technical-implementation)

---

## Core Concepts

### Payment Method
Every sale and purchase transaction requires a payment method:
- **Cash**: Money is exchanged immediately
- **Credit**: Payment is deferred (on credit/account)

### Party Ledger
The system maintains a ledger (account statement) for each party (customer/supplier):
- **Debit**: Increases what the party owes you (receivables)
- **Credit**: Increases what you owe the party (payables)

### Payment Records
Separate records tracking actual cash movements:
- **Received**: Cash received from customers
- **Paid**: Cash paid to suppliers

---

## How Cash Transactions Work

### Cash Sales (Selling Eggs/Materials)

When you make a **Cash Sale**:

1. **Transaction is recorded** with `payment_method = "Cash"`
2. **Party Ledger Entry** is created:
   - **Debit** the party account (they owe you)
3. **Payment Record** is created immediately:
   - Type: `"Received"`
   - Method: `"Cash"`
   - This records that cash was received

**Effect**: 
- The party's ledger shows they owe you money
- A payment record shows you received cash immediately
- Net effect: Party balance remains zero (they owed and paid)

### Cash Purchases (Buying Materials)

When you make a **Cash Purchase**:

1. **Transaction is recorded** with `payment_method = "Cash"`
2. **Party Ledger Entry** is created:
   - **Credit** the party account (you owe them)
3. **Payment Record** is created immediately:
   - Type: `"Paid"`
   - Method: `"Cash"`
   - This records that cash was paid

**Effect**:
- The party's ledger shows you owe them money
- A payment record shows you paid cash immediately
- Net effect: Party balance remains zero (you owed and paid)

### Why Record Both?

You might wonder why we create both a ledger entry AND a payment record for cash transactions:

1. **Ledger Entry**: Tracks the business transaction (what was bought/sold)
2. **Payment Record**: Tracks the cash flow (when money changed hands)

This separation allows:
- **Business Reporting**: Sales/Purchase reports from ledger
- **Cash Flow Reporting**: Actual cash movement tracking
- **Reconciliation**: Match transactions with payments

---

## How Credit Transactions Work

### Credit Sales (Selling on Account)

When you make a **Credit Sale**:

1. **Transaction is recorded** with `payment_method = "Credit"`
2. **Party Ledger Entry** is created:
   - **Debit** the party account (they owe you)
3. **NO Payment Record** is created

**Effect**:
- The party's ledger shows they owe you money
- No cash flow record (no payment yet)
- Party balance increases (outstanding receivable)

**Later**: When customer pays, a separate payment transaction settles the balance.

### Credit Purchases (Buying on Account)

When you make a **Credit Purchase**:

1. **Transaction is recorded** with `payment_method = "Credit"`
2. **Party Ledger Entry** is created:
   - **Credit** the party account (you owe them)
3. **NO Payment Record** is created

**Effect**:
- The party's ledger shows you owe them money
- No cash flow record (no payment yet)
- Party balance increases (outstanding payable)

**Later**: When you pay the supplier, a separate payment transaction settles the balance.

---

## Party Ledger System

### Understanding Debits and Credits

In the party ledger:

**For Sales (You sell to party)**:
- **Debit (+)**: Party owes you money
- Entry: `debit_afg = sale_amount`

**For Purchases (You buy from party)**:
- **Credit (+)**: You owe the party money
- Entry: `credit_afg = purchase_amount`

### Party Balance Calculation

```
Party Balance = Total Debits - Total Credits

Positive Balance = Party owes you (Receivable)
Negative Balance = You owe the party (Payable)
Zero Balance = All settled
```

### Example Ledger Entries

**Party: ABC Company**

| Date | Description | Debit AFG | Credit AFG | Balance AFG |
|------|-------------|-----------|------------|-------------|
| Jan 1 | Sale (Credit) | 10,000 | 0 | 10,000 |
| Jan 5 | Purchase (Credit) | 0 | 5,000 | 5,000 |
| Jan 10 | Payment Received | 0 | 7,000 | -2,000 |

Balance = 10,000 - (5,000 + 7,000) = -2,000 (You owe them 2,000)

---

## Payment Records vs Ledger Entries

### Two Separate Systems

1. **Ledger Entries** (`ledger` table):
   - Track ALL transactions (Cash and Credit)
   - Calculate party balances
   - Show who owes whom

2. **Payment Records** (`payments` table):
   - Track only CASH movements
   - Used for cash flow analysis
   - Track when money actually changed hands

### When Each is Created

| Transaction Type | Ledger Entry | Payment Record |
|-----------------|--------------|----------------|
| Cash Sale | ✅ Yes (Debit) | ✅ Yes (Received) |
| Credit Sale | ✅ Yes (Debit) | ❌ No |
| Cash Purchase | ✅ Yes (Credit) | ✅ Yes (Paid) |
| Credit Purchase | ✅ Yes (Credit) | ❌ No |
| Payment Received | ✅ Yes (Credit) | ✅ Yes (Received) |
| Payment Made | ✅ Yes (Debit) | ✅ Yes (Paid) |

---

## Examples

### Example 1: Cash Sale

**Scenario**: Sell 1000 eggs to "ABC Company" for 50,000 AFG cash

**Code**:
```python
sales_manager.record_sale(
    party_id=party.id,
    quantity=1000,
    rate_afg=50.0,
    payment_method="Cash"
)
```

**What Happens**:

1. **Sale Record Created**:
   - Party: ABC Company
   - Quantity: 1000 eggs
   - Total: 50,000 AFG
   - Payment Method: Cash

2. **Ledger Entry**:
   - Description: "Egg sale: 1000 eggs"
   - Debit: 50,000 AFG
   - (ABC Company owes you 50,000)

3. **Payment Record**:
   - Type: "Received"
   - Method: "Cash"
   - Amount: 50,000 AFG
   - Reference: "Sale #123"

4. **Net Effect**:
   - Inventory: -1000 eggs
   - Cash: +50,000 AFG
   - Party Balance: 0 (they owed and paid immediately)

---

### Example 2: Credit Sale

**Scenario**: Sell 2000 eggs to "XYZ Trading" for 100,000 AFG on credit

**Code**:
```python
sales_manager.record_sale(
    party_id=party.id,
    quantity=2000,
    rate_afg=50.0,
    payment_method="Credit"
)
```

**What Happens**:

1. **Sale Record Created**:
   - Party: XYZ Trading
   - Quantity: 2000 eggs
   - Total: 100,000 AFG
   - Payment Method: Credit

2. **Ledger Entry**:
   - Description: "Egg sale: 2000 eggs"
   - Debit: 100,000 AFG
   - (XYZ Trading owes you 100,000)

3. **NO Payment Record** (cash not received yet)

4. **Net Effect**:
   - Inventory: -2000 eggs
   - Cash: No change (credit sale)
   - Party Balance: +100,000 AFG (they owe you)

**Later**: When XYZ Trading pays:
```python
payment_manager.record_payment_received(
    party_id=party.id,
    amount_afg=100,000,
    payment_method="Cash"
)
```
- Ledger Entry: Credit 100,000 (reduces receivable)
- Payment Record: Received 100,000
- Party Balance: Now 0

---

### Example 3: Cash Purchase

**Scenario**: Buy 500kg corn from "Farm Supplies" for 25,000 AFG cash

**Code**:
```python
purchase_manager.record_purchase(
    party_id=party.id,
    material_id=material.id,
    quantity=500,
    rate_afg=50.0,
    payment_method="Cash"
)
```

**What Happens**:

1. **Purchase Record Created**:
   - Party: Farm Supplies
   - Material: Corn
   - Quantity: 500kg
   - Total: 25,000 AFG
   - Payment Method: Cash

2. **Ledger Entry**:
   - Description: "Purchase: 500kg corn"
   - Credit: 25,000 AFG
   - (You owe Farm Supplies 25,000)

3. **Payment Record**:
   - Type: "Paid"
   - Method: "Cash"
   - Amount: 25,000 AFG
   - Reference: "Purchase #456"

4. **Net Effect**:
   - Inventory: +500kg corn
   - Cash: -25,000 AFG
   - Party Balance: 0 (you owed and paid immediately)

---

### Example 4: Credit Purchase

**Scenario**: Buy 1000kg feed from "Feed Mill Co" for 75,000 AFG on credit

**Code**:
```python
purchase_manager.record_purchase(
    party_id=party.id,
    material_id=material.id,
    quantity=1000,
    rate_afg=75.0,
    payment_method="Credit"
)
```

**What Happens**:

1. **Purchase Record Created**:
   - Party: Feed Mill Co
   - Material: Feed
   - Quantity: 1000kg
   - Total: 75,000 AFG
   - Payment Method: Credit

2. **Ledger Entry**:
   - Description: "Purchase: 1000kg feed"
   - Credit: 75,000 AFG
   - (You owe Feed Mill Co 75,000)

3. **NO Payment Record** (cash not paid yet)

4. **Net Effect**:
   - Inventory: +1000kg feed
   - Cash: No change (credit purchase)
   - Party Balance: -75,000 AFG (you owe them)

**Later**: When you pay:
```python
payment_manager.record_payment_made(
    party_id=party.id,
    amount_afg=75,000,
    payment_method="Cash"
)
```
- Ledger Entry: Debit 75,000 (reduces payable)
- Payment Record: Paid 75,000
- Party Balance: Now 0

---

## Technical Implementation

### Database Models

**Sale Model** (`sales` table):
```python
class Sale(Base):
    __tablename__ = "sales"
    
    party_id = Column(Integer, ForeignKey("parties.id"))
    quantity = Column(Integer)
    total_afg = Column(Float)
    payment_method = Column(String(20), default="Cash")  # "Cash" or "Credit"
    # ... other fields
```

**Purchase Model** (`purchases` table):
```python
class Purchase(Base):
    __tablename__ = "purchases"
    
    party_id = Column(Integer, ForeignKey("parties.id"))
    quantity = Column(Float)
    total_afg = Column(Float)
    payment_method = Column(String(20), default="Cash")  # "Cash" or "Credit"
    # ... other fields
```

**Ledger Model** (`ledger` table):
```python
class Ledger(Base):
    __tablename__ = "ledger"
    
    party_id = Column(Integer, ForeignKey("parties.id"))
    date = Column(DateTime)
    description = Column(Text)
    debit_afg = Column(Float, default=0)    # Party owes you
    credit_afg = Column(Float, default=0)   # You owe party
    # ... other fields
```

**Payment Model** (`payments` table):
```python
class Payment(Base):
    __tablename__ = "payments"
    
    party_id = Column(Integer, ForeignKey("parties.id"))
    amount_afg = Column(Float)
    payment_type = Column(String(50))    # "Received" or "Paid"
    payment_method = Column(String(50))  # "Cash" or "Bank"
    reference = Column(String(100))      # Links to transaction
    # ... other fields
```

### Code Flow

**When Recording a Sale**:

```python
# 1. Create sale record
sale = Sale(
    party_id=party_id,
    quantity=quantity,
    total_afg=total_afg,
    payment_method=payment_method  # "Cash" or "Credit"
)
session.add(sale)

# 2. Post to ledger (always, for both Cash and Credit)
ledger_manager.post_entry(
    party_id=party_id,
    description="Egg sale",
    debit_afg=total_afg,  # Party owes you
    reference_type="Sale",
    reference_id=sale.id
)

# 3. Create payment record (only for Cash)
if payment_method == "Cash":
    payment = Payment(
        party_id=party_id,
        amount_afg=total_afg,
        payment_type="Received",  # You received cash
        payment_method="Cash",
        reference=f"Sale #{sale.id}"
    )
    session.add(payment)

session.commit()
```

**When Recording a Purchase**:

```python
# 1. Create purchase record
purchase = Purchase(
    party_id=party_id,
    quantity=quantity,
    total_afg=total_afg,
    payment_method=payment_method  # "Cash" or "Credit"
)
session.add(purchase)

# 2. Post to ledger (always, for both Cash and Credit)
ledger_manager.post_entry(
    party_id=party_id,
    description="Purchase",
    credit_afg=total_afg,  # You owe party
    reference_type="Purchase",
    reference_id=purchase.id
)

# 3. Create payment record (only for Cash)
if payment_method == "Cash":
    payment = Payment(
        party_id=party_id,
        amount_afg=total_afg,
        payment_type="Paid",  # You paid cash
        payment_method="Cash",
        reference=f"Purchase #{purchase.id}"
    )
    session.add(payment)

session.commit()
```

---

## Key Differences Summary

| Aspect | Cash Transaction | Credit Transaction |
|--------|-----------------|-------------------|
| **Payment Timing** | Immediate | Deferred |
| **Ledger Entry** | ✅ Created | ✅ Created |
| **Payment Record** | ✅ Created | ❌ Not Created |
| **Party Balance** | Returns to zero | Creates outstanding balance |
| **Cash Flow** | Immediate impact | No immediate impact |
| **Settlement** | Immediate | Requires later payment |

---

## Business Benefits

### Cash Transactions
- **Pros**:
  - Immediate cash flow
  - No credit risk
  - Simple accounting
  
- **Cons**:
  - May lose customers who need credit
  - Lower sales volume

### Credit Transactions
- **Pros**:
  - Build customer relationships
  - Increase sales volume
  - Competitive advantage
  
- **Cons**:
  - Cash flow delay
  - Credit risk
  - Need to track receivables/payables

---

## Reports Available

### For Cash Tracking
1. **Cash Flow Report**: Shows all cash received and paid
2. **Daily Cash Report**: Today's cash movements
3. **Payment History**: All payment records by party

### For Credit Tracking
1. **Party Ledger**: Shows all transactions and balance
2. **Receivables Report**: Who owes you money
3. **Payables Report**: Who you owe money to
4. **Aging Report**: How long balances are outstanding

---

## Common Scenarios

### Scenario 1: Customer Wants to Pay Partial Amount

**Problem**: Sold 100,000 AFG on credit, customer pays 60,000

**Solution**:
1. Record sale as Credit (creates 100,000 receivable)
2. Record separate payment of 60,000 (reduces balance to 40,000)
3. Balance shows 40,000 still owed

### Scenario 2: Mixed Transactions with Same Party

**Example**:
- Day 1: Sell 50,000 on Credit (+50,000 balance)
- Day 2: Buy 20,000 on Credit (-20,000 balance)
- Day 3: Receive payment 30,000 (-30,000 balance)
- Final Balance: 50,000 - 20,000 - 30,000 = 0 (settled)

### Scenario 3: Converting Credit Sale to Cash

**Problem**: Initially recorded as Credit, customer paid immediately

**Solution**:
1. Sale is already recorded as Credit
2. Create immediate payment record manually
3. Balance becomes zero
4. System tracks both the sale and payment

---

## Validation Rules

The system enforces these rules:

1. **Payment Method**: Must be either "Cash" or "Credit"
2. **Amounts**: Must be positive (>0)
3. **Parties**: Must exist in the system
4. **Materials**: Must exist for purchases
5. **Stock**: Must be available for sales

---

## Conclusion

The Cash and Credit payment system provides:
- **Flexibility**: Support both immediate and deferred payments
- **Accuracy**: Separate tracking of business transactions and cash flow
- **Transparency**: Clear party balances and payment history
- **Control**: Know who owes you and whom you owe

Understanding this dual-entry system is crucial for effective financial management of your egg farm business.

---

**For Support**: If you have questions about Cash/Credit logic, refer to this document or contact your system administrator.

**Last Updated**: 2026-01-28
