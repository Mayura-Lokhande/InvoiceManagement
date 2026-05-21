
# Transactional Consistency for Invoice Totals

## Overview

This document describes the implementation of transactional consistency for the Invoice and InvoiceDetail models in the invoice management system. The feature ensures that Invoice totals always match the sum of associated InvoiceDetail amounts through atomic database operations, row-level locking, and comprehensive validation.

## Architecture

### Key Components

1. **Invoice Model**
   - Denormalized `total` field that stores the sum of associated InvoiceDetail amounts
   - Database CHECK constraint to ensure total is never negative
   - Methods for calculating and validating totals
   - Atomic update mechanism with row-level locking

2. **InvoiceDetail Model**
   - Line item records with product, amount, and timestamps
   - Foreign key to Invoice with CASCADE delete semantics
   - Automatic total synchronization on save/delete operations
   - CHECK constraint to ensure amount is always positive

3. **ConsistencyError Exception**
   - Custom exception raised when Invoice total diverges from calculated sum
   - Includes detailed error message with invoice_id, expected_total, and actual_total

## Implementation Details

### Atomic Transaction Handling

When an InvoiceDetail is created, updated, or deleted, the parent Invoice total is automatically updated atomically:

```python
def save(self, *args, **kwargs):
    """Override save to implement atomic transaction handling."""
    with transaction.atomic():
        # Save the detail record
        super().save(*args, **kwargs)
        
        # Atomically update the parent invoice total
        if self.invoice:
            self.invoice.update_total_atomic()
```

### Row-Level Locking

The `update_total_atomic()` method uses Django's `select_for_update()` to implement pessimistic row-level locking:

```python
def update_total_atomic(self):
    """Atomically update the Invoice total with row-level locking."""
    with transaction.atomic():
        # Row-level locking: SELECT FOR UPDATE
        locked_invoice = Invoice.objects.select_for_update().get(pk=self.pk)
        
        # Recalculate total from all details
        new_total = locked_invoice.calculate_total_from_details()
        
        # Update and validate
        locked_invoice.total = new_total
        locked_invoice.full_clean()
        locked_invoice.save(update_fields=['total'])
        locked_invoice.validate_total_consistency()
        
        return locked_invoice
```

This ensures:
- Only one transaction can modify an Invoice at a time
- Prevents race conditions where concurrent transactions read stale totals
- Guarantees ACID compliance for all invoice total updates

### Database Constraints

The following database-level constraints are enforced:

1. **Invoice Total Non-Negative Constraint**
   ```sql
   CHECK (total >= 0)
   ```

2. **InvoiceDetail Amount Positive Constraint**
   ```sql
   CHECK (amount > 0)
   ```

3. **Referential Integrity**
   - InvoiceDetail.invoice uses CASCADE delete
   - Ensures orphaned detail records cannot exist

### Consistency Validation

The `validate_total_consistency()` method verifies that stored and calculated totals match:

```python
def validate_total_consistency(self):
    """Validate that stored total matches sum of InvoiceDetail amounts."""
    calculated_total = self.calculate_total_from_details()
    
    # Allow small floating-point differences (within 0.01)
    if abs(self.total - calculated_total) > 0.01:
        error_msg = (
            f"Invoice total mismatch: stored_total={self.total}, "
            f"calculated_total={calculated_total}, invoice_id={self.id}"
        )
        logger.error(error_msg)
        raise ConsistencyError(error_msg)
```

## Usage Examples

### Creating an Invoice with Details

```python
from invoice.models import Invoice, InvoiceDetail, Product

# Create invoice
invoice = Invoice.objects.create(
    customer="John Doe",
    contact="1234567890",
    email="john@example.com"
)

# Create details - total is automatically updated atomically
product = Product.objects.get(id=1)
detail = InvoiceDetail.objects.create(
    invoice=invoice,
    product=product,
    amount=2
)

# Invoice total is automatically calculated and locked
invoice.refresh_from_db()
print(invoice.total)  # Displays calculated total
```

### Handling Consistency Errors

```python
from invoice.models import ConsistencyError

try:
    invoice.validate_total_consistency()
except ConsistencyError as e:
    print(f"Consistency error: {e}")
    # Log error for audit purposes
    # Notify administrator
```

