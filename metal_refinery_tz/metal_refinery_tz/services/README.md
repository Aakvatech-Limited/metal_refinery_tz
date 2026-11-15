# Service contract
These services calculate traceability, assay, settlement and refining mass balances. **They do not create ERPNext Stock Entries, Purchase Invoices, Journal Entries or GL Entries.** Cross-document accounting/stock integration requires explicit confirmed business rules and integration tests first.

All fine-metal calculations use Decimal, with six-decimal final weight rounding, and currently require the same UOM within a transaction. Multi-UOM conversion, multi-metal batch accounting, custody splits, reprocessing and partial lot consumption are explicitly outside the current operational MVP.

Submitted document children are immutable; create new amended transactions to correct approved values. Do not assume that a refining lot's available weight is always the lot's original gross weight.
