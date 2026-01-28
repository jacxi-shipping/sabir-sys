# Cash vs Credit Payment Flow - Visual Guide

## Quick Reference Diagrams

### Cash Sale Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       CASH SALE                             │
│                                                             │
│  You sell 1000 eggs to ABC Company for 50,000 AFG (Cash)  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Create Sale Record                                │
│  ─────────────────────────────────────────────────────────  │
│  • Party: ABC Company                                       │
│  • Quantity: 1000 eggs                                      │
│  • Amount: 50,000 AFG                                       │
│  • Payment Method: Cash ✓                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  Step 2: Ledger Entry    │  │  Step 3: Payment Record  │
│  ─────────────────────── │  │  ─────────────────────── │
│  • Party: ABC Company    │  │  • Party: ABC Company    │
│  • Debit: 50,000 AFG     │  │  • Type: Received        │
│  • Description: "Sale"   │  │  • Method: Cash          │
│  (They owe you)          │  │  • Amount: 50,000 AFG    │
└──────────────────────────┘  └──────────────────────────┘
                │                     │
                └──────────┬──────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                             │
│  ─────────────────────────────────────────────────────────  │
│  • Inventory: -1000 eggs                                    │
│  • Cash: +50,000 AFG (cash received)                        │
│  • Party Balance: 0 (they owed 50K, paid 50K)              │
│  • Ledger Shows: Debit 50K (owed), Credit 0                │
│  • Payment Shows: Received 50K                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Credit Sale Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      CREDIT SALE                            │
│                                                             │
│  You sell 2000 eggs to XYZ Trading for 100,000 AFG (Credit)│
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Create Sale Record                                │
│  ─────────────────────────────────────────────────────────  │
│  • Party: XYZ Trading                                       │
│  • Quantity: 2000 eggs                                      │
│  • Amount: 100,000 AFG                                      │
│  • Payment Method: Credit ✓                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Ledger Entry ONLY                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Party: XYZ Trading                                       │
│  • Debit: 100,000 AFG                                       │
│  • Description: "Sale"                                      │
│  (They owe you)                                             │
│                                                             │
│  ❌ NO Payment Record Created                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                             │
│  ─────────────────────────────────────────────────────────  │
│  • Inventory: -2000 eggs                                    │
│  • Cash: NO CHANGE (credit sale)                            │
│  • Party Balance: +100,000 AFG (THEY OWE YOU)               │
│  • Ledger Shows: Debit 100K (owed), Credit 0               │
│  • Payment Shows: NOTHING (no cash yet)                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                   ⏰ LATER: When customer pays
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Payment Received                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Ledger Entry: Credit 100,000 (reduces receivable)       │
│  • Payment Record: Received 100,000 AFG                     │
│  • New Balance: 0 (settled)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

### Cash Purchase Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CASH PURCHASE                           │
│                                                             │
│  You buy 500kg corn from Farm Supplies for 25,000 AFG      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Create Purchase Record                            │
│  ─────────────────────────────────────────────────────────  │
│  • Party: Farm Supplies                                     │
│  • Material: Corn                                           │
│  • Quantity: 500kg                                          │
│  • Amount: 25,000 AFG                                       │
│  • Payment Method: Cash ✓                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  Step 2: Ledger Entry    │  │  Step 3: Payment Record  │
│  ─────────────────────── │  │  ─────────────────────── │
│  • Party: Farm Supplies  │  │  • Party: Farm Supplies  │
│  • Credit: 25,000 AFG    │  │  • Type: Paid            │
│  • Description: "Purchase"│  │  • Method: Cash          │
│  (You owe them)          │  │  • Amount: 25,000 AFG    │
└──────────────────────────┘  └──────────────────────────┘
                │                     │
                └──────────┬──────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                             │
