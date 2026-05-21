from django.test import TestCase
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Invoice, InvoiceDetail, Product, ConsistencyError


class InvoiceTransactionalConsistencyTests(TestCase):
    """
    Test suite for transactional consistency of Invoice totals.
    Ensures that Invoice totals always match the sum of associated InvoiceDetail amounts.
    """

    def setUp(self):
        """Set up test data."""
        # Create test products
        self.product1 = Product.objects.create(
            product_name="Product 1",
            product_price=100.0,
            product_unit="unit"
        )
        self.product2 = Product.objects.create(
            product_name="Product 2",
            product_price=50.0,
            product_unit="unit"
        )
        
        # Create test invoice
        self.invoice = Invoice.objects.create(
            customer="Test Customer",
            contact="1234567890",
            email="test@example.com",
            comments="Test invoice"
        )

    def test_invoice_total_calculation_on_detail_creation(self):
        """Test that invoice total is calculated correctly when details are created."""
        # Create invoice detail
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        
        # Expected total: 100.0 * 2 = 200.0
        self.assertEqual(self.invoice.total, 200.0)

    def test_invoice_total_updates_on_multiple_details(self):
        """Test that invoice total correctly sums multiple detail lines."""
        # Create multiple details
        detail1 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        detail2 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product2,
            amount=3
        )
        
        # Refresh invoice
        self.invoice.refresh_from_db()
        
        # Expected total: (100.0 * 2) + (50.0 * 3) = 200.0 + 150.0 = 350.0
        self.assertEqual(self.invoice.total, 350.0)

    def test_invoice_total_updates_on_detail_update(self):
        """Test that invoice total updates when a detail is modified."""
        # Create initial detail
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total, 200.0)
        
        # Update detail amount
        detail.amount = 5
        detail.save()
        
        # Refresh invoice
        self.invoice.refresh_from_db()
        
        # Expected total: 100.0 * 5 = 500.0
        self.assertEqual(self.invoice.total, 500.0)

    def test_invoice_total_updates_on_detail_deletion(self):
        """Test that invoice total updates when a detail is deleted."""
        # Create multiple details
        detail1 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        detail2 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product2,
            amount=3
        )
        
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total, 350.0)
        
        # Delete first detail
        detail1.delete()
        
        # Refresh invoice
        self.invoice.refresh_from_db()
        
        # Expected total: 50.0 * 3 = 150.0
        self.assertEqual(self.invoice.total, 150.0)

    def test_invoice_total_consistency_validation(self):
        """Test that consistency validation detects mismatches."""
        # Create detail
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Manually corrupt the total (simulate database inconsistency)
        self.invoice.total = 999.0
        self.invoice.save(update_fields=['total'])
        
        # Validation should raise ConsistencyError
        with self.assertRaises(ConsistencyError):
            self.invoice.validate_total_consistency()

    def test_calculate_total_from_details(self):
        """Test the calculate_total_from_details method."""
        # Create details
        InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product2,
            amount=3
        )
        
        # Calculate total
        calculated_total = self.invoice.calculate_total_from_details()
        
        # Expected: (100.0 * 2) + (50.0 * 3) = 350.0
        self.assertEqual(calculated_total, 350.0)

    def test_invoice_detail_get_total_bill_property(self):
        """Test the get_total_bill property of InvoiceDetail."""
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Expected: 100.0 * 2 = 200.0
        self.assertEqual(detail.get_total_bill, 200.0)

    def test_invoice_cascade_delete_updates_total(self):
        """Test that deleting an invoice cascades to details."""
        # Create details
        detail1 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        detail2 = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product2,
            amount=3
        )
        
        invoice_id = self.invoice.id
        
        # Delete invoice
        self.invoice.delete()
        
        # Verify invoice is deleted
        self.assertFalse(Invoice.objects.filter(id=invoice_id).exists())
        
        # Verify details are cascade deleted
        self.assertEqual(InvoiceDetail.objects.filter(invoice_id=invoice_id).count(), 0)

    def test_invoice_total_with_null_product(self):
        """Test invoice total calculation when detail has null product."""
        # Create detail with null product
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=None,
            amount=2
        )
        
        self.invoice.refresh_from_db()
        
        # Total should be 0 since product is null
        self.assertEqual(self.invoice.total, 0.0)

    def test_invoice_total_constraint_prevents_negative(self):
        """Test that database constraint prevents negative totals."""
        # Try to set negative total
        self.invoice.total = -100.0
        
        # This should raise ValidationError due to CHECK constraint
        with self.assertRaises(ValidationError):
            self.invoice.full_clean()

    def test_atomic_transaction_on_detail_save(self):
        """Test that detail save is wrapped in atomic transaction."""
        # Create detail - should be atomic
        with transaction.atomic():
            detail = InvoiceDetail.objects.create(
                invoice=self.invoice,
                product=self.product1,
                amount=2
            )
        
        # Verify total was updated atomically
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total, 200.0)

    def test_update_total_atomic_method(self):
        """Test the update_total_atomic method with row-level locking."""
        # Create details
        InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Call update_total_atomic
        updated_invoice = self.invoice.update_total_atomic()
        
        # Verify total is correct
        self.assertEqual(updated_invoice.total, 200.0)
        
        # Verify consistency
        updated_invoice.validate_total_consistency()

    def test_invoice_detail_timestamps(self):
        """Test that created_at and updated_at timestamps are set."""
        detail = InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Verify timestamps are set
        self.assertIsNotNone(detail.created_at)
        self.assertIsNotNone(detail.updated_at)

    def test_multiple_invoices_independent_totals(self):
        """Test that multiple invoices maintain independent totals."""
        # Create second invoice
        invoice2 = Invoice.objects.create(
            customer="Customer 2",
            contact="9876543210",
            email="test2@example.com"
        )
        
        # Create details for first invoice
        InvoiceDetail.objects.create(
            invoice=self.invoice,
            product=self.product1,
            amount=2
        )
        
        # Create details for second invoice
        InvoiceDetail.objects.create(
            invoice=invoice2,
            product=self.product2,
            amount=3
        )
        
        # Verify independent totals
        self.invoice.refresh_from_db()
        invoice2.refresh_from_db()
        
        self.assertEqual(self.invoice.total, 200.0)
        self.assertEqual(invoice2.total, 150.0)