### Manual Total Recalculation

```python
# If needed, manually recalculate and update total atomically
updated_invoice = invoice.update_total_atomic()
print(f"Updated total: {updated_invoice.total}")
```

## Transaction Semantics

### ACID Compliance

- **Atomicity**: All detail changes and total updates happen in a single transaction
- **Consistency**: Database constraints and validation ensure valid states
- **Isolation**: Row-level locking prevents concurrent modification conflicts
- **Durability**: All changes are persisted to the database

### Concurrency Handling

The implementation handles concurrent updates through:

1. **Pessimistic Locking**: `SELECT FOR UPDATE` locks the Invoice row
2. **Atomic Transactions**: All operations within `transaction.atomic()` blocks
3. **Validation**: Post-update consistency checks ensure correctness

## Migration

The migration file `0011_add_transactional_consistency.py` applies the following schema changes:

1. Adds CHECK constraint for non-negative invoice total
2. Adds CHECK constraint for positive detail amount
3. Adds `created_at` and `updated_at` timestamp fields to InvoiceDetail
4. Changes InvoiceDetail.invoice foreign key from SET_NULL to CASCADE

To apply the migration:

```bash
python manage.py migrate
```

## Testing

Comprehensive test suite is provided in `invoice/tests.py`:

- `test_invoice_total_calculation_on_detail_creation`: Verifies total calculation on detail creation
- `test_invoice_total_updates_on_multiple_details`: Tests multiple detail line items
- `test_invoice_total_updates_on_detail_update`: Verifies total update when detail is modified
- `test_invoice_total_updates_on_detail_deletion`: Tests total update on detail deletion
- `test_invoice_total_consistency_validation`: Verifies consistency validation
- `test_atomic_transaction_on_detail_save`: Tests atomic transaction behavior
- `test_update_total_atomic_method`: Tests row-level locking mechanism
- And more...

Run tests with:

```bash
python manage.py test invoice.tests.InvoiceTransactionalConsistencyTests
```

## Error Handling

### ConsistencyError

Raised when Invoice total diverges from the sum of InvoiceDetail amounts:

```python
class ConsistencyError(Exception):
    """Raised when Invoice total does not match sum of InvoiceDetail amounts."""
    pass
```

### Logging

All consistency errors are logged with full context:

```python
logger.error(
    f"Invoice total mismatch: stored_total={self.total}, "
    f"calculated_total={calculated_total}, invoice_id={self.id}"
)
```

## Performance Considerations

1. **Row-Level Locking**: Pessimistic locking may impact performance under high concurrency
2. **Constraint Validation**: Database constraints add minimal overhead
3. **Total Recalculation**: Iterating through all details is O(n) where n is number of details
4. **Timestamp Fields**: Minimal storage and query overhead

## Future Enhancements

1. **Optimistic Locking**: Implement version fields for optimistic concurrency control
2. **Caching**: Cache calculated totals to reduce recalculation overhead
3. **Batch Operations**: Optimize bulk detail creation/updates
4. **Audit Trail**: Extend logging to capture all consistency violations with full context
5. **Concurrent Testing**: Add multi-threaded tests to verify locking under actual concurrent load

## Troubleshooting

### Consistency Error on Invoice Creation

If you receive a ConsistencyError during invoice creation:

1. Check that all InvoiceDetail records are properly associated with the Invoice
2. Verify that Product prices are correctly set
3. Ensure no concurrent modifications are happening
4. Check database logs for constraint violations

### Missing Timestamps

If `created_at` or `updated_at` fields are null:

1. Ensure migration `0011_add_transactional_consistency.py` has been applied
2. Run `python manage.py migrate` to apply pending migrations
3. For existing records, set timestamps manually or use data migration

### Cascade Delete Issues

If deleting an Invoice doesn't delete associated details:

1. Verify the foreign key relationship is CASCADE (not SET_NULL)
2. Check that migration `0011_add_transactional_consistency.py` has been applied
3. Ensure no database-level triggers are interfering with cascade delete

## References

- Django Transactions: https://docs.djangoproject.com/en/stable/topics/db/transactions/
- Database Constraints: https://docs.djangoproject.com/en/stable/ref/models/constraints/
- SELECT FOR UPDATE: https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-for-update

