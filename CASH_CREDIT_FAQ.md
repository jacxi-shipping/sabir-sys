# Cash and Credit - Frequently Asked Questions (FAQ)

## General Questions

### Q1: What is the difference between Cash and Credit?

**A**: 
- **Cash**: Money is exchanged immediately when the transaction happens
- **Credit**: Money will be exchanged later (the transaction is "on account")

Think of it like this:
- Cash = Pay now
- Credit = Pay later (create a debt)

---

### Q2: Which payment method should I use?

**A**: It depends on your situation:

**Use CASH when**:
- You need immediate money
- Dealing with unknown/new customers
- The transaction is small
- You want to avoid tracking balances

**Use CREDIT when**:
- Building customer relationships
- Working with regular/trusted parties
- Managing cash flow (preserve cash)
- The transaction is large

---

### Q3: Can I change a transaction from Credit to Cash later?

**A**: The transaction itself cannot be changed, but you can:
1. Leave the sale/purchase as Credit
2. Record an immediate payment to settle the balance
3. The end result is the same as if it was Cash

---

## Ledger Questions

### Q4: Why does the ledger show an entry even for Cash transactions?

**A**: The ledger tracks ALL business transactions, not just credit transactions. This allows you to:
- See complete transaction history
- Generate business reports
- Track what was sold/bought regardless of payment method

---

### Q5: What does "Debit" and "Credit" mean in the party ledger?

**A**: From your business perspective:
- **Debit** = Party owes you money (Receivable)
- **Credit** = You owe the party money (Payable)

Examples:
- You sell eggs → Debit the customer (they owe you)
- You buy feed → Credit the supplier (you owe them)

---

### Q6: Why is my party balance not zero after a Cash transaction?

**A**: For Cash transactions, the balance should be zero because:
1. Ledger entry records the debt (Debit or Credit)
2. Payment record settles it immediately

If the balance is not zero, check:
- Was the payment recorded correctly?
- Are there other Credit transactions?
- Is there a data entry error?

---

## Payment Record Questions

### Q7: What are Payment Records?

**A**: Payment records track actual cash movements:
- When you received cash from customers
- When you paid cash to suppliers

These are separate from ledger entries and are used for:
- Cash flow analysis
- Bank reconciliation
- Tracking when money actually changed hands

---

### Q8: Why don't Credit transactions create Payment Records?

**A**: Because no cash has actually moved yet!
- Credit transactions create a debt (ledger entry)
- Payment records are created only when cash is exchanged
- Later, when payment is made, a payment record is created

---

### Q9: If I make a Credit sale, when is the Payment Record created?

**A**: When the customer actually pays you. For example:
1. Day 1: Credit sale of 100,000 → Ledger entry only
2. Day 5: Customer pays 60,000 → Payment record created
3. Day 10: Customer pays remaining 40,000 → Another payment record

---

## Balance Questions

### Q10: What does a positive party balance mean?

**A**: The party owes you money (Accounts Receivable)

Example:
- Balance: +50,000 AFG
- Meaning: This party needs to pay you 50,000 AFG

---

### Q11: What does a negative party balance mean?

**A**: You owe the party money (Accounts Payable)

Example:
- Balance: -30,000 AFG
- Meaning: You need to pay this party 30,000 AFG

---

### Q12: Can I have both sales and purchases with the same party?

**A**: Yes! The ledger tracks both:
- Sales → Debit (they owe you)
- Purchases → Credit (you owe them)
- Balance = Total debits - Total credits

Example:
- Sell 100,000 to party (Debit 100,000)
- Buy 40,000 from same party (Credit 40,000)
- Balance = 100,000 - 40,000 = 60,000 (they owe you net)

---

## Cash Flow Questions

### Q13: How does Credit affect my cash flow?

**A**: Credit transactions do NOT immediately affect cash:
- Credit Sale: No cash received yet (cash flow = 0)
- Credit Purchase: No cash paid yet (cash flow = 0)

This can cause cash flow issues if:
- You have many Credit sales (money owed to you)
- You have many Credit purchases to pay (money you owe)
- There's a timing mismatch

---

### Q14: How can I see my actual cash position?

**A**: Look at the "Payment Records" or "Cash Flow Report":
- Shows only actual cash received/paid
- Ignores Credit transactions until they're settled
- Gives you true cash-on-hand picture

---

### Q15: What if I have high sales but low cash?

**A**: This happens when most sales are on Credit:
- Sales ledger shows high revenue
- But cash hasn't been collected yet
- Solution: 
  - Follow up on receivables
  - Consider more Cash sales
  - Offer discounts for immediate payment

---

## Practical Scenarios

### Q16: Customer wants to pay partial amount for a Credit sale. How do I record it?

**A**: 
1. Original Credit sale is already recorded
2. Record the partial payment separately
3. The payment reduces the party balance

Example:
- Credit sale: 100,000 AFG (Balance: +100,000)
- Customer pays: 60,000 AFG (Balance: +40,000 remaining)
- Later pays: 40,000 AFG (Balance: 0, settled)

---

### Q17: I sold on Credit but customer paid immediately. What should I do?

**A**: Two options:

**Option 1** (Recommended):
- Record the sale as Credit
- Record an immediate payment
- Result: Same as Cash sale

**Option 2**:
- If you haven't saved yet, change payment method to Cash
- System will handle both ledger and payment

---

### Q18: Can I convert a Cash transaction to Credit?

**A**: Not directly, because:
- Cash transaction has both ledger and payment records
- You would need to:
  1. Delete the payment record (if allowed)
  2. Or accept it as is (cash was exchanged)