│  ─────────────────────────────────────────────────────────  │
│  • Inventory: +500kg corn                                   │
│  • Cash: -25,000 AFG (cash paid)                            │
│  • Party Balance: 0 (you owed 25K, paid 25K)               │
│  • Ledger Shows: Debit 0, Credit 25K (owed)                │
│  • Payment Shows: Paid 25K                                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Credit Purchase Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CREDIT PURCHASE                          │
│                                                             │
│  You buy 1000kg feed from Feed Mill for 75,000 AFG (Credit)│
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Create Purchase Record                            │
│  ─────────────────────────────────────────────────────────  │
│  • Party: Feed Mill                                         │
│  • Material: Feed                                           │
│  • Quantity: 1000kg                                         │
│  • Amount: 75,000 AFG                                       │
│  • Payment Method: Credit ✓                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Ledger Entry ONLY                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Party: Feed Mill                                         │
│  • Credit: 75,000 AFG                                       │
│  • Description: "Purchase"                                  │
│  (You owe them)                                             │
│                                                             │
│  ❌ NO Payment Record Created                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                             │
│  ─────────────────────────────────────────────────────────  │
│  • Inventory: +1000kg feed                                  │
│  • Cash: NO CHANGE (credit purchase)                        │
│  • Party Balance: -75,000 AFG (YOU OWE THEM)                │
│  • Ledger Shows: Debit 0, Credit 75K (owed)                │
│  • Payment Shows: NOTHING (no cash yet)                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                   ⏰ LATER: When you pay supplier
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Payment Made                                               │
│  ─────────────────────────────────────────────────────────  │
│  • Ledger Entry: Debit 75,000 (reduces payable)            │
│  • Payment Record: Paid 75,000 AFG                          │
│  • New Balance: 0 (settled)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Side-by-Side Comparison

### For SALES (You sell to customer)

```
┌─────────────────────────────┬─────────────────────────────┐
│         CASH SALE           │       CREDIT SALE           │
├─────────────────────────────┼─────────────────────────────┤
│ Payment: Immediate          │ Payment: Later              │
│                             │                             │
│ Creates:                    │ Creates:                    │
│  ✓ Sale Record              │  ✓ Sale Record              │
│  ✓ Ledger Entry (Debit)     │  ✓ Ledger Entry (Debit)     │
│  ✓ Payment Record (Received)│  ✗ NO Payment Record        │
│                             │                             │
│ Cash Impact: +Amount        │ Cash Impact: None           │
│ Party Balance: 0            │ Party Balance: +Amount      │
│                             │   (They owe you)            │
│                             │                             │
│ Best for:                   │ Best for:                   │
│  • Immediate cash needs     │  • Building relationships   │
│  • Unknown customers        │  • Regular customers        │
│  • Small transactions       │  • Large orders             │
└─────────────────────────────┴─────────────────────────────┘
```

### For PURCHASES (You buy from supplier)

```
┌─────────────────────────────┬─────────────────────────────┐
│       CASH PURCHASE         │      CREDIT PURCHASE        │
├─────────────────────────────┼─────────────────────────────┤
│ Payment: Immediate          │ Payment: Later              │
│                             │                             │
│ Creates:                    │ Creates:                    │
│  ✓ Purchase Record          │  ✓ Purchase Record          │
│  ✓ Ledger Entry (Credit)    │  ✓ Ledger Entry (Credit)    │
│  ✓ Payment Record (Paid)    │  ✗ NO Payment Record        │
│                             │                             │
│ Cash Impact: -Amount        │ Cash Impact: None           │
│ Party Balance: 0            │ Party Balance: -Amount      │
│                             │   (You owe them)            │
│                             │                             │
│ Best for:                   │ Best for:                   │
│  • Discount for cash        │  • Preserve cash flow       │
│  • Unknown suppliers        │  • Regular suppliers        │
│  • Small purchases          │  • Large purchases          │
└─────────────────────────────┴─────────────────────────────┘
```

---

## Party Balance Over Time

### Example Timeline: ABC Company

```
Day 1: Credit Sale 50,000
┌─────────────────────────────────────┐
│ Balance: +50,000 (They owe you)     │
└─────────────────────────────────────┘

Day 3: Credit Purchase 20,000
┌─────────────────────────────────────┐
│ Balance: +30,000                    │
│ (50,000 they owe - 20,000 you owe)  │
└─────────────────────────────────────┘

Day 5: Payment Received 40,000
┌─────────────────────────────────────┐
│ Balance: -10,000 (You owe them)     │
│ (30,000 - 40,000 received)          │
└─────────────────────────────────────┘

Day 7: Cash Sale 10,000
┌─────────────────────────────────────┐
│ Balance: 0 (Settled!)               │
│ (-10,000 + 10,000)                  │
└─────────────────────────────────────┘
```

---

## Decision Tree: Which Payment Method?

```
                    Making a Transaction?
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
         Do you have cash?         Is this a
         Can you pay now?        trusted party?
                │                       │
         ┌──────┴──────┐         ┌──────┴──────┐
         ▼             ▼         ▼             ▼
        Yes            No        Yes            No
         │             │         │             │
         ▼             ▼         ▼             ▼
    Use CASH      Use CREDIT   Either OK   Use CASH
                                (your       (safer)
                                choice)
```