Better approach: Record accurately from the start

---

### Q19: How do I know which parties owe me money?

**A**: Check the "Receivables Report" or "Party Balances":
- Shows all parties with positive balances
- These are your accounts receivable
- Consider following up on old balances

---

### Q20: How do I know whom I owe money?

**A**: Check the "Payables Report" or "Party Balances":
- Shows all parties with negative balances
- These are your accounts payable
- Prioritize payments based on terms

---

## Accounting Questions

### Q21: Why does the system have both ledger and payment records?

**A**: They serve different purposes:

**Ledger (Party Account)**:
- Tracks business transactions
- Shows who owes whom
- Used for party statements
- Includes both Cash and Credit

**Payment Records (Cash Flow)**:
- Tracks only cash movements
- Shows when money changed hands
- Used for cash flow analysis
- Only for Cash transactions and settlements

---

### Q22: How does the system ensure accuracy?

**A**: Through validation:
- Payment method must be "Cash" or "Credit"
- Amounts must be positive
- Parties must exist
- Stock must be available
- For Cash, both ledger and payment are created atomically

---

### Q23: What happens if a transaction fails?

**A**: The system uses database transactions:
- If any step fails, everything is rolled back
- No partial records are created
- Your data stays consistent
- You'll see an error message explaining what went wrong

---

## Reporting Questions

### Q24: Which reports show Cash transactions?

**A**: 
- **Cash Flow Report**: All cash movements
- **Payment History**: All payments received/made
- **Daily Cash Report**: Today's cash activity

---

### Q25: Which reports show Credit transactions?

**A**: 
- **Party Ledger**: All transactions (Cash and Credit)
- **Receivables Report**: Who owes you
- **Payables Report**: Whom you owe
- **Aging Report**: How old the balances are

---

### Q26: How do I see both Cash and Credit together?

**A**: 
- **Party Statement**: Shows all transactions for a party
- **Transaction Reports**: Shows all sales/purchases
- **Balance Sheet**: Shows total receivables/payables

---

## Troubleshooting

### Q27: Party balance doesn't match my expectations. What to check?

**A**: 
1. Review all transactions in party ledger
2. Check if any payments were missed
3. Look for:
   - Duplicate entries
   - Missing payments
   - Wrong amounts
   - Incorrect payment methods

---

### Q28: Cash amount doesn't match payment records. Why?

**A**: Possible reasons:
1. Some transactions were Credit (no payment record)
2. Manual adjustments were made
3. Payments were deleted or modified
4. Different time periods in the reports

Compare: Sales/Purchase totals vs Payment record totals

---

### Q29: Can I delete a Cash transaction?

**A**: Depends on permissions, but generally:
- Only if you have admin rights
- Both the transaction and payment record must be deleted
- This affects party balance and inventory
- Better to create a reversal/correction entry

---

### Q30: What if I entered wrong payment method?

**A**: 
1. If not saved yet: Just change it
2. If already saved:
   - For Cash → Credit: Delete payment record (if allowed)
   - For Credit → Cash: Add a payment record
   - Or: Delete and re-enter (if permitted)

Best practice: Double-check before saving!

---

## Best Practices

### Q31: What percentage should be Cash vs Credit?

**A**: No fixed rule, but consider:
- **More Cash**: Better for cash flow, less tracking
- **More Credit**: Better for sales volume, customer relationships

Healthy mix: 60-70% credit with trusted parties, 30-40% cash

---

### Q32: How often should I collect Credit payments?

**A**: Depends on your agreement:
- **Weekly**: Good for regular customers
- **Monthly**: Standard business practice
- **Upon delivery**: For large amounts
- **Net 30/60**: Industry standard terms

Set clear payment terms with each party!

---

### Q33: Should I offer discounts for Cash payment?

**A**: Consider it if:
- You need immediate cash flow
- Customer typically buys on Credit
- Discount is less than interest cost

Example: "2% discount if paid within 7 days"

---

### Q34: How do I manage Credit risk?

**A**: 
1. Set credit limits per party
2. Monitor aging of receivables
3. Follow up on overdue balances
4. Consider stopping Credit for non-payers
5. Review party balances weekly

---

### Q35: What records should I keep?

**A**: 
- All transaction receipts
- Payment confirmations
- Party agreements (credit terms)
- Monthly party statements
- Bank reconciliation records

The system keeps digital records, but keep physical backups!

---

## Quick Reference

### When to Use Cash
✅ Immediate cash needed
✅ Unknown customer/supplier
✅ Small transactions
✅ Want simple accounting
✅ Avoid tracking balances

### When to Use Credit
✅ Regular customers/suppliers
✅ Large transactions
✅ Preserve cash flow
✅ Build relationships
✅ Competitive advantage

### Red Flags
🚩 Balance > 500,000 (too much credit)
🚩 Balance negative (you overpaid?)
🚩 90+ days old balance (collection issue)
🚩 No payment records for Cash transactions
🚩 Ledger doesn't match your records

---

## Getting Help

**Still confused?**
1. Read: `CASH_CREDIT_LOGIC_EXPLANATION.md` (detailed guide)
2. View: `CASH_CREDIT_VISUAL_GUIDE.md` (visual diagrams)
3. Check: Party ledger for your specific case
4. Contact: Your system administrator

**For Developers**:
- See code in: `egg_farm_system/modules/sales.py`
- See code in: `egg_farm_system/modules/purchases.py`
- See ledger: `egg_farm_system/modules/ledger.py`

---

**Last Updated**: 2026-01-28
**Version**: 1.0