---

## Common Patterns

### Pattern 1: Regular Customer - Mixed Transactions

```
Month: January
┌────────────────────────────────────────────────────────┐
│ Jan 5:  Credit Sale      +100,000                      │
│ Jan 12: Credit Sale      +50,000                       │
│ Jan 15: Payment Received -100,000                      │
│ Jan 20: Credit Purchase  -30,000                       │
│ Jan 25: Cash Sale        +20,000 (immediate)           │
│ Jan 28: Payment Received -40,000                       │
│                                                        │
│ Month End Balance: 0 ✓ (All settled)                  │
└────────────────────────────────────────────────────────┘
```

### Pattern 2: Cash-Only Operations

```
All transactions use Cash payment method
┌────────────────────────────────────────────────────────┐
│ • Every sale: Cash received immediately                │
│ • Every purchase: Cash paid immediately                │
│ • Party balances: Always 0                             │
│ • Cash flow: Real-time tracking                        │
│ • No receivables/payables to manage                    │
│                                                        │
│ Pros: Simple, immediate cash                           │
│ Cons: May lose business, lower volumes                 │
└────────────────────────────────────────────────────────┘
```

### Pattern 3: Credit Management

```
Weekly settlement cycle
┌────────────────────────────────────────────────────────┐
│ Mon-Fri: All transactions on Credit                    │
│          (Track daily balances)                        │
│                                                        │
│ Saturday: Settlement Day                               │
│          • Review all party balances                   │
│          • Collect from customers (receivables)        │
│          • Pay suppliers (payables)                    │
│          • Goal: Zero or minimal balances              │
│                                                        │
│ Pros: Flexible during week, organized settlement       │
│ Cons: Need good tracking, weekly reconciliation        │
└────────────────────────────────────────────────────────┘
```

---

## Warning Signs

### When Balances Get Too High

```
⚠️  Customer Balance > 500,000 AFG
    ├─ Action: Request partial payment
    ├─ Consider: Credit limit
    └─ Risk: Bad debt if they don't pay

⚠️  Supplier Balance > 300,000 AFG
    ├─ Action: Make payment soon
    ├─ Consider: Your cash flow
    └─ Risk: Supply disruption

⚠️  Party Balance Negative (You owe them)
    ├─ Check: Did you overpay?
    ├─ Action: Review transactions
    └─ Contact: Party to clarify
```

---

## Report Indicators

### Dashboard Metrics

```
┌────────────────────────────────────┐
│     Cash Position                  │
│  ─────────────────────────────     │
│  Cash on Hand:      250,000 AFG    │
│  (From Cash transactions)          │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│     Credit Position                │
│  ─────────────────────────────     │
│  Receivables:       150,000 AFG ↑  │
│  (Customers owe you)               │
│                                    │
│  Payables:          -80,000 AFG ↓  │
│  (You owe suppliers)               │
│                                    │
│  Net Credit:         70,000 AFG    │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│     Total Position                 │
│  ─────────────────────────────     │
│  Cash + Net Credit = 320,000 AFG   │
│  (True business value)             │
└────────────────────────────────────┘
```

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════╗
║               CASH vs CREDIT CHEAT SHEET              ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  CASH = Money exchanges hands NOW                    ║
║  ─────────────────────────────────                    ║
║  ✓ Ledger entry created                               ║
║  ✓ Payment record created                             ║
║  ✓ Cash increases/decreases                           ║
║  ✓ Party balance stays 0                              ║
║                                                       ║
║  CREDIT = Money exchanges hands LATER                 ║
║  ─────────────────────────────────────                ║
║  ✓ Ledger entry created                               ║
║  ✗ NO payment record                                  ║
║  ✗ NO cash impact                                     ║
║  ✓ Party balance changes                              ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  SALES (You sell)                                     ║
║  ────────────────                                     ║
║  Ledger: DEBIT   (Customer owes you)                  ║
║  Cash:   RECEIVED (if Cash method)                    ║
║                                                       ║
║  PURCHASES (You buy)                                  ║
║  ────────────────────                                 ║
║  Ledger: CREDIT  (You owe supplier)                   ║
║  Cash:   PAID    (if Cash method)                     ║
╚═══════════════════════════════════════════════════════╝
```

---

**Remember**: 
- Cash = Immediate settlement
- Credit = Track balances, settle later
- Both methods post to ledger
- Only Cash creates payment records

**For detailed explanations, see**: `CASH_CREDIT_LOGIC_EXPLANATION.md`
